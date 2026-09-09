"""
JagX Full Voice Pipeline
Continuous listening → Wake word "JagX" → Record command → STT → Agent → TTS

JRILICENSE
"""

from __future__ import annotations

import asyncio
import queue
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from rich.console import Console

console = Console()

# Optional dependencies
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

try:
    import edge_tts
    import pygame
    HAS_TTS = True
except ImportError:
    HAS_TTS = False


class VoicePipeline:
    """
    Full voice interface for JagX.

    Modes:
    - continuous: always listening for the wake word "JagX"
    - push_to_talk: record while you hold / press enter
    """

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
        self._listening = False

        if not HAS_AUDIO:
            console.print("[red]sounddevice not installed. Voice input disabled.[/red]")
        if not HAS_STT:
            console.print("[red]faster-whisper not installed. Speech recognition disabled.[/red]")
        if not HAS_TTS:
            console.print("[yellow]edge-tts / pygame not installed. Speech output disabled.[/yellow]")

    # ------------------------------------------------------------------
    # STT
    # ------------------------------------------------------------------
    def _get_stt_model(self):
        if self._stt_model is None and HAS_STT:
            console.print(f"[dim]Loading Whisper model ({self.stt_model_size})...[/dim]")
            self._stt_model = WhisperModel(
                self.stt_model_size,
                device="cpu",
                compute_type="int8",
            )
        return self._stt_model

    def transcribe(self, audio_path: str) -> str:
        if not HAS_STT:
            return ""
        model = self._get_stt_model()
        if model is None:
            return ""
        try:
            segments, _ = model.transcribe(audio_path, language=self.language)
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return text
        except Exception as e:
            console.print(f"[red]STT error:[/red] {e}")
            return ""

    # ------------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------------
    async def _speak_async(self, text: str):
        if not HAS_TTS or not text.strip():
            return
        communicate = edge_tts.Communicate(text, self.tts_voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tmp = f.name
        await communicate.save(tmp)

        pygame.mixer.init()
        pygame.mixer.music.load(tmp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.08)
        Path(tmp).unlink(missing_ok=True)

    def speak(self, text: str):
        """Speak text out loud (blocking)."""
        if not HAS_TTS:
            console.print(f"[dim](TTS unavailable) {text}[/dim]")
            return
        try:
            # Clean text a bit for speech
            clean = text.replace("*", "").replace("#", "").replace("`", "")
            # Limit length for comfort
            if len(clean) > 600:
                clean = clean[:600] + "..."
            asyncio.run(self._speak_async(clean))
        except Exception as e:
            console.print(f"[red]TTS error:[/red] {e}")

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------
    def _record_until_silence(self) -> Optional[str]:
        """Record from microphone until silence is detected. Returns path to wav file."""
        if not HAS_AUDIO:
            return None

        console.print("[bold green]Listening... speak now.[/bold green]")

        frames = []
        silent_chunks = 0
        chunk_duration = 0.2  # seconds
        chunk_samples = int(self.sample_rate * chunk_duration)
        max_chunks = int(self.max_record_seconds / chunk_duration)
        started = False

        def callback(indata, frames_count, time_info, status):
            nonlocal silent_chunks, started
            volume = np.linalg.norm(indata) / np.sqrt(len(indata))
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
        except Exception as e:
            console.print(f"[red]Microphone error:[/red] {e}")
            return None

        if not frames:
            console.print("[yellow]No speech detected.[/yellow]")
            return None

        audio = np.concatenate(frames, axis=0)
        # Convert to int16 for wav
        audio_int16 = (audio * 32767).astype(np.int16)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return tmp.name

    def listen_once(self) -> str:
        """Record one utterance and return transcribed text."""
        wav_path = self._record_until_silence()
        if not wav_path:
            return ""
        try:
            text = self.transcribe(wav_path)
            return text
        finally:
            Path(wav_path).unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Continuous wake-word loop
    # ------------------------------------------------------------------
    def start_continuous(self, on_command: Callable[[str], str]):
        """
        Continuously listen for the wake word "JagX".
        When detected, record the following command, call on_command(text),
        then speak the returned response.
        """
        if not (HAS_AUDIO and HAS_STT):
            console.print("[red]Cannot start continuous voice mode — missing audio or STT dependencies.[/red]")
            return

        self._running = True
        console.print("[bold orange1]JagX voice mode active[/bold orange1]")
        console.print(f"[dim]Say \"{self.wake_word}\" followed by your command. Ctrl+C to stop.[/dim]\n")

        # Load model early
        self._get_stt_model()

        while self._running:
            try:
                # Short listening window looking for wake word
                console.print("[dim]Waiting for wake word...[/dim]")
                wav_path = self._record_until_silence()
                if not wav_path:
                    continue

                text = self.transcribe(wav_path)
                Path(wav_path).unlink(missing_ok=True)

                if not text:
                    continue

                text_lower = text.lower()
                console.print(f"[dim]Heard: {text}[/dim]")

                # Check for wake word
                if self.wake_word in text_lower:
                    # Extract command after wake word if present
                    idx = text_lower.find(self.wake_word)
                    command = text[idx + len(self.wake_word):].strip(" ,.")

                    if not command:
                        # Wake word only → ask for the actual command
                        self.speak("Yes?")
                        command = self.listen_once()

                    if command:
                        console.print(f"[bold cyan]Command:[/bold cyan] {command}")
                        response = on_command(command)
                        if response:
                            console.print(f"[bold orange1]JagX:[/bold orange1] {response[:200]}...")
                            self.speak(response)
                    else:
                        self.speak("I didn't catch that.")
                else:
                    # Optional: allow direct commands without wake word in continuous mode
                    # For now we require the wake word for safety
                    pass

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Voice loop error:[/red] {e}")
                time.sleep(1)

        self._running = False
        console.print("[yellow]Voice mode stopped.[/yellow]")

    def stop(self):
        self._running = False
