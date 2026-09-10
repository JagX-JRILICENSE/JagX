"""
JagX — 15 powerful everyday features.
JRILICENSE
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def _ps(cmd: str, timeout: int = 30) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode != 0 and err:
            return f"Error: {err[:500]}"
        return out or "OK"
    except Exception as e:
        return f"Error: {e}"


# 1. Find files across the PC
def find_files(query: str, root: str = "", limit: int = 30) -> str:
    """Search for files by name across user folders."""
    base = Path(root).expanduser() if root else Path.home()
    matches: List[str] = []
    q = query.lower()
    try:
        for p in base.rglob("*"):
            if q in p.name.lower():
                matches.append(str(p))
                if len(matches) >= limit:
                    break
    except Exception as e:
        return f"Search error: {e}"
    if not matches:
        return f"No files matching '{query}' under {base}"
    return f"Found {len(matches)} matches:\n" + "\n".join(matches)


# 2. Switch / focus window by title
def focus_window(title_contains: str) -> str:
    """Bring a window to the front by partial title."""
    safe = title_contains.replace("'", "''")
    script = f"""
$w = Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{safe}*' }} | Select-Object -First 1
if (-not $w) {{ 'No window matched' ; exit }}
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W {{ [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n); }}
'@
[void][W]::ShowWindow($w.MainWindowHandle, 9)
[void][W]::SetForegroundWindow($w.MainWindowHandle)
"Focused: $($w.MainWindowTitle)"
"""
    return _ps(script)


# 3. Set system volume (0-100)
def set_volume(level: int) -> str:
    level = max(0, min(100, int(level)))
    # Uses Windows CoreAudio via PowerShell COM where available
    script = f"""
try {{
  $obj = New-Object -ComObject WScript.Shell
  # approximate via key presses from current unknown level is hard; use nircmd if present
  if (Get-Command nircmd -ErrorAction SilentlyContinue) {{
    nircmd setsysvolume {int(level * 655.35)}
    "Volume set to {level}%"
  }} else {{
    "Install nircmd for exact volume, or use volume_up/volume_down. Requested: {level}%"
  }}
}} catch {{ $_.Exception.Message }}
"""
    return _ps(script)


def volume_up(steps: int = 4) -> str:
    try:
        import pyautogui
        for _ in range(max(1, int(steps))):
            pyautogui.press("volumeup")
        return f"Volume up x{steps}"
    except Exception as e:
        return str(e)


def volume_down(steps: int = 4) -> str:
    try:
        import pyautogui
        for _ in range(max(1, int(steps))):
            pyautogui.press("volumedown")
        return f"Volume down x{steps}"
    except Exception as e:
        return str(e)


def volume_mute_toggle() -> str:
    try:
        import pyautogui
        pyautogui.press("volumemute")
        return "Mute toggled"
    except Exception as e:
        return str(e)


# 4. Battery and power status
def battery_status() -> str:
    script = """
try {
  $b = Get-CimInstance Win32_Battery
  if (-not $b) { 'No battery (desktop?)'; return }
  $b | Select-Object EstimatedChargeRemaining, BatteryStatus, @{N='Charging';E={$_.BatteryStatus -eq 2}} | ConvertTo-Json
} catch { $_.Exception.Message }
"""
    return _ps(script)


# 5. Empty temp / quick cleanup
def clean_temp_files() -> str:
    removed = 0
    errors = 0
    for folder in [os.environ.get("TEMP", ""), str(Path.home() / "AppData" / "Local" / "Temp")]:
        p = Path(folder)
        if not p.is_dir():
            continue
        for item in p.iterdir():
            try:
                if item.is_file():
                    item.unlink(missing_ok=True)
                    removed += 1
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item, ignore_errors=True)
                    removed += 1
            except Exception:
                errors += 1
    return f"Cleanup done. Removed ~{removed} items ({errors} locked/skipped)."


# 6. Organize Downloads into folders by extension
def organize_downloads() -> str:
    dl = Path.home() / "Downloads"
    if not dl.is_dir():
        return "Downloads folder not found"
    mapping = {
        "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"},
        "Videos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
        "Audio": {".mp3", ".wav", ".flac", ".m4a"},
        "Documents": {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"},
        "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
        "Installers": {".exe", ".msi", ".msix"},
    }
    moved = 0
    for f in dl.iterdir():
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        target_name = "Other"
        for folder, exts in mapping.items():
            if ext in exts:
                target_name = folder
                break
        dest_dir = dl / target_name
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / f.name
        if dest.exists():
            dest = dest_dir / f"{f.stem}_{int(time.time())}{f.suffix}"
        try:
            f.rename(dest)
            moved += 1
        except Exception:
            pass
    return f"Organized Downloads: moved {moved} files into category folders."


# 7. Quick note to desktop
def quick_note(text: str, filename: str = "") -> str:
    name = filename.strip() or f"JagX_Note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    if not name.endswith(".txt"):
        name += ".txt"
    path = Path.home() / "Desktop" / name
    path.write_text(text, encoding="utf-8")
    return f"Note saved: {path}"


# 8. Summarize clipboard text (returns clipboard content for model to summarize)
def read_clipboard() -> str:
    try:
        import pyperclip
        text = pyperclip.paste()
        if not text:
            return "Clipboard is empty"
        if len(text) > 8000:
            return text[:8000] + "\n…[truncated]"
        return text
    except Exception as e:
        return f"Clipboard error: {e}"


def write_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Clipboard updated ({len(text)} chars)"
    except Exception as e:
        return str(e)


# 9. Open common apps quickly
def open_app(app_name: str) -> str:
    """Open a common Windows app or anything start can launch."""
    name = app_name.strip().lower()
    aliases = {
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "explorer": "explorer",
        "file explorer": "explorer",
        "cmd": "cmd",
        "terminal": "wt",
        "powershell": "powershell",
        "browser": "start https://",
        "chrome": "start chrome",
        "edge": "start msedge",
        "paint": "mspaint",
        "settings": "start ms-settings:",
        "task manager": "taskmgr",
        "whatsapp": "start whatsapp:",
        "spotify": "start spotify:",
    }
    cmd = aliases.get(name, f"start {app_name}")
    try:
        subprocess.Popen(cmd, shell=True)
        return f"Launched: {app_name}"
    except Exception as e:
        return f"Launch failed: {e}"


# 10. Kill process by name
def kill_process(name: str) -> str:
    safe = name.replace(".exe", "").strip()
    return _ps(f"Get-Process -Name '{safe}' -ErrorAction SilentlyContinue | Stop-Process -Force; 'Stopped {safe} if it was running'")


# 11. List top CPU/RAM processes
def top_processes(limit: int = 10) -> str:
    limit = max(3, min(25, int(limit)))
    script = f"""
Get-Process | Sort-Object CPU -Descending | Select-Object -First {limit} Name,Id,CPU,@{{N='WS_MB';E={{[math]::Round($_.WorkingSet64/1MB,1)}}}} | ConvertTo-Json
"""
    return _ps(script)


# 12. Wi-Fi status / list networks
def wifi_status() -> str:
    return _ps("netsh wlan show interfaces")


def wifi_list() -> str:
    return _ps("netsh wlan show networks mode=bssid")


# 13. Schedule a reminder (creates a Windows scheduled task one-shot via msg or notepad)
def set_reminder(message: str, minutes_from_now: int = 10) -> str:
    minutes = max(1, int(minutes_from_now))
    # Simple local reminder file + optional toast via powershell
    reminder_file = Path.home() / ".jagx_reminders.json"
    data = []
    if reminder_file.exists():
        try:
            data = json.loads(reminder_file.read_text(encoding="utf-8"))
        except Exception:
            data = []
    when = time.time() + minutes * 60
    data.append({"when": when, "message": message})
    reminder_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Fire a delayed popup
    ps = f"""
Start-Job -ScriptBlock {{
  Start-Sleep -Seconds {minutes * 60}
  Add-Type -AssemblyName System.Windows.Forms
  [System.Windows.Forms.MessageBox]::Show('{message.replace("'", "''")}', 'JagX Reminder')
}} | Out-Null
"Reminder set in {minutes} minute(s): {message}"
"""
    return _ps(ps)


# 14. Take screenshot and open it
def screenshot_and_open(path: str = "") -> str:
    try:
        import pyautogui
        dest = Path(path).expanduser() if path else Path.home() / "Desktop" / f"JagX_Shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        img = pyautogui.screenshot()
        img.save(str(dest))
        os.startfile(str(dest))  # type: ignore
        return f"Screenshot saved and opened: {dest}"
    except Exception as e:
        return f"Screenshot failed: {e}"


# 15. System briefing
def system_briefing() -> str:
    info = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user": os.environ.get("USERNAME") or os.environ.get("USER"),
        "home": str(Path.home()),
    }
    try:
        import psutil
        info["cpu_percent"] = psutil.cpu_percent(interval=0.3)
        info["ram_percent"] = psutil.virtual_memory().percent
        info["disk_percent"] = psutil.disk_usage("C:\\" if os.name == "nt" else "/").percent
    except Exception:
        pass
    batt = battery_status()
    top = top_processes(5)
    return (
        f"JagX Briefing — {info.get('time')}\n"
        f"User: {info.get('user')}\n"
        f"CPU: {info.get('cpu_percent', '?')}% | RAM: {info.get('ram_percent', '?')}% | Disk: {info.get('disk_percent', '?')}%\n"
        f"Battery: {batt}\n"
        f"Top processes: {top[:800]}"
    )


POWER_FEATURE_TOOLS = [
    {"type": "function", "function": {"name": "find_files", "description": "Search the PC for files by name.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "root": {"type": "string", "default": ""}, "limit": {"type": "integer", "default": 30}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "focus_window", "description": "Bring a window to the front by partial title.", "parameters": {"type": "object", "properties": {"title_contains": {"type": "string"}}, "required": ["title_contains"]}}},
    {"type": "function", "function": {"name": "volume_up", "description": "Increase system volume.", "parameters": {"type": "object", "properties": {"steps": {"type": "integer", "default": 4}}, "required": []}}},
    {"type": "function", "function": {"name": "volume_down", "description": "Decrease system volume.", "parameters": {"type": "object", "properties": {"steps": {"type": "integer", "default": 4}}, "required": []}}},
    {"type": "function", "function": {"name": "volume_mute_toggle", "description": "Toggle mute.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "battery_status", "description": "Show battery charge status.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "clean_temp_files", "description": "Delete temporary files to free space.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "organize_downloads", "description": "Sort Downloads folder into Images/Videos/Documents/etc.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "quick_note", "description": "Save a text note to the Desktop.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "filename": {"type": "string", "default": ""}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "read_clipboard", "description": "Read current clipboard text.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "write_clipboard", "description": "Write text to the clipboard.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "open_app", "description": "Open an application (notepad, chrome, explorer, whatsapp, etc.).", "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}}},
    {"type": "function", "function": {"name": "kill_process", "description": "Force-stop a process by name (e.g. chrome).", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "top_processes", "description": "List processes using the most CPU/RAM.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "default": 10}}, "required": []}}},
    {"type": "function", "function": {"name": "wifi_status", "description": "Show current Wi-Fi connection status.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "wifi_list", "description": "List nearby Wi-Fi networks.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "set_reminder", "description": "Set a popup reminder after N minutes.", "parameters": {"type": "object", "properties": {"message": {"type": "string"}, "minutes_from_now": {"type": "integer", "default": 10}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "screenshot_and_open", "description": "Take a screenshot, save it, and open it.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": ""}}, "required": []}}},
    {"type": "function", "function": {"name": "system_briefing", "description": "Give a quick system status briefing (CPU, RAM, battery, top apps).", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "find_files": find_files,
    "focus_window": focus_window,
    "set_volume": set_volume,
    "volume_up": volume_up,
    "volume_down": volume_down,
    "volume_mute_toggle": volume_mute_toggle,
    "battery_status": battery_status,
    "clean_temp_files": clean_temp_files,
    "organize_downloads": organize_downloads,
    "quick_note": quick_note,
    "read_clipboard": read_clipboard,
    "write_clipboard": write_clipboard,
    "open_app": open_app,
    "kill_process": kill_process,
    "top_processes": top_processes,
    "wifi_status": wifi_status,
    "wifi_list": wifi_list,
    "set_reminder": set_reminder,
    "screenshot_and_open": screenshot_and_open,
    "system_briefing": system_briefing,
}
