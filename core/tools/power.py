"""JagX Windows power and idle-control tools."""
from __future__ import annotations
import platform
import subprocess


def _windows(command: list[str]) -> str:
    if platform.system() != "Windows":
        return "Power control currently supports Windows only."
    try:
        subprocess.Popen(command, shell=False)
        return "Power action started."
    except Exception as exc:
        return f"Power action failed: {exc}"


def shutdown_windows(delay_seconds: int = 0) -> str:
    return _windows(["shutdown", "/s", "/t", str(max(0, int(delay_seconds)))])


def restart_windows(delay_seconds: int = 0) -> str:
    return _windows(["shutdown", "/r", "/t", str(max(0, int(delay_seconds)))])


def sleep_windows() -> str:
    if platform.system() != "Windows":
        return "Sleep control currently supports Windows only."
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"], shell=False)
        return "Sleep action started."
    except Exception as exc:
        return f"Sleep action failed: {exc}"


def hibernate_windows() -> str:
    return _windows(["shutdown", "/h"])


def cancel_shutdown() -> str:
    return _windows(["shutdown", "/a"])

POWER_TOOL_DEFINITIONS = [
    {"type":"function","function":{"name":"shutdown_windows","description":"Shut down this Windows computer after a delay. Use only when explicitly requested.","parameters":{"type":"object","properties":{"delay_seconds":{"type":"integer","default":0}},"required":[]}}},
    {"type":"function","function":{"name":"restart_windows","description":"Restart this Windows computer after a delay. Use only when explicitly requested.","parameters":{"type":"object","properties":{"delay_seconds":{"type":"integer","default":0}},"required":[]}}},
    {"type":"function","function":{"name":"sleep_windows","description":"Put this Windows computer to sleep.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"hibernate_windows","description":"Hibernate this Windows computer.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"cancel_shutdown","description":"Cancel a pending Windows shutdown or restart.","parameters":{"type":"object","properties":{},"required":[]}}},
]
TOOL_FUNCTIONS = {"shutdown_windows":shutdown_windows,"restart_windows":restart_windows,"sleep_windows":sleep_windows,"hibernate_windows":hibernate_windows,"cancel_shutdown":cancel_shutdown}
