"""JagX Windows-friendly hybrid text + voice chat UI."""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

from core.agent import JagXAgent
from voice.pipeline import VoicePipeline


class JagXChat:
    def __init__(self, agent: JagXAgent):
        self.agent = agent
        self.voice = VoicePipeline(
            wake_word="jagx", stt_model_size="base",
            tts_voice="en-US-AriaNeural", language="en"
        )
        self.root = tk.Tk()
        self.root.title("JagX — Personal Assistant")
        self.root.geometry("900x650")
        self.root.minsize(650, 500)
        self._build()
        self._first_run()

    def _build(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=12, pady=10)
        tk.Label(top, text="🐆 JagX", font=("Segoe UI", 22, "bold")).pack(side="left")
        self.status = tk.Label(top, text="Ready", font=("Segoe UI", 10))
        self.status.pack(side="right")

        self.chat = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state="disabled", font=("Segoe UI", 11))
        self.chat.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        self.entry = tk.Entry(bottom, font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.entry.bind("<Return>", lambda _e: self.send())
        tk.Button(bottom, text="Send", command=self.send, width=10).pack(side="left", padx=6)
        tk.Button(bottom, text="🎙 Speak", command=self.listen, width=10).pack(side="left")

        tk.Label(self.root, text="Type a request or press Speak. If voice recognition fails, JagX will let you type instead.", fg="gray").pack(pady=(0, 8))

    def _first_run(self):
        marker = Path(self.agent.config.get("memory", {}).get("path", "./data/memory")) / ".first_run_done"
        if not marker.exists():
            intro = "I’m JagX, your personal assistant created by JagX and JRILICENSE to make work easier for you. You can talk to me or type to me."
            self._append("JagX", intro)
            threading.Thread(target=self.voice.speak, args=(intro,), daemon=True).start()
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("done", encoding="utf-8")
        else:
            self._append("JagX", "Welcome back. How can I help?")

    def _append(self, who: str, text: str):
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{who}:\n{text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)

    def _set_status(self, text: str):
        self.root.after(0, lambda: self.status.configure(text=text))

    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._append("You", text)
        self._set_status("Thinking…")
        threading.Thread(target=self._think, args=(text,), daemon=True).start()

    def _think(self, text: str):
        try:
            response = self.agent.think(text)
        except Exception as e:
            response = f"Sorry, something went wrong: {e}"
        self.root.after(0, lambda: self._append("JagX", response))
        self._set_status("Ready")
        threading.Thread(target=self.voice.speak, args=(response,), daemon=True).start()

    def listen(self):
        self._set_status("Listening…")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        try:
            text = self.voice.listen_once()
        except Exception:
            text = ""
        if not text:
            self.root.after(0, lambda: self._append("JagX", "I didn't catch that. Please type your request below."))
            self._set_status("Type your request")
            self.root.after(0, self.entry.focus_set)
            return
        self.root.after(0, lambda: (self.entry.delete(0, tk.END), self.entry.insert(0, text), self.send()))

    def run(self):
        self.entry.focus_set()
        self.root.mainloop()


def launch_chat(agent: JagXAgent):
    JagXChat(agent).run()
