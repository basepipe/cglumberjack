import pyautogui
import threading
import time
import pyperclip
from cglumberjack.cgl.core.utils.general import cgl_execute


premiere_open = False
# Launch Adobe Premiere


def launch_premiere():
    premiere_path = r"C:\Program Files\Adobe\Adobe Premiere Pro 2020\Adobe Premiere Pro.exe"
    cgl_execute(premiere_path)


def launch_fcp_xml(folder_path, file, wait=9):
    thread = threading.Thread(target=launch_premiere)
    thread.start()
    time.sleep(9)
    pyautogui.keyDown('ctrl')
    pyautogui.press('o')
    pyautogui.keyUp('ctrl')
    pyperclip.copy(folder_path)
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('enter')
    pyautogui.press('backspace')
    # paste the folder path
    pyautogui.keyDown('ctrl')
    pyautogui.press('v')
    pyautogui.keyUp('ctrl')
    pyautogui.press('enter')

    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')

    pyperclip.copy(file)
    pyautogui.keyDown('ctrl')
    pyautogui.press('v')
    pyautogui.keyUp('ctrl')

    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('enter')


