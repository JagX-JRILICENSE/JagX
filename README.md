# JagX 🐆

**JagX** — Your personal jaguar AI companion that lives on your laptop.

> "Call JagX... and it answers."

JagX is a local-first personal AI agent. It listens for its name, understands what you say, acts on your computer, searches the internet when needed, and speaks back.

**Branding**: JagX  
**License Tag**: JRILICENSE

---

## ⚠️ Critical Warning

JagX has powerful system privileges (files, shell, mouse, keyboard, uninstall, camera monitoring).  
Only run it on a machine you fully own and trust.

---

## Voice Pipeline (Fully Working)

1. JagX continuously listens through your microphone.
2. When you say **"JagX"**, it wakes up.
3. You speak your command.
4. It transcribes your speech (local Whisper).
5. The agent understands and executes (tools, internet, system control...).
6. It speaks the answer back to you.

You can also run pure text mode if you prefer.

---

## Quick Start

```bash
# 1. Install Ollama + a model
ollama pull llama3.1

# 2. Install dependencies
git clone https://github.com/JagX-JRILICENSE/JagX.git
cd JagX
pip install -r requirements.txt

# 3. Run in Voice mode (default)
python main.py

# Or text-only mode
python main.py --mode text
```

**First run tips**
- Allow microphone access when your OS asks.
- Speak clearly after saying "JagX".
- For better accuracy change `stt_model` to `small` or `medium` in `config/settings.yaml` (slower but smarter).

---

## What JagX Can Do Right Now

| Feature                    | Status     |
|---------------------------|------------|
| Continuous voice listening | ✅ Working |
| Wake word "JagX"           | ✅ Working |
| Speech-to-Text (local)     | ✅ Working |
| Text-to-Speech             | ✅ Working |
| Local LLM + tool calling   | ✅ Working |
| Internet search            | ✅ Working |
| File read/write/delete     | ✅ Working |
| App uninstall              | ✅ Working |
| Mouse & keyboard control   | ✅ Working |
| Camera / mic privacy scan  | ✅ Working |
| Personal memory            | ✅ Working |
| Smart safety (high-risk only) | ✅ Working |

---

## Example Voice Commands

- "JagX, what's the weather in Lagos?"
- "JagX, list the files on my Desktop"
- "JagX, delete the folder called old-stuff"
- "JagX, check if anything is using my camera"
- "JagX, open notepad and type hello"
- "JagX, remember that I like short answers"

---

## Requirements

- Python 3.11+
- Working microphone + speakers
- Ollama running locally (recommended)
- `pip install -r requirements.txt`

---

## License

**JRILICENSE**  
Personal use only. All rights reserved to JagX-JRILICENSE.

---

**JagX**  
*Always watching. Always ready.*

JRILICENSE
