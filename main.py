#!/usr/bin/env python3
"""JagX - Personal Jaguar AI Companion: GUI + voice + text + system tray."""
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
from ui.chat import launch_chat
console = Console()

def print_banner():
    console.print(Panel.fit("[bold orange1]JagX[/bold orange1] 🐆\n[dim]Personal Jaguar AI Companion[/dim]\n\n[yellow]JRILICENSE[/yellow]", border_style="orange1"))

def run_text_mode(agent): agent.run()

def run_voice_mode(agent, pipeline):
    def handle_command(text):
        try: return agent.think(text)
        except Exception as e: return f"Sorry, something went wrong: {e}"
    pipeline.speak("JagX online. Say my name when you need me.")
    try: pipeline.start_continuous(on_command=handle_command)
    except KeyboardInterrupt: pipeline.stop()

def run_tray_mode(agent):
    pipeline = VoicePipeline(wake_word="jagx", stt_model_size="base", tts_voice="en-US-AriaNeural", language="en")
    voice_running = {"value": False}
    def start_voice():
        if voice_running["value"]: return
        voice_running["value"] = True
        def handle_command(text):
            try: return agent.think(text)
            except Exception as e: return f"Sorry, something went wrong: {e}"
        def loop():
            try:
                pipeline.speak("JagX is ready in the background.")
                pipeline.start_continuous(on_command=handle_command)
            finally: voice_running["value"] = False
        threading.Thread(target=loop, daemon=True).start()
    def stop_voice(): pipeline.stop(); voice_running["value"] = False
    def toggle_voice(): stop_voice() if voice_running["value"] else start_voice()
    def on_quit(): stop_voice(); time.sleep(.3); sys.exit(0)
    JagXTray(on_voice_toggle=toggle_voice, on_quit=on_quit).start()
    start_voice()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: on_quit()

def main():
    parser = argparse.ArgumentParser(description="JagX - Personal Jaguar AI")
    parser.add_argument("--mode", choices=["gui", "voice", "text", "tray"], default="gui")
    args = parser.parse_args()
    print_banner()
    agent = JagXAgent()
    if args.mode == "gui": launch_chat(agent)
    elif args.mode == "text": run_text_mode(agent)
    elif args.mode == "voice": run_voice_mode(agent, VoicePipeline())
    else: run_tray_mode(agent)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)
