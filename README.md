# JagX 🐆

**JagX** — Your personal jaguar AI companion that lives on your laptop.

> Say **"JagX"** and it answers.

Local-first • Voice controlled • Full system access • Internet enabled • Privacy conscious

**License**: JRILICENSE

---

## ⚠️ Warning

JagX can control your mouse, keyboard, files, install/uninstall apps, and run commands.  
Only install it on a computer you fully own and trust.

---

## Features

- Continuous voice listening + wake word **"JagX"**
- Local speech recognition (Whisper) + high-quality TTS
- Local LLM (Ollama) with full tool calling
- Internet search & page reading (when online / hotspot on)
- File management (list, read, write, **easy delete**)
- App uninstall
- Mouse + keyboard control
- Clipboard, notifications, open websites & apps
- Camera / microphone privacy scanner
- Personal memory that remembers you
- Smart safety (only asks confirmation for high-risk/hacking actions)
- System tray icon — runs quietly in the background

---

## Quick Start (Developer Mode)

```bash
git clone https://github.com/JagX-JRILICENSE/JagX.git
cd JagX
pip install -r requirements.txt

# Make sure Ollama is installed and a model is pulled
ollama pull llama3.1

# Run (tray mode is default — best experience)
python main.py

# Other modes
python main.py --mode voice
python main.py --mode text
```

---

## Build the Windows App (Recommended)

This creates a real Windows executable you can run without Python.

### Steps

1. Make sure you have **Python 3.11+** installed and added to PATH.
2. Open Command Prompt or PowerShell **in the JagX folder**.
3. Double-click or run:

```bat
build_windows.bat
```

4. Wait 3–8 minutes. When it finishes you will see:

```
dist\JagX\JagX.exe
```

5. You can now:
   - Double-click `JagX.exe` to run
   - Copy the whole `dist\JagX` folder anywhere
   - Create a desktop shortcut to `JagX.exe`
   - (Optional) Right-click → Pin to Start / Taskbar

---

## What To Do After Installing / First Run

1. **Allow Microphone**  
   Windows will ask for microphone permission → click Allow.

2. **Start Ollama** (if you want the smart local brain)  
   Make sure Ollama is running in the background (`ollama serve` or just open the Ollama app).

3. **Look for the orange icon** in the system tray (bottom-right near the clock).

4. **Right-click the icon** for the menu:
   - Toggle Voice
   - Quit JagX

5. **Talk to it**:
   - Say clearly: **"JagX"**
   - Wait for the short reply ("Yes?")
   - Then give your command

### Good first commands to try

- "JagX, what can you do?"
- "JagX, check if anything is using my camera"
- "JagX, list files on my Desktop"
- "JagX, open Notepad"
- "JagX, search the web for latest AI news"
- "JagX, remember that my name is [Your Name]"

---

## Recommended Settings After Install

Edit `config/settings.yaml` (inside the app folder) if you want:

```yaml
voice:
  stt_model: "small"     # better accuracy than "base"
  tts_voice: "en-US-AriaNeural"

llm:
  model: "llama3.1"      # or qwen2.5, mistral, phi3, etc.
```

Bigger Whisper models (`small` / `medium`) understand speech much better but use more RAM.

---

## Auto-start with Windows (Optional)

1. Press `Win + R` → type `shell:startup` → Enter
2. Create a shortcut to `JagX.exe` inside that folder
3. JagX will now start automatically when you log in

---

## Project Structure

```
JagX/
├── main.py              # Entry point (tray mode default)
├── build_windows.bat    # One-click Windows build
├── core/                # Agent + LLM + tools
├── voice/               # Full voice pipeline
├── ui/                  # System tray
├── config/settings.yaml
└── requirements.txt
```

---

## License

**JRILICENSE**  
Personal use only. All rights reserved to the owner.

---

**JagX**  
*Always watching. Always ready.*

JRILICENSE
