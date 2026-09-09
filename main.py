#!/usr/bin/env python3
"""
JagX - Personal Jaguar AI Companion
Entry point with Voice + Text modes.

JRILICENSE
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.panel import Panel

from core.agent import JagXAgent
from voice.pipeline import VoicePipeline

console = Console()

def print_banner():
    console.print(Panel.fit(
        "[bold orange1]JagX[/bold orange1] 🐆\n"
        "[dim]Personal Jaguar AI Companion[/dim]\n\n"
        "[yellow]JRILICENSE[/yellow]",
        border_style="orange1"
    ))

def run_text_mode(agent: JagXAgent):
    """Classic text chat."""
    agent.run()

def run_voice_mode(agent: JagXAgent):
    """Full continuous voice mode."""
    pipeline = VoicePipeline(
        wake_word="jagx",
        stt_model_size="base",      # use "small" or "medium" for better accuracy
        tts_voice="en-US-AriaNeural",
        language="en",
    )

    def handle_command(text: str) -> str:
        """Send transcribed speech to the agent and return the reply."""
        try:
            return agent.think(text)
        except Exception as e:
            return f"Sorry, something went wrong: {e}"

    # Greet the user
    pipeline.speak("JagX online. Say my name when you need me.")

    try:
        pipeline.start_continuous(on_command=handle_command)
    except KeyboardInterrupt:
        pipeline.stop()
        console.print("\n[yellow]JagX voice mode stopped.[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="JagX - Personal Jaguar AI")
    parser.add_argument(
        "--mode",
        choices=["voice", "text", "both"],
        default="voice",
        help="Interface mode (default: voice)",
    )
    args = parser.parse_args()

    print_banner()
    console.print("[bold green]JagX is starting...[/bold green]\n")

    agent = JagXAgent()

    if args.mode == "text":
        console.print("[dim]Running in text mode. Type your commands.[/dim]\n")
        run_text_mode(agent)
    elif args.mode == "voice":
        console.print("[dim]Running in voice mode. Say \"JagX\" followed by your command.[/dim]\n")
        run_voice_mode(agent)
    else:  # both – simple hybrid
        console.print("[dim]Hybrid mode: type or speak. Type 'voice' to switch to pure voice.[/dim]\n")
        # For simplicity we start in text; user can relaunch with --mode voice
        run_text_mode(agent)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]JagX shutting down...[/bold red]")
        sys.exit(0)
