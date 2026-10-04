from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QRadialGradient, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def create_nova_icon() -> QIcon:
    """Generate a high-tech glowing Cosmic Nova Star / Orb icon (Cyan & Violet)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    center = QPoint(32, 32)

    # 1. Outer Cyan Aura / Glow
    radial = QRadialGradient(32, 32, 28)
    radial.setColorAt(0.0, QColor(0, 242, 254, 220))    # Intense Cyan center
    radial.setColorAt(0.45, QColor(79, 172, 254, 180))  # Blue transition
    radial.setColorAt(0.75, QColor(127, 0, 255, 120))   # Violet shimmer
    radial.setColorAt(1.0, QColor(0, 0, 0, 0))          # Fade to transparent

    painter.setBrush(QBrush(radial))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(center, 28, 28)

    # 2. Solid Inner Cyber Core
    painter.setBrush(QBrush(QColor(15, 16, 24)))
    painter.setPen(QPen(QColor(0, 242, 254), 2.5))
    painter.drawEllipse(center, 14, 14)

    # 3. Bright White-Cyan Star Flare at center
    painter.setBrush(QBrush(QColor(255, 255, 255)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(center, 5, 5)

    painter.end()
    return QIcon(pixmap)


class AssistantTrayIcon(QSystemTrayIcon):
    open_dashboard_signal = pyqtSignal()
    trigger_listen_signal = pyqtSignal()
    quit_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(create_nova_icon())
        self.setToolTip("NOVA AI Assistant (Windows)")
        self._create_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0F1018;
                color: #FFFFFF;
                border: 1px solid rgba(0, 242, 254, 0.4);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 7px 22px;
                border-radius: 5px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #1A1C2C;
                color: #00F2FE;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.12);
                margin: 4px 8px;
            }
        """)

        action_dashboard = QAction("⚡ Mở Bảng Điều Khiển NOVA", self)
        action_dashboard.triggered.connect(self.open_dashboard_signal.emit)

        action_listen = QAction("🎤 Lắng Nghe Ngay (Ctrl + Space)", self)
        action_listen.triggered.connect(self.trigger_listen_signal.emit)

        menu.addAction(action_dashboard)
        menu.addAction(action_listen)
        menu.addSeparator()

        action_quit = QAction("❌ Thoát NOVA", self)
        action_quit.triggered.connect(self.quit_signal.emit)
        menu.addAction(action_quit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_dashboard_signal.emit()
