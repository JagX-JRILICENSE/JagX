"""
JagX Text-to-Speech — always try to talk.
1) edge-tts + pygame
2) Windows SAPI (built-in)
3) pyttsx3 if present
JRILICENSE
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import threading
from pathlib import Path

_lock = threading.Lock()

try:
    import edge_tts
    import pygame

    HAS_EDGE = True
except ImportError:
    HAS_EDGE = False

try:
    import pyttsx3

    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


def _clean(text: str) -> str:
    t = (text or "").replace("*", " ").replace("#", " ").replace("`", " ")
    t = " ".join(t.split())
    if len(t) > 400:
        t = t[:400] + "..."
    return t.strip()


async def _edge_speak(text: str, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp = f.name
    try:
        await communicate.save(tmp)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)
    finally:
        Path(tmp).unlink(missing_ok=True)


def _windows_sapi(text: str) -> bool:
    if os.name != "nt":
        return False
    safe = text.replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 1; "
        f"$s.Speak('{safe}');"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0
    except Exception:
        return False


def _pyttsx3_speak(text: str) -> bool:
    if not HAS_PYTTSX3:
        return False
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception:
        return False


def speak(text: str, voice: str = "en-US-AriaNeural") -> str:
    clean = _clean(text)
    if not clean:
        return "empty"
    with _lock:
        if HAS_EDGE:
            try:
                asyncio.run(_edge_speak(clean, voice))
                return "spoken:edge"
            except Exception:
                pass
        if _windows_sapi(clean):
            return "spoken:sapi"
        if _pyttsx3_speak(clean):
            return "spoken:pyttsx3"
    return "TTS unavailable"


def speak_async(text: str, voice: str = "en-US-AriaNeural") -> None:
    threading.Thread(target=speak, args=(text, voice), daemon=True).start()
