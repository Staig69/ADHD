import pygetwindow as gw
import pyautogui
import pyperclip
import time
from block_structure.config import BLOCK_SITES, REDIRECT_URL


def redirect_browser():
    for window in gw.getAllWindows():
        title = window.title.lower()

        if "block_page" in title:
            continue

        if any(s.lower() in title for s in BLOCK_SITES):
            if any(b in window.title for b in ["Chrome", "Firefox", "Edge", "Opera"]):
                try:
                    window.activate()
                    time.sleep(0.5)

                    pyperclip.copy(REDIRECT_URL)

                    pyautogui.press('f6')
                    time.sleep(0.1)

                    pyautogui.hotkey('shift', 'insert')
                    pyautogui.press('enter')
                except Exception as e:
                    print(f"Ошибка: {e}")