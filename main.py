#!/usr/bin/env python3
"""
JagX — Premium Personal Jaguar AI
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
            preferred_model="qwen2.5:3b",
            auto_pull=True,
            auto_install_ollama=True,
            specialize=False,
            on_progress=on_progress,
        )
        if result.get("ok") and result.get("model"):
            agent.llm.model = result["model"]
            agent.llm.available_models = result.get("available") or []
            # Force 3b when present
            for m in agent.llm.available_models:
                if "qwen2.5:3b" in m.lower() and "coder" not in m.lower():
                    agent.llm.model = m
                    break
            try:
                agent.llm.warm_up()
            except Exception:
                pass
        return result
    except Exception as e:
        return {"ok": False, "message": str(e)}


def run_premium(agent):
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
            try:
                pet.say(text[:40], seconds=min(6, max(2, len(text) // 12)))
            except Exception:
                pass
        if tray:
            try:
                tray.set_talking(True)
                tray.notify("JagX", text[:120])
            except Exception:
                pass
        if voice:
            try:
                voice.speak(text)
            except Exception:
                try:
                    from voice.tts import speak as tts_speak

                    tts_speak(text)
                except Exception:
                    pass
        if tray:
            try:
                tray.set_talking(False)
            except Exception:
                pass

    def open_window():
        ui = state.get("ui")
        if ui and getattr(ui, "root", None):
            try:
                ui.root.deiconify()
                ui.root.lift()
                ui.root.focus_force()
            except Exception:
                pass

    def run_command(text: str):
        """From jaguar head type box."""
        ui = state.get("ui")
        if ui:
            try:
                ui.entry.delete(0, "end")
                ui.entry.insert(0, text)
                ui.send()
                open_window()
                return
            except Exception:
                pass
        # Fallback direct
        try:
            result = agent.think(text)
            speak(result[:200] if result else "Done")
        except Exception as e:
            speak(str(e)[:120])

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

    tray = JagXTray(
        on_open=open_window,
        on_type=open_window,
        on_voice_toggle=lambda: speak("Type a command in the box or use the mic button."),
        on_quit=on_quit,
    )
    state["tray"] = tray
    tray.start()

    def ai_job():
        result = bootstrap_ai(agent, on_progress=lambda m: console.print(f"[dim]{m}[/dim]"))
        msg = result.get("message") or "Ready"
        model = getattr(agent.llm, "model", "?")
        speak(f"JagX online with {model}")

    threading.Thread(target=ai_job, daemon=True).start()

    ui = JagXChat(agent)
    state["ui"] = ui

    pet = JaguarCompanion(on_click=open_window, on_double_click=open_window, on_command=run_command)
    pet.start(master=ui.root)
    state["pet"] = pet

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
                pet.say("Still here", seconds=2)
        except Exception:
            on_quit()

    try:
        ui.root.protocol("WM_DELETE_WINDOW", hide_to_tray)
    except Exception:
        pass

    try:
        ui._append(
            "JagX",
            "Ready.\n"
            "• Type in the main box OR in the box on the jaguar's head\n"
            "• Try: open notepad · take a screenshot · quick virus scan\n"
            "• Model should show qwen2.5:3b after Ollama is running",
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

    if args.mode in ("premium", "gui", "voice"):
        run_premium(agent)
    else:
        agent.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
