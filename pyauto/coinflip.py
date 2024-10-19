from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import pyautogui
import time

chrome_options = Options()
chrome_options.add_argument('--disable-webusb')
driver_path = r"D:\WinPython\PipModules\chromedriver_win32\chromedriver.exe"
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

driver.get("https://www.google.com/search?q=coin+flip")
image_loc = r"D:\Hulme\pyauto\pyimages\\"

# Wait for the page to load
time.sleep(5)

heads_found = 0
while heads_found < 5:
    time.sleep(2)
    flip_button_location = pyautogui.locateOnScreen(image_loc + 'flipbutton.png', confidence=0.7)
    if flip_button_location:
        pyautogui.click(pyautogui.center(flip_button_location))
    time.sleep(5)
    try:
        if pyautogui.locateOnScreen(image_loc + "heads.png", confidence=0.7):
            heads_found += 1
            print("Heads found :)")
    except pyautogui.ImageNotFoundException:
        print("Could not find the coin. Flipping again.")

driver.quit()