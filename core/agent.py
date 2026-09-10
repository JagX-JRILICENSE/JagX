"""JagX Agent - reliable action execution for typed and voice commands."""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

import yaml
from rich.console import Console
from rich.markdown import Markdown

from core.llm import create_llm_from_config
from core.memory import Memory
from core.tools.web import WEB_TOOLS, TOOL_FUNCTIONS as WEB_FUNCS
from core.tools.system import SYSTEM_TOOLS, TOOL_FUNCTIONS as SYSTEM_FUNCS
from core.tools.desktop import DESKTOP_TOOLS, TOOL_FUNCTIONS as DESKTOP_FUNCS
from core.tools.privacy import PRIVACY_TOOLS, TOOL_FUNCTIONS as PRIVACY_FUNCS
from core.tools.extra import EXTRA_TOOLS, TOOL_FUNCTIONS as EXTRA_FUNCS

try:
    from core.tools.credentials import CREDENTIAL_TOOLS, TOOL_FUNCTIONS as CREDENTIAL_FUNCS
except Exception:
    CREDENTIAL_TOOLS, CREDENTIAL_FUNCS = [], {}
try:
    from core.tools.media import MEDIA_TOOLS, TOOL_FUNCTIONS as MEDIA_FUNCS
except Exception:
    MEDIA_TOOLS, MEDIA_FUNCS = [], {}
try:
    from core.tools.productivity import PRODUCTIVITY_TOOLS, TOOL_FUNCTIONS as PRODUCTIVITY_FUNCS
except Exception:
    PRODUCTIVITY_TOOLS, PRODUCTIVITY_FUNCS = [], {}
try:
    from core.tools.browser import BROWSER_TOOLS, TOOL_FUNCTIONS as BROWSER_FUNCS
except Exception:
    BROWSER_TOOLS, BROWSER_FUNCS = [], {}
try:
    from core.tools.screen import SCREEN_TOOLS, TOOL_FUNCTIONS as SCREEN_FUNCS
except Exception:
    SCREEN_TOOLS, SCREEN_FUNCS = [], {}
try:
    from core.tools.system_plus import SYSTEM_PLUS_TOOLS, TOOL_FUNCTIONS as SYSTEM_PLUS_FUNCS
except Exception:
    SYSTEM_PLUS_TOOLS, SYSTEM_PLUS_FUNCS = [], {}
try:
    from core.tools.system_plus2 import SYSTEM_PLUS2_TOOLS, TOOL_FUNCTIONS as SYSTEM_PLUS2_FUNCS
except Exception:
    SYSTEM_PLUS2_TOOLS, SYSTEM_PLUS2_FUNCS = [], {}
try:
    from core.tools.power import POWER_TOOL_DEFINITIONS, TOOL_FUNCTIONS as POWER_FUNCS
except Exception:
    POWER_TOOL_DEFINITIONS, POWER_FUNCS = [], {}

console = Console()

HIGH_RISK_PATTERNS = [
    r"hack", r"exploit", r"payload", r"metasploit", r"nmap", r"sqlmap",
    r"keylog", r"rat\b", r"backdoor", r"rootkit", r"reverse.?shell",
    r"mimikatz", r"credential.?dump", r"password.?crack",
    r"ddos", r"botnet", r"ransomware",
    r"format\s+c:", r"rm\s+-rf\s+/", r"mkfs", r"dd\s+if=",
]

DESTRUCTIVE_TOOLS = {
    "delete_path", "uninstall_app", "run_shell",
    "shutdown_windows", "restart_windows", "empty_recycle_bin",
    "block_camera_access", "kill_process_by_name",
    "save_credential", "get_credential", "delete_credential",
}

# Banking / money-move intents — never automate PIN entry or transfers
BANKING_BLOCK_PATTERNS = [
    r"\btransfer money\b", r"\bsend money\b", r"\bbank transfer\b",
    r"\bwire transfer\b", r"\benter (my )?pin\b", r"\baccount (number|no)\b",
    r"\brouting number\b", r"\botp\b", r"\b2fa code\b",
]


class JagXAgent:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.llm = create_llm_from_config(self.config)
        self.memory = Memory(self.config.get("memory", {}).get("path", "./data/memory"))
        self.messages: List[Dict[str, Any]] = []
        self.running = False
        self.gui_mode = False
        self.on_tool_start: Optional[Callable[[str, dict], None]] = None
        self.on_tool_end: Optional[Callable[[str, str], None]] = None
        self.confirm_callback: Optional[Callable[[str], bool]] = None

        context = self.memory.get_context_summary()
        if context and context != "No long-term memory yet.":
            self.llm.system_prompt += f"\n\n### Personal Memory\n{context}"

        self.llm.system_prompt += """

### CRITICAL ACTION RULES
When the user asks you to DO something on the computer, call tools immediately.
Use desktop tools for mouse/keyboard, system tools for files/apps, browser tools for websites.

### PASSWORDS (allowed for personal accounts)
- You may save website/app passwords using save_credential_interactive (hidden local input).
- You may check has_credential and help log into the user's OWN social accounts (X, Facebook, etc.).
- NEVER print, quote, or remember the actual password text in chat.
- Prefer opening the site and letting the user confirm before filling credentials.

### HARD LIMITS (must refuse)
- Do NOT store bank PINs, OTP codes, or card CVV.
- Do NOT automate money transfers or enter banking PINs for the user.
- For banking: open the bank site / app and ask the user to enter PIN themselves.
- Do NOT help hack, steal accounts, or access accounts that are not the user's.

### SOCIAL / WHATSAPP
- You may open X, Facebook, WhatsApp Web/Desktop and help the user post, like, or reply
  using UI control tools, with confirmation before posting.
"""

        self.tool_functions = {
            **WEB_FUNCS, **SYSTEM_FUNCS, **DESKTOP_FUNCS, **PRIVACY_FUNCS, **EXTRA_FUNCS,
            **CREDENTIAL_FUNCS, **MEDIA_FUNCS, **PRODUCTIVITY_FUNCS, **BROWSER_FUNCS,
            **SCREEN_FUNCS, **SYSTEM_PLUS_FUNCS, **SYSTEM_PLUS2_FUNCS, **POWER_FUNCS,
        }
        self.tool_definitions = (
            WEB_TOOLS + SYSTEM_TOOLS + DESKTOP_TOOLS + PRIVACY_TOOLS + EXTRA_TOOLS +
            CREDENTIAL_TOOLS + MEDIA_TOOLS + PRODUCTIVITY_TOOLS + BROWSER_TOOLS +
            SCREEN_TOOLS + SYSTEM_PLUS_TOOLS + SYSTEM_PLUS2_TOOLS + POWER_TOOL_DEFINITIONS
        )

        console.print(f"[bold orange1]JagX ready[/bold orange1] — {len(self.tool_definitions)} tools — model: {self.llm.model}")

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _is_banking_request(self, text: str) -> bool:
        low = (text or "").lower()
        return any(re.search(p, low, re.I) for p in BANKING_BLOCK_PATTERNS)

    def _is_high_risk(self, name: str, arguments: Dict[str, Any]) -> bool:
        if name in DESTRUCTIVE_TOOLS:
            if name == "run_shell":
                cmd = str(arguments.get("command", "")).lower()
                safe_prefixes = ("start ", "explorer", "notepad", "calc", "mspaint", "dir", "cd ", "type ", "echo ")
                if any(cmd.strip().startswith(p) for p in safe_prefixes):
                    return False
            return True
        blob = (name + " " + json.dumps(arguments)).lower()
        return any(re.search(p, blob, re.I) for p in HIGH_RISK_PATTERNS)

    def _ask_confirm(self, message: str) -> bool:
        if self.confirm_callback:
            try:
                return bool(self.confirm_callback(message))
            except Exception:
                return False
        if self.gui_mode:
            return True
        try:
            from rich.prompt import Confirm
            return Confirm.ask(message, default=False)
        except Exception:
            return False

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        func = self.tool_functions.get(name)
        if not func:
            return f"Unknown tool: {name}"

        # Never allow credential tools to target banking labels
        if name in {"save_credential", "save_credential_interactive", "get_credential"}:
            account = str(arguments.get("account", "")).lower()
            if any(w in account for w in ("bank", "pin", "otp", "cvv", "card", "wallet", "transfer")):
                return "Refused: JagX will not store or auto-fill banking PINs, OTPs, or card secrets. Open the bank site and enter those yourself."

        if self._is_high_risk(name, arguments):
            console.print(f"[yellow]Confirm:[/yellow] {name}")
            if not self._ask_confirm(f"Allow sensitive action {name}?"):
                return "Action cancelled by user."

        if self.on_tool_start:
            try:
                self.on_tool_start(name, arguments)
            except Exception:
                pass

        # Never log raw passwords
        safe_args = dict(arguments)
        for k in list(safe_args):
            if any(s in k.lower() for s in ("password", "secret", "token", "pin")):
                safe_args[k] = "[hidden]"
        console.print(f"[cyan]→ {name}[/cyan] {safe_args}")

        try:
            result = str(func(**arguments))
        except TypeError as e:
            result = f"Tool argument error: {e}"
        except Exception as e:
            result = f"Tool execution error: {e}"

        # Sanitize credential tool results before model sees them
        if name in {"get_credential", "request_password", "save_credential"}:
            if result.startswith("SECURE_CREDENTIAL:"):
                result = "CREDENTIAL_AVAILABLE_LOCALLY (secret not shown to chat)"
            elif name == "request_password" and not result.startswith("PASSWORD_INPUT_"):
                result = "PASSWORD_RECEIVED_LOCALLY (secret not shown to chat)"

        if self.on_tool_end:
            try:
                self.on_tool_end(name, result)
            except Exception:
                pass
        return result

    def think(self, user_input: str) -> str:
        user_input = (user_input or "").strip()
        if not user_input:
            return "Tell me what you want me to do."

        # Hard stop for automated banking transfers / PIN handling
        if self._is_banking_request(user_input):
            return (
                "I can open your bank website or app for you, but I will **not** store your PIN "
                "or automatically transfer money. That is too dangerous if anything goes wrong.\n\n"
                "What I can do:\n"
                "1. Open your bank site/app\n"
                "2. Wait while you enter PIN yourself\n"
                "3. Help navigate screens after you are logged in\n\n"
                "For social logins (X, Facebook) and normal website passwords, I can save them securely "
                "and help you sign in."
            )

        self.messages.append({"role": "user", "content": user_input})
        if len(self.messages) > 40:
            self.messages = self.messages[-30:]

        for _ in range(12):
            response = self.llm.chat(
                messages=self.messages,
                tools=self.tool_definitions,
                tool_choice="auto",
            )

            tool_calls = response.get("tool_calls")
            if tool_calls:
                self.messages.append(response)
                for call in tool_calls:
                    fn = call.get("function") or {}
                    name = fn.get("name") or ""
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result = self._execute_tool(name, args)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", name),
                        "name": name,
                        "content": result,
                    })
                continue

            content = (response.get("content") or "").strip()
            self.messages.append({"role": "assistant", "content": content})

            low = user_input.lower()
            if any(w in low for w in ("remember", "my name is", "i like", "i prefer", "note that")):
                try:
                    self.memory.add_note(user_input)
                except Exception:
                    pass
            return content or "Done."

        return "I hit the tool-round limit. Try a shorter command."

    def run(self):
        self.running = True
        console.print("[green]JagX text mode. Type a command and press Enter.[/green]")
        while self.running:
            try:
                text = input("[You] > ").strip()
                if not text:
                    continue
                if text.lower() in {"exit", "quit", "stop", "sleep"}:
                    break
                reply = self.think(text)
                console.print("[bold orange1]JagX:[/bold orange1]")
                console.print(Markdown(reply))
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
        self.running = False
