from mimetypes import init
import os
from re import escape
import pyautogui
import time
import pytesseract
from PIL import Image
import threading

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"D:\WinPython\PipModules\Tesseract-OCR\tesseract.exe"

# Paths setup
input_dir = r"D:\Hulme\pyauto\scriptFiles"   # Path to input file
image_folder = r"D:\Hulme\pyauto\pyimages"   # Path to folder with images

#edit bbox coords as needed
#                 insertnamebbox: (669, 424, 171, 19)
# default values: insertproviderbbox: (1005, 800, 197, 15)
#                 insertassistantbbox: (1294, 802, 193, 14)
insertnamebbox = (669, 424, 840, 443)
insertproviderbbox = (1011, 783, 1210, 801)
insertassistantbbox = (1297, 784, 1496, 800)


name_x1 = insertnamebbox[0]
name_y1 = insertnamebbox[1]
name_x2 = insertnamebbox[2] - insertnamebbox[0]
name_y2 = insertnamebbox[3] - insertnamebbox[1]

provider_x1 = insertproviderbbox[0]
provider_y1 = insertproviderbbox[1]
provider_x2 = insertproviderbbox[2] - insertproviderbbox[0]
provider_y2 = insertproviderbbox[3] - insertproviderbbox[1]

assistant_x1 = insertassistantbbox[0]
assistant_y1 = insertassistantbbox[1]
assistant_x2 = insertassistantbbox[2] - insertassistantbbox[0]
assistant_y2 = insertassistantbbox[3] - insertassistantbbox[1]

initial = {
    'actualname': None,
    'namebbox': (name_x1, name_y1, name_x2, name_y2),
    'providerbbox': (provider_x1, provider_y1, provider_x2, provider_y2),
    'assistantbbox': (assistant_x1, assistant_y1, assistant_x2, assistant_y2),
}

def reformat_name(name):
    """
    Reformat name from 'Doe, John' to 'doe,john'.

    Parameters:
        name (str): The name to reformat.

    Returns:
        str: The reformatted name.
    """
    parts = name.strip().split(", ")
    if len(parts) == 2:
        return f"{parts[0].lower()},{parts[1].lower()}"
    return name.lower()


def truncate_name(reformatted_name):
    """
    Truncate both parts of the reformatted name to their first three characters.

    Parameters:
        reformatted_name (str): The reformatted name to truncate.

    Returns:
        str: The truncated name.
    """
    parts = reformatted_name.split(',')
    if len(parts) == 2:
        surname, firstname = parts
        truncated_surname = surname[:3]
        truncated_firstname = firstname[:3]
        return f"{truncated_surname},{truncated_firstname}"
    return reformatted_name[:3]


def search_image(image_folder, image_file, confidence=0.8):
    """
    Searches the screen for an image.

    Parameters:
        image_folder (str): The folder where the image is stored.
        image_file (str): The image file to search for.

    Returns:
        bool: True if the image is found, False otherwise.
    """
    try:
        image_path = os.path.join(image_folder, image_file)
        return pyautogui.locateOnScreen(image_path, confidence) is not None
    except Exception as e:
        pass


def click_image(image_folder, image_file, confidence=0.7):
    """
    Find the given image on screen and click on it. If the image is not found or an error occurs,
    the function will raise an exception.

    Parameters:
        image_folder (str): The folder where the image is stored.
        image_file (str): The image file to search and click.
    """
    image_path = os.path.join(image_folder, image_file)
    try:
        # Use locateOnScreen with confidence and find the center manually
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location:
            center_x, center_y = location.left - location.width / 2, location.top - location.height / 2
            pyautogui.click(center_x, center_y)
        else:
            print(f"Image '{image_path}' not found on screen.")
    except Exception as e:
        print(f"Error clicking image '{image_path}': {e}")

def collect_data(line):
    """
    Grabs text within the specified bbox and writes it to 'objFound.txt'.

    Parameters:
        line (str): The line of text to append to the data collection.
    """
    time.sleep(1)
    try:
        bbox1 = initial['providerbbox']  # Coordinates for the first screenshot
        screenshot1 = pyautogui.screenshot(region=bbox1)
        provider = pytesseract.image_to_string(screenshot1)

        bbox2 = initial['assistantbbox']  # Coordinates for the second screenshot
        screenshot2 = pyautogui.screenshot(region=bbox2)
        assistant = pytesseract.image_to_string(screenshot2)

        # Check if 'actualname' has been set and use it in addition to 'line'
        if initial['actualname']:
            output_line = f"{initial['actualname'].strip()}({line.strip()})"
        else:
            output_line = line.strip()

        # Write to the file and print the output
        with open(os.path.join(input_dir, 'objFound.txt'), 'a') as file:
            file.write(f"{output_line}; {provider.strip()}; {assistant.strip()}\n")

        print(f"Data collection successful for {output_line}: {provider.strip()}; {assistant.strip()}")
        initial['actualname'] = None
    except Exception as e:
        print(e)


def find_info(line):
    """
    Scrolls through the treatment card looking for a specific object.

    Parameters:
        line (str): The line of text to use for finding information.
    """
    try:
        pyautogui.press('down')
        pyautogui.press('enter')
        time.sleep(4)
        click_image(image_folder, 'treatment_card.png')
        time.sleep(7)

        obj_found = False
        scrolled = False
        x = 0
        while scrolled == False and x < 16:
            if search_image(image_folder, 'redCross.png'):
                pyautogui.press('enter')

            # if search_image(image_folder, 'ignore.png'):
            #     click_image(image_folder, 'ignore.png')
            #     time.sleep(1)
            for _ in range(5):
                pyautogui.press('up')
            time.sleep(0.1)
            if search_image(image_folder, 'blank.png'):
                time.sleep(0.1)
                pyautogui.press('down')
            time.sleep(0.1)
            confirm = input("Collect data?\n")
            collect_data(line)
            obj_found = True
            time.sleep(1)
            break

        if not obj_found:
            with open(os.path.join(input_dir, 'objNotFound.txt'), 'a') as file:
                file.write(line)
            print(f"{line.strip()} -- Obj not found.")

        if search_image(image_folder, 'close.png'):
            click_image(image_folder, "close.png")
            time.sleep(1)
        else:
            #if alt-f4 works and close is not an option, uncomment line below
            #pyautogui.hotkey('alt', 'f4')
            pass
        time.sleep(1)

    except Exception as e:
        print(e)


def process_names(input_dir):
    """
    Process each name in the given file.

    Parameters:
        input_dir (str): The directory where the input file is located.
    """
    try:
        with open(os.path.join(input_dir, "input.txt"), 'r') as file:
            for line in file:
                reformatted_name = reformat_name(line)
                # if search_image(image_folder, 'ignore.png'):
                #     click_image(image_folder, 'ignore.png')
                #     time.sleep(1)
                click_image(image_folder, 'any.png', confidence=0.9)
                time.sleep(2)
                pyautogui.write(reformatted_name)
                pyautogui.press('enter')
                time.sleep(1)
                nameFound = False
                try:
                    time.sleep(0.1)
                    pyautogui.locateOnScreen(os.path.join(image_folder, 'name_found.png'), confidence=0.9)
                    nameFound = True

                except:
                    pass

                if nameFound == True:
                    find_info(line)
                elif nameFound == False:
                    time.sleep(1)
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('backspace')
                    short_name = truncate_name(reformatted_name)
                    pyautogui.write(short_name)
                    pyautogui.press('enter')
                    time.sleep(0.5)

                    try:    
                        pyautogui.locateOnScreen(os.path.join(image_folder, 'name_found.png'), confidence=0.9)
                        bbox = initial['namebbox']  # Coordinates for the actual name in blue
                        screenshot = pyautogui.screenshot(region=bbox)
                        initial['actualname'] = pytesseract.image_to_string(screenshot)
                        find_info(line)
                    except:
                        with open(os.path.join(input_dir, 'notFound.txt'), 'a') as file:
                            file.write(line)
                        print(f"{line.strip()} -- Not Found")
                        pyautogui.press('esc')
                        time.sleep(1)

                else:
                    print('something goofy happened. nameFound = ' - nameFound)
    except Exception as e:
        print(e)


def check_for_ignore():
    while True:
        if search_image(image_folder, 'ignore.png'):
            click_image(image_folder, 'ignore.png')
        time.sleep(1)  # Check every second


def main():
    # Start the thread to check for ignore.png
    ignore_thread = threading.Thread(target=check_for_ignore, daemon=True)
    ignore_thread.start()

    process_names(input_dir)

if __name__ == "__main__":
    main()