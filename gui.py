import sys
import os
from PySide6.QtWidgets import (
    QApplication, QLabel, QMessageBox, QPushButton,
    QListWidgetItem, QWidget
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFontDatabase, QIntValidator
from PySide6.QtUiTools import QUiLoader

from backend import ADHD_Backend
from timer import Timer
from block_structure.floating_warning import show_floating_warning

# Константы для навигации
PAGE_START = 0
PAGE_ALL_TASKS = 1
PAGE_TASK_DETAILS = 2
PAGE_GENERATE = 3
PAGE_SETTINGS = 4
PAGE_FOCUS = 5
PAGE_TASK_TIME_SETTINGS = 6
PAGE_CONFIG_EDITOR = 7
PAGE_ADD_TO_CONFIG = 8

class App(QWidget):
    # Сигналы для безопасного показа уведомлений из других потоков
    show_site_warning_signal = Signal(str)
    show_app_warning_signal = Signal(str)

    def __init__(self):
        super().__init__()

        # Подключение шрифта
        try:
            QFontDatabase.addApplicationFont("Intro.otf")
        except:
            print("Шрифт Intro.otf не найден")

        # Загрузка интерфейса
        loader = QUiLoader()

        if not os.path.exists("focus.ui"):
            QMessageBox.critical(None, "Ошибка", "Файл focus.ui не найден!")
            sys.exit(1)

        self.ui = loader.load("focus.ui")
        if self.ui is None:
            print("Ошибка загрузки UI")
            sys.exit(1)

        self.ui.setWindowTitle("Green Focus App 🌿")

        # Подключаем сигналы к методам показа уведомлений
        self.show_site_warning_signal.connect(self.show_site_warning_popup)
        self.show_app_warning_signal.connect(self.show_app_warning_popup)

        # Передаём ссылку на приложение в модули блокировки
        from block_structure import sites_block, process_block
        sites_block.set_app_instance(self)
        process_block.set_app_instance(self)

        # Подключение логики
        self.engine = ADHD_Backend()
        self.timer_logic = Timer()
        self.current_task_index = 0
        self.time_left = 0
        self.is_break = False

        # Таймер интерфейса
        self.gui_timer = QTimer(self.ui)
        self.gui_timer.timeout.connect(self.hidden_timer_tick)

        # Настройка UI
        self.setup_ui_elements()
        self.setup_connections()

        # Показываем стартовый экран
        self.ui.screen_manager.setCurrentIndex(PAGE_START)
        self.check_and_restore_task()

    # =========================================================
    # МЕТОДЫ ДЛЯ ПОКАЗА УВЕДОМЛЕНИЙ
    # =========================================================

    def show_site_warning_popup(self, site_name):
        """Показать всплывающее окно для сайта"""
        try:
            msg = QMessageBox(self.ui)
            msg.setWindowTitle("Внимание! 🌿")
            msg.setText(f"Вы отвлекаетесь на:\n\n{site_name}\n\nВернитесь к работе!")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #eaffe1;
                }
                QLabel {
                    color: #3d2500;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #bfecac;
                    color: #3d2500;
                    border-radius: 10px;
                    font-weight: bold;
                    border: 1px solid #a3d98d;
                    min-width: 80px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #a8dba1;
                }
            """)
            QTimer.singleShot(3000, msg.close)
            msg.show()
        except Exception as e:
            print(f"Ошибка показа окна: {e}")

    def show_app_warning_popup(self, app_name):
        """Показать всплывающее окно для приложения"""
        try:
            msg = QMessageBox(self.ui)
            msg.setWindowTitle("Внимание! 🌿")
            msg.setText(f"Отвлекающее приложение:\n\n{app_name}\n\nЗакройте его и вернитесь к работе!")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #eaffe1;
                }
                QLabel {
                    color: #3d2500;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #bfecac;
                    color: #3d2500;
                    border-radius: 10px;
                    font-weight: bold;
                    border: 1px solid #a3d98d;
                    min-width: 80px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #a8dba1;
                }
            """)
            QTimer.singleShot(3000, msg.close)
            msg.show()
        except Exception as e:
            print(f"Ошибка показа окна: {e}")

    # =========================================================
    # НАСТРОЙКА UI
    # =========================================================

    def setup_ui_elements(self):
        """Настройка элементов интерфейса"""
        if hasattr(self.ui, 'input_work'):
            validator = QIntValidator(1, 99, self.ui)
            self.ui.input_work.setValidator(validator)
            self.ui.input_work.setText("25")

        if hasattr(self.ui, 'input_break'):
            validator = QIntValidator(1, 99, self.ui)
            self.ui.input_break.setValidator(validator)
            self.ui.input_break.setText("5")

        # Настраиваем существующую кнопку btn_mode из UI
        if hasattr(self.ui, 'btn_mode'):
            self.ui.btn_mode.setText("🟢 Упрощенный режим")
            self.ui.btn_mode.setCursor(Qt.PointingHandCursor)
            self.ui.btn_mode.setMinimumHeight(70)
            self.ui.btn_mode.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: none;
                    border-radius: 35px;
                    color: #3d2500;
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 70px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #F0F0F0;
                }
            """)

        if hasattr(self.ui, 'label_task_title'):
            self.ui.label_task_title.setWordWrap(True)

    def setup_connections(self):
        """Подключение сигналов кнопок"""
        # Навигация
        if hasattr(self.ui, 'btn_start_app'):
            self.ui.btn_start_app.clicked.connect(self.load_all_tasks_screen)

        if hasattr(self.ui, 'btn_generate_new'):
            self.ui.btn_generate_new.clicked.connect(self.open_clean_generation_screen)

        if hasattr(self.ui, 'btn_to_menu'):
            self.ui.btn_to_menu.clicked.connect(self.load_all_tasks_screen)

        if hasattr(self.ui, 'btn_back'):
            self.ui.btn_back.clicked.connect(self.load_all_tasks_screen)

        if hasattr(self.ui, 'btn_back_from_time_settings'):
            self.ui.btn_back_from_time_settings.clicked.connect(self.save_and_back_from_time_settings)

        if hasattr(self.ui, 'btn_change_time'):
            self.ui.btn_change_time.clicked.connect(self.open_task_time_settings)

        # Настройки времени
        if hasattr(self.ui, 'btn_open_time_settings'):
            self.ui.btn_open_time_settings.clicked.connect(
                lambda: self.ui.screen_manager.setCurrentIndex(PAGE_SETTINGS))

        if hasattr(self.ui, 'btn_save_time'):
            self.ui.btn_save_time.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(PAGE_GENERATE))

        if hasattr(self.ui, 'btn_hint'):
            self.ui.btn_hint.clicked.connect(self.show_time_hint)

        # Список задач
        if hasattr(self.ui, 'tasks_list_widget'):
            self.ui.tasks_list_widget.itemClicked.connect(self.on_task_clicked)

        # Генерация
        if hasattr(self.ui, 'btn_generate'):
            self.ui.btn_generate.clicked.connect(self.generate_tasks)

        # Фокус-сессия
        if hasattr(self.ui, 'btn_start_focus'):
            self.ui.btn_start_focus.clicked.connect(self.start_focus_session)

        if hasattr(self.ui, 'btn_continue_focus'):
            self.ui.btn_continue_focus.clicked.connect(self.continue_focus_session)

        if hasattr(self.ui, 'btn_stop_focus'):
            self.ui.btn_stop_focus.clicked.connect(self.stop_focus_session)

        # Перегенерация
        if hasattr(self.ui, 'btn_regenerate'):
            self.ui.btn_regenerate.clicked.connect(self.regenerate_subtasks)

        # Режим блокировки
        if hasattr(self.ui, 'btn_mode'):
            self.ui.btn_mode.clicked.connect(self.toggle_blocking_mode)

        # --- Управление конфигом ---
        if hasattr(self.ui, 'btn_open_config'):
            self.ui.btn_open_config.clicked.connect(self.open_config_editor)

        if hasattr(self.ui, 'btn_back_from_config'):
            self.ui.btn_back_from_config.clicked.connect(self.load_all_tasks_screen)

        if hasattr(self.ui, 'btn_add_to_config'):
            self.ui.btn_add_to_config.clicked.connect(self.open_add_to_config)

        # Клики по спискам для удаления
        if hasattr(self.ui, 'listview_apps'):
            self.ui.listview_apps.itemClicked.connect(
                lambda: self.remove_from_config(self.ui.listview_apps, "приложение")
            )

        if hasattr(self.ui, 'listview_sites'):
            self.ui.listview_sites.itemClicked.connect(
                lambda: self.remove_from_config(self.ui.listview_sites, "сайт")
            )

        # Добавление в конфиг
        if hasattr(self.ui, 'btn_add_app'):
            self.ui.btn_add_app.clicked.connect(self.add_app_to_config)

        if hasattr(self.ui, 'btn_add_site'):
            self.ui.btn_add_site.clicked.connect(self.add_site_to_config)

        if hasattr(self.ui, 'btn_back_from_add'):
            self.ui.btn_back_from_add.clicked.connect(self.open_config_editor)

    # =========================================================
    # ПЕРЕКЛЮЧЕНИЕ РЕЖИМА БЛОКИРОВКИ
    # =========================================================

    def toggle_blocking_mode(self):
        """Переключение режима блокировки"""
        new_mode = self.engine.toggle_mode()

        if new_mode == "hard":
            self.ui.btn_mode.setText("🔴 Жесткий режим")
            self.ui.btn_mode.setStyleSheet("""
                QPushButton {
                    background-color: #ffaaaa;
                    border: none;
                    border-radius: 35px;
                    color: #3d2500;
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 70px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #ff8888;
                }
            """)
            QMessageBox.information(
                self.ui,
                "Режим изменён",
                "🔴 Включен ЖЕСТКИЙ режим!\n\n"
                "Отвлекающие сайты будут перенаправляться на страницу блокировки.\n"
                "Отвлекающие приложения будут закрываться."
            )
        else:
            self.ui.btn_mode.setText("🟢 Упрощенный режим")
            self.ui.btn_mode.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: none;
                    border-radius: 35px;
                    color: #3d2500;
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 70px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #F0F0F0;
                }
            """)
            QMessageBox.information(
                self.ui,
                "Режим изменён",
                "🟢 Включен УПРОЩЕННЫЙ режим!\n\n"
                "Будут только всплывающие предупреждения (не чаще раза в минуту)."
            )

    # =========================================================
    # ЭКРАН 1: СПИСОК ВСЕХ ЗАДАЧ
    # =========================================================

    def load_all_tasks_screen(self):
        """Загрузка страницы со списком всех задач"""
        if hasattr(self.ui, 'tasks_list_widget'):
            self.ui.tasks_list_widget.clear()
            tasks = self.engine.db.get_all_tasks()

            for task in tasks:
                task_details = self.engine.db.get_task_with_subtasks(task['id_task'])
                total_time = sum(sub.get('time_planned', 0) for sub in task_details['subtasks'])
                status_mark = "✅" if task['status'] == 'выполнен' else "⏳"

                if total_time > 0:
                    item_text = f"{status_mark} {task['title']}  [ ⏱ {total_time} мин ]"
                else:
                    item_text = f"{status_mark} {task['title']}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, task['id_task'])
                self.ui.tasks_list_widget.addItem(item)

        self.ui.screen_manager.setCurrentIndex(PAGE_ALL_TASKS)

    def on_task_clicked(self, item):
        """Обработчик клика по задаче"""
        task_id = item.data(Qt.UserRole)
        self.open_task_details(task_id)

    # =========================================================
    # ЭКРАН 2: ДЕТАЛИ ЗАДАЧИ
    # =========================================================

    def open_task_details(self, task_id):
        """Открыть страницу с деталями задачи"""
        self.engine.load_task_by_id(task_id)
        task_data = self.engine.db.get_task_with_subtasks(task_id)

        if hasattr(self.ui, 'label_task_title'):
            self.ui.label_task_title.setText(task_data['title'])

        if hasattr(self.ui, 'label_time_info'):
            total_work_time = sum(sub.get('time_planned', 0) for sub in task_data['subtasks'])
            break_time = task_data.get('break_time', 5)
            self.ui.label_time_info.setText(f"⏱ Работа: ~{total_work_time} мин  |  🍵 Отдых: {break_time} мин")

        if hasattr(self.ui, 'subtasks_list_widget'):
            self.ui.subtasks_list_widget.clear()
            for sub in task_data['subtasks']:
                if sub['status'] == 'выполнен':
                    icon = "✅"
                elif sub['status'] == 'активный':
                    icon = "🟢"
                else:
                    icon = "⬜"
                self.ui.subtasks_list_widget.addItem(f"{icon} {sub['title']} ({sub['time_planned']} мин)")

        if hasattr(self.ui, 'btn_continue_focus'):
            if task_data['status'] == 'выполнен':
                self.ui.btn_continue_focus.setEnabled(False)
                self.ui.btn_continue_focus.setText("✅ Завершена")
            else:
                self.ui.btn_continue_focus.setEnabled(True)
                self.ui.btn_continue_focus.setText("▶ Начать / Продолжить")

        self.ui.screen_manager.setCurrentIndex(PAGE_TASK_DETAILS)

    def check_and_restore_task(self):
        """Проверить наличие незавершённой задачи при старте"""
        if self.engine.has_unfinished_task():
            unfinished = self.engine.get_unfinished_tasks()
            if len(unfinished) == 1:
                task = unfinished[0]
                progress = self.engine.db.get_task_progress(task['id_task'])
                reply = QMessageBox.question(
                    self.ui,
                    "Восстановление",
                    f"У вас есть незавершённая задача:\n\n"
                    f"「 {task['title']} 」\n\n"
                    f"Прогресс: {progress['completed']}/{progress['total']}\n\n"
                    f"Продолжить?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.open_task_details(task['id_task'])

    # =========================================================
    # ЭКРАН 3: ГЕНЕРАЦИЯ ЗАДАЧ
    # =========================================================

    def generate_tasks(self):
        """Генерация новой задачи через нейросеть"""
        if not hasattr(self.ui, 'task_input'):
            return

        task_text = self.ui.task_input.text()
        if not task_text.strip():
            QMessageBox.warning(self.ui, "Внимание", "Введите описание задачи")
            return

        work_mins = int(self.ui.input_work.text() or 25)

        self.ui.btn_generate.setEnabled(False)
        self.clear_tasks_layout()

        temp_lbl = QLabel("🧠 НЕЙРОСЕТЬ СОСТАВЛЯЕТ ПЛАН...")
        temp_lbl.setAlignment(Qt.AlignCenter)
        self.ui.tasks_layout.addWidget(temp_lbl)
        QApplication.processEvents()

        success, tasks = self.engine.generate_initial_plan(task_text, work_mins)
        self.clear_tasks_layout()

        if success:
            for task in tasks:
                self.ui.tasks_layout.addWidget(QLabel(f"• {task}"))
            if hasattr(self.ui, 'btn_start_focus'):
                self.ui.btn_start_focus.setEnabled(True)
            QMessageBox.information(self.ui, "Готово", f"Сгенерировано {len(tasks)} подзадач!")
        else:
            error_text = tasks[0] if tasks else "Ошибка"
            QMessageBox.warning(self.ui, "Ошибка", f"Не удалось сгенерировать план:\n{error_text}")

        self.ui.btn_generate.setEnabled(True)

    def regenerate_subtasks(self):
        """Перегенерация подзадач"""
        if not self.engine.current_task_id:
            QMessageBox.warning(self.ui, "Ошибка", "Нет активной задачи")
            return

        completed = self.engine.db.get_subtasks_by_task(self.engine.current_task_id, status='выполнен')

        if not completed:
            reply = QMessageBox.question(
                self.ui,
                "Перегенерация",
                "Нет выполненных подзадач. Все текущие подзадачи будут удалены.\nПродолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        work_mins = int(self.ui.input_work.text() or 25)

        self.ui.btn_regenerate.setEnabled(False)
        self.clear_tasks_layout()

        temp_lbl = QLabel("🔄 ПЕРЕГЕНЕРАЦИЯ ПЛАНА...")
        temp_lbl.setAlignment(Qt.AlignCenter)
        self.ui.tasks_layout.addWidget(temp_lbl)
        QApplication.processEvents()

        success = self.engine.regenerate_subtasks(work_mins)
        self.clear_tasks_layout()

        if success:
            new_subtasks = self.engine.db.get_subtasks_by_task(self.engine.current_task_id)
            for sub in new_subtasks:
                if sub['status'] == 'выполнен':
                    self.ui.tasks_layout.addWidget(QLabel(f"✅ {sub['title']} (выполнено)"))
                else:
                    self.ui.tasks_layout.addWidget(QLabel(f"• {sub['title']} (~{sub['time_planned']} мин)"))

            if hasattr(self.ui, 'btn_start_focus'):
                self.ui.btn_start_focus.setEnabled(True)
            QMessageBox.information(self.ui, "Готово", "План обновлён!")
        else:
            QMessageBox.warning(self.ui, "Ошибка", "Не удалось перегенерировать план")

        self.ui.btn_regenerate.setEnabled(True)

    def clear_tasks_layout(self):
        """Очистка списка подзадач"""
        if hasattr(self.ui, 'tasks_layout'):
            while self.ui.tasks_layout.count():
                child = self.ui.tasks_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    # =========================================================
    # НАСТРОЙКА ВРЕМЕНИ
    # =========================================================

    def show_time_hint(self):
        """Подсказка по времени"""
        msg = QMessageBox(self.ui)
        msg.setWindowTitle("Советы 🌿")
        msg.setText(
            "<b>25/5</b> — классический режим, установлен по умолчанию;<br>"
            "<b>30/10</b> — для небольших учебных задач;<br>"
            "<b>45/10</b> — для учебы;<br>"
            "<b>50/15</b> — для серьёзных задач.<br><br>"
            "Экспериментируйте! (⌒▽⌒)♡"
        )
        msg.setStyleSheet("""
            QMessageBox { background-color: #eaffe1; }
            QLabel { color: #3d2500; font-size: 13px; }
            QPushButton {
                background-color: #bfecac; color: #3d2500;
                border-radius: 10px; font-weight: bold;
                border: 1px solid #a3d98d;
                min-width: 70px; min-height: 25px;
            }
            QPushButton:hover { background-color: #a8dba1; }
        """)
        msg.exec()

    # =========================================================
    # ФОКУС-СЕССИЯ
    # =========================================================

    def continue_focus_session(self):
        """Продолжить сессию с сохранёнными настройками"""
        if not self.engine.current_task_id:
            return

        task_data = self.engine.db.get_task_with_subtasks(self.engine.current_task_id)
        work_mins = task_data.get('work_time', 25)
        break_mins = task_data.get('break_time', 5)
        self._run_focus_logic(work_mins, break_mins)

    def start_focus_session(self):
        """Начать сессию с настройками из полей ввода"""
        if not self.engine.current_task_id:
            return

        work_mins = int(self.ui.input_work.text() or 25)
        break_mins = int(self.ui.input_break.text() or 5)
        self.engine.update_active_session_time(work_mins, break_mins)
        self._run_focus_logic(work_mins, break_mins)

    def _run_focus_logic(self, work_mins, break_mins):
        """Запуск логики таймера"""
        self.engine.start_task()
        self.timer_logic.set_durations(work_mins, break_mins)

        self.is_break = False
        self.time_left = self.timer_logic.work_duration

        active_sub = self.engine.get_current_active_subtask()
        if not active_sub:
            self.engine.start_next_subtask()

        self.ui.screen_manager.setCurrentIndex(PAGE_FOCUS)
        self.update_status_ui()
        self.engine.start_blocking()

        if self.gui_timer.isActive():
            self.gui_timer.stop()
        self.gui_timer.start(1000)

    def hidden_timer_tick(self):
        """Тик таймера (каждую секунду)"""
        if self.time_left > 0:
            self.time_left -= 1
            self.update_status_ui()
            return

        if not self.is_break:
            self.engine.complete_current_subtask()
            self.timer_logic.play_sound("work_end")

            progress = self.engine.get_current_progress()
            if progress['completed'] == progress['total'] and progress['total'] > 0:
                self.finish_app()
                return

            self.is_break = True
            self.time_left = self.timer_logic.break_duration
            self.engine.stop_blocking()
            self.timer_logic.play_sound("break_start")
            self.update_status_ui()
        else:
            self.is_break = False
            self.engine.start_next_subtask()
            self.time_left = self.timer_logic.work_duration
            self.engine.start_blocking()
            self.timer_logic.play_sound("work_start")
            self.update_status_ui()

    def update_status_ui(self):
        """Обновление отображения таймера"""
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        if self.is_break:
            status = f"🍃 ОТДЫХ\n{time_str}\n\nОтдохните!"
            self.ui.lbl_timer_display.setText(status)
            return

        current_sub = self.engine.get_current_active_subtask()
        task_title = current_sub if current_sub else "Выполнение плана"
        progress = self.engine.get_current_progress()

        status = f"🎯 В ФОКУСЕ:\n{task_title}\n[{progress['completed']}/{progress['total']}]\n\n⏱ {time_str}"
        self.ui.lbl_timer_display.setText(status)

    def stop_focus_session(self):
        """Остановка фокус-сессии"""
        self.gui_timer.stop()
        self.engine.stop_blocking()
        self.open_task_details(self.engine.current_task_id)

    def finish_app(self):
        """Завершение задачи"""
        self.gui_timer.stop()
        self.engine.stop_blocking()
        self.ui.lbl_timer_display.setText("🎉 ПОЗДРАВЛЯЮ! ВСЁ ВЫПОЛНЕНО! 🎉")
        self.timer_logic.play_sound("finish")

        QMessageBox.information(self.ui, "Поздравляем!", "Вы выполнили все подзадачи!\nОтличная работа! 🌟")
        QTimer.singleShot(3000, self.load_all_tasks_screen)

    # =========================================================
    # НАСТРОЙКИ ВРЕМЕНИ ЗАДАЧИ
    # =========================================================

    def open_clean_generation_screen(self):
        """Открыть экран генерации новой задачи"""
        self.engine.current_task_id = None
        self.engine.subtasks_list = []
        self.engine.original_task = ""

        if hasattr(self.ui, 'task_input'):
            self.ui.task_input.clear()
        self.clear_tasks_layout()

        if hasattr(self.ui, 'btn_start_focus'):
            self.ui.btn_start_focus.setEnabled(False)

        self.ui.screen_manager.setCurrentIndex(PAGE_GENERATE)

    def open_task_time_settings(self):
        """Открыть настройки времени задачи"""
        if not self.engine.current_task_id:
            return

        task_data = self.engine.db.get_task_with_subtasks(self.engine.current_task_id)
        if task_data and hasattr(self.ui, 'label_task_time_title'):
            self.ui.label_task_time_title.setText(f"📋 {task_data['title']}")

            if hasattr(self.ui, 'input_task_work_time'):
                self.ui.input_task_work_time.setText(str(task_data.get('work_time', 25)))
            if hasattr(self.ui, 'input_task_break_time'):
                self.ui.input_task_break_time.setText(str(task_data.get('break_time', 5)))

        self.ui.screen_manager.setCurrentIndex(PAGE_TASK_TIME_SETTINGS)

    def save_and_back_from_time_settings(self):
        """Сохранить настройки времени и вернуться"""
        if not self.engine.current_task_id:
            self.load_all_tasks_screen()
            return

        try:
            work_time = int(self.ui.input_task_work_time.text()) if hasattr(self.ui, 'input_task_work_time') else 25
            break_time = int(self.ui.input_task_break_time.text()) if hasattr(self.ui, 'input_task_break_time') else 5
            self.engine.update_active_session_time(work_time, break_time)
            self.open_task_details(self.engine.current_task_id)
        except ValueError:
            QMessageBox.warning(self.ui, "Ошибка", "Введите корректные числа")

    def show_floating_warning(self, site_name):
        """Показать всплывающее предупреждение (вызывается из главного потока)"""
        show_floating_warning(site_name)

    def show_app_floating_warning(self, app_name, warning_type):
        """Показать всплывающее предупреждение для приложения"""
        show_floating_warning(
            app_name,
            f"Вы пытаетесь открыть отвлекающее приложение:\n{app_name}\n\nВернитесь к работе! 🌿"
        )

    # =========================================================
    # ЭКРАН 7: УПРАВЛЕНИЕ КОНФИГОМ БЛОКИРОВКИ
    # =========================================================

    def open_config_editor(self):
        """Открыть редактор конфигурации блокировки"""
        self.load_config_lists()
        self.ui.screen_manager.setCurrentIndex(PAGE_CONFIG_EDITOR)

    def load_config_lists(self):
        """Загрузить списки в listview"""
        from block_structure.config import get_blocked_apps, get_blocked_sites, get_mode, MODE_HARD

        # Загружаем приложения
        if hasattr(self.ui, 'listview_apps'):
            self.ui.listview_apps.clear()
            apps = get_blocked_apps()
            for app in apps:
                item = QListWidgetItem(f"🔴 {app}")
                item.setData(Qt.UserRole, app)
                self.ui.listview_apps.addItem(item)

            if hasattr(self.ui, 'label_apps_count'):
                self.ui.label_apps_count.setText(f"Приложений: {len(apps)}")

        # Загружаем сайты
        if hasattr(self.ui, 'listview_sites'):
            self.ui.listview_sites.clear()
            sites = get_blocked_sites()
            for site in sites:
                item = QListWidgetItem(f"🌐 {site}")
                item.setData(Qt.UserRole, site)
                self.ui.listview_sites.addItem(item)

            if hasattr(self.ui, 'label_sites_count'):
                self.ui.label_sites_count.setText(f"Сайтов: {len(sites)}")

        # Обновляем кнопку режима
        if hasattr(self.ui, 'btn_mode'):
            current_mode = get_mode()
            if current_mode == MODE_HARD:
                self.ui.btn_mode.setText("🔴 Жесткий режим")
            else:
                self.ui.btn_mode.setText("🟢 Мягкий режим")

    def remove_from_config(self, list_widget, item_type):
        """Удалить элемент из конфига"""
        current_item = list_widget.currentItem()
        if not current_item:
            return

        item_name = current_item.data(Qt.UserRole)

        reply = QMessageBox.question(
            self.ui,
            "Подтверждение",
            f"Удалить из списка блокировки?\n\n{item_name}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from block_structure.config import remove_blocked_app, remove_blocked_site

            if item_type == "приложение":
                remove_blocked_app(item_name)
            else:
                remove_blocked_site(item_name)

            self.load_config_lists()

    # =========================================================
    # ЭКРАН 8: ДОБАВЛЕНИЕ В КОНФИГ
    # =========================================================

    def open_add_to_config(self):
        """Открыть страницу добавления в конфиг"""
        if hasattr(self.ui, 'input_new_app'):
            self.ui.input_new_app.clear()
            self.ui.input_new_app.setPlaceholderText("Например: steam.exe")

        if hasattr(self.ui, 'input_new_site'):
            self.ui.input_new_site.clear()
            self.ui.input_new_site.setPlaceholderText("Например: YouTube")

        self.ui.screen_manager.setCurrentIndex(PAGE_ADD_TO_CONFIG)

    def add_app_to_config(self):
        """Добавить приложение в список блокировки"""
        if not hasattr(self.ui, 'input_new_app'):
            return

        app_name = self.ui.input_new_app.text().strip()

        if not app_name:
            QMessageBox.warning(self.ui, "Пустое поле", "Введите название приложения")
            return

        from block_structure.config import add_blocked_app, get_blocked_apps

        # Проверяем без учета регистра
        existing_apps = [app.lower() for app in get_blocked_apps()]
        if app_name.lower() in existing_apps:
            QMessageBox.warning(self.ui, "Уже есть", f"Приложение уже в списке:\n{app_name}")
            return

        if add_blocked_app(app_name):
            QMessageBox.information(self.ui, "Добавлено", f"Приложение добавлено:\n{app_name}")
            self.ui.input_new_app.clear()
        else:
            QMessageBox.warning(self.ui, "Ошибка", "Не удалось добавить приложение")

    def add_site_to_config(self):
        """Добавить сайт в список блокировки"""
        if not hasattr(self.ui, 'input_new_site'):
            return

        site_name = self.ui.input_new_site.text().strip()

        if not site_name:
            QMessageBox.warning(self.ui, "Пустое поле", "Введите название сайта")
            return

        from block_structure.config import add_blocked_site, get_blocked_sites

        # Проверяем без учета регистра
        existing_sites = [site.lower() for site in get_blocked_sites()]
        if site_name.lower() in existing_sites:
            QMessageBox.warning(self.ui, "Уже есть", f"Сайт уже в списке:\n{site_name}")
            return

        if add_blocked_site(site_name):
            QMessageBox.information(self.ui, "Добавлено", f"Сайт добавлен:\n{site_name}")
            self.ui.input_new_site.clear()
        else:
            QMessageBox.warning(self.ui, "Ошибка", "Не удалось добавить сайт")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.ui.show()
    sys.exit(app.exec())