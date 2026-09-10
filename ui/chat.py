"""JagX Windows command-center dashboard with reliable typed command execution."""
from __future__ import annotations

import platform
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

from core.agent import JagXAgent

try:
    from core.tools.power import shutdown_windows, sleep_windows, hibernate_windows
except Exception:
    def shutdown_windows(): return "unavailable"
    def sleep_windows(): return "unavailable"
    def hibernate_windows(): return "unavailable"

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


class JagXChat:
    def __init__(self, agent: JagXAgent):
        self.agent = agent
        self.agent.gui_mode = True

        # GUI confirmation dialog for sensitive actions
        def _confirm(msg: str) -> bool:
            try:
                return bool(messagebox.askyesno("JagX confirmation", msg))
            except Exception:
                return False

        self.agent.confirm_callback = _confirm

        # Live tool status in the UI
        def _tool_start(name: str, args: dict):
            self.root.after(0, lambda: self._set_status(f"Running {name}…", True))
            self.root.after(0, lambda: self._append("System", f"→ {name}({args})"))

        def _tool_end(name: str, result: str):
            short = (result[:180] + "…") if len(result) > 180 else result
            self.root.after(0, lambda: self._append("System", f"✓ {name}: {short}"))

        self.agent.on_tool_start = _tool_start
        self.agent.on_tool_end = _tool_end

        self.voice = None
        if VoicePipeline is not None:
            try:
                self.voice = VoicePipeline(
                    wake_word="jagx",
                    stt_model_size="base",
                    tts_voice="en-US-AriaNeural",
                    language="en",
                )
            except Exception:
                self.voice = None

        self.root = tk.Tk()
        self.root.title("JagX — Windows Command Center")
        self.root.geometry("1400x900")
        self.root.minsize(1050, 700)
        self._busy = False
        self._build()
        self._first_run()
        self._refresh_dashboard()
        self._start_idle_monitor()

    def _button(self, parent, text, command, width=None):
        return tk.Button(
            parent, text=text, command=command, anchor="w", relief="flat", bd=0,
            bg=CARD, fg=TEXT, activebackground="#273142", activeforeground=TEXT,
            font=("Segoe UI", 10), padx=12, pady=8, width=width,
        )

    def _build(self):
        self.root.configure(bg=BG)
        top = tk.Frame(self.root, bg=PANEL, height=70)
        top.pack(fill="x")
        tk.Label(top, text="🐆 JagX", bg=PANEL, fg=TEXT, font=("Segoe UI", 24, "bold")).pack(side="left", padx=20, pady=12)
        tk.Label(top, text="WINDOWS COMMAND CENTER", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.ai_status = tk.Label(top, text="● AI: checking…", bg=PANEL, fg=WARN, font=("Segoe UI", 10, "bold"))
        self.ai_status.pack(side="right", padx=18)
        self.status = tk.Label(top, text="● Ready — type a command below", bg=PANEL, fg=GOOD, font=("Segoe UI", 10, "bold"))
        self.status.pack(side="right", padx=8)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=PANEL, width=220)
        nav.pack(side="left", fill="y", padx=(10, 6), pady=10)
        nav.pack_propagate(False)
        tk.Label(nav, text="QUICK ACTIONS", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(15, 8))

        quicks = [
            ("📁 Open Explorer", "Open File Explorer now"),
            ("🌐 Open Browser", "Open my default web browser"),
            ("📝 Open Notepad", "Open Notepad"),
            ("🖱 Mouse position", "Get the current mouse position"),
            ("📸 Screenshot", "Take a screenshot of my screen"),
            ("⌨ Type hello", "Click the center of the screen then type Hello from JagX"),
            ("📷 Camera check", "Check if anything is using my camera or microphone"),
            ("🧠 What can you do?", "What system actions can you perform for me right now?"),
        ]
        for label, prompt in quicks:
            self._button(nav, label, lambda p=prompt: self.quick(p)).pack(fill="x", padx=8, pady=2)

        tk.Frame(nav, bg=PANEL).pack(fill="both", expand=True)
        self._button(nav, "🔄 Refresh dashboard", self._refresh_dashboard).pack(fill="x", padx=8, pady=5)
        if self.voice:
            self._button(nav, "🎙 Voice (optional)", self.listen).pack(fill="x", padx=8, pady=5)

        content = tk.Frame(body, bg=BG)
        content.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        cards = tk.Frame(content, bg=BG)
        cards.pack(fill="x")
        self.cpu_card = self._card(cards, "CPU", "—", 0)
        self.ram_card = self._card(cards, "MEMORY", "—", 1)
        self.disk_card = self._card(cards, "SYSTEM", platform.system(), 2)
        self.model_card = self._card(cards, "AI MODEL", getattr(self.agent.llm, "model", "local"), 3)

        # Big chat area for typing commands
        self._section(content, "TYPE YOUR COMMAND", "Press Enter or click Send — JagX will act on your system")
        self.chat = scrolledtext.ScrolledText(
            content, wrap=tk.WORD, bg=PANEL, fg=TEXT, relief="flat", font=("Segoe UI", 11), height=22
        )
        self.chat.pack(fill="both", expand=True, pady=(0, 8))

        composer = tk.Frame(content, bg=PANEL)
        composer.pack(fill="x")
        self.entry = tk.Entry(composer, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=8, pady=10, ipady=10)
        self.entry.bind("<Return>", lambda _e: self.send())
        if self.voice:
            tk.Button(composer, text="🎙", command=self.listen, bg=CARD, fg=TEXT, relief="flat", width=4, font=("Segoe UI", 12)).pack(side="left")
        tk.Button(
            composer, text="Send / Do it", command=self.send, bg=ACCENT, fg="white",
            relief="flat", width=12, pady=10, font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=8)

    def _card(self, parent, title, value, column):
        card = tk.Frame(parent, bg=PANEL, height=90)
        card.grid(row=0, column=column, sticky="nsew", padx=4)
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        label = tk.Label(card, text=value, bg=PANEL, fg=TEXT, font=("Segoe UI", 16, "bold"))
        label.pack(anchor="w", padx=14)
        return label

    def _section(self, parent, title, subtitle):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 5))
        tk.Label(row, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(row, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(side="right")

    def _first_run(self):
        intro = (
            "I’m JagX. Type what you want me to do and press Send.\n"
            "Examples:\n"
            "• open notepad\n"
            "• take a screenshot\n"
            "• move the mouse to the center and click\n"
            "• open file explorer\n"
            "• check if anything is using my camera"
        )
        self._append("JagX", intro)

    def _append(self, who, text):
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{who}: {text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)

    def _set_status(self, text, busy=False):
        self.root.after(0, lambda: self.status.configure(text="● " + text, fg=WARN if busy else GOOD))

    def quick(self, text):
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
        threading.Thread(target=self._think, args=(text,), daemon=True).start()

    def _think(self, text):
        try:
            response = self.agent.think(text)
        except Exception as exc:
            response = f"Sorry, something went wrong: {exc}"
        self.root.after(0, lambda: self._append("JagX", response))
        self._busy = False
        self._set_status("Ready — type next command")
        if self.voice:
            try:
                threading.Thread(target=self.voice.speak, args=(response,), daemon=True).start()
            except Exception:
                pass

    def listen(self):
        if not self.voice or self._busy:
            self._append("JagX", "Voice is unavailable. Please type your command.")
            return
        self._set_status("Listening…", True)
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        try:
            text = self.voice.listen_once()
        except Exception:
            text = ""
        if not text:
            self.root.after(0, lambda: self._append("JagX", "I didn't catch that. Please type instead."))
            self._set_status("Type your request")
            self.root.after(0, self.entry.focus_set)
            return
        self.root.after(0, lambda: (self.entry.delete(0, tk.END), self.entry.insert(0, text), self.send()))

    def _refresh_dashboard(self):
        def worker():
            cpu = ram = "—"
            try:
                import psutil
                cpu = f"{psutil.cpu_percent(interval=0.3):.0f}%"
                ram = f"{psutil.virtual_memory().percent:.0f}%"
            except Exception:
                pass
            self.root.after(0, lambda: self.cpu_card.configure(text=cpu))
            self.root.after(0, lambda: self.ram_card.configure(text=ram))
            self.root.after(0, self._refresh_ai_status)
        threading.Thread(target=worker, daemon=True).start()

    def _refresh_ai_status(self):
        try:
            model = getattr(getattr(self.agent, "llm", None), "model", "local")
            self.model_card.configure(text=str(model))
            self.ai_status.configure(text=f"● AI: {model}", fg=GOOD)
        except Exception:
            self.ai_status.configure(text="● AI: check Ollama", fg=WARN)

    def _start_idle_monitor(self):
        policy = self.agent.config.get("idle_power", {})
        if not policy.get("enabled", False):
            return
        self._idle_check()

    def _idle_check(self):
        policy = self.agent.config.get("idle_power", {})
        if not policy.get("enabled", False):
            return
        try:
            import ctypes

            class LI(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            li = LI()
            li.cbSize = ctypes.sizeof(LI)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li))
            idle = (ctypes.windll.kernel32.GetTickCount() - li.dwTime) / 1000
            limit = int(policy.get("timeout_minutes", 30)) * 60
            if idle >= limit and not self._busy:
                action = str(policy.get("action", "sleep")).lower()
                self._append("JagX", f"Idle timeout — starting {action}.")
                fn = {"sleep": sleep_windows, "hibernate": hibernate_windows, "shutdown": shutdown_windows}.get(action)
                if fn:
                    fn()
                return
        except Exception:
            pass
        self.root.after(15000, self._idle_check)

    def run(self):
        self.entry.focus_set()
        self.root.mainloop()


def launch_chat(agent: JagXAgent):
    JagXChat(agent).run()
