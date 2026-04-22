import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional
import winsound  # для звуковых сигналов


class Timer:
    """
    Таймер для управления сессиями работы и отдыха
    """

    def __init__(self, time_work:int = 30, time_break: int = 15):
        """
        time_work - время в работы в минутах
        time_break - время отдыха в минутах
        """
        self.work_duration = time_work * 60  # работа в секундах
        self.break_duration = time_break * 60  # отдых в секундах
        self.is_working = False
        self.is_running = False
        self.timer_thread = None
        self.on_work_start = None  # callback при начале работы
        self.on_work_end = None  # callback при конце работы
        self.on_break_start = None  # callback при начале отдыха
        self.on_break_end = None  # callback при конце отдыха
        self.on_tick = None  # callback каждую секунду

    def set_callbacks(self, on_work_start: Optional[Callable] = None,
                      on_work_end: Optional[Callable] = None,
                      on_break_start: Optional[Callable] = None,
                      on_break_end: Optional[Callable] = None,
                      on_tick: Optional[Callable] = None):
        """Устанавливает функции обратного вызова"""
        self.on_work_start = on_work_start
        self.on_work_end = on_work_end
        self.on_break_start = on_break_start
        self.on_break_end = on_break_end
        self.on_tick = on_tick

    def beep(self):
        """Звуковой сигнал"""
        winsound.Beep(1000, 700)

    def run_session(self, duration: int, session_type: str):
        """
        Запускает одну сессию (работу или отдых)
        duration - длительность в секундах
        session_type - "work" или "break"
        """
        start_time = time.time()
        end_time = start_time + duration

        # Вызываем callback начала сессии
        if session_type == "work" and self.on_work_start:
            self.on_work_start()
        elif session_type == "break" and self.on_break_start:
            self.on_break_start()

        # Обратный отсчет
        while self.is_running and time.time() < end_time:
            remaining = int(end_time - time.time())
            minutes = remaining // 60
            seconds = remaining % 60

            if self.on_tick:
                self.on_tick(session_type, minutes, seconds)

            time.sleep(1)

        # Вызываем callback конца сессии
        if self.is_running:
            self.beep()  # звуковой сигнал
            if session_type == "work" and self.on_work_end:
                self.on_work_end()
            elif session_type == "break" and self.on_break_end:
                self.on_break_end()

    def start(self):
        """Запускает бесконечный цикл работа -> отдых"""
        if self.is_running:
            print("Таймер уже запущен")
            return

        self.is_running = True

        def timer_loop():
            while self.is_running:
                # Рабочая сессия
                self.is_working = True
                self.run_session(self.work_duration, "work")

                if not self.is_running:
                    break

                # Сессия отдыха
                self.is_working = False
                self.run_session(self.break_duration, "break")

        self.timer_thread = threading.Thread(target=timer_loop, daemon=True)
        self.timer_thread.start()

    def stop(self):
        """Останавливает таймер"""
        self.is_running = False
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
        print("Таймер остановлен")

    #будет сделан позже
    def skip_break(self):
        """Пропустить перерыв и начать работу"""
        pass
