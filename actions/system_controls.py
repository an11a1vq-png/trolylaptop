import os
import ctypes
import subprocess
from typing import Tuple

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except Exception:
    PYCAW_AVAILABLE = False


def _get_audio_endpoint():
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    except Exception:
        return None


def get_volume() -> int:
    """Get master volume as a percentage 0 - 100."""
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            val = endpoint.GetMasterVolumeLevelScalar()
            return int(round(val * 100))
        except Exception:
            pass
    return 50


def set_volume(percent: int) -> Tuple[bool, str]:
    """Set master volume to percentage 0 - 100."""
    percent = max(0, min(100, percent))
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            endpoint.SetMasterVolumeLevelScalar(percent / 100.0, None)
            return True, f"Đã đặt âm lượng thành {percent}%"
        except Exception as e:
            return False, f"Lỗi chỉnh âm lượng: {e}"
    # Fallback via powershell / keyboard
    return False, "Không thể truy cập bộ điều khiển âm lượng"


def change_volume(delta: int) -> Tuple[bool, str]:
    """Increase or decrease master volume by delta percentage."""
    current = get_volume()
    new_vol = max(0, min(100, current + delta))
    return set_volume(new_vol)


def toggle_mute() -> Tuple[bool, str]:
    """Toggle mute on master audio."""
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            current_mute = endpoint.GetMute()
            new_mute = not current_mute
            endpoint.SetMute(new_mute, None)
            state_str = "Tắt tiếng" if new_mute else "Bật tiếng"
            return True, f"Đã {state_str}"
        except Exception as e:
            return False, f"Lỗi tắt tiếng: {e}"
    return False, "Không tìm thấy bộ điều khiển âm thanh"


def lock_screen() -> Tuple[bool, str]:
    """Lock the Windows workstation."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Đã khóa màn hình"
    except Exception as e:
        return False, f"Không thể khóa màn hình: {e}"


def shutdown_computer(delay_seconds: int = 10) -> Tuple[bool, str]:
    """Shutdown Windows after delay."""
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True)
        return True, f"Máy tính sẽ tắt trong {delay_seconds} giây. Để hủy, hãy nói 'hủy tắt máy'."
    except Exception as e:
        return False, f"Lỗi khi tắt máy: {e}"


def restart_computer(delay_seconds: int = 10) -> Tuple[bool, str]:
    """Restart Windows after delay."""
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True)
        return True, f"Máy tính sẽ khởi động lại trong {delay_seconds} giây."
    except Exception as e:
        return False, f"Lỗi khi khởi động lại: {e}"


def cancel_shutdown() -> Tuple[bool, str]:
    """Cancel pending shutdown or restart."""
    try:
        subprocess.run(["shutdown", "/a"], check=True)
        return True, "Đã hủy lệnh tắt hoặc khởi động lại máy."
    except Exception as e:
        return False, f"Không có lệnh tắt máy nào để hủy: {e}"
