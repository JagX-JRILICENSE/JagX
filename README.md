# JagX 🐆

**JagX** — Your personal jaguar AI companion that lives on your laptop.

> "Call JagX... and it answers."

JagX is a local-first personal AI agent designed for **you**.  
It runs on your machine, has deep system access, can search the internet, control your desktop, protect your privacy, and remember you.

**Branding**: JagX  
**License Tag**: JRILICENSE

---

## ⚠️ Critical Warning

JagX has powerful system privileges:

- Full file system access (read / write / **delete**)
- Shell command execution
- Mouse & keyboard control
- Application uninstall
- Camera / microphone monitoring and blocking attempts
- Internet access (when your laptop or hotspot is online)

**Only run this on a machine you fully own and trust.**

---

## Current Capabilities

### Core Intelligence
- Local LLM via Ollama (or any OpenAI-compatible API)
- Full multi-step tool-calling agent

### Internet
- Web search
- Fetch any webpage content  
(Works automatically when your laptop/hotspot has internet)

### Local System Control
- List / read / write files
- **Easy delete** of files and folders (`delete_path`)
- **Easy uninstall** of apps (`uninstall_app`)
- Run any shell command
- System information

### Desktop Control
- Move mouse, click, type text, press keys
- Take screenshots

### Privacy Guard
- Detect processes using camera / microphone
- List audio/video devices
- Kill suspicious processes
- Attempt to block camera access

### Safety (Smart Confirmation)
- **Does NOT** ask for confirmation on normal actions
- **Only** asks when the action looks related to hacking tools or extremely destructive commands

### Memory
- Persistent personal memory (facts, preferences, notes)
- Automatically remembers things you tell it to remember

### Voice (Foundation)
- High-quality TTS (edge-tts)
- Local STT (faster-whisper)
- Full wake-word pipeline still in progress

---

## Quick Start

```bash
# 1. Install Ollama and a model
ollama pull llama3.1

# 2. Clone & install
git clone https://github.com/JagX-JRILICENSE/JagX.git
cd JagX
pip install -r requirements.txt

# 3. Run
python main.py
```

---

## Roadmap Status

1. [x] Create repository & branding
2. [x] Basic project structure
3. [x] Local LLM + tool calling
4. [x] Core tools (files, shell, internet)
5. [x] Easy delete + uninstall
6. [x] Mouse & keyboard control
7. [x] Privacy guard (camera/mic detection & block)
8. [x] Selective safety (only confirm high-risk/hacking actions)
9. [x] Personal memory system
10. [ ] Full voice pipeline (wake word "JagX" → listen → act → speak)
11. [ ] System tray + always-on mode
12. [ ] Installer

---

## License

**JRILICENSE**  
Custom personal license. All rights reserved to the owner (JagX-JRILICENSE).

---

**JagX**  
*Always watching. Always ready.*

JRILICENSE
