import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import asyncio
import threading
import tempfile
from typing import Optional

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class TTSEngine:
    def __init__(self, config: dict):
        self.config = config
        self.tts_cfg = config.get("text_to_speech", {})
        self.voice_vi = self.tts_cfg.get("online_voice_vi", "vi-VN-HoaiMyNeural")
        self.voice_en = self.tts_cfg.get("online_voice_en", "en-US-JennyNeural")
        self.rate = self.tts_cfg.get("rate", "+0%")
        self.volume = self.tts_cfg.get("volume", "+0%")
        self.prefer_online = self.tts_cfg.get("prefer_online", True)
        
        self._init_audio()
        self._init_pyttsx3()
        self.is_speaking = False

    def _init_audio(self):
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"[Audio Init Warning] {e}")

    def _init_pyttsx3(self):
        self.offline_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.offline_engine = pyttsx3.init()
                self.offline_engine.setProperty('rate', 160)
            except Exception as e:
                print(f"[pyttsx3 Init Warning] {e}")

    def play_sound_effect(self, sound_path: str):
        """Play short wav sound effect without blocking."""
        if not os.path.exists(sound_path) or not PYGAME_AVAILABLE:
            return
        def _play():
            try:
                sound = pygame.mixer.Sound(sound_path)
                sound.play()
            except Exception as e:
                print(f"[Sound Play Error] {e}")
        threading.Thread(target=_play, daemon=True).start()

    def speak(self, text: str, callback_on_finish=None):
        """Speak the given text asynchronously."""
        if not text.strip():
            return
        threading.Thread(target=self._speak_worker, args=(text, callback_on_finish), daemon=True).start()

    def _speak_worker(self, text: str, callback_on_finish):
        self.is_speaking = True
        success = False

        # Detect language heuristic (Check for Vietnamese diacritics)
        is_vietnamese = any(ord(c) > 127 for c in text)
        voice = self.voice_vi if is_vietnamese else self.voice_en

        # 1. Try Edge-TTS (Neural, human-like voice)
        if self.prefer_online and EDGE_TTS_AVAILABLE:
            try:
                temp_file = os.path.join(tempfile.gettempdir(), f"tts_{os.getpid()}_{int(pygame.time.get_ticks() if PYGAME_AVAILABLE else 0)}.mp3")
                asyncio.run(self._generate_edge_tts(text, voice, temp_file))
                
                if os.path.exists(temp_file):
                    self._play_file(temp_file)
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                    success = True
            except Exception as e:
                print(f"[Edge-TTS Error, falling back to offline] {e}")

        # 2. Fallback to offline pyttsx3
        if not success and self.offline_engine:
            try:
                self.offline_engine.say(text)
                self.offline_engine.runAndWait()
                success = True
            except Exception as e:
                print(f"[pyttsx3 Error] {e}")

        self.is_speaking = False
        if callback_on_finish:
            callback_on_finish()

    async def _generate_edge_tts(self, text: str, voice: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice, rate=self.rate, volume=self.volume)
        await communicate.save(output_path)

    def _play_file(self, file_path: str):
        if not PYGAME_AVAILABLE:
            return
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"[Audio playback error] {e}")

    def stop(self):
        """Stop any active speech."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.is_speaking = False
