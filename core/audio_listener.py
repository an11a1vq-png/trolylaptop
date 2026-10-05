import time
import queue
import threading
import numpy as np
from typing import Callable, Optional

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


class AudioListener:
    """
    Microphone listener with dynamic ambient noise floor calibration,
    toggle-listening (Ctrl + Space to open, Ctrl + Space to close),
    and automatic timeout protection against background noise.
    """
    def __init__(
        self,
        config: dict,
        on_speech_recorded: Callable[[np.ndarray], None],
        on_listen_canceled: Optional[Callable[[str], None]] = None
    ):
        self.config = config
        stt_cfg = config.get("speech_recognition", {})
        gen_cfg = config.get("general", {})

        self.sample_rate = 16000
        self.silence_threshold_time = stt_cfg.get("silence_duration_seconds", 0.8)
        self.base_energy_threshold = float(stt_cfg.get("energy_threshold", 25.0))
        self.no_speech_timeout = 30.0  # Safe idle timeout (user can press Ctrl+Space anytime to close)

        self.on_speech_recorded = on_speech_recorded
        self.on_listen_canceled = on_listen_canceled

        self.audio_queue = queue.Queue()
        self.is_running = False
        self.is_recording = False
        self.speech_detected = False

        self.stream: Optional[sd.InputStream] = None
        self.recorded_frames = []
        self.silence_start_time = None
        self.record_start_time = None

        # Ambient noise calibration (real mic noise floor is ~1.8 - 2.8 RMS)
        self.ambient_noise_floor = 2.0
        self.effective_threshold = self.base_energy_threshold
        self.consecutive_speech_chunks = 0

    def _audio_callback(self, indata, frames, time_info, status):
        if not self.is_running:
            return

        rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))

        # Continually track room noise floor when idle
        if not self.is_recording:
            self.ambient_noise_floor = 0.90 * self.ambient_noise_floor + 0.10 * float(rms)
        else:
            self.audio_queue.put(indata.copy())

    def start(self):
        """Start background microphone stream."""
        if not SOUNDDEVICE_AVAILABLE:
            print("[AudioListener Error] sounddevice chưa sẵn sàng!")
            return False

        if self.is_running:
            return True

        self.is_running = True
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=1024,
                callback=self._audio_callback
            )
            self.stream.start()
            threading.Thread(target=self._process_stream, daemon=True).start()
            print("[AudioListener] Micro đã khởi động! Chế độ Toggle: Bấm Ctrl+Space để mở / đóng.")
            return True
        except Exception as e:
            print(f"[Audio Stream Error] {e}")
            self.is_running = False
            return False

    def trigger_hotkey_listen(self):
        """Called on 1st Ctrl + Space press: starts listening with dynamic noise threshold."""
        self.recorded_frames.clear()
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        # Dynamically set speech threshold higher than measured ambient noise
        self.effective_threshold = max(
            float(self.base_energy_threshold),
            float(self.ambient_noise_floor * 2.5 + 8.0)
        )
        self.speech_detected = False
        self.consecutive_speech_chunks = 0
        self.silence_start_time = None
        self.record_start_time = time.time()
        self.is_recording = True
        print(f"[AudioListener] Đã bật micro! (Độ ồn nền: {round(self.ambient_noise_floor, 1)}, Ngưỡng phát hiện: {round(self.effective_threshold, 1)})")

    def stop_listen_manually(self) -> bool:
        """
        Called on 2nd Ctrl + Space press: toggles listening OFF immediately.
        If speech/audio was captured (>0.25s), transcribes it immediately instead of canceling.
        """
        if not self.is_recording:
            return False

        if len(self.recorded_frames) > 4:
            print("[AudioListener] Nhận phím tắt đóng (Ctrl + Space): Đang xử lý giọng nói đã ghi...")
            self._finish_phrase(force_transcribe=True)
            return True
        else:
            print("[AudioListener] Nhận phím tắt đóng (Ctrl + Space): Đã tắt micro.")
            self._cancel_listen(reason="manual_stop")
            return False

    def _process_stream(self):
        while self.is_running:
            if not self.is_recording:
                time.sleep(0.04)
                continue

            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self.recorded_frames.append(data)
            rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))

            # State A: Waiting for user to start speaking
            if not self.speech_detected:
                # Safety timeout if user opened mic but didn't speak for 30s
                if self.record_start_time and (time.time() - self.record_start_time > self.no_speech_timeout):
                    print(f"[AudioListener] Không phát hiện giọng nói sau {self.no_speech_timeout}s -> Tự động đóng micro.")
                    self._cancel_listen(reason="timeout")
                    continue

                if rms > self.effective_threshold:
                    self.consecutive_speech_chunks += 1
                    if self.consecutive_speech_chunks >= 1:
                        self.speech_detected = True
                        self.silence_start_time = None
                        print(f"[AudioListener] Đã nhận diện tiếng nói (RMS: {round(rms, 1)})")
                else:
                    self.consecutive_speech_chunks = 0

            # State B: User started speaking, now track silence to finish phrase
            else:
                if rms < self.effective_threshold:
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    elif time.time() - self.silence_start_time >= self.silence_threshold_time:
                        print(f"[AudioListener] Kết thúc câu lệnh sau {self.silence_threshold_time}s im lặng.")
                        self._finish_phrase()
                        continue
                else:
                    self.silence_start_time = None

                # Safety maximum duration (15.0 seconds of continuous speech)
                if self.record_start_time and (time.time() - self.record_start_time > 15.0):
                    print("[AudioListener] Đạt giới hạn thời gian ghi âm (15s) -> Đang xử lý...")
                    self._finish_phrase()

    def _finish_phrase(self, force_transcribe: bool = False):
        """Finish recording and send to STT if valid speech was detected."""
        was_detected = self.speech_detected or force_transcribe
        frames_count = len(self.recorded_frames)

        self.is_recording = False
        self.speech_detected = False
        self.silence_start_time = None
        self.record_start_time = None

        if was_detected and frames_count > 4:
            raw_audio = np.concatenate(self.recorded_frames, axis=0)
            float_audio = raw_audio.astype(np.float32) / 32768.0
            float_audio = np.squeeze(float_audio)
            self.recorded_frames.clear()
            self.on_speech_recorded(float_audio)
        else:
            self._cancel_listen(reason="too_short_or_no_speech")

    def _cancel_listen(self, reason: str = "canceled"):
        """Cleanly cancel listening and reset state."""
        self.is_recording = False
        self.speech_detected = False
        self.silence_start_time = None
        self.record_start_time = None
        self.recorded_frames.clear()

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        if self.on_listen_canceled:
            self.on_listen_canceled(reason)

    def stop(self):
        """Stop microphone stream and worker thread."""
        self.is_running = False
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
