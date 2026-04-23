import threading
import time
import winsound
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taskSplitter import split_tasks
from block_structure.process_block import kill_apps
from block_structure.sites_block import redirect_browser

# об этом написано щее ниже, но вся инициализация работает чисто на gui-шку
# чтоб ничего не зависало и работало стабильно
class ADHD_Backend:
    def __init__(self):

        self.is_blocking = False
        self.current_subtask = ""
        self.subtasks_list = []
        self.completed_subtasks = []

        # вообще, изначальное значение времени здесь не нужно, так как при нажатии на кнопочки
        # оно автоматически передается в функцию ниже, но для перестраховки пойдет (и на случай тестов, если где-то
        # будет дыра)
        self.work_duration = 1
        self.break_duration = 1
        self.original_task = ""

    # работает отдельно в потоках, чтобы приложение на зависло и не превратилось в безрукого инвалида
    def start_blocking(self):
        if self.is_blocking:
            return

        self.is_blocking = True

        def block_loop():
            while self.is_blocking:
                try:
                    redirect_browser()
                    kill_apps()
                except Exception:
                    pass
                time.sleep(2)

        self.blocking_thread = threading.Thread(target=block_loop, daemon=True)
        self.blocking_thread.start()

    def stop_blocking(self):
        self.is_blocking = False

    # gui вызывает этот метод и передает в него выбранные пользователем данные о времени отдыха и
    def generate_initial_plan(self, task_text, work_minutes, break_minutes):
        self.original_task = task_text
        self.work_duration = work_minutes
        self.break_duration = break_minutes

        # вызов нейронки для формирования задач
        subtasks = split_tasks(self.original_task, self.work_duration)

        if subtasks and not subtasks[0].startswith("Произошла ошибка"):
            self.subtasks_list = subtasks
            return True, self.subtasks_list
        return False, subtasks


    # все теперь делается через общение с gui, консольный ввод и вывод можно добавлять на тестах для выявления неполадок
    def replane_tasks(self):
        completed_text = ", ".join(self.completed_subtasks) if self.completed_subtasks else "пока нет"
        new_subtasks = split_tasks(self.original_task, self.work_duration, completed_text)

        if new_subtasks and not new_subtasks[0].startswith("Произошла ошибка"):
            cleaned_subtasks = []
            for sub in new_subtasks:
                is_already_done = False
                for done in self.completed_subtasks:
                    if done.lower() in sub.lower() or sub.lower() in done.lower():
                        is_already_done = True
                        break
                if not is_already_done and sub not in self.completed_subtasks:
                    cleaned_subtasks.append(sub)

            self.subtasks_list = self.completed_subtasks + cleaned_subtasks
            return True, self.subtasks_list
        return False, []

    # этим я не пользовалась
    def play_sound(self, event_type):
        if event_type == "work_start":
            winsound.Beep(2000, 300)
        elif event_type == "work_end":
            winsound.Beep(1500, 500)
            winsound.Beep(2000, 500)
        elif event_type == "break_start":
            winsound.Beep(1000, 300)
        elif event_type == "break_end":
            winsound.Beep(2000, 300)
