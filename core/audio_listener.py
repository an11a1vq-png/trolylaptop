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
    def __init__(self, config: dict, on_speech_recorded: Callable[[np.ndarray], None]):
        self.config = config
        stt_cfg = config.get("speech_recognition", {})
        gen_cfg = config.get("general", {})
        
        self.sample_rate = 16000
        self.silence_threshold_time = stt_cfg.get("silence_duration_seconds", 0.9)
        self.energy_threshold = stt_cfg.get("energy_threshold", 800)
        self.activation_mode = gen_cfg.get("activation_mode", "hotkey_only")
        self.on_speech_recorded = on_speech_recorded

        self.audio_queue = queue.Queue()
        self.is_running = False
        self.is_recording = False
        self.speech_detected = False
        self.stream: Optional[sd.InputStream] = None
        self.recorded_frames = []
        self.silence_start_time = None
        self.record_start_time = None

    def _audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
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
            print("[AudioListener] Micro sẵn sàng ở chế độ Phím tắt (Ctrl + Space) - 0% tạp âm nền!")
            return True
        except Exception as e:
            print(f"[Audio Stream Error] {e}")
            self.is_running = False
            return False

    def trigger_hotkey_listen(self):
        """Called when Ctrl + Space or UI button is pressed."""
        self.recorded_frames.clear()
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        self.speech_detected = False
        self.silence_start_time = None
        self.record_start_time = time.time()
        self.is_recording = True
        print("[AudioListener] Đã bật micro! Hãy nói câu lệnh...")

    def _process_stream(self):
        while self.is_running:
            if not self.is_recording:
                time.sleep(0.05)
                continue

            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self.recorded_frames.append(data)
            rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))

            # Check if user started speaking
            if rms > self.energy_threshold:
                self.speech_detected = True
                self.silence_start_time = None

            # After user started speaking, check for silence to end phrase
            if self.speech_detected:
                if rms < self.energy_threshold:
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    elif time.time() - self.silence_start_time >= self.silence_threshold_time:
                        self._finish_phrase()
                        continue
                else:
                    self.silence_start_time = None

            # Safety maximum duration (8 seconds without ending)
            if self.record_start_time and (time.time() - self.record_start_time > 8.0):
                self._finish_phrase()

    def _finish_phrase(self):
        self.is_recording = False
        self.speech_detected = False
        self.silence_start_time = None
        self.record_start_time = None

        if len(self.recorded_frames) > 8:  # At least 0.5s of audio
            raw_audio = np.concatenate(self.recorded_frames, axis=0)
            float_audio = raw_audio.astype(np.float32) / 32768.0
            float_audio = np.squeeze(float_audio)
            self.recorded_frames.clear()
            self.on_speech_recorded(float_audio)
        else:
            self.recorded_frames.clear()

    def stop(self):
        self.is_running = False
        self.is_recording = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
