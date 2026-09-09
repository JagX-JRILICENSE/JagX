"""
JagX Text-to-Speech
Uses edge-tts (high quality, free, no API key).

JRILICENSE
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from rich.console import Console

console = Console()

try:
    import edge_tts
    import pygame
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


async def _speak_async(text: str, voice: str = "en-US-AriaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp_path = f.name
    await communicate.save(tmp_path)

    # Play with pygame
    pygame.mixer.init()
    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    Path(tmp_path).unlink(missing_ok=True)


def speak(text: str, voice: str = "en-US-AriaNeural") -> str:
    """Speak the given text out loud."""
    if not HAS_TTS:
        return "TTS not available. Install edge-tts and pygame."
    try:
        asyncio.run(_speak_async(text, voice))
        return "Spoken successfully."
    except Exception as e:
        return f"TTS error: {e}"
