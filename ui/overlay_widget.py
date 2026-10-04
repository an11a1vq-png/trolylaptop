import math
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect


class GoogleWaveWidget(QWidget):
    """Animated 4 Google-colored dots wave."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 36)
        self.phase = 0.0
        self.is_animating = False
        self.colors = [
            QColor(66, 133, 244),   # Google Blue
            QColor(234, 67, 53),    # Google Red
            QColor(251, 188, 5),    # Google Yellow
            QColor(52, 168, 83)     # Google Green
        ]

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_wave)

    def start(self):
        self.is_animating = True
        self.anim_timer.start(30)

    def stop(self):
        self.is_animating = False
        self.anim_timer.stop()
        self.phase = 0.0
        self.update()

    def _update_wave(self):
        self.phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        spacing = 30
        start_x = 25
        center_y = self.height() / 2

        for i, color in enumerate(self.colors):
            x = start_x + i * spacing
            if self.is_animating:
                offset_y = math.sin(self.phase + i * 0.9) * 8.0
                radius = 6.0 + math.cos(self.phase + i * 0.9) * 1.5
            else:
                offset_y = 0.0
                radius = 5.0

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(x), int(center_y + offset_y)), int(radius), int(radius))


class FloatingOverlayWidget(QWidget):
    """Modern translucent floating overlay widget for Google Assistant."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 140)

        # Positioning at top-center of the screen
        self._position_on_screen()

        # Layout
        self.main_container = QWidget(self)
        self.main_container.setGeometry(10, 10, 480, 120)
        self.main_container.setStyleSheet("""
            QWidget {
                background-color: rgba(28, 28, 32, 0.94);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
        """)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.main_container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Header row: Status and Google wave
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Hey Google sẵn sàng", self)
        self.status_label.setStyleSheet("color: #9AA0A6; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        self.wave_widget = GoogleWaveWidget(self)
        self.wave_widget.setStyleSheet("border: none; background: transparent;")

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.wave_widget)
        layout.addLayout(header_layout)

        # Content text (user command or assistant response)
        self.text_label = QLabel("Nhấn 'Ctrl + Space' hoặc gọi 'Hey Google'...", self)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 400; border: none; background: transparent;")
        layout.addWidget(self.text_label)

        # Auto hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def _position_on_screen(self):
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 35  # 35px from top
        self.move(x, y)

    def show_listening(self):
        self.hide_timer.stop()
        self.status_label.setText("Đang lắng nghe...")
        self.status_label.setStyleSheet("color: #4285F4; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        self.text_label.setText("Tôi đang nghe bạn nói...")
        self.wave_widget.start()
        self.show()
        self.raise_()

    def show_thinking(self, prompt=""):
        self.status_label.setText("Đang xử lý...")
        self.status_label.setStyleSheet("color: #FBBC05; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        if prompt:
            self.text_label.setText(f"\"{prompt}\"")
        self.wave_widget.start()
        self.show()

    def show_response(self, text: str, auto_hide_seconds: int = 5):
        self.wave_widget.stop()
        self.status_label.setText("Hey Google")
        self.status_label.setStyleSheet("color: #34A853; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        self.text_label.setText(text)
        self.show()
        if auto_hide_seconds > 0:
            self.hide_timer.start(auto_hide_seconds * 1000)
