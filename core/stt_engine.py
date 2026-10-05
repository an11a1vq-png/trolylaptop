import os
import threading
import numpy as np
from typing import Optional, Tuple

# Suppress HuggingFace cache and symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class STTEngine:
    """
    Hybrid Speech-to-Text Engine for NOVA:
    - Primary: Google Cloud Speech Recognition (Near 99% accuracy on Vietnamese, handles slow speech, 0 config/API key required).
    - Offline Fallback: Faster-Whisper (base model with int8, beam_size=3) if internet connection is unavailable.
    """
    def __init__(self, config: dict):
        self.config = config
        stt_cfg = config.get("speech_recognition", {})
        self.mode = stt_cfg.get("mode", "online_first")  # "online_first", "offline_only", "online_only"
        self.model_size = stt_cfg.get("model_size", "base")
        self.device = stt_cfg.get("device", "cpu")
        self.compute_type = stt_cfg.get("compute_type", "int8")
        self.language = stt_cfg.get("language", "vi")

        # Whisper offline model
        self.model: Optional[WhisperModel] = None
        self._load_lock = threading.Lock()

        # Online Google Recognizer
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None

        # Context priming prompt for Whisper offline decoder
        self.initial_prompt = (
            "NOVA, mở ứng dụng, mở chrome, youtube, bài hát, nghe nhạc, "
            "cài đặt, tắt máy, chụp màn hình, google, facebook, "
            "goose goose duck, liên minh, tft, game ngỗng, máy tính, thư mục"
        )

    def load_model(self) -> bool:
        """Preload Whisper offline model in background for seamless offline fallback."""
        if not WHISPER_AVAILABLE:
            print("[STT Error] Thư viện faster-whisper chưa được cài đặt!")
            return False

        with self._load_lock:
            if self.model is not None:
                return True

            try:
                print(f"[STT Offline] Đang nạp mô hình Whisper ({self.model_size}) trên {self.device} ({self.compute_type})...")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=4,
                    num_workers=1
                )
                print(f"[STT Offline] Đã nạp thành công mô hình Whisper ({self.model_size})!")
                return True
            except Exception as e:
                print(f"[STT Offline Load Error] {e}")
                return False

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[str, str]:
        """
        Transcribe audio numpy array (float32, 16kHz mono).
        1. Checks for silence or minimum duration.
        2. Normalizes audio gain.
        3. Attempts Online Google Speech Recognition for near 99% accuracy.
        4. If network fails or offline mode is chosen, seamlessly falls back to Whisper Offline.
        """
        if len(audio_data) < sample_rate * 0.3:
            return "", "unknown"

        # Check silence
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        if rms < 0.004:
            return "", self.language

        # Audio Normalization (boost quiet speech or scale loud speech cleanly)
        max_amp = float(np.max(np.abs(audio_data)))
        if max_amp > 0:
            normalized_audio = (audio_data / max_amp) * 0.85
        else:
            normalized_audio = audio_data

        # 1. Primary: Try Online Google Speech Recognition
        if self.mode in ["online_first", "online_only"] and self.recognizer is not None:
            try:
                int16_bytes = (np.clip(normalized_audio, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
                sr_audio = sr.AudioData(int16_bytes, sample_rate, 2)
                recognized_text = self.recognizer.recognize_google(sr_audio, language="vi-VN")

                if recognized_text and recognized_text.strip():
                    text_clean = recognized_text.strip()
                    print(f"[STT Online - Google] Nhận diện thành công (Độ chính xác cao): '{text_clean}'")
                    return text_clean, self.language
                else:
                    return "", self.language
            except sr.UnknownValueError:
                # Audio heard, but speech was unintelligible or non-word sound
                print("[STT Online - Google] Không nhận dạng được từ ngữ rõ ràng.")
                return "", self.language
            except (sr.RequestError, Exception) as e:
                print(f"[STT Online Warning] Lỗi kết nối Google STT: {e}")
                if self.mode == "online_only":
                    return "", "error"
                print("[STT] Đang chuyển sang Whisper Offline dự phòng...")

        # 2. Fallback: Local Whisper Offline
        if not WHISPER_AVAILABLE:
            return "", "error"

        if self.model is None:
            if not self.load_model():
                return "", "error"

        try:
            segments, info = self.model.transcribe(
                normalized_audio,
                language=self.language,
                beam_size=3,  # Higher accuracy than beam_size=1
                best_of=3,
                condition_on_previous_text=False,
                initial_prompt=self.initial_prompt,
                no_speech_threshold=0.6,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300)
            )

            text_segments = [seg.text for seg in segments]
            full_text = " ".join(text_segments).strip()
            print(f"[STT Offline - Whisper] Kết quả: '{full_text}'")
            return full_text, self.language
        except Exception as e:
            print(f"[STT Offline Error] {e}")
            return "", "error"
