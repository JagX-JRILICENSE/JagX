# JagX 🐆

**JagX** — Your personal jaguar AI companion that lives on your laptop.

> Say **"JagX"** and it answers.

**GitHub Repository:** https://github.com/JagX-JRILICENSE/JagX

Local-first • Voice controlled • Full system access • Internet enabled • Privacy conscious

**License**: JRILICENSE

---

## ⚠️ Warning

JagX can control your mouse, keyboard, files, install/uninstall apps, and run commands.  
Only install it on a computer you fully own and trust.

---

## Features

- Continuous voice listening + wake word **"JagX"**
- Local speech recognition + high-quality voice replies
- Local LLM (Ollama) with full tool calling
- Internet search (works when laptop/hotspot is online)
- Easy file delete & app uninstall
- Mouse + keyboard control
- Clipboard, notifications, open websites & apps
- Camera / microphone privacy scanner
- Personal memory
- Smart safety (only confirms high-risk actions)
- System tray icon (runs in background)
- Professional Windows installer

---

## Repository Link

**https://github.com/JagX-JRILICENSE/JagX**

---

## Option A — Build the Full Windows Installer (Recommended)

### Requirements
- Windows 10/11
- Python 3.11+
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (free)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/JagX-JRILICENSE/JagX.git
   cd JagX
   ```

2. Double-click **`build_installer.bat`**

   This will:
   - Create the standalone app
   - Generate a professional installer: `dist_installer\JagX_Setup.exe`

3. Run `JagX_Setup.exe` to install JagX like any normal Windows program.

---

## Option B — Quick Executable Only

```bat
build_windows.bat
```

Then run `dist\JagX\JagX.exe`

---

## What To Do After Installing

1. **Allow Microphone** when Windows asks.
2. Install and start **Ollama** → `ollama pull llama3.1`
3. Look for the **orange icon** in the system tray (near the clock).
4. Right-click the icon for menu options.
5. Say clearly:

   > **"JagX"**

   Then give your command.

### Great first commands

- "JagX, what can you do?"
- "JagX, check if anything is using my camera"
- "JagX, list files on my Desktop"
- "JagX, open Notepad"
- "JagX, search the web for AI news"
- "JagX, remember that my name is ..."

---

## Developer Mode (no build needed)

```bash
git clone https://github.com/JagX-JRILICENSE/JagX.git
cd JagX
pip install -r requirements.txt
ollama pull llama3.1
python main.py
```

---

## Project Structure

```
JagX/
├── main.py
├── build_windows.bat          # Creates the .exe
├── build_installer.bat        # Creates the full Setup.exe
├── installer/JagX.iss         # Inno Setup script
├── core/                      # Agent, LLM, tools
├── voice/                     # Full voice pipeline
├── ui/                        # System tray
├── config/settings.yaml
└── requirements.txt
```

---

## License

**JRILICENSE**  
Personal use only. All rights reserved.

---

**JagX**  
*Always watching. Always ready.*

JRILICENSE
