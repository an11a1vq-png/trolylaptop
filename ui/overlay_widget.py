import math
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect


class NovaCosmicWaveWidget(QWidget):
    """Futuristic Cosmic Neon Glow waveform for NOVA (Cyan to Purple/Violet)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 36)
        self.phase = 0.0
        self.is_animating = False

        # Cosmic Neon Palette (Cyan -> Electric Blue -> Violet -> Neon Magenta)
        self.colors = [
            QColor(0, 242, 254),    # Electric Cyan
            QColor(79, 172, 254),   # Bright Cosmic Blue
            QColor(127, 0, 255),    # Neon Violet
            QColor(225, 0, 255),    # Neon Magenta
            QColor(0, 242, 254)     # Shimmer Cyan
        ]

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_wave)

    def start(self):
        self.is_animating = True
        self.anim_timer.start(25)

    def stop(self):
        self.is_animating = False
        self.anim_timer.stop()
        self.phase = 0.0
        self.update()

    def _update_wave(self):
        self.phase += 0.20
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        spacing = 26
        start_x = 22
        center_y = self.height() / 2

        for i, color in enumerate(self.colors):
            x = start_x + i * spacing
            if self.is_animating:
                offset_y = math.sin(self.phase + i * 0.85) * 9.0
                radius = 5.5 + math.cos(self.phase + i * 0.85) * 2.0
                # Outer glow ring
                glow_color = QColor(color.red(), color.green(), color.blue(), 70)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPoint(int(x), int(center_y + offset_y)), int(radius + 3.5), int(radius + 3.5))
            else:
                offset_y = 0.0
                radius = 4.5

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(x), int(center_y + offset_y)), int(radius), int(radius))


class FloatingOverlayWidget(QWidget):
    """Modern futuristic floating overlay widget for NOVA AI."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 130)

        self._position_on_screen()

        # Layout
        self.main_container = QWidget(self)
        self.main_container.setGeometry(10, 10, 500, 110)
        self.main_container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 16, 24, 0.95);
                border-radius: 18px;
                border: 1px solid rgba(0, 242, 254, 0.35);
            }
        """)

        # Cosmic Cyan drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 242, 254, 120))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(6)

        # Header row: Status and Cosmic wave
        header_layout = QHBoxLayout()
        self.status_label = QLabel("⚡ NOVA SẴN SÀNG", self)
        self.status_label.setStyleSheet("color: #00F2FE; font-size: 13px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        self.wave_widget = NovaCosmicWaveWidget(self)
        self.wave_widget.setStyleSheet("border: none; background: transparent;")

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.wave_widget)
        layout.addLayout(header_layout)

        # Content text (user command or assistant response)
        self.text_label = QLabel("Gọi 'Hey Nova' hoặc bấm 'Ctrl + Space'...", self)
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
        y = 30
        self.move(x, y)

    def show_listening(self):
        self.hide_timer.stop()
        self.status_label.setText("⚡ NOVA ĐANG LẮNG NGHE...")
        self.status_label.setStyleSheet("color: #00F2FE; font-size: 13px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        self.text_label.setText("Đang ghi nhận giọng nói...")
        self.wave_widget.start()
        self.show()
        self.raise_()

    def show_thinking(self, prompt=""):
        self.status_label.setText("⚡ NOVA ĐANG XỬ LÝ...")
        self.status_label.setStyleSheet("color: #E100FF; font-size: 13px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        if prompt:
            self.text_label.setText(f"\"{prompt}\"")
        self.wave_widget.start()
        self.show()

    def show_response(self, text: str, auto_hide_seconds: int = 5):
        self.wave_widget.stop()
        self.status_label.setText("⚡ NOVA AI")
        self.status_label.setStyleSheet("color: #4FACFE; font-size: 13px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        self.text_label.setText(text)
        self.show()
        if auto_hide_seconds > 0:
            self.hide_timer.start(auto_hide_seconds * 1000)
