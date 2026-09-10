#!/usr/bin/env python3
"""
JagX — Premium Personal Jaguar AI
Live desktop companion + tray + command center + local AI.
JRILICENSE
"""
from __future__ import annotations

import argparse
import sys
import threading
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
            "[dim]Premium Personal Jaguar AI[/dim]\n"
            "[yellow]JRILICENSE[/yellow]",
            border_style="orange1",
        )
    )


def bootstrap_ai(agent, on_progress=None):
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
    """Full premium experience: walking jaguar + tray + main window."""
    from ui.tray import JagXTray
    from ui.chat import JagXChat
    from ui.companion import JaguarCompanion

    voice = None
    try:
        from voice.pipeline import VoicePipeline

        voice = VoicePipeline()
    except Exception:
        voice = None

    state = {"tray": None, "ui": None, "pet": None}

    def speak(text: str):
        pet = state.get("pet")
        tray = state.get("tray")
        if pet:
            pet.say(text[:40], seconds=min(6, max(2, len(text) // 12)))
        if tray:
            tray.set_talking(True)
            try:
                tray.notify("JagX", text[:120])
            except Exception:
                pass
        if voice:
            try:
                voice.speak(text)
            except Exception:
                pass
        if tray:
            tray.set_talking(False)

    def open_window():
        ui = state.get("ui")
        if ui and getattr(ui, "root", None):
            try:
                ui.root.deiconify()
                ui.root.lift()
                ui.root.focus_force()
            except Exception:
                pass
        pet = state.get("pet")
        if pet:
            pet.say("Opening…", seconds=1.5)

    def on_quit():
        try:
            if voice:
                voice.stop()
        except Exception:
            pass
        for key in ("pet", "tray"):
            obj = state.get(key)
            if obj:
                try:
                    obj.stop()
                except Exception:
                    pass
        ui = state.get("ui")
        if ui and getattr(ui, "root", None):
            try:
                ui.root.destroy()
            except Exception:
                pass
        sys.exit(0)

    # Tray jaguar (notification area)
    tray = JagXTray(
        on_open=open_window,
        on_type=open_window,
        on_voice_toggle=lambda: speak("Use the mic button in the window, or just type."),
        on_quit=on_quit,
    )
    state["tray"] = tray
    tray.start()

    # AI bootstrap in background
    def ai_job():
        result = bootstrap_ai(agent, on_progress=lambda m: console.print(f"[dim]{m}[/dim]"))
        msg = result.get("message") or "Ready"
        speak(f"JagX online. {msg}")

    threading.Thread(target=ai_job, daemon=True).start()

    # Main window
    ui = JagXChat(agent)
    state["ui"] = ui

    # Live walking companion on the desktop (same Tk app)
    pet = JaguarCompanion(on_click=open_window, on_double_click=open_window)
    pet.start(master=ui.root)
    state["pet"] = pet

    # Hook agent tool success → jaguar celebrates
    old_end = agent.on_tool_end

    def tool_end(name, result):
        if old_end:
            try:
                old_end(name, result)
            except Exception:
                pass
        if pet and not str(result).lower().startswith("error"):
            try:
                pet.celebrate()
            except Exception:
                pass

    agent.on_tool_end = tool_end

    def hide_to_tray():
        try:
            ui.root.withdraw()
            if pet:
                pet.say("I'm still here", seconds=2)
            if tray:
                tray.notify("JagX", "Jaguar is still on your desktop. Click it anytime.")
        except Exception:
            on_quit()

    try:
        ui.root.protocol("WM_DELETE_WINDOW", hide_to_tray)
    except Exception:
        pass

    # Premium first line in chat
    try:
        ui._append(
            "JagX",
            "I'm on your desktop now — the walking jaguar.\n"
            "Click the jaguar anytime, or type a command above.\n"
            "Try: open notepad · take a screenshot · system briefing",
        )
    except Exception:
        pass

    ui.run()


def main():
    parser = argparse.ArgumentParser(description="JagX Premium")
    parser.add_argument("--mode", choices=["premium", "gui", "text", "voice"], default="premium")
    args = parser.parse_args()
    print_banner()

    from core.agent import JagXAgent

    agent = JagXAgent()

    if args.mode in ("premium", "gui"):
        run_premium(agent)
    elif args.mode == "text":
        agent.run()
    else:
        run_premium(agent)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
