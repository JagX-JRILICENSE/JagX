"""JagX Windows command-center dashboard."""
from __future__ import annotations
import os
import platform
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext
from core.agent import JagXAgent
from core.tools.power import shutdown_windows, sleep_windows, hibernate_windows
from voice.pipeline import VoicePipeline
BG="#0d1117"; PANEL="#161b22"; CARD="#1d2430"; TEXT="#f0f3f6"; MUTED="#8b949e"; ACCENT="#2f81f7"; GOOD="#3fb950"; WARN="#d29922"
class JagXChat:
    def __init__(self,agent:JagXAgent):
        self.agent=agent; self.voice=VoicePipeline(wake_word="jagx",stt_model_size="base",tts_voice="en-US-AriaNeural",language="en"); self.root=tk.Tk(); self.root.title("JagX — Windows Command Center"); self.root.geometry("1400x900"); self.root.minsize(1050,700); self._busy=False; self._build(); self._first_run(); self._refresh_dashboard(); self._start_idle_monitor()
    def _button(self,parent,text,command,width=None): return tk.Button(parent,text=text,command=command,anchor="w",relief="flat",bd=0,bg=CARD,fg=TEXT,activebackground="#273142",activeforeground=TEXT,font=("Segoe UI",10),padx=12,pady=8,width=width)
    def _build(self):
        self.root.configure(bg=BG); top=tk.Frame(self.root,bg=PANEL,height=70); top.pack(fill="x"); tk.Label(top,text="🐆 JagX",bg=PANEL,fg=TEXT,font=("Segoe UI",24,"bold")).pack(side="left",padx=20,pady=12); tk.Label(top,text="WINDOWS COMMAND CENTER",bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left"); self.ai_status=tk.Label(top,text="● AI: checking…",bg=PANEL,fg=WARN,font=("Segoe UI",10,"bold")); self.ai_status.pack(side="right",padx=18); self.status=tk.Label(top,text="● Ready",bg=PANEL,fg=GOOD,font=("Segoe UI",10,"bold")); self.status.pack(side="right",padx=8)
        body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True); nav=tk.Frame(body,bg=PANEL,width=220); nav.pack(side="left",fill="y",padx=(10,6),pady=10); nav.pack_propagate(False); tk.Label(nav,text="COMMAND CENTER",bg=PANEL,fg=MUTED,font=("Segoe UI",9,"bold")).pack(anchor="w",padx=14,pady=(15,8))
        for label,prompt in [("⌂  Assistant","What can you help me do on Windows?"),("⚡  Action Center","Show me useful actions I can perform right now."),("📁  Files & Apps","Show me how to manage my files and applications."),("🌐  Browser","Help me control the browser."),("💻  Coding","Help me code, test, debug, or build a project."),("🖼  Image Studio","Create an image for me."),("🧠  Memory","Show me and manage what you remember about me."),("📸  Screenshots","Take a screenshot and understand what is on my screen.")]: self._button(nav,label,lambda p=prompt:self.quick(p)).pack(fill="x",padx=8,pady=2)
        tk.Frame(nav,bg=PANEL).pack(fill="both",expand=True); self._button(nav,"🔄  Refresh dashboard",self._refresh_dashboard).pack(fill="x",padx=8,pady=5); self._button(nav,"🎙  Voice assistant",self.listen).pack(fill="x",padx=8,pady=5); tk.Label(nav,text="Power actions and automatic idle power-down are opt-in and confirmation-gated.",wraplength=185,justify="left",bg=PANEL,fg=MUTED,font=("Segoe UI",8)).pack(padx=14,pady=14)
        content=tk.Frame(body,bg=BG); content.pack(side="left",fill="both",expand=True,padx=(0,10),pady=10); cards=tk.Frame(content,bg=BG); cards.pack(fill="x"); self.cpu_card=self._card(cards,"CPU","—",0); self.ram_card=self._card(cards,"MEMORY","—",1); self.disk_card=self._card(cards,"SYSTEM",platform.system(),2); self.model_card=self._card(cards,"AI MODEL","qwen2.5",3)
        lower=tk.Frame(content,bg=BG); lower.pack(fill="both",expand=True,pady=(10,0)); left=tk.Frame(lower,bg=BG); left.pack(side="left",fill="both",expand=True,padx=(0,5)); self._section(left,"RUNNING APPS","Refreshes with the dashboard"); self.apps=scrolledtext.ScrolledText(left,height=8,wrap=tk.WORD,bg=PANEL,fg=TEXT,relief="flat",font=("Consolas",9)); self.apps.pack(fill="x",pady=(0,8)); self._section(left,"RECENT / HOME FILES","Quick access"); self.files=scrolledtext.ScrolledText(left,height=8,wrap=tk.WORD,bg=PANEL,fg=TEXT,relief="flat",font=("Consolas",9)); self.files.pack(fill="both",expand=True)
        right=tk.Frame(lower,bg=BG,width=390); right.pack(side="left",fill="y",padx=(5,0)); right.pack_propagate(False); self._section(right,"ACTION CENTER","Ask JagX to perform a task"); actions=[("Open File Explorer","Open my file explorer."),("Open Browser","Open my web browser."),("Show Screenshot","Take a screenshot of my screen."),("Check Ollama","Check my local Ollama connection and model."),("Project Status","Inspect the current project and show its Git status."),("Remember Something","Help me save a preference to memory.")]; [self._button(right,"⚡ "+label,lambda p=prompt:self.quick(p)).pack(fill="x",pady=3) for label,prompt in actions]; self._section(right,"COMMAND / CHAT","Natural language works everywhere"); self.chat=scrolledtext.ScrolledText(right,wrap=tk.WORD,bg=PANEL,fg=TEXT,relief="flat",font=("Segoe UI",9),height=14); self.chat.pack(fill="both",expand=True)
        composer=tk.Frame(content,bg=PANEL); composer.pack(fill="x",pady=(10,0)); self.entry=tk.Entry(composer,bg=CARD,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Segoe UI",11)); self.entry.pack(side="left",fill="x",expand=True,padx=8,pady=8,ipady=8); self.entry.bind("<Return>",lambda _e:self.send()); tk.Button(composer,text="🎙",command=self.listen,bg=CARD,fg=TEXT,relief="flat",width=4,font=("Segoe UI",12)).pack(side="left"); tk.Button(composer,text="Send",command=self.send,bg=ACCENT,fg="white",relief="flat",width=8,pady=8,font=("Segoe UI",10,"bold")).pack(side="left",padx=8)
    def _card(self,parent,title,value,column):
        card=tk.Frame(parent,bg=PANEL,height=90); card.grid(row=0,column=column,sticky="nsew",padx=4); parent.grid_columnconfigure(column,weight=1); tk.Label(card,text=title,bg=PANEL,fg=MUTED,font=("Segoe UI",8,"bold")).pack(anchor="w",padx=14,pady=(12,2)); label=tk.Label(card,text=value,bg=PANEL,fg=TEXT,font=("Segoe UI",16,"bold")); label.pack(anchor="w",padx=14); return label
    def _section(self,parent,title,subtitle):
        row=tk.Frame(parent,bg=BG); row.pack(fill="x",pady=(0,5)); tk.Label(row,text=title,bg=BG,fg=TEXT,font=("Segoe UI",10,"bold")).pack(side="left"); tk.Label(row,text=subtitle,bg=BG,fg=MUTED,font=("Segoe UI",8)).pack(side="right")
    def _first_run(self):
        marker=Path(self.agent.config.get("memory",{}).get("path","./data/memory"))/".first_run_done"
        if not marker.exists():
            intro="I’m JagX, your personal assistant created by JagX and JRILICENSE to make work easier for you. You can talk to me or type to me."; self._append("JagX",intro); threading.Thread(target=self.voice.speak,args=(intro,),daemon=True).start(); marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text("done",encoding="utf-8")
        else:self._append("JagX","Welcome back. Your Windows command center is ready.")
    def _append(self,who,text): self.chat.configure(state="normal"); self.chat.insert(tk.END,f"{who}: {text}\n\n"); self.chat.configure(state="disabled"); self.chat.see(tk.END)
    def _set_status(self,text,busy=False): self.root.after(0,lambda:self.status.configure(text="● "+text,fg=WARN if busy else GOOD))
    def quick(self,text): self.entry.delete(0,tk.END); self.entry.insert(0,text); self.send()
    def send(self):
        text=self.entry.get().strip()
        if not text or self._busy:return
        self.entry.delete(0,tk.END); self._append("You",text); self._busy=True; self._set_status("Thinking…",True); threading.Thread(target=self._think,args=(text,),daemon=True).start()
    def _think(self,text):
        try: response=self.agent.think(text)
        except Exception as exc: response=f"Sorry, something went wrong: {exc}"
        self.root.after(0,lambda:self._append("JagX",response)); self._busy=False; self._set_status("Ready"); threading.Thread(target=self.voice.speak,args=(response,),daemon=True).start()
    def listen(self):
        if self._busy:return
        self._set_status("Listening…",True); threading.Thread(target=self._listen_worker,daemon=True).start()
    def _listen_worker(self):
        try:text=self.voice.listen_once()
        except Exception:text=""
        if not text:self.root.after(0,lambda:self._append("JagX","I didn't catch that. Please type your request.")); self._set_status("Type your request"); self.root.after(0,self.entry.focus_set); return
        self.root.after(0,lambda:(self.entry.delete(0,tk.END),self.entry.insert(0,text),self.send()))
    def _refresh_dashboard(self):
        def worker():
            cpu=ram="Unavailable"
            try:
                import psutil; cpu=f"{psutil.cpu_percent(interval=.4):.0f}%"; ram=f"{psutil.virtual_memory().percent:.0f}%"; processes=sorted(psutil.process_iter(["name","memory_percent"]),key=lambda p:p.info.get("memory_percent") or 0,reverse=True)[:10]; app_text="\n".join(f"{p.info.get('name','?')}  •  {p.info.get('memory_percent',0):.1f}% RAM" for p in processes)
            except Exception as exc:app_text=f"Unable to read process list: {exc}"
            try: items=list(Path.home().iterdir())[:30]; file_text="\n".join(("📁 " if p.is_dir() else "📄 ")+p.name for p in items)
            except Exception as exc:file_text=f"Unable to read home folder: {exc}"
            self.root.after(0,lambda:self.cpu_card.configure(text=cpu)); self.root.after(0,lambda:self.ram_card.configure(text=ram)); self.root.after(0,lambda:self.apps_replace(app_text)); self.root.after(0,lambda:self.files_replace(file_text)); self.root.after(0,self._refresh_ai_status)
        threading.Thread(target=worker,daemon=True).start()
    def apps_replace(self,text): self.apps.delete("1.0",tk.END); self.apps.insert(tk.END,text)
    def files_replace(self,text): self.files.delete("1.0",tk.END); self.files.insert(tk.END,text)
    def _refresh_ai_status(self):
        try:
            model=getattr(getattr(self.agent,"llm",None),"model","qwen2.5"); self.model_card.configure(text=str(model)); self.ai_status.configure(text=f"● AI: {model}",fg=GOOD)
        except Exception:self.ai_status.configure(text="● AI: local model status unavailable",fg=WARN)
    def _start_idle_monitor(self):
        policy=self.agent.config.get("idle_power",{})
        if not policy.get("enabled",False): return
        self._idle_check()
    def _idle_check(self):
        policy=self.agent.config.get("idle_power",{})
        if not policy.get("enabled",False): return
        try:
            import ctypes
            class LI(ctypes.Structure): _fields_=[("cbSize",ctypes.c_uint),("dwTime",ctypes.c_uint)]
            li=LI(); li.cbSize=ctypes.sizeof(LI); ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li)); idle=(ctypes.windll.kernel32.GetTickCount()-li.dwTime)/1000
            limit=int(policy.get("timeout_minutes",30))*60
            if idle>=limit and not self._busy:
                action=str(policy.get("action","sleep")).lower(); self._append("JagX",f"Idle timeout reached. Starting configured power action: {action}.")
                fn={"sleep":sleep_windows,"hibernate":hibernate_windows,"shutdown":shutdown_windows}.get(action)
                if fn: fn()
                return
        except Exception: pass
        self.root.after(15000,self._idle_check)
    def run(self): self.entry.focus_set(); self.root.mainloop()
def launch_chat(agent:JagXAgent): JagXChat(agent).run()
