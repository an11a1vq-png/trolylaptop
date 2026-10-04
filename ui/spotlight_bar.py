from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QEvent
from PyQt6.QtGui import QColor, QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QGraphicsDropShadowEffect, QPushButton
)
from ui.slash_popup import SlashCommandPopup


class SpotlightBar(QWidget):
    """
    Spotlight-style floating Quick Command Bar for NOVA.
    Allows typing commands silently without speaking.
    """
    submit_command_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(650, 150)
        self._init_ui()

    def _init_ui(self):
        self.container = QWidget(self)
        self.container.setGeometry(10, 10, 630, 130)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 16, 24, 0.96);
                border: 2px solid #00F2FE;
                border-radius: 18px;
            }
        """)

        # Cosmic Cyan Glow Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 242, 254, 160))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        # Top Row: Icon + Input Bar + Send Button + Close hint
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 20px; color: #00F2FE; border: none; background: transparent;")

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nhập lệnh hoặc câu hỏi cho NOVA (Esc để đóng)...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 16px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
                padding: 4px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.input_field.returnPressed.connect(self._on_submit)

        send_btn = QPushButton("↵ Gửi")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #00F2FE;
                color: #0F1018;
                font-weight: 700;
                font-size: 13px;
                padding: 6px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4FACFE;
                color: #FFFFFF;
            }
        """)
        send_btn.clicked.connect(self._on_submit)

        input_row.addWidget(icon_label)
        input_row.addWidget(self.input_field)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        # Bottom Row: Result feedback label
        self.result_label = QLabel("Chế độ nhập lệnh im lặng (Không phát âm thanh qua loa)")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("color: #7F8C8D; font-size: 13px; border: none; background: transparent; padding-left: 28px;")
        layout.addWidget(self.result_label)

        # Slash Command Popup
        self.slash_popup = SlashCommandPopup(self.input_field, parent=None)

    def _center_on_screen(self):
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 3  # Upper third of screen like Spotlight
        self.move(x, y)

    def show_spotlight(self):
        """Summon Spotlight bar, center and focus cursor."""
        self._center_on_screen()
        self.result_label.setText("Chế độ nhập lệnh im lặng (Không phát âm thanh qua loa)")
        self.result_label.setStyleSheet("color: #7F8C8D; font-size: 13px; border: none; background: transparent; padding-left: 28px;")
        self.input_field.setPlaceholderText("Nhập lệnh, câu hỏi hoặc gõ '/' để xem danh sách lệnh...")
        self.input_field.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def hide(self):
        """Hide Spotlight bar and close any open slash command popup."""
        if hasattr(self, "slash_popup"):
            self.slash_popup.hide()
        super().hide()

    def show_result(self, text: str, auto_hide: bool = True):
        """Display command result or AI reply, with auto-hide for actions."""
        self.result_label.setText(text)
        self.result_label.setStyleSheet("color: #00F2FE; font-size: 13px; font-weight: 500; border: none; background: transparent; padding-left: 28px;")
        if auto_hide:
            QTimer.singleShot(1500, self.hide)

    def changeEvent(self, event):
        """Hide Spotlight bar when clicking outside or switching to another window."""
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.hide()
        super().changeEvent(event)

    def _on_submit(self):
        text = self.input_field.text().strip()
        if not text:
            return
        if hasattr(self, "slash_popup"):
            self.slash_popup.hide()
        self.result_label.setText(f"Đang xử lý: \"{text}\"...")
        self.result_label.setStyleSheet("color: #E100FF; font-size: 13px; font-weight: 500; border: none; background: transparent; padding-left: 28px;")
        self.input_field.clear()
        self.submit_command_signal.emit(text)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
