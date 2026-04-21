import pygetwindow as gw
import keyboard
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
                    time.sleep(0.2)


                    keyboard.press_and_release('ctrl+l')
                    time.sleep(0.1)
                    keyboard.write(REDIRECT_URL)
                    keyboard.press_and_release('enter')
                    time.sleep(2.0)
                except Exception as e:
                    print(f"Ошибка: {e}")