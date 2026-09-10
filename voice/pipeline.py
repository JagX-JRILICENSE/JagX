"""
JagX Voice Pipeline — always speaks via robust TTS fallbacks.
JRILICENSE
"""
from __future__ import annotations

import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from rich.console import Console

console = Console()

try:
    import sounddevice as sd

    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    from faster_whisper import WhisperModel

    HAS_STT = True
except ImportError:
    HAS_STT = False

from voice.tts import speak as tts_speak, speak_async as tts_speak_async


class VoicePipeline:
    def __init__(
        self,
        wake_word: str = "jagx",
        stt_model_size: str = "base",
        tts_voice: str = "en-US-AriaNeural",
        language: str = "en",
        sample_rate: int = 16000,
        silence_threshold: float = 0.015,
        silence_duration: float = 1.4,
        max_record_seconds: float = 25.0,
    ):
        self.wake_word = wake_word.lower()
        self.stt_model_size = stt_model_size
        self.tts_voice = tts_voice
        self.language = language
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_record_seconds = max_record_seconds
        self._stt_model = None
        self._running = False

    def _get_stt_model(self):
        if self._stt_model is None and HAS_STT:
            self._stt_model = WhisperModel(self.stt_model_size, device="cpu", compute_type="int8")
        return self._stt_model

    def transcribe(self, audio_path: str) -> str:
        if not HAS_STT:
            return ""
        model = self._get_stt_model()
        if model is None:
            return ""
        try:
            segments, _ = model.transcribe(audio_path, language=self.language)
            return " ".join(seg.text.strip() for seg in segments).strip()
        except Exception:
            return ""

    def speak(self, text: str):
        """Always try to talk (blocking)."""
        tts_speak(text, self.tts_voice)

    def speak_async(self, text: str):
        """Talk without blocking the UI."""
        tts_speak_async(text, self.tts_voice)

    def _record_until_silence(self) -> Optional[str]:
        if not HAS_AUDIO:
            return None
        frames = []
        silent_chunks = 0
        chunk_duration = 0.2
        chunk_samples = int(self.sample_rate * chunk_duration)
        max_chunks = int(self.max_record_seconds / chunk_duration)
        started = False

        def callback(indata, frames_count, time_info, status):
            nonlocal silent_chunks, started
            volume = float(np.linalg.norm(indata) / np.sqrt(max(len(indata), 1)))
            if volume > self.silence_threshold:
                started = True
                silent_chunks = 0
                frames.append(indata.copy())
            elif started:
                silent_chunks += 1
                frames.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_samples,
                callback=callback,
            ):
                for _ in range(max_chunks):
                    time.sleep(chunk_duration)
                    if started and silent_chunks * chunk_duration >= self.silence_duration:
                        break
        except Exception:
            return None

        if not frames:
            return None
        audio = np.concatenate(frames, axis=0)
        audio_int16 = (audio * 32767).astype(np.int16)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        return tmp.name

    def listen_once(self) -> str:
        wav_path = self._record_until_silence()
        if not wav_path:
            return ""
        try:
            return self.transcribe(wav_path)
        finally:
            Path(wav_path).unlink(missing_ok=True)

    def start_continuous(self, on_command: Callable[[str], str]):
        if not (HAS_AUDIO and HAS_STT):
            self.speak("Voice listening is not available. Type your command instead.")
            return
        self._running = True
        self._get_stt_model()
        self.speak("JagX voice is ready. Say JagX, then your command.")
        while self._running:
            try:
                wav_path = self._record_until_silence()
                if not wav_path:
                    continue
                text = self.transcribe(wav_path)
                Path(wav_path).unlink(missing_ok=True)
                if not text:
                    continue
                text_lower = text.lower()
                if self.wake_word in text_lower:
                    idx = text_lower.find(self.wake_word)
                    command = text[idx + len(self.wake_word) :].strip(" ,.")
                    if not command:
                        self.speak("Yes?")
                        command = self.listen_once()
                    if command:
                        self.speak(f"Working on {command[:40]}")
                        response = on_command(command)
                        if response:
                            self.speak(response)
                    else:
                        self.speak("I didn't catch that.")
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(1)
        self._running = False

    def stop(self):
        self._running = False
