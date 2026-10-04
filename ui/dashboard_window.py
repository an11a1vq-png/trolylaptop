import os
import yaml
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QTabWidget, QGroupBox,
    QComboBox, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from ui.slash_popup import SlashCommandPopup
from core.command_manager import command_manager


class DashboardWindow(QMainWindow):
    # Signals to communicate with core
    trigger_action_signal = pyqtSignal(str)
    trigger_text_command_signal = pyqtSignal(str)
    save_config_signal = pyqtSignal(dict)

    def __init__(self, config: dict, config_path: str):
        super().__init__()
        self.config = config
        self.config_path = config_path

        self.setWindowTitle("NOVA AI Assistant - Bảng Điều Khiển")
        self.resize(760, 570)
        self._setup_style()
        self._init_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0B10;
            }
            QWidget {
                color: #E8EAED;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid rgba(0, 242, 254, 0.25);
                background-color: #12131D;
                border-radius: 10px;
            }
            QTabBar::tab {
                background: #1A1C2C;
                color: #9AA0A6;
                padding: 10px 22px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #12131D;
                color: #00F2FE;
                border-bottom: 2px solid #00F2FE;
            }
            QPushButton {
                background-color: #00F2FE;
                color: #0A0B10;
                font-weight: 700;
                padding: 9px 18px;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4FACFE;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #00C4D6;
            }
            QPushButton.secondary {
                background-color: #222538;
                color: #E8EAED;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QPushButton.secondary:hover {
                background-color: #2E334D;
                border-color: rgba(0, 242, 254, 0.4);
            }
            QLineEdit, QTextEdit {
                background-color: #161826;
                color: #E8EAED;
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 6px;
                padding: 8px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #00F2FE;
            }
            QGroupBox {
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
                color: #00F2FE;
            }
        """)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # Header Title
        header_layout = QHBoxLayout()
        title_label = QLabel("⚡ NOVA AI ASSISTANT")
        title_label.setStyleSheet("font-size: 21px; font-weight: bold; color: #00F2FE; letter-spacing: 1px;")
        self.status_badge = QLabel("● NOVA ONLINE")
        self.status_badge.setStyleSheet("color: #00F2FE; font-size: 13px; font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_history_tab(), "Lịch Sử Lệnh")
        tabs.addTab(self._create_slash_commands_tab(), "Quản Lý Lệnh (/)")
        tabs.addTab(self._create_quick_actions_tab(), "Bảng Điều Khiển Nhanh")
        tabs.addTab(self._create_settings_tab(), "Cài Đặt & AI")
        main_layout.addWidget(tabs)

        # Load persisted conversation history on startup
        self._load_saved_history()

    def _load_saved_history(self):
        try:
            from core.memory_manager import memory_manager
            past_msgs = memory_manager.conversation_history[-15:]
            if past_msgs:
                self.log_text.append("<span style='color: #00F2FE;'><i>📜 Lịch sử hội thoại trước đó (Bộ nhớ vĩnh viễn):</i></span>")
                for item in past_msgs:
                    role = "User" if item.get("role") == "user" else "Assistant"
                    ts = item.get("timestamp", "").split(" ")[-1] if " " in item.get("timestamp", "") else ""
                    msg = item.get("content", "")
                    color = "#00F2FE" if role == "Assistant" else "#00FF87"
                    time_str = f"[{ts}] " if ts else ""
                    self.log_text.append(f"<span style='color: #7F8C8D;'>{time_str}</span><b style='color: {color};'>{role}:</b> {msg}")
                self.log_text.append("<span style='color: #00F2FE;'><i>──────────────────────────────────────────</i></span>")
        except Exception:
            pass

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        info_label = QLabel("Nhật ký đàm thoại & Thanh gõ lệnh trực tiếp:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Các câu lệnh nhận dạng và thao tác thực thi sẽ hiển thị tại đây...")

        # Bottom Chat Bar
        chat_layout = QHBoxLayout()
        self.dashboard_chat_input = QLineEdit()
        self.dashboard_chat_input.setPlaceholderText("💬 Nhập câu lệnh, câu hỏi, hoặc gõ '/' để xem danh sách lệnh...")
        self.dashboard_chat_input.returnPressed.connect(self._on_dashboard_chat_submit)

        send_btn = QPushButton("Gửi ↵")
        send_btn.clicked.connect(self._on_dashboard_chat_submit)

        chat_layout.addWidget(self.dashboard_chat_input)
        chat_layout.addWidget(send_btn)

        # Attach Slash Command Popup
        self.dashboard_slash_popup = SlashCommandPopup(self.dashboard_chat_input, parent=None)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Xóa lịch sử")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self._on_clear_history)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)

        layout.addWidget(info_label)
        layout.addWidget(self.log_text)
        layout.addLayout(chat_layout)
        layout.addLayout(btn_layout)
        return widget

    def _on_clear_history(self):
        try:
            from core.memory_manager import memory_manager
            memory_manager.clear_history_only()
        except Exception:
            pass
        self.log_text.clear()
        self.log_text.append("<span style='color: #7F8C8D;'><i>Đã xóa lịch sử trò chuyện. Thông tin ghi nhớ dài hạn (Tên, sở thích) vẫn được bảo toàn.</i></span>")

    def _on_dashboard_chat_submit(self):
        text = self.dashboard_chat_input.text().strip()
        if text:
            if hasattr(self, "dashboard_slash_popup"):
                self.dashboard_slash_popup.hide()
            self.dashboard_chat_input.clear()
            self.trigger_text_command_signal.emit(text)

    def hideEvent(self, event):
        if hasattr(self, "dashboard_slash_popup"):
            self.dashboard_slash_popup.hide()
        super().hideEvent(event)

    def _create_slash_commands_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_lbl = QLabel("Danh Sách Lệnh Slash (/) & Huấn Luyện Lệnh Mới:")
        header_lbl.setStyleSheet("font-weight: 700; color: #00F2FE; font-size: 14px;")
        layout.addWidget(header_lbl)

        # Table of Commands
        self.cmd_table = QTableWidget()
        self.cmd_table.setColumnCount(5)
        self.cmd_table.setHorizontalHeaderLabels(["Icon", "Tên Lệnh", "Loại", "Mô Tả / Hành Động", "Thao Tác"])
        self.cmd_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.cmd_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cmd_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cmd_table.setStyleSheet("""
            QTableWidget {
                background-color: #12131D;
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.05);
            }
            QHeaderView::section {
                background-color: #1A1C2C;
                color: #00F2FE;
                font-weight: 600;
                padding: 6px;
                border: none;
            }
        """)
        layout.addWidget(self.cmd_table)

        # Training Box
        train_box = QGroupBox("➕ Huấn Luyện / Thêm Lệnh Mới")
        train_layout = QVBoxLayout(train_box)
        train_layout.setSpacing(8)

        # Row 1: Name & Type
        row1 = QHBoxLayout()
        name_lbl = QLabel("Tên lệnh:")
        self.new_cmd_name = QLineEdit()
        self.new_cmd_name.setPlaceholderText("Ví dụ: /game hoặc /dich")

        type_lbl = QLabel("Loại lệnh:")
        self.new_cmd_type = QComboBox()
        self.new_cmd_type.addItem("🎮 Hành động máy tính / Mở app", "action")
        self.new_cmd_type.addItem("🧠 Prompt AI chuyên biệt", "ai_prompt")
        self.new_cmd_type.addItem("🌐 Mở liên kết Web", "web")

        row1.addWidget(name_lbl)
        row1.addWidget(self.new_cmd_name)
        row1.addWidget(type_lbl)
        row1.addWidget(self.new_cmd_type)
        train_layout.addLayout(row1)

        # Row 2: Content / Action
        row2 = QHBoxLayout()
        action_lbl = QLabel("Hành động / Prompt:")
        self.new_cmd_action = QLineEdit()
        self.new_cmd_action.setPlaceholderText("Ví dụ: 'mở goose goose duck' HOẶC 'Dịch đoạn sau sang tiếng Anh:'")
        row2.addWidget(action_lbl)
        row2.addWidget(self.new_cmd_action)
        train_layout.addLayout(row2)

        # Row 3: Description & Save Button
        row3 = QHBoxLayout()
        desc_lbl = QLabel("Mô tả ngắn:")
        self.new_cmd_desc = QLineEdit()
        self.new_cmd_desc.setPlaceholderText("Mô tả hiển thị trong menu gợi ý...")

        add_btn = QPushButton("💾 Lưu Lệnh Mới")
        add_btn.clicked.connect(self._on_add_custom_command)

        row3.addWidget(desc_lbl)
        row3.addWidget(self.new_cmd_desc)
        row3.addWidget(add_btn)
        train_layout.addLayout(row3)

        layout.addWidget(train_box)

        # Load initial commands into table
        self._reload_commands_table()
        return widget

    def _reload_commands_table(self):
        commands = command_manager.get_all_commands()
        self.cmd_table.setRowCount(len(commands))

        for row, cmd in enumerate(commands):
            icon_item = QTableWidgetItem(cmd.get("icon", "⚡"))
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            name_item = QTableWidgetItem(cmd.get("name", ""))
            name_item.setForeground(QColor("#00F2FE"))

            is_custom = cmd.get("type") in ["ai_prompt", "web"] or bool(cmd.get("action_content"))
            type_text = "Tùy chỉnh" if is_custom else "Hệ thống"
            type_item = QTableWidgetItem(type_text)
            if is_custom:
                type_item.setForeground(QColor("#A78BFA"))

            desc_item = QTableWidgetItem(cmd.get("desc", ""))

            self.cmd_table.setItem(row, 0, icon_item)
            self.cmd_table.setItem(row, 1, name_item)
            self.cmd_table.setItem(row, 2, type_item)
            self.cmd_table.setItem(row, 3, desc_item)

            if is_custom:
                del_btn = QPushButton("🗑 Xóa")
                del_btn.setProperty("class", "secondary")
                del_btn.setStyleSheet("padding: 3px 8px; font-size: 11px;")
                cmd_name = cmd.get("name")
                del_btn.clicked.connect(lambda checked, name=cmd_name: self._on_delete_custom_command(name))
                self.cmd_table.setCellWidget(row, 4, del_btn)
            else:
                lock_item = QTableWidgetItem("Cố định")
                lock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                lock_item.setForeground(QColor("#7F8C8D"))
                self.cmd_table.setItem(row, 4, lock_item)

    def _on_add_custom_command(self):
        name = self.new_cmd_name.text().strip()
        action = self.new_cmd_action.text().strip()
        desc = self.new_cmd_desc.text().strip()
        cmd_type = self.new_cmd_type.currentData()

        if not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên lệnh (ví dụ: /game).")
            return
        if not action:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập hành động hoặc prompt cho lệnh.")
            return

        icon = "🎮" if cmd_type == "action" else ("🧠" if cmd_type == "ai_prompt" else "🌐")
        success, msg = command_manager.add_custom_command(
            name=name,
            desc=desc or action,
            cmd_type=cmd_type,
            action_or_prompt=action,
            icon=icon,
            is_immediate=(cmd_type != "ai_prompt")
        )
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.new_cmd_name.clear()
            self.new_cmd_action.clear()
            self.new_cmd_desc.clear()
            self._reload_commands_table()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _on_delete_custom_command(self, name: str):
        reply = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn xóa lệnh '{name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = command_manager.delete_custom_command(name)
            self._reload_commands_table()

    def _create_quick_actions_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)

        # Test Mic & Activation
        mic_box = QGroupBox("Kích Hoạt Nhanh")
        mic_layout = QHBoxLayout(mic_box)
        listen_btn = QPushButton("🎤 Bắt đầu nghe ngay (Thay phím tắt)")
        listen_btn.clicked.connect(lambda: self.trigger_action_signal.emit("hotkey"))
        dictation_btn = QPushButton("📝 Bật/Tắt Gõ văn bản (Dictation)")
        dictation_btn.setProperty("class", "secondary")
        dictation_btn.clicked.connect(lambda: self.trigger_action_signal.emit("toggle_dictation"))
        mic_layout.addWidget(listen_btn)
        mic_layout.addWidget(dictation_btn)
        layout.addWidget(mic_box)

        # System controls
        sys_box = QGroupBox("Thao Tác Hệ Thống Nhanh")
        sys_layout = QVBoxLayout(sys_box)

        row1 = QHBoxLayout()
        vol_up_btn = QPushButton("🔊 Tăng âm lượng (+10%)")
        vol_up_btn.setProperty("class", "secondary")
        vol_up_btn.clicked.connect(lambda: self.trigger_action_signal.emit("tăng âm lượng"))
        vol_down_btn = QPushButton("🔉 Giảm âm lượng (-10%)")
        vol_down_btn.setProperty("class", "secondary")
        vol_down_btn.clicked.connect(lambda: self.trigger_action_signal.emit("giảm âm lượng"))
        mute_btn = QPushButton("🔇 Bật/Tắt tiếng")
        mute_btn.setProperty("class", "secondary")
        mute_btn.clicked.connect(lambda: self.trigger_action_signal.emit("tắt tiếng"))
        row1.addWidget(vol_up_btn)
        row1.addWidget(vol_down_btn)
        row1.addWidget(mute_btn)

        row2 = QHBoxLayout()
        shot_btn = QPushButton("📸 Chụp ảnh màn hình")
        shot_btn.setProperty("class", "secondary")
        shot_btn.clicked.connect(lambda: self.trigger_action_signal.emit("chụp màn hình"))
        lock_btn = QPushButton("🔒 Khóa màn hình")
        lock_btn.setProperty("class", "secondary")
        lock_btn.clicked.connect(lambda: self.trigger_action_signal.emit("khóa máy"))
        desk_btn = QPushButton("💻 Hiện màn hình Desktop")
        desk_btn.setProperty("class", "secondary")
        desk_btn.clicked.connect(lambda: self.trigger_action_signal.emit("hiện màn hình chính"))
        row2.addWidget(shot_btn)
        row2.addWidget(lock_btn)
        row2.addWidget(desk_btn)

        row3 = QHBoxLayout()
        chrome_btn = QPushButton("🌐 Mở Google Chrome")
        chrome_btn.setProperty("class", "secondary")
        chrome_btn.clicked.connect(lambda: self.trigger_action_signal.emit("mở chrome"))
        yt_btn = QPushButton("▶ Mở YouTube")
        yt_btn.setProperty("class", "secondary")
        yt_btn.clicked.connect(lambda: self.trigger_action_signal.emit("mở youtube"))
        folder_btn = QPushButton("📁 Mở thư mục dự án")
        folder_btn.setProperty("class", "secondary")
        folder_btn.clicked.connect(lambda: self.trigger_action_signal.emit("mở thư mục dự án"))
        row3.addWidget(chrome_btn)
        row3.addWidget(yt_btn)
        row3.addWidget(folder_btn)

        sys_layout.addLayout(row1)
        sys_layout.addLayout(row2)
        sys_layout.addLayout(row3)
        layout.addWidget(sys_box)
        layout.addStretch()
        return widget

    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)

        # General
        gen_box = QGroupBox("Từ Khóa & Phím Tắt")
        gen_layout = QVBoxLayout(gen_box)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Phím tắt kích hoạt:"))
        self.hotkey_input = QLineEdit(self.config.get("general", {}).get("activation_hotkey", "ctrl+space"))
        row1.addWidget(self.hotkey_input)
        gen_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Các từ khóa (ngăn cách bằng dấu phẩy):"))
        wake_words = ", ".join(self.config.get("general", {}).get("wake_words", ["hey google", "trợ lý ơi"]))
        self.wakewords_input = QLineEdit(wake_words)
        row2.addWidget(self.wakewords_input)
        gen_layout.addLayout(row2)
        layout.addWidget(gen_box)

        # Intelligence
        ai_box = QGroupBox("Cấu Hình Trí Tuệ AI (Hybrid Engine)")
        ai_layout = QVBoxLayout(ai_box)

        row_ollama = QHBoxLayout()
        row_ollama.addWidget(QLabel("Mô hình Ollama cục bộ:"))
        self.ollama_model_input = QLineEdit(self.config.get("intelligence", {}).get("ollama", {}).get("model", "qwen2.5:1.5b"))
        row_ollama.addWidget(self.ollama_model_input)
        ai_layout.addLayout(row_ollama)

        row_gemini = QHBoxLayout()
        row_gemini.addWidget(QLabel("Google Gemini API Key (Tùy chọn):"))
        self.gemini_key_input = QLineEdit(self.config.get("intelligence", {}).get("gemini", {}).get("api_key", ""))
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setPlaceholderText("Nhập API key nếu muốn câu trả lời trực tuyến siêu thông minh...")
        row_gemini.addWidget(self.gemini_key_input)
        ai_layout.addLayout(row_gemini)
        layout.addWidget(ai_box)

        # Save button
        save_btn = QPushButton("💾 Lưu Cài Đặt")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
        layout.addStretch()
        return widget

    def add_log(self, sender: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "#8AB4F8" if sender.lower() == "user" else "#81C995"
        self.log_text.append(f"<span style='color: #9AA0A6;'>[{timestamp}]</span> <b style='color: {color};'>{sender}:</b> {message}")

    def _save_settings(self):
        # Update config dictionary
        self.config["general"]["activation_hotkey"] = self.hotkey_input.text().strip()
        words = [w.strip() for w in self.wakewords_input.text().split(",") if w.strip()]
        self.config["general"]["wake_words"] = words
        self.config["intelligence"]["ollama"]["model"] = self.ollama_model_input.text().strip()
        self.config["intelligence"]["gemini"]["api_key"] = self.gemini_key_input.text().strip()

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt mới thành công!")
            self.save_config_signal.emit(self.config)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cấu hình: {e}")
