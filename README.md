# Trợ Lý Ảo Hey Google Trên Máy Tính Windows

Trợ lý ảo thông minh điều khiển máy tính bằng giọng nói theo phong cách **Hey Google**, hỗ trợ **song ngữ Việt - Anh**, cơ chế **lai (Hybrid)** hoạt động độc lập không cần internet và tích hợp giao diện Widget nổi hiện đại.

---

## 🚀 Cách Khởi Động Nhanh

Bạn có thể mở trợ lý ảo bằng 1 trong 2 cách:
1. **Nhấp đúp chuột** vào file `run_assistant.bat`.
2. Hoặc mở PowerShell/CMD tại `D:\ailap` và chạy:
   ```powershell
   .\venv\Scripts\python.exe app.py
   ```

Khi khởi động, ứng dụng sẽ:
- Xuất hiện biểu tượng 4 màu Google ở **Khay hệ thống (System Tray)** dưới góc phải màn hình.
- Mở **Bảng Điều Khiển (Dashboard)** để xem log, test giọng nói và tùy chỉnh.
- Hiển thị thanh **Widget nổi** ở cạnh trên màn hình mỗi khi bạn nói chuyện.

---

## 🎙️ Cách Kích Hoạt & Gọi Trợ Lý

- **Cách 1: Bằng giọng nói (Hands-free):**
  - Nói: *"Hey Google"*, *"Google ơi"*, *"Trợ lý ơi"*, hoặc *"Jarvis"*.
  - Bạn có thể nói kèm lệnh ngay: ví dụ *"Hey Google mở Chrome"* hoặc chỉ nói *"Hey Google"* rồi đợi tiếng ting để nói câu lệnh.
- **Cách 2: Bằng phím tắt nhanh:**
  - Nhấn tổ hợp phím: `Ctrl + Space` (có thể đổi phím khác trong Cài đặt).
  - Trợ lý sẽ lập tức phát tiếng chuông và sẵn sàng nghe bạn nói.

---

## 🛠️ Danh Sách Câu Lệnh Điều Khiển Máy Tính Tích Hợp Sẵn

### 1. Âm thanh & Hệ thống (Phản hồi tức thì < 5ms)
- `Tăng âm lượng` / `Volume up` (Tăng 10%)
- `Giảm âm lượng` / `Volume down` (Giảm 10%)
- `Âm lượng 50%` / `Set volume to 70` (Chỉnh chính xác)
- `Tắt tiếng` / `Mute` / `Bật tiếng`
- `Chụp màn hình` / `Screenshot` (Lưu tự động vào `Pictures\Screenshots`)
- `Khóa màn hình` / `Lock screen`
- `Đóng cửa sổ` (`Alt + F4`) / `Chuyển tab` (`Alt + Tab`) / `Hiện màn hình chính` (`Win + D`)

### 2. Mở Ứng Dụng & Web
- `Mở Chrome`, `Mở Cốc Cốc`, `Mở Edge`
- `Mở Spotify`, `Mở YouTube`, `Mở VS Code`, `Mở Notepad`, `Mở Máy tính`
- `Mở thư mục dự án` (Mở trực tiếp thư mục `D:\ailap`)
- `Tìm kiếm Google [nội dung]` (Ví dụ: *"Tìm kiếm Google thời tiết hôm nay"*)
- `Mở YouTube tìm [tên bài hát]` (Ví dụ: *"Mở YouTube tìm nhạc lofi"*)

### 3. Gõ Văn Bản Bằng Giọng Nói (Voice Dictation)
- Nói: **`Bật gõ văn bản`** (hoặc bấm nút trong Dashboard).
- Đặt con trỏ chuột vào bất kỳ phần mềm nào (Word, Notepad, Zalo, Chrome, Facebook...).
- Mọi câu nói tiếp theo của bạn sẽ được tự động gõ vào màn hình với đầy đủ dấu tiếng Việt chuẩn xác!
- Nói: **`Tắt gõ văn bản`** để dừng.

### 4. Cơ Chế An Toàn (Safety Confirmation)
- Khi bạn nói **`Tắt máy`** hoặc **`Khởi động lại`**, trợ lý sẽ hỏi lại:
  > *"Bạn có chắc chắn muốn tắt máy tính không?"*
- Bạn chỉ cần trả lời: **`Có`** hoặc **`Xác nhận`** để thực hiện, hoặc **`Hủy`** / **`Không`** để hủy lệnh.

---

## 🧠 Cấu Hình Trí Tuệ Nhân Tạo (Hybrid AI)

Hệ thống được thiết kế theo cơ chế kép:
1. **Chế độ Ngoại Tuyến (Offline Local LLM):**
   - Cài đặt [Ollama](https://ollama.com/) và tải mô hình Qwen 2.5:
     ```cmd
     ollama run qwen2.5:1.5b
     ```
   - Trợ lý sẽ tự động kết nối tới Ollama trên máy để trả lời mọi câu hỏi tự do, viết code, dịch thuật khi mất mạng.
2. **Chế độ Trực Tuyến Đám Mây (Google Gemini Cloud):**
   - Vào tab **Cài đặt & AI** trên Dashboard.
   - Nhập khóa API Google Gemini của bạn rồi nhấn **Lưu Cài Đặt**. Trợ lý sẽ chuyển sang bộ não siêu thông minh với tốc độ xử lý nhanh như chớp.

---

## 📁 Cấu Trúc Thư Mục
- `app.py`: Bộ điều phối trung tâm.
- `config.yaml`: File cấu hình chung.
- `core/`:
  - `stt_engine.py`: Xử lý nhận dạng giọng nói bằng `faster-whisper`.
  - `tts_engine.py`: Giọng nói truyền cảm bằng `edge-tts` (online) & `pyttsx3` (offline).
  - `intent_router.py`: Bộ định tuyến lệnh nhanh và cơ chế an toàn.
  - `brain_hybrid.py`: Kết nối Ollama và Gemini.
  - `audio_listener.py`: Thu âm micro và phát hiện tiếng nói (VAD).
  - `wake_word.py`: Quản lý từ khóa và phím tắt toàn cầu.
- `actions/`: Thư viện điều khiển máy tính, âm lượng, mở app, gõ văn bản.
- `ui/`: Giao diện widget nổi Google và Dashboard.
- `scripts/`: Thư mục chứa các script tự động hóa tùy biến người dùng.
