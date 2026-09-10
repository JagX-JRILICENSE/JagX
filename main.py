#!/usr/bin/env python3
"""
JagX — Personal Jaguar AI Companion
Premium always-on Windows experience: tray jaguar + chat + voice.
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

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold orange1]🐆  JagX[/bold orange1]\n"
            "[dim]Personal Jaguar AI Companion[/dim]\n"
            "[yellow]JRILICENSE[/yellow]",
            border_style="orange1",
        )
    )


def bootstrap_ai(agent, on_progress=None):
    """Make local AI ready as soon as the app starts."""
    try:
        from core.setup_ai import ensure_local_ai

        result = ensure_local_ai(
            base_url=getattr(agent.llm, "base_url", "http://127.0.0.1:11434"),
            preferred_model=getattr(agent.llm, "model", "qwen2.5:3b"),
            auto_pull=True,
            auto_install_ollama=True,
            on_progress=on_progress,
        )
        if result.get("ok") and result.get("model"):
            agent.llm.model = result["model"]
            agent.llm.available_models = result.get("available") or []
        return result
    except Exception as e:
        return {"ok": False, "message": str(e)}


def run_premium(agent):
    """Default mode: jaguar tray + main window + optional voice."""
    from ui.tray import JagXTray
    from ui.chat import JagXChat

    voice = None
    try:
        from voice.pipeline import VoicePipeline

        voice = VoicePipeline()
    except Exception:
        voice = None

    tray_holder = {"tray": None}
    chat_holder = {"ui": None}

    def speak(text: str):
        tray = tray_holder.get("tray")
        if tray:
            tray.set_talking(True)
            tray.notify("JagX", text[:120])
        if voice:
            try:
                voice.speak(text)
            except Exception:
                pass
        if tray:
            tray.set_talking(False)

    def open_window():
        ui = chat_holder.get("ui")
        if ui and getattr(ui, "root", None):
            try:
                ui.root.deiconify()
                ui.root.lift()
                ui.root.focus_force()
            except Exception:
                pass

    def on_quit():
        try:
            if voice:
                voice.stop()
        except Exception:
            pass
        tray = tray_holder.get("tray")
        if tray:
            tray.stop()
        ui = chat_holder.get("ui")
        if ui and getattr(ui, "root", None):
            try:
                ui.root.destroy()
            except Exception:
                pass
        sys.exit(0)

    def toggle_voice():
        speak("Voice toggle is available from the main window microphone button.")

    # Start tray jaguar first so user always sees the animal
    tray = JagXTray(
        on_open=open_window,
        on_type=open_window,
        on_voice_toggle=toggle_voice,
        on_quit=on_quit,
    )
    tray_holder["tray"] = tray
    tray_ok = tray.start()
    if tray_ok:
        tray.notify("JagX", "Jaguar is online. Click the orange icon anytime.")

    # Prepare AI in background while UI loads
    def ai_job():
        def prog(msg):
            console.print(f"[dim]{msg}[/dim]")

        result = bootstrap_ai(agent, on_progress=prog)
        msg = result.get("message") or ("AI ready" if result.get("ok") else "AI needs setup")
        speak(f"JagX online. {msg}")

    threading.Thread(target=ai_job, daemon=True).start()

    # Main premium window (blocks until closed)
    ui = JagXChat(agent)
    chat_holder["ui"] = ui

    # When window is closed, hide to tray instead of full quit
    def hide_to_tray():
        try:
            ui.root.withdraw()
            if tray_holder.get("tray"):
                tray_holder["tray"].notify("JagX", "Still running in the system tray. Click the jaguar to open.")
        except Exception:
            on_quit()

    try:
        ui.root.protocol("WM_DELETE_WINDOW", hide_to_tray)
    except Exception:
        pass

    ui.run()


def main():
    parser = argparse.ArgumentParser(description="JagX — Personal Jaguar AI")
    parser.add_argument(
        "--mode",
        choices=["premium", "gui", "voice", "text", "tray"],
        default="premium",
        help="premium = tray jaguar + window (default)",
    )
    args = parser.parse_args()
    print_banner()

    from core.agent import JagXAgent

    agent = JagXAgent()

    if args.mode in ("premium", "gui"):
        run_premium(agent)
    elif args.mode == "text":
        agent.run()
    elif args.mode == "voice":
        from voice.pipeline import VoicePipeline

        pipeline = VoicePipeline()

        def handle(text):
            try:
                return agent.think(text)
            except Exception as e:
                return f"Error: {e}"

        pipeline.speak("JagX online.")
        pipeline.start_continuous(on_command=handle)
    else:
        # tray-only fallback
        run_premium(agent)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
