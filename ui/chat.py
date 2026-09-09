"""JagX Windows assistant interface: chat, quick actions, status and voice."""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from core.agent import JagXAgent
from voice.pipeline import VoicePipeline


class JagXChat:
    def __init__(self, agent: JagXAgent):
        self.agent = agent
        self.voice = VoicePipeline(wake_word="jagx", stt_model_size="base", tts_voice="en-US-AriaNeural", language="en")
        self.root = tk.Tk()
        self.root.title("JagX — Windows Personal Assistant")
        self.root.geometry("1180x760")
        self.root.minsize(820, 600)
        self._busy = False
        self._build()
        self._first_run()

    def _build(self):
        self.root.configure(bg="#101216")
        header = tk.Frame(self.root, bg="#171a21", height=72)
        header.pack(fill="x")
        tk.Label(header, text="🐆  JagX", fg="#ffffff", bg="#171a21", font=("Segoe UI", 24, "bold")).pack(side="left", padx=22, pady=14)
        tk.Label(header, text="WINDOWS PERSONAL ASSISTANT", fg="#8f98a8", bg="#171a21", font=("Segoe UI", 9, "bold")).pack(side="left", padx=6, pady=18)
        self.status = tk.Label(header, text="● Ready", fg="#62d394", bg="#171a21", font=("Segoe UI", 10, "bold"))
        self.status.pack(side="right", padx=22)

        body = tk.Frame(self.root, bg="#101216")
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg="#171a21", width=235)
        side.pack(side="left", fill="y", padx=(12, 8), pady=12)
        side.pack_propagate(False)
        tk.Label(side, text="QUICK ACTIONS", fg="#8f98a8", bg="#171a21", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(18, 10))
        for label, command in [
            ("⌂  Windows help", lambda: self.quick("Help me with Windows.")),
            ("📁  Files & apps", lambda: self.quick("Help me manage my files and applications.")),
            ("🌐  Browse the web", lambda: self.quick("Open the browser and help me browse the web.")),
            ("💻  Coding mode", lambda: self.quick("Help me inspect, code, test, and build my project.")),
            ("🧠  Memory", lambda: self.quick("Show me what you remember about my preferences.")),
            ("🖼  Create image", lambda: self.quick("Help me create an image.")),
        ]:
            tk.Button(side, text=label, command=command, anchor="w", relief="flat", bd=0, bg="#20242d", fg="#e8ebf0", activebackground="#2b303b", activeforeground="#ffffff", font=("Segoe UI", 10), padx=12, pady=9).pack(fill="x", padx=10, pady=3)
        tk.Label(side, text="JagX can use voice, local AI, apps, files, browser controls and developer tools. Sensitive or destructive actions still require confirmation.", wraplength=195, justify="left", fg="#7f8795", bg="#171a21", font=("Segoe UI", 8)).pack(side="bottom", padx=16, pady=18)

        main = tk.Frame(body, bg="#101216")
        main.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)
        self.chat = scrolledtext.ScrolledText(main, wrap=tk.WORD, state="disabled", bg="#15181e", fg="#e9edf3", insertbackground="#ffffff", relief="flat", borderwidth=0, font=("Segoe UI", 11), padx=16, pady=16)
        self.chat.pack(fill="both", expand=True)

        composer = tk.Frame(main, bg="#171a21")
        composer.pack(fill="x", pady=(10, 0))
        self.entry = tk.Entry(composer, bg="#20242d", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10, ipady=9)
        self.entry.bind("<Return>", lambda _e: self.send())
        tk.Button(composer, text="🎙", command=self.listen, relief="flat", bg="#20242d", fg="#ffffff", font=("Segoe UI", 13), width=4).pack(side="left", padx=3)
        tk.Button(composer, text="Send", command=self.send, relief="flat", bg="#315efb", fg="#ffffff", activebackground="#4770ff", font=("Segoe UI", 10, "bold"), width=9, pady=8).pack(side="left", padx=(3, 10))
        tk.Label(main, text="Enter to send  •  Speak for voice input  •  JagX reads responses aloud", fg="#737b89", bg="#101216", font=("Segoe UI", 8)).pack(anchor="w", pady=(7, 0))

    def _first_run(self):
        marker = Path(self.agent.config.get("memory", {}).get("path", "./data/memory")) / ".first_run_done"
        if not marker.exists():
            intro = "I’m JagX, your personal assistant created by JagX and JRILICENSE to make work easier for you. You can talk to me or type to me."
            self._append("JagX", intro)
            threading.Thread(target=self.voice.speak, args=(intro,), daemon=True).start()
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("done", encoding="utf-8")
        else:
            self._append("JagX", "Welcome back. What would you like me to do?")

    def _append(self, who: str, text: str):
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{who}\n{text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)

    def _set_status(self, text: str, busy: bool = False):
        self.root.after(0, lambda: self.status.configure(text=("● " + text), fg=("#f0b35b" if busy else "#62d394")))

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
            response = self.agent.think(text)
        except Exception as e:
            response = f"Sorry, something went wrong: {e}"
        self.root.after(0, lambda: self._append("JagX", response))
        self._busy = False
        self._set_status("Ready")
        threading.Thread(target=self.voice.speak, args=(response,), daemon=True).start()

    def listen(self):
        if self._busy:
            return
        self._set_status("Listening…", True)
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
