"""JagX main window — always talks while working."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from core.agent import JagXAgent

try:
    from voice.pipeline import VoicePipeline
except Exception:
    VoicePipeline = None

try:
    from voice.tts import speak_async as direct_speak_async
except Exception:
    direct_speak_async = None

BG = "#0d1117"
PANEL = "#161b22"
CARD = "#1d2430"
TEXT = "#f0f3f6"
MUTED = "#8b949e"
ACCENT = "#2f81f7"
GOOD = "#3fb950"
WARN = "#d29922"
SPEAK = "#a371f7"


class JagXChat:
    def __init__(self, agent: JagXAgent):
        self.agent = agent
        self.agent.gui_mode = True

        def _confirm(msg: str) -> bool:
            try:
                return bool(messagebox.askyesno("JagX — confirm", msg))
            except Exception:
                return False

        self.agent.confirm_callback = _confirm

        self.voice = None
        if VoicePipeline is not None:
            try:
                self.voice = VoicePipeline()
            except Exception:
                self.voice = None

        def _tool_start(name: str, args: dict):
            self._set_status(f"Working: {name}", True)
            self._append("System", f"→ {name}")
            # Always narrate actions
            nice = name.replace("_", " ")
            self._talk(f"Working on {nice}")

        def _tool_end(name: str, result: str):
            short = result if len(result) < 160 else result[:160] + "…"
            self._append("System", f"✓ {short}")

        self.agent.on_tool_start = _tool_start
        self.agent.on_tool_end = _tool_end

        self.root = tk.Tk()
        self.root.title("JagX")
        self.root.geometry("980x720")
        self.root.minsize(720, 560)
        self._busy = False
        self._build()
        self._append(
            "JagX",
            "I will talk while I work.\n"
            "Examples: open notepad · open 2048 · press space in game · system briefing",
        )
        self._talk("JagX is ready. Tell me what to do.")
        threading.Thread(target=self._startup_ai_check, daemon=True).start()

    def _talk(self, text: str):
        """Always attempt speech."""
        if not text:
            return
        self._set_speaking(f"🔊 {text[:80]}")
        try:
            if self.voice:
                self.voice.speak_async(text)
            elif direct_speak_async:
                direct_speak_async(text)
        except Exception:
            try:
                if direct_speak_async:
                    direct_speak_async(text)
            except Exception:
                pass

    def _build(self):
        self.root.configure(bg=BG)
        top = tk.Frame(self.root, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text="🐆 JagX", bg=PANEL, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left", padx=16, pady=12)
        self.status = tk.Label(top, text="● Starting…", bg=PANEL, fg=WARN, font=("Segoe UI", 10, "bold") )
        self.status.pack(side="right", padx=16)
        self.model_lbl = tk.Label(top, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.model_lbl.pack(side="right", padx=8)

        type_frame = tk.Frame(self.root, bg=PANEL)
        type_frame.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(type_frame, text="TYPE HERE", bg=PANEL, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=4)
        row = tk.Frame(type_frame, bg=PANEL)
        row.pack(fill="x", pady=6)
        self.entry = tk.Entry(row, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 13))
        self.entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 8))
        self.entry.bind("<Return>", lambda _e: self.send())
        self.entry.focus_set()
        tk.Button(row, text="Do it", command=self.send, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 11, "bold"), padx=16, pady=10).pack(side="left")
        tk.Button(row, text="🎤", command=self.listen, bg=CARD, fg=TEXT, relief="flat", font=("Segoe UI", 12), padx=10, pady=8).pack(side="left", padx=(8, 0))

        chips = tk.Frame(self.root, bg=BG)
        chips.pack(fill="x", padx=12, pady=4)
        for label, cmd in [
            ("Open Notepad", "open notepad"),
            ("Play 2048", "open 2048"),
            ("Play dino", "open dino game"),
            ("Screenshot", "take a screenshot"),
            ("Train / Fix AI", "__fix_ai__"),
        ]:
            tk.Button(
                chips, text=label,
                command=(self.fix_ai if cmd == "__fix_ai__" else lambda c=cmd: self.quick(c)),
                bg=CARD, fg=TEXT, relief="flat", font=("Segoe UI", 9), padx=10, pady=6,
            ).pack(side="left", padx=3, pady=3)

        mid = tk.Frame(self.root, bg=BG)
        mid.pack(fill="both", expand=True, padx=12, pady=8)
        tk.Label(mid, text="ACTIVITY", bg=BG, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.chat = scrolledtext.ScrolledText(mid, wrap=tk.WORD, bg=PANEL, fg=TEXT, relief="flat", font=("Segoe UI", 11), state="disabled")
        self.chat.pack(fill="both", expand=True, pady=(4, 0))
        self.speak_lbl = tk.Label(self.root, text="", bg=BG, fg=SPEAK, font=("Segoe UI", 10, "bold"))
        self.speak_lbl.pack(fill="x", padx=16, pady=(0, 10))

    def _append(self, who: str, text: str):
        def _do():
            self.chat.configure(state="normal")
            self.chat.insert(tk.END, f"{who}: {text}\n\n")
            self.chat.configure(state="disabled")
            self.chat.see(tk.END)
        self.root.after(0, _do)

    def _set_status(self, text: str, busy: bool = False):
        color = WARN if busy else GOOD
        self.root.after(0, lambda: self.status.configure(text="● " + text, fg=color))

    def _set_speaking(self, text: str):
        self.root.after(0, lambda: self.speak_lbl.configure(text=text))

    def quick(self, text: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.send()

    def send(self):
        text = self.entry.get().strip()
        if not text or self._busy:
            return
        self.entry.delete(0, tk.END)
        self._append("You", text)
        self._busy = True
        self._set_status("Working…", True)
        self._talk(f"Okay. {text[:60]}")
        threading.Thread(target=self._think, args=(text,), daemon=True).start()

    def _think(self, text: str):
        try:
            self._append("JagX", f"Got it: “{text}”. Working…")
            response = self.agent.think(text)
        except Exception as exc:
            response = f"Something went wrong: {exc}"
        self._append("JagX", response)
        self._busy = False
        self._set_status("Ready")
        # Always speak the result (shortened for speech)
        spoken = response if len(response) < 350 else response[:350] + "..."
        self._talk(spoken)
        self.root.after(8000, lambda: self._set_speaking(""))

    def listen(self):
        if self._busy:
            return
        self._set_status("Listening…", True)
        self._set_speaking("🎤 Listening")
        self._talk("I'm listening")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        text = ""
        if self.voice:
            try:
                text = self.voice.listen_once()
            except Exception:
                text = ""
        self._set_speaking("")
        if not text:
            self._append("JagX", "Didn't catch that — type here.")
            self._talk("I did not catch that. Please type.")
            self._set_status("Type a command")
            return
        self.root.after(0, lambda: (self.entry.delete(0, tk.END), self.entry.insert(0, text), self.send()))

    def _startup_ai_check(self):
        self._set_status("Checking AI…", True)
        try:
            st = self.agent.llm.status()
            model = st.get("model") or getattr(self.agent.llm, "model", "?")
            self.root.after(0, lambda: self.model_lbl.configure(text=f"Model: {model}"))
            if st.get("reachable"):
                self._set_status("Ready")
            else:
                self._set_status("AI not ready", True)
                self._talk("AI model not ready. Click Train Fix AI.")
        except Exception as e:
            self._set_status("AI check failed", True)
            self._append("JagX", str(e))

    def fix_ai(self):
        if self._busy:
            return
        self._busy = True
        self._set_status("Installing model…", True)
        self._talk("Installing the best model for your PC")
        self._append("JagX", "Installing / specializing model…")

        def worker():
            def progress(msg: str):
                self._set_status(msg[:60], True)
                self._append("Setup", msg)

            try:
                from core.train_jagx import install_best_jagx_model
                result = install_best_jagx_model(on_progress=progress, force_recreate=True)
            except Exception:
                from core.setup_ai import ensure_local_ai
                result = ensure_local_ai(preferred_model="jagx", auto_pull=True, specialize=True, on_progress=progress)

            if result.get("ok") and result.get("model"):
                self.agent.llm.model = result["model"]
                self.root.after(0, lambda: self.model_lbl.configure(text=f"Model: {result['model']}"))
                self._append("JagX", f"Ready with {result['model']}")
                self._talk(f"AI ready with {result['model']}")
                self._set_status("Ready")
            else:
                self._append("JagX", result.get("message") or "Setup failed")
                self._talk("Model setup failed")
                self._set_status("AI setup failed", True)
            self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        self.root.mainloop()


def launch_chat(agent: JagXAgent):
    JagXChat(agent).run()
