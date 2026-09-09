"""
JagX Media & Creative Tools
Music playback, singing, screenshots, and AI image generation.

JRILICENSE
"""
from __future__ import annotations

import os
import subprocess
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

try:
    import pygame
    HAS_PYGAME = True
except Exception:
    HAS_PYGAME = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False


def play_music(query: str) -> str:
    """Open a music search in the default browser."""
    q = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={q}"
    webbrowser.open(url)
    return f"Opened music search for: {query}"


def play_local_audio(path: str) -> str:
    """Play a local audio file using pygame when available."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Audio file not found: {p}"
    if not HAS_PYGAME:
        os.startfile(str(p)) if os.name == "nt" else subprocess.Popen(["xdg-open", str(p)])
        return f"Opened audio file: {p}"
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(str(p))
        pygame.mixer.music.play()
        return f"Playing: {p.name}"
    except Exception as e:
        return f"Could not play audio: {e}"


def stop_music() -> str:
    """Stop JagX-managed audio playback."""
    if HAS_PYGAME:
        try:
            pygame.mixer.music.stop()
            return "Music stopped."
        except Exception as e:
            return f"Could not stop music: {e}"
    return "No JagX audio player is active."


def sing(song_or_text: str) -> str:
    """Open a music/singing search for a requested song or lyric idea."""
    q = urllib.parse.quote_plus(f"{song_or_text} karaoke instrumental")
    webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
    return f"Opened a karaoke/instrumental search for: {song_or_text}"


def take_screenshot(path: str = "data/screenshots/jagx_screenshot.png") -> str:
    """Capture the user's screen to a local PNG."""
    if not HAS_PYAUTOGUI:
        return "Screenshot support is unavailable because pyautogui is not installed."
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        image = pyautogui.screenshot()
        image.save(target)
        return f"Screenshot saved to {target}"
    except Exception as e:
        return f"Screenshot failed: {e}"


def generate_image(prompt: str, filename: str = "data/generated/jagx_image.png", width: int = 1024, height: int = 1024) -> str:
    """Generate an image through a public image-generation endpoint and save it locally.

    The endpoint is intentionally configurable with JAGX_IMAGE_API_BASE. No API key is
    stored by this tool. If the endpoint is unavailable, the user gets a clear error.
    """
    base = os.getenv("JAGX_IMAGE_API_BASE", "https://image.pollinations.ai/prompt")
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{base.rstrip('/')}/{encoded}?width={int(width)}&height={int(height)}&nologo=true"
    target = Path(filename).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, target)
        return f"Generated image saved to {target}"
    except Exception as e:
        return f"Image generation failed: {e}. Check the internet connection or JAGX_IMAGE_API_BASE."


MEDIA_TOOLS = [
    {"type":"function","function":{"name":"play_music","description":"Search for and play music in the user's browser.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"play_local_audio","description":"Play a local audio file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"stop_music","description":"Stop audio started by JagX.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"sing","description":"Find a karaoke/instrumental version of a requested song or singing idea.","parameters":{"type":"object","properties":{"song_or_text":{"type":"string"}},"required":["song_or_text"]}}},
    {"type":"function","function":{"name":"take_screenshot","description":"Take a screenshot of the user's screen and save it locally.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"data/screenshots/jagx_screenshot.png"}},"required":[]}}},
    {"type":"function","function":{"name":"generate_image","description":"Generate an image from a text prompt and save it locally. Useful for diagrams, UI concepts, illustrations, and creative assets.","parameters":{"type":"object","properties":{"prompt":{"type":"string"},"filename":{"type":"string","default":"data/generated/jagx_image.png"},"width":{"type":"integer","default":1024},"height":{"type":"integer","default":1024}},"required":["prompt"]}}},
]

TOOL_FUNCTIONS = {
    "play_music": play_music,
    "play_local_audio": play_local_audio,
    "stop_music": stop_music,
    "sing": sing,
    "take_screenshot": take_screenshot,
    "generate_image": generate_image,
}
