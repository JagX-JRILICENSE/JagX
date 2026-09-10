"""
JagX Streaming Studio
Open OBS / Streamlabs and go-live pages on major platforms.
Helps you stream in real time from your PC (you still start the broadcast).
JRILICENSE
"""
from __future__ import annotations

import os
import shutil
import subprocess
import webbrowser
from pathlib import Path


def _start_exe(candidates: list[str]) -> str:
    for c in candidates:
        p = Path(c)
        if p.is_file():
            try:
                subprocess.Popen([str(p)], shell=False)
                return f"Launched {p.name}"
            except Exception as e:
                return f"Failed to launch {p}: {e}"
        found = shutil.which(c)
        if found:
            try:
                subprocess.Popen([found], shell=False)
                return f"Launched {found}"
            except Exception as e:
                return str(e)
    if os.name == "nt":
        # Try start by app name
        for name in candidates:
            os.system(f'start "" "{name}"')
        return f"Tried to start: {', '.join(candidates)}"
    return "App not found. Install OBS / Streamlabs first."


def open_obs() -> str:
    local = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    return _start_exe([
        str(Path(pf) / "obs-studio" / "bin" / "64bit" / "obs64.exe"),
        str(Path(local) / "Programs" / "obs-studio" / "bin" / "64bit" / "obs64.exe"),
        "obs64",
        "obs",
    ])


def open_streamlabs() -> str:
    local = os.environ.get("LOCALAPPDATA", "")
    return _start_exe([
        str(Path(local) / "Programs" / "Streamlabs Desktop" / "Streamlabs OBS.exe"),
        str(Path(local) / "Programs" / "Streamlabs Desktop" / "Streamlabs Desktop.exe"),
        "Streamlabs OBS",
    ])


def open_twitch_dashboard() -> str:
    webbrowser.open("https://dashboard.twitch.tv/u/home")
    return "Opened Twitch Creator Dashboard"


def open_twitch_stream_manager() -> str:
    webbrowser.open("https://dashboard.twitch.tv/u/stream-manager")
    return "Opened Twitch Stream Manager — start OBS then Go Live"


def open_youtube_studio_live() -> str:
    webbrowser.open("https://studio.youtube.com/channel/UC/livestreaming")
    return "Opened YouTube Studio Live"


def open_kick_dashboard() -> str:
    webbrowser.open("https://kick.com/dashboard/stream")
    return "Opened Kick stream dashboard"


def open_tiktok_live_studio() -> str:
    webbrowser.open("https://livecenter.tiktok.com/")
    return "Opened TikTok LIVE Center"


def open_facebook_live() -> str:
    webbrowser.open("https://www.facebook.com/live/producer")
    return "Opened Facebook Live Producer"


def open_instagram_live_help() -> str:
    webbrowser.open("https://www.instagram.com/")
    return "Opened Instagram — start LIVE from the mobile/app flow (IG Live is app-first)"


def open_x_media_studio() -> str:
    webbrowser.open("https://studio.x.com/")
    return "Opened X Media Studio"


def open_discord() -> str:
    webbrowser.open("https://discord.com/app")
    return "Opened Discord (Go Live in a voice channel)"


def stream_setup_guide() -> str:
    return (
        "STREAM SETUP (real-time):\n"
        "1. Open OBS or Streamlabs (say: open obs)\n"
        "2. Add sources: Display Capture + Mic + Camera\n"
        "3. Copy Stream Key from Twitch/YouTube/Kick dashboard\n"
        "4. Paste key in OBS Settings → Stream\n"
        "5. Click Start Streaming in OBS\n"
        "6. Click Go Live on the platform dashboard\n"
        "JagX opens the tools; you stay logged into your accounts."
    )


def prepare_stream(platform: str = "twitch") -> str:
    """Open OBS + the chosen platform dashboard for a quick go-live path."""
    p = (platform or "twitch").lower().strip()
    parts = [open_obs()]
    if p in ("twitch", "ttv"):
        parts.append(open_twitch_stream_manager())
    elif p in ("youtube", "yt"):
        parts.append(open_youtube_studio_live())
    elif p == "kick":
        parts.append(open_kick_dashboard())
    elif p in ("tiktok", "tt"):
        parts.append(open_tiktok_live_studio())
    elif p in ("facebook", "fb"):
        parts.append(open_facebook_live())
    elif p in ("x", "twitter"):
        parts.append(open_x_media_studio())
    else:
        parts.append(open_twitch_stream_manager())
        parts.append(f"Unknown platform '{platform}', opened Twitch as default.")
    parts.append(stream_setup_guide())
    return " | ".join(parts)


STREAMING_TOOLS = [
    {"type": "function", "function": {"name": "open_obs", "description": "Open OBS Studio for live streaming.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_streamlabs", "description": "Open Streamlabs Desktop.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_twitch_dashboard", "description": "Open Twitch creator dashboard.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_twitch_stream_manager", "description": "Open Twitch stream manager.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_youtube_studio_live", "description": "Open YouTube Studio livestreaming.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_kick_dashboard", "description": "Open Kick stream dashboard.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_tiktok_live_studio", "description": "Open TikTok LIVE center.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_facebook_live", "description": "Open Facebook Live Producer.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_instagram_live_help", "description": "Open Instagram for live context.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_x_media_studio", "description": "Open X Media Studio.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_discord", "description": "Open Discord for Go Live.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "stream_setup_guide", "description": "Explain how to go live step by step.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "prepare_stream", "description": "Open OBS + platform dashboard for twitch/youtube/kick/tiktok/facebook/x.", "parameters": {"type": "object", "properties": {"platform": {"type": "string", "default": "twitch"}}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "open_obs": open_obs,
    "open_streamlabs": open_streamlabs,
    "open_twitch_dashboard": open_twitch_dashboard,
    "open_twitch_stream_manager": open_twitch_stream_manager,
    "open_youtube_studio_live": open_youtube_studio_live,
    "open_kick_dashboard": open_kick_dashboard,
    "open_tiktok_live_studio": open_tiktok_live_studio,
    "open_facebook_live": open_facebook_live,
    "open_instagram_live_help": open_instagram_live_help,
    "open_x_media_studio": open_x_media_studio,
    "open_discord": open_discord,
    "stream_setup_guide": stream_setup_guide,
    "prepare_stream": prepare_stream,
}
