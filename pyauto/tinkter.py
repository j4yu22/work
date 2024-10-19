import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pyautogui
import os
from screeninfo import get_monitors
for m in get_monitors():
    print(str(m))

def main():
    # Take a full-screen screenshot
    screenshot = pyautogui.screenshot()

    # Save the screenshot to a temporary file
    temp_screenshot_path = "temp_screenshot.png"
    screenshot.save(temp_screenshot_path)

    # Initialize the dictionary to store the coordinates
    initial = {
        'namebbox': None,
        'providerbbox': None,
        'assistantbbox': None
    }

    colors = ['blue', 'orange', 'green']  # Colors for each box

    def on_drag(event):
        global rect, startX, startY
        curX, curY = event.x, event.y
        canvas.coords(rect, startX, startY, curX, curY)

    def on_click(event):
        global startX, startY, rect
        startX, startY = event.x, event.y
        rect = canvas.create_rectangle(startX, startY, startX, startY, outline='red', width=2)

    def on_key_press(event):
        global boxCount, rect
        if event.keysym == 'Return' and rect:
            x0, y0, x1, y1 = canvas.coords(rect)
            canvas.itemconfig(rect, outline=colors[boxCount])  # Change rectangle color

            # Calculate width and height
            width = x1 - x0
            height = y1 - y0

            # Save the bounding box coordinates with labels
            label = list(initial.keys())[boxCount]
            initial[label] = (int(x0), int(y0), int(width), int(height))
            boxCount += 1

            if boxCount >= 3:  # After drawing three boxes
                print("Selections complete with bbox format:")
                for key, value in initial.items():
                    print(f"{key}: ({value[0]}, {value[1]}, {value[2]}, {value[3]})")
                root.after(500, root.destroy)  # Close the window after a short delay

            rect = None  # Reset rect for the next selection


    root = tk.Tk()
    root.title("Select Areas")
    canvas = tk.Canvas(root, cursor="cross")
    img = ImageTk.PhotoImage(file=temp_screenshot_path)
    canvas.create_image(0, 0, anchor="nw", image=img)
    canvas.pack(fill="both", expand=True)

    canvas.bind('<ButtonPress-1>', on_click)
    canvas.bind('<B1-Motion>', on_drag)
    root.bind('<Return>', on_key_press)

    # Display instructions
    messagebox.showinfo("Instructions", "Please select areas in order: Provider, Assistant, Actual Name. Press 'Enter' to confirm each.")

    print("Starting Tkinter mainloop")
    root.mainloop()
    print("Tkinter mainloop has ended")

    # Cleanup
    os.remove(temp_screenshot_path)

if __name__ == "__main__":
    boxCount = 0  # Count how many boxes have been drawn
    startX, startY, rect = None, None, None  # Initialize variables for rectangle drawing
    main()
