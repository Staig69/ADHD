import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taskSplitter import split_tasks
from block_structure.process_block import kill_apps
from block_structure.sites_block import redirect_browser
from timer import Timer

import winsound


class ADHD:

    def __init__(self):
        self.timer = Timer()
        self.is_blocking = False
        self.current_subtask = ""
        self.subtasks_list = []
        self.completed_subtasks = []  # Список выполненных подзадач
        self.current_subtask_index = 0
        self.original_task = ""  # Сохраняем исходную задачу

        # Настраиваем callback'и таймера
        self.timer.set_callbacks(
            on_work_start=self.on_work_start,
            on_work_end=self.on_work_end,
            on_break_start=self.on_break_start,
            on_break_end=self.on_break_end,
            on_tick=self.on_tick
        )

        # Настройки времени
        self.timer.work_duration = 30 * 60  # 30 минут работы
        self.timer.break_duration = 15 * 60  # 15 минут отдыха

    def on_work_start(self):
        """Действия при начале работы"""
        print("\n")
        print(f"НАЧАЛО РАБОТЫ над подзадачей {self.current_subtask_index + 1}/{len(self.subtasks_list)}")
        print(f"{self.current_subtask}")
        print(f"{self.timer.work_duration // 60} минут до перерыва")
        print("\n")

        # Включаем блокировку отвлекающих факторов
        self.start_blocking()

        # Звуковой сигнал начала работы
        winsound.Beep(2000, 300)

    def on_work_end(self):
        """Действия при окончании работы"""
        print(f"\n{'=' * 50}")
        print(f"ЗАКОНЧЕНА подзадача: {self.current_subtask}")
        print(f"{'=' * 50}\n")

        # Добавляем выполненную подзадачу в список
        if self.current_subtask not in self.completed_subtasks:
            self.completed_subtasks.append(self.current_subtask)

        # Выключаем блокировку
        self.stop_blocking()

        # Звуковой сигнал окончания работы
        winsound.Beep(1500, 500)
        winsound.Beep(2000, 500)

    def on_break_start(self):
        """Действия при начале перерыва"""
        print(f"\n")
        print(f"ПЕРЕРЫВ {self.timer.break_duration // 60} минут")
        print(f"Отдохните, вы заслужили!")
        print(f"\n")

        # Звуковой сигнал начала перерыва
        winsound.Beep(1000, 300)

    def on_break_end(self):
        """Действия при окончании перерыва"""
        print(f"\n")
        print(f"ПЕРЕРЫВ ЗАКОНЧЕН! Возвращаемся к работе")
        print(f"\n")

        # Звуковой сигнал окончания перерыва
        winsound.Beep(2000, 300)

    def on_tick(self, session_type: str, minutes: int, seconds: int):
        """Каждую секунду - обновление таймера"""
        # Раскомментируйте для отображения таймера
        if session_type == "work":
            print(f"\r Работаем: {minutes:02d}:{seconds:02d}", end="")
        else:
            print(f"\r Отдыхаем: {minutes:02d}:{seconds:02d}", end="")

    def start_blocking(self):
        """Запускает фоновую блокировку сайтов и приложений"""
        if self.is_blocking:
            return

        self.is_blocking = True

        def block_loop():
            """Бесконечный цикл блокировки"""
            while self.is_blocking:
                try:
                    redirect_browser()
                    kill_apps()
                except Exception as e:
                    print(f"Ошибка блокировки: {e}")
                time.sleep(2)

        self.blocking_thread = threading.Thread(target=block_loop, daemon=True)
        self.blocking_thread.start()
        print("Блокировка отвлекающих факторов ВКЛЮЧЕНА")

    def stop_blocking(self):
        """Останавливает блокировку"""
        self.is_blocking = False
        print("Блокировка отвлекающих факторов ВЫКЛЮЧЕНА")

    def replane(self):
        """
        Перепланирование оставшихся задач
        """
        print("ПЕРЕПЛАНИРОВАНИЕ ЗАДАЧ")

        # Формируем список выполненных задач
        completed_text = ", ".join(self.completed_subtasks) if self.completed_subtasks else "пока нет"

        print(f"Выполненные подзадачи: {completed_text}")
        print(f"Оставшиеся подзадачи: {len(self.subtasks_list) - len(self.completed_subtasks)} шт.")

        print("\nОтправляем запрос для перепланирования...")

        new_subtasks = split_tasks(self.original_task, self.timer.work_duration, completed_text)

        if new_subtasks and not new_subtasks[0].startswith("Произошла ошибка"):
            # Очищаем новые подзадачи от возможных дубликатов выполненных
            cleaned_subtasks = []
            for sub in new_subtasks:
                # Проверяем, не является ли эта подзадача уже выполненной
                is_already_done = False
                for done in self.completed_subtasks:
                    if done.lower() in sub.lower() or sub.lower() in done.lower():
                        is_already_done = True
                        break
                if not is_already_done and sub not in self.completed_subtasks:
                    cleaned_subtasks.append(sub)

            # Обновляем список подзадач (выполненные + новые)
            self.subtasks_list = self.completed_subtasks + cleaned_subtasks

            print(f"\nНейросеть перепланировала задачи!")
            print(f"Новый план ({len(self.subtasks_list)} подзадач):")
            for i, sub in enumerate(self.subtasks_list, 1):
                if sub in self.completed_subtasks:
                    print(f"  {i}. {sub} (выполнено)")
                else:
                    print(f"  {i}. {sub}")

            return True
        else:
            print(f"\nОшибка при перепланировании: {new_subtasks[0] if new_subtasks else 'Неизвестная ошибка'}")
            print("Продолжаем с текущим планом...")
            return False

    def run_subtask_with_menu(self):
        """
        Запускает одну подзадачу с меню после завершения
        Возвращает: "next" - перейти к следующей, "replan" - перепланировать, "stop" - остановить
        """
        print(f"\n")
        print(f"ТЕКУЩАЯ ПОДЗАДАЧА {self.current_subtask_index + 1}/{len(self.subtasks_list)}")
        print(f"{self.current_subtask}")
        print(f"")
        print(f"Настройки: {self.timer.work_duration // 60} мин работы / {self.timer.break_duration // 60} мин отдыха")

        # Запускаем рабочую сессию
        print("\nНАЧИНАЕМ РАБОТУ...")

        # Включаем блокировку и запускаем таймер работы
        self.is_blocking = True
        self.on_work_start()

        # Таймер обратного отсчета
        work_seconds = self.timer.work_duration
        for remaining in range(work_seconds, 0, -1):
            minutes = remaining // 60
            seconds = remaining % 60
            print(f"\rРаботаем: {minutes:02d}:{seconds:02d}", end="")

            # Продолжаем блокировать
            if self.is_blocking:
                try:
                    redirect_browser()
                    kill_apps()
                except:
                    pass

            time.sleep(1)

        # Конец работы
        self.on_work_end()
        self.is_blocking = False

        # Меню после работы
        print("\n")
        print("ЧТО ДЕЛАЕМ ДАЛЬШЕ?")
        print("1. Начать перерыв (рекомендуется)")
        print("2. Сразу следующую подзадачу (без перерыва)")
        print("3. Изменить время работы/отдыха")
        print("4. Закончить сессию")

        choice = input("\nВаш выбор (1-4): ").strip()

        match choice:
            case "1":
                print("\nПЕРЕРЫВ...")
                break_seconds = self.timer.break_duration
                for remaining in range(break_seconds, 0, -1):
                    minutes = remaining // 60
                    seconds = remaining % 60
                    print(f"\rОтдыхаем: {minutes:02d}:{seconds:02d}", end="")
                    time.sleep(1)
                self.on_break_end()
                return "next"

            case "2":
                # Без перерыва
                print("\nПропускаем перерыв!")
                return "next"

            case "3":
                # Изменение времени
                try:
                    new_work = int(input(f"Новое время работы (мин) [{self.timer.work_duration // 60}]: ") or self.timer.work_duration // 60)
                    new_break = int(input(f"Новое время отдыха (мин) [{self.timer.break_duration // 60}]: ") or self.timer.break_duration // 60)
                    self.timer.work_duration = new_work * 60
                    self.timer.break_duration = new_break * 60
                    print(f"Настройки обновлены: {new_work} мин работы / {new_break} мин отдыха")

                    return "replan"
                except:
                    print("Ошибка ввода")
                    return "next"
            case "4":
                return "stop"
        return "next"

    def run_subtasks(self, subtasks: list):
        """Запускает последовательное выполнение подзадач с возможностью перепланирования"""
        self.subtasks_list = subtasks
        self.completed_subtasks = []
        self.current_subtask_index = 0

        while self.current_subtask_index < len(self.subtasks_list):
            # Пропускаем уже выполненные задачи
            if self.subtasks_list[self.current_subtask_index] in self.completed_subtasks:
                self.current_subtask_index += 1
                continue

            self.current_subtask = self.subtasks_list[self.current_subtask_index]

            # Ждем, пока пользователь готов начать
            input(f"\nГотовы начать подзадачу {self.current_subtask_index + 1}/{len(self.subtasks_list)}? Нажмите Enter...")

            # Запускаем подзадачу с меню
            result = self.run_subtask_with_menu()

            if result == "next":
                # Переходим к следующей подзадаче
                self.current_subtask_index += 1

            elif result == "replan":
                # После перепланирования начинаем сначала с обновленным списком
                if self.replane():
                    self.current_subtask_index = 0
                continue

            elif result == "stop":
                print("\nСессия прервана пользователем")
                break

        if self.current_subtask_index >= len(self.subtasks_list):
            print(f"\n")
            print(f"ПОЗДРАВЛЯЮ! Все {len(self.subtasks_list)} подзадач выполнены!")

    def start(self):
        """Главный метод запуска приложения"""
        print("\n")
        print("ДОБРО ПОЖАЛОВАТЬ В ПОМОЩНИК ДЛЯ ЛЮДЕЙ С СДВГ")

        # Получаем задачу от пользователя
        self.original_task = input("\nОпишите вашу задачу: ")

        # Получаем время на задачу
        try:
            self.timer.work_duration = int(input("Сколько минут у вас есть на эту задачу? (по умолч. 30): ") or 30)
            self.timer.work_duration *= 60
        except:
            self.timer.work_duration = 60*30

        print("\nНейросеть разбивает задачу на подзадачи...")

        # Разбиваем задачу через нейросеть
        subtasks = split_tasks(self.original_task, self.timer.work_duration)

        if subtasks and not subtasks[0].startswith("Произошла ошибка"):
            print(f"\nНейросеть разбила задачу на {len(subtasks)} подзадач:")
            for i, sub in enumerate(subtasks, 1):
                print(f"  {i}. {sub}")

            # Запускаем выполнение подзадач
            self.run_subtasks(subtasks)
        else:
            print(f"\nОшибка при разбиении задачи: {subtasks[0] if subtasks else 'Неизвестная ошибка'}")


if __name__ == "__main__":
    # Проверка прав администратора для блокировки
    import ctypes

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("✅ Запущено с правами администратора")
        else:
            print("⚠️ ВНИМАНИЕ: Для блокировки сайтов запустите программу от имени администратора!")
            print("   Некоторые функции могут работать некорректно.\n")
    except:
        print("⚠️ Не удалось проверить права администратора")

    assistant = ADHD()

    try:
        assistant.start()
    except KeyboardInterrupt:
        print("\n\n👋 Программа остановлена. Отключаем блокировки...")
        assistant.stop_blocking()
        print("До свидания! Не забывайте делать перерывы 😊")