import os
import threading
import numpy as np
from typing import Optional, Tuple

# Suppress HuggingFace cache and symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class STTEngine:
    def __init__(self, config: dict):
        self.config = config
        stt_cfg = config.get("speech_recognition", {})
        self.model_size = stt_cfg.get("model_size", "tiny")
        self.device = stt_cfg.get("device", "cpu")
        self.compute_type = stt_cfg.get("compute_type", "int8")
        self.language = stt_cfg.get("language", "vi")  # Khóa tiếng Việt
        self.model: Optional[WhisperModel] = None
        self._load_lock = threading.Lock()

    def load_model(self) -> bool:
        """Thread-safe preload of Whisper model."""
        if not WHISPER_AVAILABLE:
            print("[STT Error] Thư viện faster-whisper chưa được cài đặt!")
            return False

        with self._load_lock:
            if self.model is not None:
                return True

            try:
                print(f"[STT] Đang tải mô hình Whisper ({self.model_size}) trên {self.device} ({self.compute_type})...")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=4,
                    num_workers=1
                )
                print(f"[STT] Đã nạp thành công mô hình Whisper (Ngôn ngữ: Tiếng Việt)!")
                return True
            except Exception as e:
                print(f"[STT Load Error] {e}")
                return False

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, str]:
        """
        Transcribe audio numpy array (float32, 16kHz mono).
        Enforces Vietnamese to completely eliminate foreign language hallucinations.
        """
        if self.model is None:
            if not self.load_model():
                return "", "unknown"

        try:
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Check if audio is completely silent
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < 0.005:  # Pure silence or very low noise
                return "", self.language

            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,  # Cố định tiếng Việt
                beam_size=1,            # Tốc độ nhanh hơn trên CPU
                best_of=1,
                condition_on_previous_text=False,  # Tránh lặp ảo giác
                no_speech_threshold=0.6,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300)
            )

            text_segments = [seg.text for seg in segments]
            full_text = " ".join(text_segments).strip()
            return full_text, self.language
        except Exception as e:
            print(f"[Transcription Error] {e}")
            return "", "error"
