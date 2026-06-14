import pygetwindow as gw
import keyboard
import time
import winsound
import threading
from block_structure.config import get_blocked_sites, REDIRECT_URL, get_mode, MODE_HARD, WARNING_COOLDOWN
from PySide6.QtCore import QObject, Signal

# Глобальные переменные
last_warning_time = 0
warning_lock = threading.Lock()

# Сигнал для показа предупреждения в главном потоке
class WarningSignal(QObject):
    show_warning = Signal(str)

warning_signal = WarningSignal()

def set_app_instance(app):
    """Установить ссылку на главное приложение и подключить сигнал"""
    warning_signal.show_warning.connect(app.show_floating_warning)


def show_site_warning(site_name):
    """Показать предупреждение через сигнал в главный поток"""
    global last_warning_time

    with warning_lock:
        current_time = time.time()
        if current_time - last_warning_time < WARNING_COOLDOWN:
            return

        last_warning_time = current_time

    winsound.Beep(1000, 200)
    winsound.Beep(800, 200)

    # Отправляем сигнал в главный поток
    warning_signal.show_warning.emit(site_name)


def block_site_hard(window):
    """Жесткая блокировка сайта - переадресация на страницу блокировки"""
    try:
        window.activate()
        time.sleep(0.3)

        keyboard.press_and_release('ctrl+l')
        time.sleep(0.2)

        keyboard.write(REDIRECT_URL)
        time.sleep(0.2)

        keyboard.press_and_release('enter')
        time.sleep(0.3)

    except Exception as e:
        print(f"Ошибка блокировки: {e}")


def redirect_browser():
    """Блокировка сайтов в зависимости от режима"""
    try:
        current_mode = get_mode()
        blocked_sites = get_blocked_sites()

        for window in gw.getAllWindows():
            title = window.title.lower()
            window_title_full = window.title

            if "block_page" in title:
                continue

            is_blocked = False
            blocked_site = ""
            for site in blocked_sites:
                if site.lower() in title:
                    is_blocked = True
                    blocked_site = site
                    break

            if is_blocked:
                browser_names = ["Chrome", "Firefox", "Edge", "Opera", "Yandex", "Brave", "Chromium", "Safari"]
                is_browser = any(b in window_title_full for b in browser_names)

                if is_browser:
                    if current_mode == MODE_HARD:
                        block_site_hard(window)
                    else:
                        show_site_warning(blocked_site)

    except Exception as e:
        print(f"Ошибка в redirect_browser: {e}")