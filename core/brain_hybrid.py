import os
import time
import subprocess
import json
import requests
import datetime
import platform
import re
from typing import Tuple, Optional, Callable, List, Dict


SYSTEM_PROMPT = """Bạn là NOVA, hệ thống trợ lý AI cá nhân thông minh trên máy tính Windows.
Phong cách giao tiếp của bạn:
- Tối giản, siêu nhanh, dứt khoát và chính xác tuyệt đối.
- Báo cáo kết quả trực tiếp, không chào hỏi hay xưng hô rườm rà.
- Trả lời bằng cùng ngôn ngữ của người dùng (tiếng Việt hoặc tiếng Anh)."""


class HybridBrain:
    def __init__(self, config: dict):
        self.config = config
        self.intel_cfg = config.get("intelligence", {})
        self.ollama_cfg = self.intel_cfg.get("ollama", {})
        self.gemini_cfg = self.intel_cfg.get("gemini", {})
        self.mode = self.intel_cfg.get("engine_mode", "hybrid")

        # Load local .env secrets if present
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip()
            except Exception:
                pass

        # Multi-turn Conversation Memory (stores last N turns)
        self.history: List[Dict[str, str]] = []
        self.max_history_turns = 8  # 8 turns = 16 messages

    def clear_memory(self) -> str:
        """Reset conversation context memory."""
        self.history.clear()
        return "Đã xóa toàn bộ ngữ cảnh trò chuyện trước đó."

    def think_and_reply(self, user_query: str, on_sentence_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process user query with multi-turn memory and optional streaming voice response.
        """
        query_lower = user_query.strip().lower()

        # Check Memory Reset command
        if any(q in query_lower for q in ["xóa bộ nhớ", "xóa lịch sử trò chuyện", "quên các câu trước", "bắt đầu cuộc trò chuyện mới", "reset memory"]):
            return self.clear_memory()

        # 1. Quick built-in offline knowledge (<5ms response)
        if any(q in query_lower for q in ["mấy giờ", "bây giờ là mấy giờ", "thời gian", "what time is it"]):
            dt = datetime.datetime.now()
            now_str = f"{dt.hour} giờ {dt.minute} phút, ngày {dt.day} tháng {dt.month} năm {dt.year}"
            return f"Bây giờ là {now_str}."

        if any(q in query_lower for q in ["ngày mấy", "ngày bao nhiêu", "thứ mấy", "hôm nay là ngày", "what date"]):
            dt = datetime.datetime.now()
            days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
            day_str = days[dt.weekday()]
            return f"Hôm nay là {day_str}, ngày {dt.day} tháng {dt.month} năm {dt.year}."

        if any(q in query_lower for q in ["bạn là ai", "tên bạn là gì", "who are you", "tên gì"]):
            return "Tôi là NOVA, trợ lý AI cá nhân trên máy tính của bạn."

        if any(q in query_lower for q in ["thông tin máy tính", "cấu hình máy", "system info"]):
            return f"Máy tính của bạn đang chạy hệ điều hành {platform.system()} {platform.release()}, vi xử lý {platform.processor()}."

        # 2. Try Cloud Gemini API if key is provided and mode allows
        gemini_key = (self.gemini_cfg.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")).strip()
        if gemini_key and self.mode in ["hybrid", "online_only"]:
            reply = self._query_gemini(user_query, gemini_key)
            if reply:
                self._record_turn(user_query, reply)
                return reply

        # 3. Try Local Ollama LLM (Offline Multi-turn with Streaming)
        if self.mode in ["hybrid", "offline_only"]:
            reply = self._query_ollama(user_query, on_sentence_callback)
            if reply:
                self._record_turn(user_query, reply)
                return reply

        # 4. Fallback if Ollama is not yet started and no Gemini API key
        return (
            f"Tôi đã ghi nhận: '{user_query}'. "
            "Để trả lời câu hỏi tự do này, hãy đảm bảo Ollama đang cài trên máy hoặc nhập Gemini API Key vào Cài đặt nhé!"
        )

    def _record_turn(self, user_msg: str, assistant_msg: str):
        """Append turn to history and keep within window."""
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": assistant_msg})
        # Prune older turns
        if len(self.history) > self.max_history_turns * 2:
            self.history = self.history[-(self.max_history_turns * 2):]

    def _ensure_ollama_alive(self) -> bool:
        """Ensure Ollama service is alive, start it silently if not."""
        base_url = self.ollama_cfg.get("base_url", "http://localhost:11434")
        try:
            requests.get(base_url, timeout=1)
            return True
        except Exception:
            ollama_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
            if os.path.exists(ollama_path):
                subprocess.Popen(
                    [ollama_path, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
                time.sleep(2)
                return True
        return False

    def preload_model(self):
        """Warm up / Preload Ollama model into RAM in background so first query has zero cold-start delay."""
        if self.mode in ["hybrid", "offline_only"] and self.ollama_cfg.get("preload", True):
            try:
                self._ensure_ollama_alive()
                base_url = self.ollama_cfg.get("base_url", "http://localhost:11434")
                model = self.ollama_cfg.get("model", "qwen2.5:3b")
                payload = {
                    "model": model,
                    "keep_alive": -1  # Keep loaded indefinitely while NOVA is active
                }
                requests.post(f"{base_url.rstrip('/')}/api/generate", json=payload, timeout=25)
                print(f"[Ollama] Đã nạp sẵn model '{model}' vào RAM sẵn sàng phản hồi tức thì!")
            except Exception as e:
                print(f"[Ollama Preload Notice] {e}")

    def _query_ollama(self, query: str, on_sentence_callback: Optional[Callable[[str], None]] = None) -> str:
        """Call local Ollama REST API using multi-turn /api/chat with streaming."""
        self._ensure_ollama_alive()
        base_url = self.ollama_cfg.get("base_url", "http://localhost:11434")
        model = self.ollama_cfg.get("model", "qwen2.5:3b")
        timeout = self.ollama_cfg.get("timeout_seconds", 30)

        # Build messages payload with conversation memory
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.history[-10:])
        messages.append({"role": "user", "content": query})

        endpoint = f"{base_url.rstrip('/')}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": -1
        }

        try:
            resp = requests.post(endpoint, json=payload, timeout=timeout, stream=True)
            if resp.status_code != 200:
                return ""

            full_reply = []
            sentence_buffer = ""

            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        full_reply.append(token)
                        sentence_buffer += token

                        # Check for sentence end: '.', '!', '?', or '\n'
                        if on_sentence_callback and re.search(r"[.!?\n]\s*$", sentence_buffer):
                            clean_sentence = sentence_buffer.strip()
                            if len(clean_sentence) > 5:
                                on_sentence_callback(clean_sentence)
                                sentence_buffer = ""

                except Exception:
                    continue

            # Send any trailing sentence left in buffer
            if on_sentence_callback and sentence_buffer.strip():
                on_sentence_callback(sentence_buffer.strip())

            return "".join(full_reply).strip()

        except requests.exceptions.RequestException:
            pass
        return ""

    def _query_gemini(self, query: str, api_key: str) -> str:
        """Call Google Gemini API with multi-turn context."""
        model = self.gemini_cfg.get("model", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        # Build Gemini contents from memory
        contents = []
        for turn in self.history[-8:]:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn["content"]}]})

        contents.append({
            "role": "user",
            "parts": [{"text": f"{SYSTEM_PROMPT}\n\nNgười dùng: {query}"}]
        })

        payload = {"contents": contents}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception as e:
            print(f"[Gemini API Error] {e}")
        return ""
