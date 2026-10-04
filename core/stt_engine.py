import os
import numpy as np
from typing import Optional, Tuple

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
        self.model: Optional[WhisperModel] = None
        self._is_loading = False

    def load_model(self):
        """Preload the Whisper model into memory."""
        if not WHISPER_AVAILABLE:
            print("[STT Error] Thư viện faster-whisper chưa được cài đặt!")
            return False

        if self.model is not None:
            return True

        self._is_loading = True
        try:
            print(f"[STT] Đang tải mô hình Whisper ({self.model_size}) trên {self.device} ({self.compute_type})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
                num_workers=1
            )
            print("[STT] Đã nạp thành công mô hình Whisper!")
            self._is_loading = False
            return True
        except Exception as e:
            print(f"[STT Load Error] {e}")
            self._is_loading = False
            return False

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, str]:
        """
        Transcribe audio numpy array (float32, 16kHz mono).
        Returns: (transcribed_text, detected_language)
        """
        if self.model is None:
            if not self.load_model():
                return "", "unknown"

        try:
            # faster-whisper accepts float32 numpy array normalized between -1.0 and 1.0
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            segments, info = self.model.transcribe(
                audio_data,
                beam_size=2,
                best_of=2,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            text_segments = [seg.text for seg in segments]
            full_text = " ".join(text_segments).strip()
            detected_lang = info.language if info else "vi"

            return full_text, detected_lang
        except Exception as e:
            print(f"[Transcription Error] {e}")
            return "", "error"
