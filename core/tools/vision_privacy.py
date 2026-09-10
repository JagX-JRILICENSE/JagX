"""
JagX Vision + Privacy Guard
- Capture camera / screen and describe
- Detect which processes are using camera or microphone
- Check public IP reputation / blacklist signals
JRILICENSE
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import List

DATA = Path(__file__).resolve().parents[2] / "data" / "vision"
DATA.mkdir(parents=True, exist_ok=True)


def _ps(script: str, timeout: int = 40) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return str(e)


def capture_webcam_photo() -> str:
    """Capture one frame from the default webcam using OpenCV if available."""
    try:
        import cv2
    except ImportError:
        return "OpenCV not installed. Run: pip install opencv-python"
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return "Could not open webcam. Check privacy settings and if another app is using it."
    ok, frame = cam.read()
    cam.release()
    if not ok:
        return "Webcam opened but failed to capture a frame."
    path = DATA / f"webcam_{int(time.time())}.jpg"
    cv2.imwrite(str(path), frame)
    try:
        os.startfile(str(path))  # type: ignore
    except Exception:
        pass
    return f"Webcam photo saved: {path}"


def capture_screen_photo() -> str:
    try:
        import pyautogui
    except ImportError:
        return "pyautogui missing"
    path = DATA / f"screen_{int(time.time())}.png"
    pyautogui.screenshot(str(path))
    try:
        os.startfile(str(path))  # type: ignore
    except Exception:
        pass
    return f"Screenshot saved: {path}"


def describe_webcam() -> str:
    """Capture webcam and return a simple local description (colors / brightness)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return "Need opencv-python and numpy"
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        return "Webcam unavailable"
    ok, frame = cam.read()
    cam.release()
    if not ok:
        return "Capture failed"
    path = DATA / f"describe_{int(time.time())}.jpg"
    cv2.imwrite(str(path), frame)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    brightness = float(frame.mean())
    h = hsv[:, :, 0]
    # rough dominant hue bucket
    hist = np.bincount(h.flatten(), minlength=180)
    dom = int(hist.argmax())
    if brightness < 40:
        light = "very dark"
    elif brightness < 90:
        light = "dim"
    elif brightness < 160:
        light = "normal lighting"
    else:
        light = "bright"
    color = "warm/reddish" if dom < 15 or dom > 160 else "greenish" if 35 < dom < 85 else "bluish" if 85 <= dom <= 130 else "mixed colors"
    return (
        f"I looked through your camera.\n"
        f"Scene looks {light}, with mostly {color}.\n"
        f"Photo: {path}\n"
        f"(Local analysis only — not cloud vision.)"
    )


def list_camera_users() -> str:
    """List processes that may be using the webcam (Windows)."""
    script = r"""
$ErrorActionPreference='SilentlyContinue'
# Capability access / apps that recently used camera
$cam = Get-Process | Where-Object { $_.ProcessName -match 'Camera|WindowsCamera|Skype|Teams|Zoom|Discord|obs|Streamlabs|chrome|msedge|firefox|Jaguar|JagX' } |
  Select-Object ProcessName,Id | Format-Table -AutoSize | Out-String
Write-Output '=== Running apps that often use camera ==='
Write-Output $cam
# Privacy capability usage if available
try {
  $pkg = Get-AppxPackage *WindowsCamera* | Select-Object Name,Status
  Write-Output $pkg
} catch {}
"""
    out = _ps(script)
    return out or "No obvious camera-related processes found."


def list_microphone_users() -> str:
    script = r"""
$ErrorActionPreference='SilentlyContinue'
Get-Process | Where-Object {
  $_.ProcessName -match 'Skype|Teams|Zoom|Discord|obs|Streamlabs|chrome|msedge|firefox|VoiceRecorder|YourPhone|GameBar'
} | Select-Object ProcessName,Id | Format-Table -AutoSize | Out-String
"""
    return "Apps that often use the mic:\n" + (_ps(script) or "None matched")


def privacy_guard_scan() -> str:
    """One-shot privacy scan: camera apps, mic apps, open privacy settings advice."""
    cam = list_camera_users()
    mic = list_microphone_users()
    return (
        "=== JagX Privacy Guard ===\n"
        f"{cam}\n\n{mic}\n\n"
        "Notes:\n"
        "• Laptop makers (Dell/HP/Lenovo/etc.) do not normally stream your mic/camera continuously.\n"
        "• Risk is usually from apps you installed or malware, not the brand itself.\n"
        "• Open Windows Settings → Privacy → Camera / Microphone to review app permissions.\n"
        "• Say 'open camera privacy' or 'open mic privacy' to open those panels.\n"
    )


def open_camera_privacy() -> str:
    if os.name == "nt":
        os.system("start ms-settings:privacy-webcam")
        return "Opened Camera privacy settings"
    return "Windows only"


def open_mic_privacy() -> str:
    if os.name == "nt":
        os.system("start ms-settings:privacy-microphone")
        return "Opened Microphone privacy settings"
    return "Windows only"


def get_public_ip() -> str:
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            with urllib.request.urlopen(url, timeout=8) as r:
                return r.read().decode().strip()
        except Exception:
            continue
    return ""


def check_ip_reputation() -> str:
    """Check public IP against free lookup endpoints (not a legal blacklist guarantee)."""
    ip = get_public_ip()
    if not ip:
        return "Could not detect public IP (offline?)."
    lines = [f"Public IP: {ip}"]
    # ip-api.com free
    try:
        with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,proxy,hosting,query", timeout=10) as r:
            data = json.loads(r.read().decode())
        if data.get("status") == "success":
            lines.append(
                f"Location: {data.get('city')}, {data.get('regionName')}, {data.get('country')}"
            )
            lines.append(f"ISP/Org: {data.get('isp')} / {data.get('org')}")
            lines.append(f"AS: {data.get('as')}")
            if data.get("proxy"):
                lines.append("Signal: IP flagged as proxy/VPN by ip-api")
            if data.get("hosting"):
                lines.append("Signal: IP looks like hosting/datacenter")
    except Exception as e:
        lines.append(f"ip-api lookup failed: {e}")
    # Spamhaus / abuse are not freely scrapable in a reliable way without keys — point user to checkers
    lines.append("Manual checks: https://scamalytics.com/ip  |  https://www.abuseipdb.com/")
    lines.append("This is a reputation signal check, not a court blacklist.")
    return "\n".join(lines)


def watch_privacy_loop_once() -> str:
    """Single monitoring pass you can run often."""
    return privacy_guard_scan() + "\n\n" + check_ip_reputation()


VISION_PRIVACY_TOOLS = [
    {"type": "function", "function": {"name": "capture_webcam_photo", "description": "Take a photo with the laptop webcam.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "capture_screen_photo", "description": "Capture the screen.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "describe_webcam", "description": "Look through the webcam and describe lighting/colors locally.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "list_camera_users", "description": "List processes that may be using the camera.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "list_microphone_users", "description": "List processes that may be using the microphone.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "privacy_guard_scan", "description": "Full privacy scan for camera/mic usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_camera_privacy", "description": "Open Windows camera privacy settings.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_mic_privacy", "description": "Open Windows microphone privacy settings.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_public_ip", "description": "Get your public IP address.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "check_ip_reputation", "description": "Check public IP reputation / proxy/hosting signals.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "watch_privacy_loop_once", "description": "Run privacy scan + IP check once.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "capture_webcam_photo": capture_webcam_photo,
    "capture_screen_photo": capture_screen_photo,
    "describe_webcam": describe_webcam,
    "list_camera_users": list_camera_users,
    "list_microphone_users": list_microphone_users,
    "privacy_guard_scan": privacy_guard_scan,
    "open_camera_privacy": open_camera_privacy,
    "open_mic_privacy": open_mic_privacy,
    "get_public_ip": get_public_ip,
    "check_ip_reputation": check_ip_reputation,
    "watch_privacy_loop_once": watch_privacy_loop_once,
}
