import json
import requests
import datetime
import platform
from typing import Tuple


SYSTEM_PROMPT = """Bạn là trợ lý ảo 'Hey Google' trên máy tính Windows.
Nhiệm vụ của bạn là hỗ trợ người dùng nhiệt tình, ngắn gọn, súc tích và hữu ích.
Hãy trả lời trực tiếp, tự nhiên bằng cùng ngôn ngữ của người dùng (tiếng Việt hoặc tiếng Anh).
Không viết câu trả lời quá dài dòng trừ khi người dùng yêu cầu giải thích chi tiết."""


class HybridBrain:
    def __init__(self, config: dict):
        self.config = config
        self.intel_cfg = config.get("intelligence", {})
        self.ollama_cfg = self.intel_cfg.get("ollama", {})
        self.gemini_cfg = self.intel_cfg.get("gemini", {})
        self.mode = self.intel_cfg.get("engine_mode", "hybrid")

    def think_and_reply(self, user_query: str) -> str:
        """Process user query and return response text."""
        # 1. Quick built-in offline knowledge
        query_lower = user_query.strip().lower()
        if any(q in query_lower for q in ["mấy giờ", "bây giờ là mấy giờ", "thời gian", "what time is it"]):
            dt = datetime.datetime.now()
            now_str = f"{dt.hour} giờ {dt.minute} phút, ngày {dt.day} tháng {dt.month} năm {dt.year}"
            return f"Bây giờ là {now_str}."

        if any(q in query_lower for q in ["bạn là ai", "tên bạn là gì", "who are you"]):
            return "Tôi là Hey Google, trợ lý ảo thông minh chạy trực tiếp trên máy tính Windows của bạn."

        if any(q in query_lower for q in ["thông tin máy tính", "cấu hình máy", "system info"]):
            return f"Máy tính của bạn đang chạy hệ điều hành {platform.system()} {platform.release()}, vi xử lý {platform.processor()}."

        # 2. Try Cloud Gemini API if key is provided and mode allows
        gemini_key = self.gemini_cfg.get("api_key", "").strip()
        if gemini_key and self.mode in ["hybrid", "online_only"]:
            reply = self._query_gemini(user_query, gemini_key)
            if reply:
                return reply

        # 3. Try Local Ollama LLM (Offline)
        if self.mode in ["hybrid", "offline_only"]:
            reply = self._query_ollama(user_query)
            if reply:
                return reply

        # 4. Fallback if Ollama is not yet started and no Gemini API key
        return (
            f"Tôi đã nghe rõ câu hỏi: '{user_query}'. "
            "Để tôi trả lời câu hỏi tự do này, bạn có thể khởi động Ollama (mô hình Qwen2.5) hoặc nhập Gemini API key vào phần Cài đặt nhé!"
        )

    def _query_ollama(self, query: str) -> str:
        """Call local Ollama REST API."""
        base_url = self.ollama_cfg.get("base_url", "http://localhost:11434")
        model = self.ollama_cfg.get("model", "qwen2.5:1.5b")
        timeout = self.ollama_cfg.get("timeout_seconds", 15)

        endpoint = f"{base_url.rstrip('/')}/api/generate"
        payload = {
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\nNgười dùng: {query}\nTrợ lý:",
            "stream": False
        }

        try:
            resp = requests.post(endpoint, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
        except requests.exceptions.RequestException:
            # Ollama service not reachable
            pass
        return ""

    def _query_gemini(self, query: str, api_key: str) -> str:
        """Call Google Gemini API."""
        model = self.gemini_cfg.get("model", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\nNgười dùng: {query}"}
                    ]
                }
            ]
        }

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
