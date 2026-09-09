"""
JagX Privacy Guard
Detects and helps block potential camera / microphone / speaker abuse.

Note: Perfect detection of manufacturer/firmware-level surveillance is extremely hard.
This provides practical monitoring and blocking of common processes and devices.

JRILICENSE
"""

from __future__ import annotations

import platform
import subprocess
from typing import List, Dict, Any

from rich.console import Console

console = Console()

SUSPICIOUS_KEYWORDS = [
    "camera", "webcam", "mic", "microphone", "audio", "record", "spy",
    "surveillance", "keylog", "logger", "monitor", "listen", "voice",
    "teams", "zoom", "meet", "skype", "discord",  # common apps that use cam/mic
]

def check_camera_mic_usage() -> str:
    """
    Attempt to detect processes that may be using camera or microphone.
    Returns a human-readable report.
    """
    system = platform.system().lower()
    report = []

    try:
        if system == "windows":
            # Check for processes that often access camera/mic
            result = subprocess.run(
                ['powershell', '-Command',
                 "Get-Process | Where-Object {$_.ProcessName -match 'camera|webcam|mic|obs|zoom|teams|skype|discord|chrome|msedge|firefox'} | Select-Object ProcessName,Id | Format-Table -AutoSize"],
                capture_output=True, text=True, timeout=15
            )
            report.append("Windows process scan:\n" + (result.stdout or "No obvious matches"))

        elif system == "darwin":  # macOS
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=10
            )
            lines = [line for line in result.stdout.splitlines()
                     if any(k in line.lower() for k in ["camera", "avcapture", "coreaudiod", "zoom", "teams", "meet"])]
            report.append("macOS relevant processes:\n" + ("\n".join(lines[:20]) or "None obvious"))

        else:  # Linux
            # Check for processes using video/audio devices
            result = subprocess.run(
                ["lsof", "/dev/video0", "/dev/snd/*"], capture_output=True, text=True, timeout=10
            )
            report.append("Linux device users:\n" + (result.stdout or "No processes currently using video0/snd"))

            # Also general process scan
            result2 = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10)
            lines = [line for line in result2.stdout.splitlines()
                     if any(k in line.lower() for k in SUSPICIOUS_KEYWORDS)]
            if lines:
                report.append("\nSuspicious-looking processes:\n" + "\n".join(lines[:15]))

    except Exception as e:
        report.append(f"Scan error: {e}")

    return "\n".join(report) if report else "No clear camera/microphone activity detected."


def list_audio_video_devices() -> str:
    """List known camera and audio devices."""
    system = platform.system().lower()
    try:
        if system == "windows":
            cmd = 'powershell "Get-PnpDevice -Class Camera,Media,AudioEndpoint | Select-Object Status,Class,FriendlyName | Format-Table -AutoSize"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return result.stdout or "Could not list devices"
        elif system == "darwin":
            result = subprocess.run(["system_profiler", "SPCameraDataType", "SPAudioDataType"],
                                    capture_output=True, text=True, timeout=15)
            return result.stdout[:3000] or "No info"
        else:
            # Linux
            cams = subprocess.run(["v4l2-ctl", "--list-devices"], capture_output=True, text=True, timeout=5)
            audio = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            return f"Cameras:\n{cams.stdout}\n\nAudio:\n{audio.stdout}"
    except Exception as e:
        return f"Device listing failed: {e}"


def kill_process_by_name(name: str) -> str:
    """Kill processes matching a name (use carefully)."""
    system = platform.system().lower()
    try:
        if system == "windows":
            result = subprocess.run(["taskkill", "/F", "/IM", f"{name}.exe"],
                                    capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(["pkill", "-f", name], capture_output=True, text=True, timeout=10)
        return f"Kill attempt for '{name}': {result.stdout or result.stderr or 'done'}"
    except Exception as e:
        return f"Failed to kill {name}: {e}"


def block_camera_access() -> str:
    """
    Attempt to disable camera devices (platform dependent).
    On many systems this requires admin rights.
    """
    system = platform.system().lower()
    try:
        if system == "windows":
            # Disable camera devices via PowerShell (needs admin)
            cmd = 'powershell "Get-PnpDevice -Class Camera | Disable-PnpDevice -Confirm:$false"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
            return result.stdout or result.stderr or "Camera disable attempted (may need admin)"
        elif system == "darwin":
            return "On macOS, camera access is controlled per-app in System Settings > Privacy & Security > Camera. JagX cannot force-block at kernel level without deeper privileges."
        else:
            # Linux - unload uvcvideo module (common webcam driver)
            result = subprocess.run(["sudo", "modprobe", "-r", "uvcvideo"],
                                    capture_output=True, text=True, timeout=10)
            return result.stdout or result.stderr or "Attempted to unload uvcvideo module"
    except Exception as e:
        return f"Block camera failed: {e}"


# Tool definitions
PRIVACY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_camera_mic_usage",
            "description": "Scan for processes that appear to be using the camera, microphone, or recording audio/video. Use this to detect possible surveillance.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_audio_video_devices",
            "description": "List camera and audio devices currently known to the system.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process_by_name",
            "description": "Forcefully stop processes matching a name. Useful to stop a suspicious app that is using camera/mic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Process name or partial name"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "block_camera_access",
            "description": "Attempt to disable camera devices on the system. May require administrator privileges.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

TOOL_FUNCTIONS = {
    "check_camera_mic_usage": check_camera_mic_usage,
    "list_audio_video_devices": list_audio_video_devices,
    "kill_process_by_name": kill_process_by_name,
    "block_camera_access": block_camera_access,
}
