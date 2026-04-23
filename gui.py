import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtUiTools import QUiLoader

from backend import ADHD_Backend


class MatchaApp:
    def __init__(self):

        font_path = "Intro.otf"
        QFontDatabase.addApplicationFont(font_path)

        # 2. Загрузка интерфейса
        loader = QUiLoader()
        self.ui = loader.load("focus.ui")
        self.ui.setWindowTitle("Green Focus App ૮꒰ ˶• ༝ •˶꒱ა")

        # 0 индекс - начальный экран
        self.ui.screen_manager.setCurrentIndex(0)

        # подсоединение к логике таймера
        self.engine = ADHD_Backend()
        self.current_task_index = 0
        self.time_left = 0
        self.is_break = False

        # собственный таймер gui
        self.timer = QTimer(self.ui)
        self.timer.timeout.connect(self.hidden_timer_tick)

        # кнопка на начальном экране кидает на экран формирования подзадач
        self.ui.btn_start_app.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(1))

        # зеленая кнопка со стрелкой - генерация задач
        self.ui.btn_generate.clicked.connect(self.generate_tasks)
        # 2 индекс - страница со слайдерами
        # 0 индекс - кнопка отправляет на титульную страницу
        self.ui.btn_start_focus.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(2))
        self.ui.btn_back.clicked.connect(lambda: self.ui.screen_manager.setCurrentIndex(0))

        # обновление текста при движении слайдеров
        self.ui.sld_work.valueChanged.connect(self.update_slider_labels)
        self.ui.sld_break.valueChanged.connect(self.update_slider_labels)
        # старт логики
        self.ui.btn_start_focus_session.clicked.connect(self.start_focus_session)
        # кнопка на экране фокуса, ведет обратно на страницу с нейронкой
        self.ui.btn_stop_focus.clicked.connect(self.stop_focus_session)

    def update_slider_labels(self):
        # апдейт слайдеров
        w = self.ui.sld_work.value()
        b = self.ui.sld_break.value()
        self.ui.lbl_work_val.setText(f"Время работы: {w} мин")
        self.ui.lbl_break_val.setText(f"Время отдыха: {b} мин")

    def clear_tasks_layout(self):
        while self.ui.tasks_layout.count():
            item = self.ui.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def generate_tasks(self):
        user_text = self.ui.task_input.text()
        if not user_text.strip(): return

        self.ui.btn_generate.setEnabled(False)
        self.clear_tasks_layout()

        temp_lbl = QLabel("НЕЙРОСЕТЬ ДУМАЕТ...")
        temp_lbl.setAlignment(Qt.AlignCenter)
        self.ui.tasks_layout.addWidget(temp_lbl)
        QApplication.processEvents()

        success, tasks = self.engine.generate_initial_plan(user_text, self.ui.sld_work.value(),
                                                           self.ui.sld_break.value())

        self.clear_tasks_layout()
        if success:
            for task in tasks:
                lbl = QLabel(f"• {task}")
                lbl.setWordWrap(True)
                self.ui.tasks_layout.addWidget(lbl)
            # только когда есть задачи, то можем переходить к странице времени
            self.ui.btn_start_focus.setEnabled(True)
            self.current_task_index = 0
        else:
            self.ui.tasks_layout.addWidget(QLabel("Ошибка генерации..."))

        self.ui.btn_generate.setEnabled(True)

    def start_focus_session(self):

        self.engine.work_duration = self.ui.sld_work.value()
        self.engine.break_duration = self.ui.sld_break.value()

        self.current_task_index = 0
        self.is_break = False
        self.time_left = self.engine.work_duration

        # запуск основных процессов
        self.ui.screen_manager.setCurrentIndex(3)
        self.update_status_ui()
        self.timer.start(1000)
        self.engine.start_blocking()

    def hidden_timer_tick(self):
        # управление внутренним таймером
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
            task = self.engine.subtasks_list[self.current_task_index] if self.current_task_index < len(
                self.engine.subtasks_list) else "..."
            status = f"В ФОКУСЕ:\n{task}\n\n⏱ {time_str}"

        self.ui.lbl_timer_display.setText(status)

    def stop_focus_session(self):
        self.timer.stop()
        self.engine.stop_blocking()
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