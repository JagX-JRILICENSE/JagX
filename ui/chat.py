"""JagX main window — type-first, higher-model training button."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from core.agent import JagXAgent

try:
    from voice.pipeline import VoicePipeline
except Exception:
    VoicePipeline = None

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

        def _tool_start(name: str, args: dict):
            self._set_status(f"Working: {name}", True)
            self._append("System", f"→ {name}")

        def _tool_end(name: str, result: str):
            short = result if len(result) < 160 else result[:160] + "…"
            self._append("System", f"✓ {short}")

        self.agent.on_tool_start = _tool_start
        self.agent.on_tool_end = _tool_end

        self.voice = None
        if VoicePipeline is not None:
            try:
                self.voice = VoicePipeline()
            except Exception:
                self.voice = None

        self.root = tk.Tk()
        self.root.title("JagX")
        self.root.geometry("980x720")
        self.root.minsize(720, 560)
        self._busy = False
        self._build()
        self._append(
            "JagX",
            "Type a command below.\n"
            "Click **Train / Fix AI** once to install the best model for your PC and specialize it as JagX.\n"
            "Examples: open notepad · take a screenshot · system briefing",
        )
        threading.Thread(target=self._startup_ai_check, daemon=True).start()

    def _build(self):
        self.root.configure(bg=BG)

        top = tk.Frame(self.root, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text="🐆 JagX", bg=PANEL, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left", padx=16, pady=12)
        self.status = tk.Label(top, text="● Starting…", bg=PANEL, fg=WARN, font=("Segoe UI", 10, "bold"))
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

        tk.Button(
            row, text="Do it", command=self.send, bg=ACCENT, fg="white", relief="flat",
            font=("Segoe UI", 11, "bold"), padx=16, pady=10,
        ).pack(side="left")
        if self.voice:
            tk.Button(
                row, text="🎤", command=self.listen, bg=CARD, fg=TEXT, relief="flat",
                font=("Segoe UI", 12), padx=10, pady=8,
            ).pack(side="left", padx=(8, 0))

        chips = tk.Frame(self.root, bg=BG)
        chips.pack(fill="x", padx=12, pady=4)
        for label, cmd in [
            ("Open Notepad", "open notepad"),
            ("Screenshot", "take a screenshot"),
            ("System briefing", "system briefing"),
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
        self.chat = scrolledtext.ScrolledText(
            mid, wrap=tk.WORD, bg=PANEL, fg=TEXT, relief="flat", font=("Segoe UI", 11), state="disabled"
        )
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
        self._set_status("Thinking…", True)
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
        if self.voice and response:
            self._set_speaking("🔊 Speaking…")
            try:
                self.voice.speak(response)
            except Exception:
                pass
            self._set_speaking("")

    def listen(self):
        if not self.voice:
            self._append("JagX", "Voice unavailable — type instead.")
            return
        if self._busy:
            return
        self._set_status("Listening…", True)
        self._set_speaking("🎤 Listening")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        try:
            text = self.voice.listen_once()
        except Exception:
            text = ""
        self._set_speaking("")
        if not text:
            self._append("JagX", "Didn't catch that — type here.")
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
                if "coder" in str(model).lower() and "1.5b" in str(model).lower():
                    self._append("JagX", "Small coder model detected. Click **Train / Fix AI** for a better JagX model.")
            else:
                self._set_status("AI not ready", True)
                self._append("JagX", "Click **Train / Fix AI** to install the best model for your PC.")
        except Exception as e:
            self._set_status("AI check failed", True)
            self._append("JagX", str(e))

    def fix_ai(self):
        if self._busy:
            return
        self._busy = True
        self._set_status("Training / installing best model…", True)
        self._append(
            "JagX",
            "Detecting your PC power, pulling the best model it can run, "
            "then specializing it as **jagx** for desktop control. This can take several minutes.",
        )

        def worker():
            def progress(msg: str):
                self._set_status(msg[:60], True)
                self._append("Setup", msg)

            # Prefer full specialization path
            try:
                from core.train_jagx import install_best_jagx_model

                result = install_best_jagx_model(on_progress=progress, force_recreate=True)
            except Exception:
                from core.setup_ai import ensure_local_ai

                result = ensure_local_ai(
                    preferred_model="jagx",
                    auto_pull=True,
                    specialize=True,
                    on_progress=progress,
                )

            if result.get("ok") and result.get("model"):
                self.agent.llm.model = result["model"]
                try:
                    from core.setup_ai import list_models

                    self.agent.llm.available_models = list_models()
                except Exception:
                    pass
                self.root.after(0, lambda: self.model_lbl.configure(text=f"Model: {result['model']}"))
                self._append("JagX", f"Specialized AI ready: {result['model']}\nTry: open notepad")
                self._set_status("Ready")
            else:
                self._append("JagX", result.get("message") or "Could not train/install model.")
                self._set_status("AI setup failed", True)
            self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        self.root.mainloop()


def launch_chat(agent: JagXAgent):
    JagXChat(agent).run()
