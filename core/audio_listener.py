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
        self.sample_rate = 16000
        self.silence_threshold_time = stt_cfg.get("silence_duration_seconds", 1.2)
        self.energy_threshold = stt_cfg.get("energy_threshold", 500)
        self.on_speech_recorded = on_speech_recorded

        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_recording_phrase = False
        self.stream: Optional[sd.InputStream] = None
        self.recorded_frames = []
        self.silence_start_time = None
        self.force_recording = False  # Triggered by hotkey

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        self.audio_queue.put(indata.copy())

    def start(self):
        """Start background microphone stream."""
        if not SOUNDDEVICE_AVAILABLE:
            print("[AudioListener Error] sounddevice chưa sẵn sàng!")
            return False

        if self.is_listening:
            return True

        self.is_listening = True
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
            return True
        except Exception as e:
            print(f"[Audio Stream Error] {e}")
            self.is_listening = False
            return False

    def trigger_hotkey_listen(self):
        """Force activate listening immediately (e.g. from Ctrl + Space)."""
        self.force_recording = True
        self.is_recording_phrase = True
        self.recorded_frames.clear()
        self.silence_start_time = None
        print("[AudioListener] Kích hoạt thu âm qua Phím tắt!")

    def _process_stream(self):
        while self.is_listening:
            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Calculate Root Mean Square (RMS) energy
            rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))

            if self.force_recording:
                # In hotkey mode, record immediately
                self.recorded_frames.append(data)
                if rms < self.energy_threshold:
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    elif time.time() - self.silence_start_time >= self.silence_threshold_time:
                        # End phrase
                        self._finish_phrase()
                else:
                    self.silence_start_time = None
            else:
                # Normal voice activity detection mode
                if not self.is_recording_phrase:
                    if rms > self.energy_threshold:
                        self.is_recording_phrase = True
                        self.recorded_frames = [data]
                        self.silence_start_time = None
                else:
                    self.recorded_frames.append(data)
                    if rms < self.energy_threshold:
                        if self.silence_start_time is None:
                            self.silence_start_time = time.time()
                        elif time.time() - self.silence_start_time >= self.silence_threshold_time:
                            self._finish_phrase()
                    else:
                        self.silence_start_time = None

    def _finish_phrase(self):
        self.force_recording = False
        self.is_recording_phrase = False
        self.silence_start_time = None

        if len(self.recorded_frames) > 5:
            # Concatenate int16 frames and convert to float32 (-1.0 to 1.0)
            raw_audio = np.concatenate(self.recorded_frames, axis=0)
            float_audio = raw_audio.astype(np.float32) / 32768.0
            float_audio = np.squeeze(float_audio)
            self.recorded_frames.clear()
            # Dispatch to callback
            self.on_speech_recorded(float_audio)

    def stop(self):
        self.is_listening = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
