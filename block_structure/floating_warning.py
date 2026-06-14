from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent


class FloatingWarning(QWidget):
    """Всплывающее предупреждение поверх всех окон"""

    closed = Signal(str)  # Сигнал с названием сайта/приложения

    def __init__(self, message, warning_id, parent=None):
        super().__init__(None)

        self.warning_id = warning_id

        # Настройка окна - убираем проблемные флаги
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Размер окна
        self.setFixedSize(400, 160)

        # Позиционируем в правом верхнем углу
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.width() - self.width() - 20,
            20
        )

        self.drag_position = None
        self.setup_ui(message)

        # Таймер для автоматического закрытия
        self.close_timer = QTimer(self)
        self.close_timer.timeout.connect(self.close_with_animation)
        self.close_timer.start(60000)

        # Таймер для исчезновения
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_out)
        self.opacity = 1.0

        self.show()

    def setup_ui(self, message):
        """Настройка интерфейса"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("warning_container")
        self.container.setStyleSheet("""
            #warning_container {
                background-color: #FFF9C4;
                border: 2px solid #F57F17;
                border-radius: 15px;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 10, 15, 15)
        container_layout.setSpacing(8)

        # Верхняя панель
        top_panel = QHBoxLayout()

        title_label = QLabel("⚠️ Внимание!")
        title_label.setStyleSheet("color: #E65100; font-size: 14px; font-weight: bold;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BF360C;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background-color: #F44336;
                border-radius: 15px;
            }
        """)
        close_btn.clicked.connect(self.close_with_animation)

        top_panel.addWidget(title_label)
        top_panel.addStretch()
        top_panel.addWidget(close_btn)

        # Сообщение
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: #3E2723; font-size: 13px; padding: 5px;")

        container_layout.addLayout(top_panel)
        container_layout.addWidget(msg_label)

        layout.addWidget(self.container)
        self.setLayout(layout)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def fade_out(self):
        self.opacity -= 0.05
        if self.opacity <= 0:
            self.fade_timer.stop()
            self.close()
        else:
            self.setWindowOpacity(self.opacity)

    def close_with_animation(self):
        self.close_timer.stop()
        self.fade_timer.start(50)

    def closeEvent(self, event):
        self.closed.emit(self.warning_id)
        super().closeEvent(event)


# Словарь активных предупреждений
_active_warnings = {}


def show_floating_warning(warning_id, message=None):
    """Показать всплывающее предупреждение (вызывается из главного потока)"""
    if not message:
        message = f"Вы пытаетесь открыть отвлекающий ресурс:\n{warning_id}\n\nВернитесь к работе! 🌿"

    # Если уже есть предупреждение для этого ресурса - продлеваем таймер
    if warning_id in _active_warnings:
        warning = _active_warnings[warning_id]
        if warning.close_timer.isActive():
            warning.close_timer.stop()
        warning.close_timer.start(60000)
        return warning

    # Создаём новое предупреждение
    warning = FloatingWarning(message, warning_id)

    def on_closed(wid):
        if wid in _active_warnings:
            del _active_warnings[wid]

    warning.closed.connect(on_closed)
    _active_warnings[warning_id] = warning

    return warning