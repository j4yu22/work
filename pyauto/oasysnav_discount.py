"""
pip install pyautogui pytesseract pillow opencv-python screeninfo 
"""
from gc import collect
from mimetypes import init
import os
import re
from re import escape
import pyautogui
import time
import pytesseract
from PIL import Image
from PIL import ImageGrab
import threading
import cv2
import numpy
from datetime import datetime
import json
from google.oauth2.service_account import Credentials
import gspread

# Get the base directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate to the NOSHARING folder and load the merged JSON file
nosharing_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "NOSHARING"))
json_file_path = os.path.join(nosharing_dir, "hulme-keys.json")

# Load the JSON file
with open(json_file_path, 'r') as file:
    keys = json.load(file)

# Extract Google Sheets credentials from the merged JSON
google_creds = keys.get("gsheet-json")

# Set up the Google Sheets API client
creds = Credentials.from_service_account_info(
    google_creds,
    scopes=['https://www.googleapis.com/auth/spreadsheets', 
            'https://www.googleapis.com/auth/drive']
)
client = gspread.authorize(creds)
# Might not need this, we will see
discountAI_key = keys.get("discountAI-key")

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = os.path.join(base_dir, "PipModules", "Tesseract-OCR", "tesseract.exe")
# Set up relative paths for input files and image folder
input_dir = os.path.join(base_dir, "scriptFiles")   # Path to input file
image_folder = os.path.join(base_dir, "pyimages")   # Path to folder with images

#edit bbox coords as needed
initial = {
    'actualname': None,
    'namebbox':  (639, 424, 203, 19),
    'providerbbox': (1004, 782, 197, 25),
    'assistantbbox': (1291, 782, 198, 25),
    'datebbox': (234, 338, 65, 422),
    'collection_method': None,
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


def search_image(image_folder, image_file):
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
        return pyautogui.locateOnScreen(image_path, confidence=0.9) is not None
    except Exception as e:
        pass


def click_image(image_folder, image_file):
    """
    Find the given image on screen and click on it. If the image is not found or an error occurs,
    the function will raise an exception.

    Parameters:
        image_folder (str): The folder where the image is stored.
        image_file (str): The image file to search and click.
    """
    image_path = os.path.join(image_folder, image_file)
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=0.7)
        if location:
            pyautogui.click(location)
        else:
            raise Exception(f"Image '{image_path}' not found on screen.")
    except Exception as e:
        raise Exception(f"Error clicking image '{image_path}': {e}")
    

def collect_data(name):
    """
    Grabs text within the specified bbox and writes it to 'objFound.txt'.

    Parameters:
        line (str): The line of text to append to the data collection.
    """
    for _ in range(4):
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
            output_line = f"{initial['actualname'].strip()}({name.strip()})"
        else:
            output_line = name.strip()

        # Write to the file and print the output
        with open(os.path.join(input_dir, 'objFound.txt'), 'a') as file:
            file.write(f"{output_line}; {provider.strip()}; {assistant.strip()}; {initial['collection_method']}\n")

        print(f"Data collection successful for {output_line}: {provider.strip()}; {assistant.strip()}; {initial['collection_method']}")
        initial['actualname'] = None
    except Exception as e:
        print(e)


def find_info(name, start_date):
    """
    Scrolls through the treatment card looking for a specific object.

    Parameters:
        line (str): The line of text to use for finding information.
    """
    try:
        # pyautogui.press('down')
        for _ in range(4):
            time.sleep(3)
        pyautogui.press('enter')
        for _ in range(4):
            time.sleep(4)
        click_image(image_folder, 'treatment_card.png')
        for _ in range(4):
            time.sleep(7)

        month_image = parse_date(start_date)
        obj_found = False
        scrolled = False
        x = 0
        print(month_image)

        while scrolled == False and x < 16 and obj_found == False:
            if x == 0:
                pyautogui.press('pageup')
            month = None
            #initial check for med warning thing
            if search_image(image_folder, 'redCross.png'):
                pyautogui.press('enter')
                if search_image(image_folder, 'med_ok.png'):
                    click_image(image_folder, 'med_ok.png')
            for _ in range(4):
                time.sleep(0.5)
            #check by date first
            month_path = os.path.join(image_folder, month_image)
            try:
                month = pyautogui.locateCenterOnScreen(month_path, region=initial['datebbox'], confidence=0.90)
                print('searching by date for ' + month_image)
            except:
                pass
            if month:
                y = 0
                pyautogui.click(month)
                for _ in range(4):
                    time.sleep(0.5)
                if search_image(image_folder, 'entry_detail.png'):
                    click_image(image_folder, 'entry_detail.png')
                    for _ in range(4):
                        time.sleep(0.5)
                while search_image(image_folder, 'empty.png') and y < 10:
                    pyautogui.press('down')
                    y += 1
                    for _ in range(4):
                        time.sleep(0.5)
                if y > 9: 
                    while search_image(image_folder, 'empty.png'):
                        pyautogui.press('up')
                        for _ in range(4):
                            time.sleep(0.5)
                initial['collection_method'] = 'date'
                collect_data(name)
                obj_found = True
                print(month_image + "found by date")
                break
            #then by recall appt
            if search_image(image_folder, 'recall.png'):
                click_image(image_folder, 'recall.png')
                for _ in range(4):
                    time.sleep(0.5)
                initial['collection_method'] = 'recall'
                collect_data(name)
                obj_found = True
                print(month_image + "found by recall")
                break
            #lastly by NPE if others fail
            if search_image(image_folder, 'NPE.png'):
                click_image(image_folder, 'NPE.png')
                for _ in range(4):
                    time.sleep(0.5)
                initial['collection_method'] = 'NPE'
                collect_data(name)
                obj_found = True
                print(month_image + "found by NPE")
                break

            pyautogui.press("pageup")
            x += 1
            
            try:
                pyautogui.locateOnScreen(os.path.join(image_folder, 'scrolledUp.png'), confidence=0.9)
                scrolled = True            
            except:
                pass
            if obj_found == True:
                break

        if not obj_found:
            with open(os.path.join(input_dir, 'objNotFound.txt'), 'a') as file:
                file.write(name + '\n')
            print(f"{name.strip()} -- Obj not found.")

        if search_image(image_folder, 'close.png'):
            click_image(image_folder, "close.png")
            for _ in range(4):
                time.sleep(1)
        else:
            #if alt+f4 works and close is not an option, uncomment line below
             #pyautogui.hotkey('alt', 'f4')
            pass
        for _ in range(4):
            time.sleep(1)

    except Exception as e:
        print(e)


def parse_date(start_date):
    """
    Converts a date string to a string representing the first three letters of the month followed by .png.

    Parameters:
        start_date (str): The start date in the format 'm/d/yyyy'.

    Returns:
        str: A string representing the first three letters of the month from the start date, followed by .png.
    """
    date_obj = datetime.strptime(start_date, '%m/%d/%Y')
    month_abbr = date_obj.strftime('%b').lower()
    return f"{month_abbr}.png"


def process_names(input_dir):
    """
    Process each name in the given file.

    Parameters:
        input_dir (str): The directory where the input file is located.
    """
    try:
        with open(os.path.join(input_dir, "input.txt"), 'r') as file:
            for line in file:
                initial['collection_method'] = None
                line = line.strip()
                match = re.search(r"\d", line)
                if match:
                    name = line[:match.start()].strip()
                    start_date = line[match.start():].strip()
                    reformatted_name = reformat_name(name)
                if search_image(image_folder, 'fix.png'):
                    clear = False
                    while clear == False:
                        click_image(image_folder, 'fix.png')
                        for _ in range(4):
                            time.sleep(1)
                        if search_image(image_folder, 'redCross.png'):
                            pyautogui.press('enter')
                        if search_image(image_folder, 'close.png'):
                            click_image(image_folder, 'close.png')
                            clear = True
                        # else:
                        #     pyautogui.hotkey('alt', 'f4')

                try:
                    found_location = pyautogui.locateOnScreen(os.path.join(image_folder, 'tab.png'), region=(568, 1006, 893, 50), confidence=0.8)
                    center_x, center_y = pyautogui.center(found_location)
                    clear = False
                    while clear == False:
                        pyautogui.click(center_x, center_y)
                        for _ in range(4):
                            time.sleep(1)
                        if search_image(image_folder, 'redCross.png'):
                            if search_image(image_folder, 'med_ok.png'):
                                click_image(image_folder, 'med_ok.png')
                            else:    
                                pyautogui.press('enter')
                        if search_image(image_folder, 'close.png'):
                            click_image(image_folder, 'close.png')
                            clear = True
                        # else:
                        #     pyautogui.hotkey('alt', 'f4')
                except:
                    pass

                # if search_image(image_folder, 'ignore.png'):
                #     click_image(image_folder, 'ignore.png')
                #  # for _ in 4ange(2):  
                #  time.sleep(1)
                click_image(image_folder, 'any.png')
                for _ in range(4):
                    time.sleep(2)
                pyautogui.write(reformatted_name)
                for _ in range(4):
                    time.sleep(0.5)
                pyautogui.press('enter')
                for _ in range(4):
                    time.sleep(1)
                nameFound = False
                try:
                    for _ in range(4):
                        time.sleep(0.1)
                    pyautogui.locateOnScreen(os.path.join(image_folder, 'name_found.png'), confidence=0.9)
                    nameFound = True

                except:
                    pass

                if nameFound == True:
                    find_info(name, start_date)
                elif nameFound == False:
                    for _ in range(4):
                        time.sleep(1)
                    pyautogui.hotkey('ctrl', 'a')
                    for _ in range(4):
                        time.sleep(0.1)
                    pyautogui.press('backspace')
                    short_name = truncate_name(reformatted_name)
                    pyautogui.write(short_name)
                    for _ in range(4):
                        time.sleep(0.5)
                    pyautogui.press('enter')
                    for _ in range(4):
                        time.sleep(0.5)

                    try:    
                        pyautogui.locateOnScreen(os.path.join(image_folder, 'name_found.png'), confidence=0.9)
                        bbox = initial['namebbox']  # Coordinates for the actual name in blue
                        screenshot = pyautogui.screenshot(region=bbox)
                        initial['actualname'] = pytesseract.image_to_string(screenshot)
                        find_info(name, start_date)
                    except:
                        with open(os.path.join(input_dir, 'notFound.txt'), 'a') as file:
                            file.write(line + "\n")
                        print(f"{line.strip()} -- Not Found")
                        pyautogui.press('esc')
                        for _ in range(4):
                            time.sleep(1)

                else:
                    print('something goofy happened. nameFound = ' + nameFound)
    except Exception as e:
        print(e)


def check_for_ignore():
    while True:
        try:
            search_image(image_folder, 'ignore.png')
            click_image(image_folder, 'ignore.png')
        except:
            pass
        for _ in range(4):
            time.sleep(0.5)

def main():
    # Start the thread to check for ignore.png
    ignore_thread = threading.Thread(target=check_for_ignore, daemon=True)
    ignore_thread.start()

    process_names(input_dir)

if __name__ == "__main__":
    main()