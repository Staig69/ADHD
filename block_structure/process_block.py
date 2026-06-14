import psutil
import time
import winsound
import threading
from block_structure.config import get_blocked_apps, get_mode, MODE_HARD, WARNING_COOLDOWN
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
    warning_signal.show_warning.connect(app.show_app_floating_warning)


def show_app_warning(app_name):
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
    warning_signal.show_warning.emit(app_name)


def kill_app_hard(app_name, proc):
    """Жесткое закрытие приложения"""
    try:
        proc.kill()
    except Exception as e:
        print(f"Ошибка закрытия {app_name}: {e}")


def kill_apps():
    """Блокировка приложений в зависимости от режима"""
    current_mode = get_mode()
    blocked_apps = get_blocked_apps()

    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name']
            if proc_name and proc_name.lower() in [app.lower() for app in blocked_apps]:
                if current_mode == MODE_HARD:
                    kill_app_hard(proc_name, proc)
                else:
                    show_app_warning(proc_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            pass

    time.sleep(1)