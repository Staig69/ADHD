import threading
import time
import os
import sys
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taskSplitter import split_tasks
from block_structure.process_block import kill_apps
from block_structure.sites_block import redirect_browser
from block_structure import config
from database import Database


class ADHD_Backend:
    def __init__(self):
        self.is_blocking = False
        self.subtasks_list = []
        self.original_task = ""
        self.current_task_id = None
        self.db = Database()

    # =========================================================
    # УПРАВЛЕНИЕ РЕЖИМОМ БЛОКИРОВКИ
    # =========================================================

    def set_hard_mode(self):
        """Включить жесткий режим"""
        config.set_mode(config.MODE_HARD)
        #print("🔴 Включен ЖЕСТКИЙ режим блокировки")

    def set_soft_mode(self):
        """Включить упрощенный режим"""
        config.set_mode(config.MODE_SOFT)
        #print("🟢 Включен УПРОЩЕННЫЙ режим блокировки")

    def get_current_mode(self) -> str:
        """Получить текущий режим"""
        return config.get_mode()

    def toggle_mode(self) -> str:
        """Переключить режим"""
        if config.is_hard_mode():
            self.set_soft_mode()
        else:
            self.set_hard_mode()
        return self.get_current_mode()

    # =========================================================
    # УПРАВЛЕНИЕ БЛОКИРОВКОЙ
    # =========================================================

    def start_blocking(self):
        if self.is_blocking:
            return
        self.is_blocking = True

        # Импортируем и устанавливаем ссылку на приложение
        from block_structure.process_block import set_app_instance as set_proc_instance
        from block_structure.sites_block import set_app_instance as set_sites_instance

        # Передаём ссылку на главное окно приложения (app_instance)
        if hasattr(self, 'app_instance') and self.app_instance:
            set_proc_instance(self.app_instance)
            set_sites_instance(self.app_instance)

        def block_loop():
            while self.is_blocking:
                try:
                    redirect_browser()
                    kill_apps()
                except Exception as e:
                    print(f"Blocking error: {e}")
                time.sleep(2)

        threading.Thread(target=block_loop, daemon=True).start()

    def stop_blocking(self):
        self.is_blocking = False

    # =========================================================
    # СОЗДАНИЕ НОВОЙ ЗАДАЧИ
    # =========================================================

    def generate_initial_plan(self, task_text, work_mins):
        """Создать новую задачу через нейросеть"""
        self.original_task = task_text
        subtasks = split_tasks(self.original_task, work_mins)

        if subtasks and not subtasks[0].startswith("Произошла ошибка"):
            self.subtasks_list = subtasks
            self.current_task_id = self.db.save_generated_plan(
                task_title=task_text,
                subtasks_titles=subtasks,
                time_planned=work_mins
            )
            return True, self.subtasks_list
        return False, subtasks

    # =========================================================
    # ВОССТАНОВЛЕНИЕ ЗАДАЧИ
    # =========================================================

    def has_unfinished_task(self) -> bool:
        """Есть ли незавершённая задача"""
        tasks = self.db.get_all_tasks()
        for task in tasks:
            if task['status'] != 'выполнен':
                return True
        return False

    def get_unfinished_tasks(self) -> List[Dict]:
        """Получить все незавершённые задачи"""
        all_tasks = self.db.get_all_tasks()
        return [t for t in all_tasks if t['status'] != 'выполнен']

    def load_task_by_id(self, task_id: int) -> bool:
        """Загрузить задачу по ID"""
        task = self.db.get_task_with_subtasks(task_id)
        if not task:
            return False

        self.current_task_id = task_id
        self.original_task = task['title']
        self.subtasks_list = [sub['title'] for sub in task['subtasks']]

        if task['status'] != 'выполнен':
            active_sub = self.db.get_current_active_subtask(task_id)
            if not active_sub:
                self.db.start_next_subtask(task_id)
        return True

    def get_current_task_info(self) -> Dict:
        """Получить информацию о текущей задаче"""
        if not self.current_task_id:
            return {
                'has_task': False,
                'title': '',
                'subtasks': [],
                'progress': {'total': 0, 'completed': 0, 'active': 0, 'percent': 0},
                'current_subtask': None
            }

        task = self.db.get_task_with_subtasks(self.current_task_id)
        if not task:
            return {'has_task': False}

        current_sub = self.db.get_current_active_subtask(self.current_task_id)
        return {
            'has_task': True,
            'title': task['title'],
            'status': task['status'],
            'subtasks': task['subtasks'],
            'progress': task['progress'],
            'current_subtask': current_sub['title'] if current_sub else None,
            'current_subtask_id': current_sub['id_sub'] if current_sub else None
        }

    # =========================================================
    # УПРАВЛЕНИЕ ХОДОМ ВЫПОЛНЕНИЯ
    # =========================================================

    def start_task(self) -> bool:
        """Активировать задачу и первую подзадачу"""
        if self.current_task_id:
            self.db.update_task_status(self.current_task_id, 'активный')
            active_sub = self.db.get_current_active_subtask(self.current_task_id)
            if not active_sub:
                self.db.start_next_subtask(self.current_task_id)
            return True
        return False

    def complete_current_subtask(self) -> Optional[int]:
        """Завершить текущую активную подзадачу"""
        if self.current_task_id:
            return self.db.complete_current_subtask(self.current_task_id)
        return None

    def get_current_progress(self) -> Dict:
        """Получить прогресс текущей задачи"""
        if self.current_task_id:
            return self.db.get_task_progress(self.current_task_id)
        return {'total': 0, 'completed': 0, 'active': 0, 'percent': 0}

    def get_current_active_subtask(self) -> Optional[str]:
        """Получить название активной подзадачи"""
        if self.current_task_id:
            sub = self.db.get_current_active_subtask(self.current_task_id)
            return sub['title'] if sub else None
        return None

    def start_next_subtask(self) -> Optional[int]:
        """Запустить следующую подзадачу (ждет -> активный)"""
        if self.current_task_id:
            return self.db.start_next_subtask(self.current_task_id)
        return None

    # =========================================================
    # ПЕРЕГЕНЕРАЦИЯ ПОДЗАДАЧ
    # =========================================================

    def regenerate_subtasks(self, work_mins: int) -> bool:
        """Перегенерировать подзадачи для текущей задачи"""
        if not self.current_task_id:
            return False

        # Получаем выполненные подзадачи
        completed_subtasks = self.db.get_subtasks_by_task(self.current_task_id, status='выполнен')
        completed_titles = [sub['title'] for sub in completed_subtasks]

        # Удаляем незавершённые
        self.db.delete_unfinished_subtasks(self.current_task_id)

        # Генерируем новые подзадачи
        new_subtasks = split_tasks(
            task_description=self.original_task,
            time_minutes=work_mins,
            tasks_performed=', '.join(completed_titles) if completed_titles else None
        )

        if not new_subtasks or new_subtasks[0].startswith("Произошла ошибка"):
            return False

        # Сохраняем новые подзадачи со статусом 'ждет'
        start_order = len(completed_subtasks) + 1
        for idx, title in enumerate(new_subtasks, start=start_order):
            self.db.create_subtask(
                title=title,
                task_id=self.current_task_id,
                time_planned=work_mins,
                status='ждет',
                order_index=idx
            )

        # Активируем задачу и первую новую подзадачу
        self.db.update_task_status(self.current_task_id, 'активный')
        self.db.start_next_subtask(self.current_task_id)

        # Обновляем subtasks_list для GUI
        self.subtasks_list = self.db.get_subtasks_list_for_backend(self.current_task_id)

        return True

    # =========================================================
    # ОБНОВЛЕНИЕ ВРЕМЕНИ
    # =========================================================

    def update_active_session_time(self, work_mins: int, break_mins: int = None):
        """Обновить запланированное время для текущей сессии в базе данных"""
        if self.current_task_id:
            self.db.update_subtasks_time(self.current_task_id, work_mins, break_mins)

    # =========================================================
    # ДЛЯ GUI
    # =========================================================

    def get_subtasks_display_list(self) -> List[Dict]:
        """Получить список подзадач с их статусами для отображения в GUI"""
        if not self.current_task_id:
            return []

        subtasks = self.db.get_subtasks_by_task(self.current_task_id)
        return [
            {
                'id': sub['id_sub'],
                'title': sub['title'],
                'status': sub['status'],
                'order': sub['order_index'],
                'time': sub['time_planned']
            }
            for sub in subtasks
        ]

    def delete_current_task(self) -> bool:
        """Удалить текущую задачу"""
        if self.current_task_id:
            result = self.db.delete_task(self.current_task_id)
            self.current_task_id = None
            self.subtasks_list = []
            self.original_task = ""
            return result
        return False

    def reset_current_task(self) -> bool:
        """Сбросить текущую задачу (начать заново)"""
        if self.current_task_id:
            return self.db.reset_task(self.current_task_id)
        return False