# NOVA AI Assistant (Hệ Thống Trợ Lý AI Cá Nhân Trên Windows)

**NOVA** là hệ thống trợ lý ảo thông minh chạy trực tiếp trên máy tính Windows, sở hữu phong cách **Sci-Fi Cosmic Neon Glow**, hoạt động theo cơ chế **Hybrid (Cục bộ & Đám mây)**, phản hồi **siêu tốc và dứt khoát**.

---

## ⚡ 1. Cách Khởi Động Nhanh

1. **Cách 1:** Nhấp đúp chuột vào file [`run_assistant.bat`](run_assistant.bat).
2. **Cách 2:** Mở PowerShell/CMD tại `D:\ailap` và chạy:
   ```powershell
   .\venv\Scripts\python.exe app.py
   ```

Khi khởi động:
- Biểu tượng năng lượng vũ trụ **NOVA (Cyan/Tím Neon)** xuất hiện tại **Khay hệ thống (System Tray)**.
- Mở **Bảng Điều Khiển (Dashboard)** với giao diện tối hiện đại.
- Thanh **Widget nổi** với hiệu ứng sóng âm Cosmic Neon sẽ xuất hiện mượt mà mỗi khi bạn tương tác.

---

## 🎙️ 2. Kích Hoạt & Gọi NOVA

- **Kích hoạt bằng giọng nói (Hands-free):**
  - Nói: *"Hey Nova"*, *"Nova ơi"*, *"Nova"*, hoặc *"Ê Nova"*.
  - Có thể ra lệnh liền mạch: ví dụ *"Hey Nova mở Chrome"* hoặc chỉ gọi *"Nova ơi"* rồi chờ âm hiệu vũ trụ vang lên để nói lệnh.
- **Kích hoạt bằng phím tắt:**
  - Nhấn tổ hợp phím: `Ctrl + Space` (có thể tùy chỉnh lại trong Cài đặt).

---

## 🛠️ 3. Danh Sách Lệnh Điều Khiển Máy Tính Tích Hợp Sẵn

### Âm thanh & Quản lý Windows
- `Tăng âm lượng` / `Volume up` (Tăng 10%)
- `Giảm âm lượng` / `Volume down` (Giảm 10%)
- `Âm lượng 60%` / `Set volume to 50`
- `Tắt tiếng` / `Mute` / `Bật tiếng`
- `Chụp màn hình` / `Screenshot` (Tự động lưu vào `Pictures\Screenshots`)
- `Khóa màn hình` / `Lock screen`
- `Đóng cửa sổ` (`Alt + F4`) / `Chuyển tab` (`Alt + Tab`) / `Hiện màn hình chính` (`Win + D`)

### Mở Ứng Dụng & Web
- `Mở Chrome`, `Mở Cốc Cốc`, `Mở Edge`
- `Mở Spotify`, `Mở YouTube`, `Mở VS Code`, `Mở Notepad`, `Mở Máy tính`
- `Mở thư mục dự án` (Mở nhanh `D:\ailap`)
- `Tìm kiếm Google [nội dung]`
- `Mở YouTube tìm [tên bài hát / video]`

### Gõ Văn Bản Bằng Giọng Nói (Voice Dictation)
- Nói: **`Bật gõ văn bản`** (hoặc bấm nút trong Dashboard).
- Đặt con trỏ chuột vào bất kỳ ô nhập văn bản nào (Word, Notepad, Zalo, trình duyệt...).
- Mọi câu nói tiếp theo của bạn sẽ được gõ trực tiếp vào màn hình với tiếng Việt có dấu chuẩn 100%.
- Nói: **`Tắt gõ văn bản`** để quay về chế độ trợ lý.

### Cơ Chế An Toàn (Safety Confirmation)
- Khi ra lệnh **`Tắt máy`** hoặc **`Khởi động lại`**, NOVA sẽ yêu cầu xác nhận:
  > *"Bạn có chắc chắn muốn tắt máy tính không?"*
- Nói **`Có`** / **`Xác nhận`** để tiến hành, hoặc **`Hủy`** / **`Không`** để hủy bỏ.

---

## 🧠 4. Trí Tuệ Nhân Tạo (Hybrid AI Engine)

- **Offline Cục Bộ (Ollama):** Tự động liên kết mô hình `qwen2.5:1.5b` hoặc `qwen2.5:3b` trên máy tính để trả lời câu hỏi tự do, viết code, tư vấn khi không có internet.
- **Trực Tuyến Siêu Tốc (Gemini Cloud):** Tùy chọn nhập Google Gemini API Key trong tab Cài đặt của Dashboard để mở khóa khả năng phân tích nâng cao.

---

## 📂 5. Cấu Trúc Dự Án
```
d:\ailap\
├── app.py                     # Điều phối hệ thống trung tâm
├── config.yaml                # Cấu hình NOVA (Wake words, Hotkey, Model)
├── run_assistant.bat          # File chạy 1-click
├── generate_sounds.py         # Bộ tạo âm thanh hiệu ứng Sci-Fi
├── actions/                   # Module điều khiển máy tính, âm thanh, app, dictation
├── core/                      # STT (Whisper), TTS (Edge/Offline), Brain, Router
├── ui/                        # Widget nổi Cosmic Neon & Dashboard Dark Mode
└── scripts/                   # Thư mục chứa script tự động hóa tùy biến
```
