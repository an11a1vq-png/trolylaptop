from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QPoint
from PyQt6.QtGui import QColor, QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QGraphicsDropShadowEffect, QLineEdit
)
from typing import List, Dict, Any, Optional
from core.command_manager import command_manager


class SlashCommandItemWidget(QWidget):
    """Custom item row in the slash command popup."""
    def __init__(self, cmd: Dict[str, Any], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Icon
        icon_lbl = QLabel(cmd.get("icon", "⚡"))
        icon_lbl.setStyleSheet("font-size: 16px; border: none; background: transparent;")
        layout.addWidget(icon_lbl)

        # Name
        name_lbl = QLabel(cmd.get("name", ""))
        name_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #00F2FE; border: none; background: transparent;")
        layout.addWidget(name_lbl)

        # Custom Badge if user-trained
        if cmd.get("type") in ["ai_prompt", "web"] or cmd.get("action_content"):
            badge_lbl = QLabel("Tùy chỉnh")
            badge_lbl.setStyleSheet("""
                font-size: 10px;
                color: #A78BFA;
                background-color: rgba(167, 139, 250, 0.2);
                border: 1px solid rgba(167, 139, 250, 0.4);
                border-radius: 4px;
                padding: 1px 4px;
            """)
            layout.addWidget(badge_lbl)

        # Description
        desc_lbl = QLabel(cmd.get("desc", ""))
        desc_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; border: none; background: transparent;")
        layout.addWidget(desc_lbl)
        layout.addStretch()


class SlashCommandPopup(QWidget):
    """
    Floating command palette popup that appears when typing '/' in a QLineEdit.
    """
    command_selected_signal = pyqtSignal(dict)  # emits selected command dict

    def __init__(self, target_input: QLineEdit, parent=None):
        super().__init__(parent)
        self.target_input = target_input
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._init_ui()
        self._install_listeners()

    def _init_ui(self):
        self.setFixedWidth(520)
        self.setFixedHeight(230)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 17, 26, 0.98);
                border: 1px solid rgba(0, 242, 254, 0.5);
                border-radius: 12px;
            }
        """)

        # Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 242, 254, 120))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(4)

        # Header Hint
        hint_lbl = QLabel("  GỢI Ý LỆNH SLASH (↑ ↓ để chọn, Enter để áp dụng, Esc để đóng)")
        hint_lbl.setStyleSheet("font-size: 10px; font-weight: 600; color: #00F2FE; letter-spacing: 0.5px; border: none; background: transparent;")
        container_layout.addWidget(hint_lbl)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 2px;
                color: #FFFFFF;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 242, 254, 0.12);
            }
            QListWidget::item:selected {
                background-color: rgba(0, 242, 254, 0.25);
                border: 1px solid rgba(0, 242, 254, 0.5);
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        container_layout.addWidget(self.list_widget)

        main_layout.addWidget(self.container)

    def _install_listeners(self):
        """Install event filter on target QLineEdit to capture text and keys."""
        self.target_input.installEventFilter(self)
        self.target_input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        """Monitor text changes to show/filter/hide popup."""
        stripped = text.strip()
        if stripped.startswith("/") and len(stripped.split()) <= 1:
            self.refresh_list(stripped)
            if self.list_widget.count() > 0:
                self.show_at_input()
            else:
                self.hide()
        else:
            self.hide()

    def refresh_list(self, query: str):
        """Populate list widget with filtered commands."""
        self.list_widget.clear()
        commands = command_manager.search_commands(query)
        for cmd in commands:
            item = QListWidgetItem(self.list_widget)
            widget = SlashCommandItemWidget(cmd)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        # Adjust height based on item count (up to 5 items)
        visible_count = min(self.list_widget.count(), 5)
        calc_height = max(110, visible_count * 40 + 40)
        self.setFixedHeight(calc_height)

    def show_at_input(self):
        """Position popup nicely above or below the input field."""
        if not self.target_input.isVisible():
            return
        
        # Calculate target position
        input_pos = self.target_input.mapToGlobal(QPoint(0, 0))
        input_height = self.target_input.height()
        input_width = self.target_input.width()

        self.setFixedWidth(max(480, min(input_width, 620)))

        # Default place directly below input
        target_x = input_pos.x()
        target_y = input_pos.y() + input_height + 6

        # Check screen bounds
        screen = self.target_input.screen()
        if screen:
            screen_geo = screen.availableGeometry()
            # If goes below screen, place above input
            if target_y + self.height() > screen_geo.bottom():
                target_y = input_pos.y() - self.height() - 6

        self.move(target_x, target_y)
        self.show()
        self.raise_()

    def eventFilter(self, obj, event):
        """Intercept arrow keys and enter in the target QLineEdit when popup is visible."""
        if obj == self.target_input and self.isVisible():
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key == Qt.Key.Key_Down:
                    curr = self.list_widget.currentRow()
                    if curr < self.list_widget.count() - 1:
                        self.list_widget.setCurrentRow(curr + 1)
                    return True
                elif key == Qt.Key.Key_Up:
                    curr = self.list_widget.currentRow()
                    if curr > 0:
                        self.list_widget.setCurrentRow(curr - 1)
                    return True
                elif key in [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab]:
                    curr_item = self.list_widget.currentItem()
                    if curr_item:
                        cmd = curr_item.data(Qt.ItemDataRole.UserRole)
                        if cmd:
                            self._apply_command(cmd)
                            return True
                elif key == Qt.Key.Key_Escape:
                    self.hide()
                    return True

        return super().eventFilter(obj, event)

    def _on_item_clicked(self, item: QListWidgetItem):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd:
            self._apply_command(cmd)

    def _apply_command(self, cmd: Dict[str, Any]):
        """Apply chosen slash command to input field."""
        self.hide()
        is_immediate = cmd.get("is_immediate", False)
        insert_text = cmd.get("insert_text", cmd.get("name", ""))

        if is_immediate:
            self.target_input.setText(insert_text)
            self.command_selected_signal.emit(cmd)
            # Trigger submission on input
            self.target_input.returnPressed.emit()
        else:
            self.target_input.setText(insert_text)
            placeholder = cmd.get("placeholder", "")
            if placeholder:
                self.target_input.setPlaceholderText(placeholder)
            self.target_input.setFocus()
            self.command_selected_signal.emit(cmd)
