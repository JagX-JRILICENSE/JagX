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
- Network / internet access (when laptop or hotspot is connected)

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
- Search the internet and gather information when needed
- Answer questions while having full context of your machine
- Stay running in the background like a living presence

It is trained/fine-tuned primarily for **you** (personal data, preferences, workflows).

---

## Current Capabilities (Working Now)

- Local LLM via **Ollama** (or any OpenAI-compatible API)
- Full **tool-calling agent** loop
- **Internet tools**: `web_search` + `fetch_url` (works whenever your laptop/hotspot has internet)
- **Local system tools**:
  - List directories
  - Read / write files
  - Run shell commands
  - Get system info
- Interactive text chat interface

---

## Quick Start

1. Install [Ollama](https://ollama.com) and pull a model:
   ```bash
   ollama pull llama3.1
   # or mistral, qwen2.5, phi3, etc.
   ```

2. Clone & install:
   ```bash
   git clone https://github.com/JagX-JRILICENSE/JagX.git
   cd JagX
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python main.py
   ```

JagX will start. You can ask it to search the web, list your files, run commands, etc.

---

## Architecture

```
JagX/
├── core/
│   ├── agent.py          # Full tool-calling agent loop
│   ├── llm.py            # Ollama + OpenAI-compatible client
│   └── tools/
│       ├── web.py         # Internet search & page fetch
│       └── system.py      # Filesystem + shell access
├── voice/               # (coming next)
├── config/
│   └── settings.yaml
├── requirements.txt
└── main.py
```

---

## Roadmap

1. [x] Create repository & branding
2. [x] Basic project structure
3. [x] Local LLM connection (Ollama) + tool calling
4. [x] Core tools (files, shell) + Internet tools
5. [ ] Voice pipeline (wake word → STT → Agent → TTS)
6. [ ] Confirmation / safety modes
7. [ ] Mouse & keyboard control
8. [ ] Personal memory system
9. [ ] System tray + always-on mode
10. [ ] Installer / one-click setup
11. [ ] Fine-tuning path for personal data

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
