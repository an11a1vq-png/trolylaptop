import os
import yaml
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QTabWidget, QGroupBox,
    QComboBox, QCheckBox, QMessageBox
)


class DashboardWindow(QMainWindow):
    # Signals to communicate with core
    trigger_action_signal = pyqtSignal(str)
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
        tabs.addTab(self._create_quick_actions_tab(), "Bảng Điều Khiển Nhanh")
        tabs.addTab(self._create_settings_tab(), "Cài Đặt & AI")
        main_layout.addWidget(tabs)

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)

        info_label = QLabel("Nhật ký nhận diện giọng nói và phản hồi của trợ lý:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Các câu lệnh nhận dạng và thao tác thực thi sẽ hiển thị tại đây...")

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Xóa lịch sử")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)

        layout.addWidget(info_label)
        layout.addWidget(self.log_text)
        layout.addLayout(btn_layout)
        return widget

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
