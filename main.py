#!/usr/bin/env python3
"""
JagX - Personal Jaguar AI Companion
Full entry point: Voice + Text + System Tray (Windows app ready)

JRILICENSE
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel

from core.agent import JagXAgent
from voice.pipeline import VoicePipeline
from ui.tray import JagXTray

console = Console()

def print_banner():
    console.print(Panel.fit(
        "[bold orange1]JagX[/bold orange1] 🐆\n"
        "[dim]Personal Jaguar AI Companion[/dim]\n\n"
        "[yellow]JRILICENSE[/yellow]",
        border_style="orange1"
    ))


def run_text_mode(agent: JagXAgent):
    agent.run()


def run_voice_mode(agent: JagXAgent, pipeline: VoicePipeline):
    def handle_command(text: str) -> str:
        try:
            return agent.think(text)
        except Exception as e:
            return f"Sorry, something went wrong: {e}"

    pipeline.speak("JagX online. Say my name when you need me.")
    try:
        pipeline.start_continuous(on_command=handle_command)
    except KeyboardInterrupt:
        pipeline.stop()


def run_tray_mode(agent: JagXAgent):
    """Always-on mode with system tray icon (best for Windows app)."""
    pipeline = VoicePipeline(
        wake_word="jagx",
        stt_model_size="base",
        tts_voice="en-US-AriaNeural",
        language="en",
    )

    voice_thread: threading.Thread | None = None
    voice_running = {"value": False}

    def start_voice():
        if voice_running["value"]:
            return
        voice_running["value"] = True

        def handle_command(text: str) -> str:
            try:
                return agent.think(text)
            except Exception as e:
                return f"Sorry, something went wrong: {e}"

        def voice_loop():
            try:
                pipeline.speak("JagX is ready in the background.")
                pipeline.start_continuous(on_command=handle_command)
            finally:
                voice_running["value"] = False

        nonlocal voice_thread
        voice_thread = threading.Thread(target=voice_loop, daemon=True)
        voice_thread.start()
        console.print("[green]Voice listening started in background.[/green]")

    def stop_voice():
        pipeline.stop()
        voice_running["value"] = False
        console.print("[yellow]Voice listening stopped.[/yellow]")

    def toggle_voice():
        if voice_running["value"]:
            stop_voice()
        else:
            start_voice()

    def on_quit():
        stop_voice()
        console.print("[bold red]JagX shutting down...[/bold red]")
        # Give threads a moment
        time.sleep(0.5)
        sys.exit(0)

    tray = JagXTray(
        on_voice_toggle=toggle_voice,
        on_quit=on_quit,
    )
    tray.start()

    # Auto-start voice listening
    start_voice()

    console.print("[bold green]JagX is running in the system tray.[/bold green]")
    console.print("[dim]Right-click the orange icon to Toggle Voice or Quit.[/dim]")
    console.print("[dim]Say \"JagX\" followed by your command.[/dim]\n")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        on_quit()


def main():
    parser = argparse.ArgumentParser(description="JagX - Personal Jaguar AI")
    parser.add_argument(
        "--mode",
        choices=["voice", "text", "tray"],
        default="tray",
        help="Interface mode (default: tray = best for Windows app)",
    )
    args = parser.parse_args()

    print_banner()
    console.print("[bold green]JagX is starting...[/bold green]\n")

    agent = JagXAgent()

    if args.mode == "text":
        console.print("[dim]Text mode[/dim]\n")
        run_text_mode(agent)
    elif args.mode == "voice":
        console.print("[dim]Pure voice mode (console)[/dim]\n")
        pipeline = VoicePipeline()
        run_voice_mode(agent, pipeline)
    else:  # tray (recommended for the Windows app)
        console.print("[dim]System-tray / always-on mode[/dim]\n")
        run_tray_mode(agent)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]JagX shutting down...[/bold red]")
        sys.exit(0)
