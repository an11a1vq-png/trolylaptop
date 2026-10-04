from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def create_assistant_icon() -> QIcon:
    """Dynamically generate a crisp 64x64 Google Assistant 4-color icon."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 4 Google Assistant dots
    dots = [
        (20, 32, 9, QColor(66, 133, 244)),   # Blue
        (30, 24, 8, QColor(234, 67, 53)),    # Red
        (40, 28, 7, QColor(251, 188, 5)),    # Yellow
        (48, 36, 6, QColor(52, 168, 83)),    # Green
    ]

    painter.setPen(Qt.PenStyle.NoPen)
    for x, y, r, color in dots:
        painter.setBrush(QBrush(color))
        painter.drawEllipse(x - r, y - r, r * 2, r * 2)

    painter.end()
    return QIcon(pixmap)


class AssistantTrayIcon(QSystemTrayIcon):
    open_dashboard_signal = pyqtSignal()
    trigger_listen_signal = pyqtSignal()
    quit_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(create_assistant_icon())
        self.setToolTip("Hey Google Assistant (Windows)")
        self._create_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #28292A;
                color: #FFFFFF;
                border: 1px solid #3C4043;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3C4043;
                color: #8AB4F8;
            }
        """)

        action_dashboard = QAction("📊 Mở Bảng Điều Khiển", self)
        action_dashboard.triggered.connect(self.open_dashboard_signal.emit)

        action_listen = QAction("🎤 Bắt Đầu Nghe (Ctrl + Space)", self)
        action_listen.triggered.connect(self.trigger_listen_signal.emit)

        menu.addAction(action_dashboard)
        menu.addAction(action_listen)
        menu.addSeparator()

        action_quit = QAction("❌ Thoát Ứng Dụng", self)
        action_quit.triggered.connect(self.quit_signal.emit)
        menu.addAction(action_quit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_dashboard_signal.emit()
