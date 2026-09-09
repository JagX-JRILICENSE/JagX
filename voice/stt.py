"""
JagX Speech-to-Text
Uses faster-whisper for local transcription.

JRILICENSE
"""

from __future__ import annotations

from rich.console import Console

console = Console()

try:
    from faster_whisper import WhisperModel
    HAS_STT = True
except ImportError:
    HAS_STT = False

_model = None

def _get_model(size: str = "base"):
    global _model
    if _model is None:
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model

def transcribe(audio_path: str, language: str = "en") -> str:
    """Transcribe an audio file to text."""
    if not HAS_STT:
        return "STT not available. Install faster-whisper."
    try:
        model = _get_model()
        segments, info = model.transcribe(audio_path, language=language)
        text = " ".join([seg.text for seg in segments]).strip()
        return text or "(no speech detected)"
    except Exception as e:
        return f"Transcription error: {e}"
