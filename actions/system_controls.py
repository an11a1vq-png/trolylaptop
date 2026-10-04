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

# Windows Virtual Key Codes for Hardware Audio Control
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002


def _send_virtual_key(vk_code: int, times: int = 1):
    """Press Windows virtual volume hardware key directly."""
    for _ in range(max(1, times)):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def _get_audio_endpoint():
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        if not devices:
            return None
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
        except Exception:
            pass

    # Hardware fallback: calculate difference from current estimation
    current = get_volume()
    diff = percent - current
    if diff > 0:
        _send_virtual_key(VK_VOLUME_UP, times=diff // 2)
    elif diff < 0:
        _send_virtual_key(VK_VOLUME_DOWN, times=abs(diff) // 2)

    return True, f"Đã đặt âm lượng thành {percent}%"


def change_volume(delta: int) -> Tuple[bool, str]:
    """Increase or decrease master volume by delta percentage."""
    endpoint = _get_audio_endpoint()
    if endpoint:
        try:
            current = int(round(endpoint.GetMasterVolumeLevelScalar() * 100))
            new_vol = max(0, min(100, current + delta))
            endpoint.SetMasterVolumeLevelScalar(new_vol / 100.0, None)
            action_str = f"tăng lên {new_vol}%" if delta > 0 else f"giảm xuống {new_vol}%"
            return True, f"Đã {action_str}"
        except Exception:
            pass

    # Universal Windows Virtual Key Fallback (Always succeeds)
    presses = max(1, abs(delta) // 2)
    if delta > 0:
        _send_virtual_key(VK_VOLUME_UP, times=presses)
        return True, f"Đã tăng âm lượng"
    else:
        _send_virtual_key(VK_VOLUME_DOWN, times=presses)
        return True, f"Đã giảm âm lượng"


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
        except Exception:
            pass

    # Hardware key fallback
    _send_virtual_key(VK_VOLUME_MUTE)
    return True, "Đã chuyển đổi trạng thái tắt tiếng"


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
