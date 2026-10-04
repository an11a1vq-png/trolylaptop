import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import sys

# Configure UTF-8 encoding for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import yaml
import threading
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication

from core.audio_listener import AudioListener
from core.stt_engine import STTEngine
from core.tts_engine import TTSEngine
from core.intent_router import IntentRouter
from core.brain_hybrid import HybridBrain
from core.wake_word import WakeWordDetector

from ui.overlay_widget import FloatingOverlayWidget
from ui.dashboard_window import DashboardWindow
from ui.tray_icon import AssistantTrayIcon
from ui.spotlight_bar import SpotlightBar


class AssistantCoordinator(QObject):
    # Signals for thread-safe UI updates from background threads
    show_listening_signal = pyqtSignal()
    show_thinking_signal = pyqtSignal(str)
    show_response_signal = pyqtSignal(str)
    show_spotlight_signal = pyqtSignal()
    log_message_signal = pyqtSignal(str, str)

    def __init__(self, config_path: str):
        super().__init__()
        self.config_path = config_path
        self.config = self._load_config()

        # Assets
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.beep_listen = os.path.join(self.assets_dir, "beep_listen.wav")
        self.beep_done = os.path.join(self.assets_dir, "beep_done.wav")

        # Core Engines
        self.tts = TTSEngine(self.config)
        self.stt = STTEngine(self.config)
        self.router = IntentRouter(self.config)
        self.brain = HybridBrain(self.config)

        # UI Components
        self.overlay = FloatingOverlayWidget()
        self.dashboard = DashboardWindow(self.config, self.config_path)
        self.tray = AssistantTrayIcon()
        self.spotlight = SpotlightBar()

        # Connect GUI Signals
        self.show_listening_signal.connect(self.overlay.show_listening)
        self.show_thinking_signal.connect(self.overlay.show_thinking)
        self.show_response_signal.connect(self.overlay.show_response)
        self.show_spotlight_signal.connect(self.spotlight.show_spotlight)
        self.log_message_signal.connect(self.dashboard.add_log)

        # Connect Tray & Dashboard events
        self.tray.open_dashboard_signal.connect(self.dashboard.show)
        self.tray.trigger_listen_signal.connect(self._on_hotkey_activated)
        self.tray.trigger_spotlight_signal.connect(self.spotlight.show_spotlight)
        self.tray.quit_signal.connect(self.shutdown)

        self.dashboard.trigger_action_signal.connect(self._on_dashboard_trigger)
        self.dashboard.trigger_text_command_signal.connect(self._on_dashboard_text_submit)
        self.dashboard.save_config_signal.connect(self._on_config_updated)

        # Connect Spotlight Bar
        self.spotlight.submit_command_signal.connect(self._on_spotlight_submit)

        # Audio & Wake Word (Both Voice Hotkey & Spotlight Text Hotkey)
        self.listener = AudioListener(self.config, on_speech_recorded=self._on_speech_recorded)
        self.wake_detector = WakeWordDetector(
            self.config,
            on_activation=self._on_hotkey_activated,
            on_text_activation=self._on_text_hotkey_activated
        )

        # State
        self.is_waiting_direct_command = False

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def start(self):
        """Start all services."""
        print("[Assistant] Khởi động NOVA AI Assistant...")
        self.tray.show()
        self.dashboard.show()

        # Preload STT and Ollama LLM in background threads to avoid GUI freeze and cold-start latency
        threading.Thread(target=self.stt.load_model, daemon=True).start()
        threading.Thread(target=self.brain.preload_model, daemon=True).start()

        # Start microphone listener and hotkeys
        self.listener.start()
        self.wake_detector.start_hotkey_listener()

        self.log_message_signal.emit("System", "⚡ Hệ thống trợ lý AI NOVA đã sẵn sàng hoạt động!")

    def _on_hotkey_activated(self, source: str = "hotkey"):
        """Called when Ctrl + Space is pressed (Voice Mode)."""
        self.tts.stop()  # Ngắt lời tức thì nếu AI đang nói
        self.is_waiting_direct_command = True
        self.listener.trigger_hotkey_listen()
        self.tts.play_sound_effect(self.beep_listen)
        self.show_listening_signal.emit()

    def _on_text_hotkey_activated(self):
        """Called when Ctrl + Shift + Space is pressed (Spotlight Bar)."""
        self.show_spotlight_signal.emit()

    def _on_spotlight_submit(self, text: str):
        """Command submitted from floating Spotlight bar."""
        threading.Thread(target=self._process_command, args=(text,), kwargs={"is_voice": False, "source": "spotlight"}, daemon=True).start()

    def _on_dashboard_text_submit(self, text: str):
        """Command submitted from Dashboard text chat box."""
        threading.Thread(target=self._process_command, args=(text,), kwargs={"is_voice": False, "source": "dashboard"}, daemon=True).start()

    def _on_dashboard_trigger(self, action_text: str):
        if action_text == "hotkey":
            self._on_hotkey_activated()
        elif action_text == "toggle_dictation":
            from actions.voice_dictation import dictation_manager
            is_active, msg = dictation_manager.toggle()
            self.show_response_signal.emit(msg)
            self.tts.speak(msg)
            self.log_message_signal.emit("Assistant", msg)
        else:
            threading.Thread(target=self._process_command, args=(action_text,), kwargs={"is_voice": True, "source": "dashboard_button"}, daemon=True).start()

    def _on_config_updated(self, new_config: dict):
        self.config = new_config
        self.tts = TTSEngine(self.config)
        self.router = IntentRouter(self.config)
        self.brain = HybridBrain(self.config)
        self.log_message_signal.emit("System", "Đã cập nhật cấu hình mới vào hệ thống.")

    def _on_speech_recorded(self, audio_data: np.ndarray):
        """Received raw speech audio from listener in background thread."""
        threading.Thread(target=self._process_speech_worker, args=(audio_data,), daemon=True).start()

    def _process_speech_worker(self, audio_data: np.ndarray):
        text, lang = self.stt.transcribe(audio_data)
        if not text.strip():
            return

        print(f"[STT] Nhận diện (Tiếng Việt): {text}")

        # Check if dictation mode is on
        from actions.voice_dictation import dictation_manager
        if dictation_manager.is_dictating:
            dictation_manager.type_text(text)
            self.show_response_signal.emit(f"Đã gõ: {text}")
            return

        # Strip any optional wake word if spoken (e.g. 'Nova mở Chrome' -> 'mở Chrome')
        is_wake, clean_cmd = self.wake_detector.check_wake_word_in_text(text)
        command_to_run = clean_cmd if (is_wake and clean_cmd) else text

        self.show_thinking_signal.emit(command_to_run)
        self._process_command(command_to_run, is_voice=True, source="voice")

    def _process_command(self, query: str, is_voice: bool = True, source: str = "voice"):
        self.log_message_signal.emit("User", query)

        # 1. Route to Rule-Based / Dictation / Safety
        handled, result_text, action_type = self.router.route_text(query)

        if handled:
            if is_voice:
                self.show_response_signal.emit(result_text)
                self.tts.play_sound_effect(self.beep_done)
                self.tts.speak(result_text)
            else:
                # Silent mode for typed text commands
                if source == "spotlight":
                    self.spotlight.show_result(result_text, auto_hide=True)
            self.log_message_signal.emit("Assistant", result_text)
        else:
            # 2. Free Conversational Query -> Hybrid Brain
            if is_voice:
                self.show_thinking_signal.emit("Đang suy luận...")
                ai_reply = self.brain.think_and_reply(query)
                self.show_response_signal.emit(ai_reply)
                self.tts.speak(ai_reply)
            else:
                # Silent mode for typed text commands
                if source == "spotlight":
                    self.spotlight.show_result("Đang suy luận...", auto_hide=False)
                ai_reply = self.brain.think_and_reply(query)
                if source == "spotlight":
                    self.spotlight.show_result(ai_reply, auto_hide=False)

            self.log_message_signal.emit("Assistant", ai_reply)

    def shutdown(self):
        print("[Assistant] Đang dừng tất cả dịch vụ...")
        self.listener.stop()
        self.tts.stop()
        os.system("taskkill /F /IM ollama.exe >nul 2>&1")
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    coordinator = AssistantCoordinator(config_path)
    coordinator.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
