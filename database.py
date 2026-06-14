"""
Модуль работы с БД для Green Focus App
"""

import sqlite3
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


class Database:
    """Класс для работы с БД"""

    def __init__(self, db_path: str = "green_focus.db"):
        self.db_path = db_path
        self._init_tables()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """Создание таблиц, если их нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id_task INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'ждет',
                    work_time INTEGER DEFAULT 25,
                    break_time INTEGER DEFAULT 5
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtasks (
                    id_sub INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'ждет',
                    order_index INTEGER DEFAULT 0,
                    time_planned INTEGER DEFAULT 25,
                    FOREIGN KEY (task_id) REFERENCES tasks (id_task) ON DELETE CASCADE
                )
            ''')

    # =========================================================
    # МЕТОДЫ ДЛЯ ЗАДАЧ
    # =========================================================

    def get_all_tasks(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks ORDER BY id_task DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_active_task(self) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE status = ?', ('активный',))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_task_with_subtasks(self, task_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id_task = ?', (task_id,))
            task = cursor.fetchone()
            if not task:
                return None

            task_dict = dict(task)
            cursor.execute('SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index', (task_id,))
            subtasks = [dict(row) for row in cursor.fetchall()]

            total = len(subtasks)
            completed = sum(1 for s in subtasks if s['status'] == 'выполнен')
            active = sum(1 for s in subtasks if s['status'] == 'активный')

            task_dict['subtasks'] = subtasks
            task_dict['progress'] = {
                'total': total,
                'completed': completed,
                'active': active,
                'percent': int((completed / total * 100) if total > 0 else 0)
            }
            return task_dict

    def update_task_status(self, task_id: int, status: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET status = ? WHERE id_task = ?', (status, task_id))

    def delete_task(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id_task = ?', (task_id,))
            return cursor.rowcount > 0

    def reset_task(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE subtasks SET status = ? WHERE task_id = ?', ('ждет', task_id))
            cursor.execute('UPDATE tasks SET status = ? WHERE id_task = ?', ('ждет', task_id))
            return True

    def get_task_progress(self, task_id: int) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM subtasks WHERE task_id = ?', (task_id,))
            statuses = [row['status'] for row in cursor.fetchall()]
            total = len(statuses)
            completed = statuses.count('выполнен')
            active = statuses.count('активный')
            return {
                'total': total,
                'completed': completed,
                'active': active,
                'percent': int((completed / total * 100) if total > 0 else 0)
            }

    # =========================================================
    # МЕТОДЫ ДЛЯ ПОДЗАДАЧ
    # =========================================================

    def create_subtask(self, title: str, task_id: int, time_planned: int = 25,
                       status: str = 'ждет', order_index: int = 0) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO subtasks (task_id, title, status, order_index, time_planned)
                   VALUES (?, ?, ?, ?, ?)''',
                (task_id, title, status, order_index, time_planned)
            )
            return cursor.lastrowid

    def save_generated_plan(self, task_title: str, subtasks_titles: List[str], time_planned: int) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tasks (title, status, work_time) VALUES (?, ?, ?)',
                (task_title, 'активный', time_planned)
            )
            task_id = cursor.lastrowid

            for idx, sub_title in enumerate(subtasks_titles, start=1):
                status = 'активный' if idx == 1 else 'ждет'
                cursor.execute(
                    '''INSERT INTO subtasks (task_id, title, status, order_index, time_planned)
                       VALUES (?, ?, ?, ?, ?)''',
                    (task_id, sub_title, status, idx, time_planned)
                )
            return task_id

    def get_subtasks_by_task(self, task_id: int, status: Optional[str] = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    'SELECT * FROM subtasks WHERE task_id = ? AND status = ? ORDER BY order_index',
                    (task_id, status)
                )
            else:
                cursor.execute(
                    'SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index',
                    (task_id,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_current_active_subtask(self, task_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM subtasks WHERE task_id = ? AND status = ? ORDER BY order_index LIMIT 1',
                (task_id, 'активный')
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_next_waiting_subtask(self, task_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM subtasks WHERE task_id = ? AND status = ? ORDER BY order_index LIMIT 1',
                (task_id, 'ждет')
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def complete_current_subtask(self, task_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id_sub FROM subtasks WHERE task_id = ? AND status = ? ORDER BY order_index LIMIT 1',
                (task_id, 'активный')
            )
            active = cursor.fetchone()
            if not active:
                return None

            cursor.execute('UPDATE subtasks SET status = ? WHERE id_sub = ?', ('выполнен', active['id_sub']))

            cursor.execute('SELECT COUNT(*) as total FROM subtasks WHERE task_id = ?', (task_id,))
            total = cursor.fetchone()['total']
            cursor.execute('SELECT COUNT(*) as completed FROM subtasks WHERE task_id = ? AND status = ?',
                          (task_id, 'выполнен'))
            completed = cursor.fetchone()['completed']

            if total == completed:
                cursor.execute('UPDATE tasks SET status = ? WHERE id_task = ?', ('выполнен', task_id))
            return active['id_sub']

    def start_next_subtask(self, task_id: int) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id_sub FROM subtasks WHERE task_id = ? AND status = ?', (task_id, 'активный'))
            if cursor.fetchone():
                return None

            cursor.execute(
                'SELECT id_sub FROM subtasks WHERE task_id = ? AND status = ? ORDER BY order_index LIMIT 1',
                (task_id, 'ждет')
            )
            next_sub = cursor.fetchone()
            if not next_sub:
                return None

            cursor.execute('UPDATE subtasks SET status = ? WHERE id_sub = ?', ('активный', next_sub['id_sub']))
            cursor.execute('UPDATE tasks SET status = ? WHERE id_task = ? AND status != ?',
                          ('активный', task_id, 'выполнен'))
            return next_sub['id_sub']

    def delete_unfinished_subtasks(self, task_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM subtasks WHERE task_id = ? AND status != ?', (task_id, 'выполнен'))

    def update_subtasks_time(self, task_id: int, work_mins: int, break_mins: int = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE subtasks SET time_planned = ? WHERE task_id = ? AND status != ?',
                          (work_mins, task_id, 'выполнен'))
            if break_mins is not None:
                cursor.execute('UPDATE tasks SET work_time = ?, break_time = ? WHERE id_task = ?',
                              (work_mins, break_mins, task_id))
            else:
                cursor.execute('UPDATE tasks SET work_time = ? WHERE id_task = ?', (work_mins, task_id))

    def get_subtasks_list_for_backend(self, task_id: int) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title FROM subtasks WHERE task_id = ? ORDER BY order_index', (task_id,))
            return [row['title'] for row in cursor.fetchall()]