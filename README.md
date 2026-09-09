# JagX 🐆

**JagX** — Your personal jaguar AI companion that lives on your laptop.

> "Call JagX... and it answers."

JagX is a local-first personal AI agent designed for **you**.  
It runs on your machine, has deep system access, listens for its name, speaks back, and can control your computer like a highly capable assistant (or a loyal jaguar).

**Branding**: JagX  
**License Tag**: JRILICENSE

---

## ⚠️ Critical Warning

JagX is designed with **full system privileges** in mind:

- File system access (read/write/delete)
- Mouse & keyboard control
- Application launching & control
- Shell command execution
- System updates & package management
- Network access

**This is extremely powerful and dangerous.**

- Only run it on a machine you fully control and trust.
- Never grant it access on shared/work computers without extreme caution.
- Always review actions in the early stages (confirmation mode recommended).
- You are solely responsible for anything JagX does on your device.

Use at your own risk.

---

## Vision

When you say **"JagX"**, it wakes up, greets you in voice, and starts executing your requests:

- Open any file or folder
- Control the cursor and type for you
- Install / update software
- Manage your projects
- Automate repetitive tasks
- Answer questions while having full context of your machine
- Stay running in the background like a living presence

It is trained/fine-tuned primarily for **you** (personal data, preferences, workflows).

---

## Architecture (Planned)

```
JagX/
├── core/
│   ├── agent.py          # Main agent loop + tool calling
│   ├── llm.py            # Local / remote LLM interface
│   ├── memory.py         # Personal memory & context
│   └── tools/            # System tools
│       ├── filesystem.py
│       ├── mouse_keyboard.py
│       ├── shell.py
│       ├── apps.py
│       └── system.py
├── voice/
│   ├── wakeword.py       # "JagX" detection
│   ├── stt.py            # Speech-to-Text
│   └── tts.py            # Text-to-Speech
├── ui/
│   └── tray.py           # System tray presence
├── config/
│   └── settings.yaml
├── data/               # Personal memory, logs, models
├── requirements.txt
└── main.py             # Entry point
```

---

## Tech Stack (Recommended)

- **Language**: Python 3.11+
- **LLM**: Ollama (local) + optional cloud fallback (Grok, Claude, GPT, etc.)
- **Voice**:
  - Wake word: openWakeWord or Porcupine
  - STT: Whisper (local) or faster-whisper
  - TTS: Piper, Coqui, or edge-tts
- **System Control**:
  - `pyautogui` / `pynput` (mouse + keyboard)
  - `subprocess` + `psutil`
  - Platform-specific tools (AppleScript / PowerShell / xdotool)
- **Agent Framework**: Custom or LangGraph / Open Interpreter style
- **Background**: System tray + systemd / launchd / Windows service

---

## Current Status

🚧 **Scaffolding phase**  
Repository just created. Core structure and first working prototype coming next.

---

## Roadmap

1. [x] Create repository & branding
2. [ ] Basic project structure
3. [ ] Local LLM connection (Ollama)
4. [ ] Core tools (files, shell, mouse)
5. [ ] Voice pipeline (wake word → STT → Agent → TTS)
6. [ ] Confirmation / safety modes
7. [ ] Personal memory system
8. [ ] System tray + always-on mode
9. [ ] Installer / one-click setup
10. [ ] Fine-tuning path for personal data

---

## License

**JRILICENSE**  
Custom personal license. All rights reserved to the owner (JagX-JRILICENSE).

This software is intended for personal use by the repository owner.  
Redistribution, commercial use, or public deployment without explicit permission is not allowed.

---

**JagX**  
*Always watching. Always ready.*

JRILICENSE
