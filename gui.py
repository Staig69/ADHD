import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFontDatabase, QIntValidator
from PySide6.QtUiTools import QUiLoader

from backend import ADHD_Backend


class MatchaApp:
    def __init__(self):
        # 1. Шрифты
        font_path = "Intro.otf"
        QFontDatabase.addApplicationFont(font_path)

        # 2. Загрузка интерфейса
        loader = QUiLoader()
        self.ui = loader.load("focus.ui")
        self.ui.setWindowTitle("Green Focus App ૮꒰ ˶• ༝ •˶꒱ა")

        # Индекс 0 - начальный экран
        self.ui.screen_manager.setCurrentIndex(0)

        # 3. Инициализация бэкенда
        self.engine = ADHD_Backend()
        self.current_task_index = 0
        self.time_left = 0
        self.is_break = False

        # Собственный таймер GUI
        self.timer = QTimer(self.ui)
        self.timer.timeout.connect(self.hidden_timer_tick)

        # 4. Настройка валидаторов времени
        self.time_validator = QIntValidator(1, 99, self.ui)

        self.ui.input_work.setValidator(self.time_validator)
        self.ui.input_break.setValidator(self.time_validator)

        self.ui.input_work.setAlignment(Qt.AlignCenter)
        self.ui.input_break.setAlignment(Qt.AlignCenter)

        self.ui.input_work.setText("25")
        self.ui.input_break.setText("5")

        self.ui.label_9.setAlignment(Qt.AlignCenter)
        self.ui.label_8.setAlignment(Qt.AlignCenter)
        self.ui.title_name.setAlignment(Qt.AlignCenter)

        # 5. ПРИВЯЗКА КНОПОК
        # Экран 0: Кнопка старта
        self.ui.btn_start_app.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(1))

        # Экран 1: Генерация и Настройки
        self.ui.btn_back.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(0))
        self.ui.btn_generate.clicked.connect(self.generate_tasks)

        # Кнопка старта фокуса (ведет на экран 2). Изначально отключена, пока нет задач.
        self.ui.btn_start_focus.clicked.connect(self.start_focus_session)
        self.ui.btn_start_focus.setEnabled(False)

        # Экран 2: Фокус
        self.ui.btn_stop_focus.clicked.connect(self.stop_focus_session)

    def clear_tasks_layout(self):
        while self.ui.tasks_layout.count():
            item = self.ui.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def generate_tasks(self):
        user_text = self.ui.task_input.text()
        if not user_text.strip():
            return

        work_str = self.ui.input_work.text()
        break_str = self.ui.input_break.text()
        work_mins = int(work_str) if work_str else 25
        break_mins = int(break_str) if break_str else 5

        # Отключаем кнопку, чтобы не накликали
        self.ui.btn_generate.setEnabled(False)
        self.clear_tasks_layout()

        temp_lbl = QLabel("НЕЙРОСЕТЬ ДУМАЕТ...")
        temp_lbl.setAlignment(Qt.AlignCenter)
        self.ui.tasks_layout.addWidget(temp_lbl)
        QApplication.processEvents()

        # Передаем всё в бэкенд
        success, tasks = self.engine.generate_initial_plan(user_text, work_mins, break_mins)
        print(work_mins, break_mins)

        self.clear_tasks_layout()
        if success:
            for task in tasks:
                lbl = QLabel(f"• {task}")
                lbl.setWordWrap(True)
                self.ui.tasks_layout.addWidget(lbl)

            # Включаем кнопку старта только при успешной генерации
            self.ui.btn_start_focus.setEnabled(True)
            self.current_task_index = 0
        else:
            self.ui.tasks_layout.addWidget(QLabel("Ошибка генерации... Попробуйте еще раз."))

        self.ui.btn_generate.setEnabled(True)

    def start_focus_session(self):
        # Еще раз забираем значения на случай, если пользователь изменил их ПОСЛЕ генерации
        work_str = self.ui.input_work.text()
        break_str = self.ui.input_break.text()

        self.engine.work_duration = int(work_str) if work_str else 25
        self.engine.break_duration = int(break_str) if break_str else 5

        self.current_task_index = 0
        self.is_break = False
        self.time_left = self.engine.work_duration

        # Запуск основных процессов и переход на экран 2
        self.ui.screen_manager.setCurrentIndex(2)
        self.update_status_ui()
        self.timer.start(1000)
        self.engine.start_blocking()

    def hidden_timer_tick(self):
        if self.time_left > 0:
            self.time_left -= 1
        else:
            if not self.is_break:
                self.is_break = True
                self.time_left = self.engine.break_duration
                self.engine.stop_blocking()
            else:
                self.is_break = False
                self.current_task_index += 1
                if self.current_task_index >= len(self.engine.subtasks_list):
                    self.finish_app()
                    return
                self.time_left = self.engine.work_duration
                self.engine.start_blocking()

        self.update_status_ui()

    def update_status_ui(self):
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{mins:02d}:{secs:02d}"

        if self.is_break:
            status = f"ВРЕМЯ ОТДЫХА\n{time_str}"
        else:
            if self.current_task_index < len(self.engine.subtasks_list):
                task = self.engine.subtasks_list[self.current_task_index]
            else:
                task = "..."
            status = f"В ФОКУСЕ:\n{task}\n\n⏱ {time_str}"

        self.ui.lbl_timer_display.setText(status)

    def stop_focus_session(self):
        self.timer.stop()
        self.engine.stop_blocking()
        # Возвращаемся на экран 1
        self.ui.screen_manager.setCurrentIndex(1)

    def finish_app(self):
        self.timer.stop()
        self.engine.stop_blocking()
        self.ui.lbl_timer_display.setText("ВСЁ ГОТОВО!")
        QTimer.singleShot(3000, lambda: self.ui.screen_manager.setCurrentIndex(0))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MatchaApp()
    window.ui.show()
    sys.exit(app.exec())