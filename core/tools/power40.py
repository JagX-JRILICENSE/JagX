"""
JagX Power Pack 40 — extra practical tools.
JRILICENSE
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "power40"
DATA.mkdir(parents=True, exist_ok=True)


def _run(cmd: str, timeout: int = 60) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return ((r.stdout or "") + (r.stderr or "")).strip()[:4000] or "OK"
    except Exception as e:
        return str(e)


def _start(uri: str) -> str:
    if os.name == "nt":
        os.system(f'start "" {uri}')
    else:
        webbrowser.open(uri)
    return f"Opened {uri}"


# ---- productivity / system ----
def empty_temp_folder() -> str:
    temp = Path(os.environ.get("TEMP", "/tmp"))
    n = 0
    for p in temp.glob("*"):
        try:
            if p.is_file():
                p.unlink()
                n += 1
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                n += 1
        except Exception:
            pass
    return f"Cleared ~{n} temp items"


def show_wifi_password() -> str:
    if os.name != "nt":
        return "Windows only"
    profiles = _run("netsh wlan show profiles")
    return profiles[:3000]


def list_startup_programs() -> str:
    return _run('powershell "Get-CimInstance Win32_StartupCommand | Select Name,Command | Format-Table -AutoSize | Out-String"')


def enable_dark_mode() -> str:
    return _run(
        'powershell "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 0 -Type Dword -Force; New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value 0 -Type Dword -Force"'
    )


def enable_light_mode() -> str:
    return _run(
        'powershell "New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value 1 -Type Dword -Force; New-ItemProperty -Path HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value 1 -Type Dword -Force"'
    )


def set_volume_percent(level: int = 50) -> str:
    level = max(0, min(100, int(level)))
    # Use nircmd if present else powershell audio not trivial — open sound settings
    if shutil.which("nircmd"):
        return _run(f"nircmd setsysvolume {int(level * 655.35)}")
    _start("ms-settings:sound")
    return f"Opened sound settings (set volume to {level}% manually, or install nircmd for auto)"


def lock_workstation() -> str:
    if os.name == "nt":
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Workstation locked"
    return "Windows only"


def open_downloads_folder() -> str:
    p = Path.home() / "Downloads"
    if os.name == "nt":
        os.startfile(str(p))  # type: ignore
    return str(p)


def open_desktop_folder() -> str:
    p = Path.home() / "Desktop"
    if os.name == "nt":
        os.startfile(str(p))  # type: ignore
    return str(p)


def create_reminder_file(text: str) -> str:
    path = DATA / f"reminder_{int(time.time())}.txt"
    path.write_text(f"{datetime.now()}\n{text}\n", encoding="utf-8")
    return f"Reminder saved: {path}"


def daily_journal_entry(text: str) -> str:
    path = DATA / f"journal_{datetime.now().date()}.md"
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n### {datetime.now().strftime('%H:%M')}\n{text}\n")
    return f"Journal updated: {path}"


def clipboard_write(text: str) -> str:
    try:
        import pyperclip

        pyperclip.copy(text)
        return "Copied to clipboard"
    except Exception:
        if os.name == "nt":
            subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{text.replace(chr(39), chr(39)+chr(39))}'"], check=False)
            return "Clipboard set via PowerShell"
        return "Clipboard failed"


def clipboard_read() -> str:
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception:
        return _run('powershell "Get-Clipboard"')


# ---- creator / stream helpers ----
def open_obs_youtube_prep() -> str:
    webbrowser.open("https://studio.youtube.com/channel/UC/livestreaming")
    if os.name == "nt":
        os.system('start "" obs64')
    return "Opened YouTube Live + tried OBS. Paste stream key in OBS → Start Streaming."


def open_canva_thumbnail() -> str:
    webbrowser.open("https://www.canva.com/create/youtube-thumbnails/")
    return "Opened Canva YouTube thumbnail maker"


def open_stream_schedule_notion() -> str:
    webbrowser.open("https://www.notion.so/")
    return "Opened Notion for stream schedule"


def open_vidiq() -> str:
    webbrowser.open("https://vidiq.com/")
    return "Opened VidIQ"


def open_tube_buddy() -> str:
    webbrowser.open("https://www.tubebuddy.com/")
    return "Opened TubeBuddy"


def open_capcut_web() -> str:
    webbrowser.open("https://www.capcut.com/my-edit")
    return "Opened CapCut web editor"


def open_elevenlabs() -> str:
    webbrowser.open("https://elevenlabs.io/")
    return "Opened ElevenLabs voice tools"


def open_runway_ml() -> str:
    webbrowser.open("https://runwayml.com/")
    return "Opened Runway ML"


def open_pika_labs() -> str:
    webbrowser.open("https://pika.art/")
    return "Opened Pika"


def open_suno() -> str:
    webbrowser.open("https://suno.com/")
    return "Opened Suno music AI"


def open_udio() -> str:
    webbrowser.open("https://www.udio.com/")
    return "Opened Udio"


def open_chatpdf() -> str:
    webbrowser.open("https://www.chatpdf.com/")
    return "Opened ChatPDF"


def open_gamma_app() -> str:
    webbrowser.open("https://gamma.app/")
    return "Opened Gamma presentations"


def open_looka_logo() -> str:
    webbrowser.open("https://looka.com/")
    return "Opened Looka logo maker"


def open_remove_bg() -> str:
    webbrowser.open("https://www.remove.bg/")
    return "Opened remove.bg"


def open_tinywow() -> str:
    webbrowser.open("https://tinywow.com/")
    return "Opened TinyWow tools"


def open_ilovepdf() -> str:
    webbrowser.open("https://www.ilovepdf.com/")
    return "Opened iLovePDF"


def open_photopea_edit() -> str:
    webbrowser.open("https://www.photopea.com/")
    return "Opened Photopea editor"


def open_excalidraw_board() -> str:
    webbrowser.open("https://excalidraw.com/")
    return "Opened Excalidraw"


def open_google_trends() -> str:
    webbrowser.open("https://trends.google.com/trends/")
    return "Opened Google Trends"


def open_answer_the_public() -> str:
    webbrowser.open("https://answerthepublic.com/")
    return "Opened AnswerThePublic"


def open_semrush() -> str:
    webbrowser.open("https://www.semrush.com/")
    return "Opened Semrush"


def open_ahrefs() -> str:
    webbrowser.open("https://ahrefs.com/")
    return "Opened Ahrefs"


def open_mail_timings() -> str:
    webbrowser.open("https://mail.google.com/")
    return "Opened Gmail"


def open_calendar_focus() -> str:
    webbrowser.open("https://calendar.google.com/")
    return "Opened Google Calendar"


def open_speedtest_run() -> str:
    webbrowser.open("https://www.speedtest.net/")
    return "Opened Speedtest"


def open_whatismyip() -> str:
    webbrowser.open("https://whatismyipaddress.com/")
    return "Opened WhatIsMyIPAddress"


def open_haveibeenpwned() -> str:
    webbrowser.open("https://haveibeenpwned.com/")
    return "Opened Have I Been Pwned"


def open_virus_total() -> str:
    webbrowser.open("https://www.virustotal.com/")
    return "Opened VirusTotal"


def open_process_explorer_help() -> str:
    webbrowser.open("https://learn.microsoft.com/sysinternals/downloads/process-explorer")
    return "Opened Process Explorer download page"


def system_health_snapshot() -> str:
    return _run(
        'powershell "$os=Get-CimInstance Win32_OperatingSystem; $cpu=(Get-CimInstance Win32_Processor).LoadPercentage; $free=[math]::Round($os.FreePhysicalMemory/1MB,1); $total=[math]::Round($os.TotalVisibleMemorySize/1MB,1); \"CPU=$cpu% RAM_free=${free}GB / ${total}GB\""'
    )


FUNCS = {
    "empty_temp_folder": empty_temp_folder,
    "show_wifi_profiles": show_wifi_password,
    "list_startup_programs": list_startup_programs,
    "enable_dark_mode": enable_dark_mode,
    "enable_light_mode": enable_light_mode,
    "set_volume_percent": set_volume_percent,
    "lock_workstation": lock_workstation,
    "open_downloads_folder": open_downloads_folder,
    "open_desktop_folder": open_desktop_folder,
    "create_reminder_file": create_reminder_file,
    "daily_journal_entry": daily_journal_entry,
    "clipboard_write": clipboard_write,
    "clipboard_read": clipboard_read,
    "open_obs_youtube_prep": open_obs_youtube_prep,
    "open_canva_thumbnail": open_canva_thumbnail,
    "open_stream_schedule_notion": open_stream_schedule_notion,
    "open_vidiq": open_vidiq,
    "open_tube_buddy": open_tube_buddy,
    "open_capcut_web": open_capcut_web,
    "open_elevenlabs": open_elevenlabs,
    "open_runway_ml": open_runway_ml,
    "open_pika_labs": open_pika_labs,
    "open_suno": open_suno,
    "open_udio": open_udio,
    "open_chatpdf": open_chatpdf,
    "open_gamma_app": open_gamma_app,
    "open_looka_logo": open_looka_logo,
    "open_remove_bg": open_remove_bg,
    "open_tinywow": open_tinywow,
    "open_ilovepdf": open_ilovepdf,
    "open_photopea_edit": open_photopea_edit,
    "open_excalidraw_board": open_excalidraw_board,
    "open_google_trends": open_google_trends,
    "open_answer_the_public": open_answer_the_public,
    "open_semrush": open_semrush,
    "open_ahrefs": open_ahrefs,
    "open_mail_timings": open_mail_timings,
    "open_calendar_focus": open_calendar_focus,
    "open_speedtest_run": open_speedtest_run,
    "open_whatismyip": open_whatismyip,
    "open_haveibeenpwned": open_haveibeenpwned,
    "open_virus_total": open_virus_total,
    "open_process_explorer_help": open_process_explorer_help,
    "system_health_snapshot": system_health_snapshot,
}

POWER40_TOOLS = []
for name, fn in FUNCS.items():
    props, req = {}, []
    if name in ("set_volume_percent",):
        props = {"level": {"type": "integer", "default": 50}}
    if name in ("create_reminder_file", "daily_journal_entry", "clipboard_write"):
        props = {"text": {"type": "string"}}
        req = ["text"]
    POWER40_TOOLS.append(
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"JagX power feature: {name.replace('_', ' ')}",
                "parameters": {"type": "object", "properties": props, "required": req},
            },
        }
    )

TOOL_FUNCTIONS = FUNCS
