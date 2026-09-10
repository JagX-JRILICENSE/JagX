"""JagX Agent - reliable action execution with Little Brain offline fallback."""
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
try:
    from core.tools.power_features import POWER_FEATURE_TOOLS, TOOL_FUNCTIONS as POWER_FEATURE_FUNCS
except Exception:
    POWER_FEATURE_TOOLS, POWER_FEATURE_FUNCS = [], {}

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
    "block_camera_access", "kill_process_by_name", "kill_process",
    "save_credential", "get_credential", "delete_credential",
    "clean_temp_files",
}

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

        # Little Brain — always available offline fallback
        try:
            from core.little_brain import get_little_brain
            self.little = get_little_brain()
            self.little.ensure()
        except Exception:
            self.little = None

        try:
            from core.setup_ai import ensure_local_ai
            status = ensure_local_ai(
                base_url=getattr(self.llm, "base_url", "http://127.0.0.1:11434"),
                preferred_model=getattr(self.llm, "model", "qwen2.5:3b"),
                auto_pull=False,
                auto_install_ollama=False,
            )
            if status.get("ok") and status.get("model"):
                self.llm.model = status["model"]
                self.llm.available_models = status.get("available") or []
        except Exception:
            pass

        context = self.memory.get_context_summary()
        if context and context != "No long-term memory yet.":
            self.llm.system_prompt += f"\n\n### Personal Memory\n{context}"

        self.llm.system_prompt += """

### CRITICAL ACTION RULES
When the user asks you to DO something, CALL TOOLS immediately.
Prefer: open_app, screenshot_and_open, system_briefing, find_files, move_mouse, click, type_text.
No bank PIN storage or automated money transfers.
"""

        self.tool_functions = {
            **WEB_FUNCS, **SYSTEM_FUNCS, **DESKTOP_FUNCS, **PRIVACY_FUNCS, **EXTRA_FUNCS,
            **CREDENTIAL_FUNCS, **MEDIA_FUNCS, **PRODUCTIVITY_FUNCS, **BROWSER_FUNCS,
            **SCREEN_FUNCS, **SYSTEM_PLUS_FUNCS, **SYSTEM_PLUS2_FUNCS, **POWER_FUNCS,
            **POWER_FEATURE_FUNCS,
        }
        self.tool_definitions = (
            WEB_TOOLS + SYSTEM_TOOLS + DESKTOP_TOOLS + PRIVACY_TOOLS + EXTRA_TOOLS +
            CREDENTIAL_TOOLS + MEDIA_TOOLS + PRODUCTIVITY_TOOLS + BROWSER_TOOLS +
            SCREEN_TOOLS + SYSTEM_PLUS_TOOLS + SYSTEM_PLUS2_TOOLS + POWER_TOOL_DEFINITIONS +
            POWER_FEATURE_TOOLS
        )

        brain = getattr(self.little, "model_name", "rules") if self.little else "none"
        console.print(f"[bold orange1]JagX ready[/bold orange1] — tools:{len(self.tool_definitions)} model:{self.llm.model} little-brain:{brain}")

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

        if name in {"save_credential", "save_credential_interactive", "get_credential"}:
            account = str(arguments.get("account", "")).lower()
            if any(w in account for w in ("bank", "pin", "otp", "cvv", "card", "wallet", "transfer")):
                return "Refused: banking secrets are not stored or auto-filled."

        if self._is_high_risk(name, arguments):
            if not self._ask_confirm(f"Allow sensitive action {name}?"):
                return "Action cancelled by user."

        if self.on_tool_start:
            try:
                self.on_tool_start(name, arguments)
            except Exception:
                pass

        try:
            result = str(func(**arguments))
        except TypeError as e:
            result = f"Tool argument error: {e}"
        except Exception as e:
            result = f"Tool execution error: {e}"

        if name in {"get_credential", "request_password", "save_credential"}:
            if result.startswith("SECURE_CREDENTIAL:"):
                result = "CREDENTIAL_AVAILABLE_LOCALLY"
            elif name == "request_password" and not result.startswith("PASSWORD_INPUT_"):
                result = "PASSWORD_RECEIVED_LOCALLY"

        if self.on_tool_end:
            try:
                self.on_tool_end(name, result)
            except Exception:
                pass
        return result

    def _little_brain_act(self, user_input: str) -> str:
        if not self.little:
            return "Little Brain unavailable."
        resp = self.little.respond(user_input)
        calls = resp.get("tool_calls") or []
        parts = []
        for call in calls:
            fn = call.get("function") or call
            name = fn.get("name") or call.get("name") or ""
            raw = fn.get("arguments") or call.get("arguments") or {}
            if isinstance(raw, str):
                try:
                    args = json.loads(raw)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = raw or {}
            if name:
                parts.append(self._execute_tool(name, args))
        content = (resp.get("content") or "").strip()
        if parts:
            return (content + "\n" if content else "") + " | ".join(parts)
        return content or "Little Brain ready."

    def think(self, user_input: str) -> str:
        user_input = (user_input or "").strip()
        if not user_input:
            return "Tell me what you want me to do."

        if self._is_banking_request(user_input):
            return (
                "I can open your bank site/app, but I will not store your PIN or auto-transfer money. "
                "Enter the PIN yourself."
            )

        low = user_input.lower().strip()
        fast = {
            "open notepad": ("open_app", {"app_name": "notepad"}),
            "open calculator": ("open_app", {"app_name": "calculator"}),
            "open file explorer": ("open_app", {"app_name": "explorer"}),
            "open explorer": ("open_app", {"app_name": "explorer"}),
            "take a screenshot": ("screenshot_and_open", {}),
            "screenshot": ("screenshot_and_open", {}),
            "system briefing": ("system_briefing", {}),
            "organize downloads": ("organize_downloads", {}),
            "clean temp": ("clean_temp_files", {}),
            "mute": ("volume_mute_toggle", {}),
        }
        if low in fast:
            name, args = fast[low]
            return f"Done. {self._execute_tool(name, args)}"

        # Prefer main LLM; on failure use Little Brain
        self.messages.append({"role": "user", "content": user_input})
        if len(self.messages) > 40:
            self.messages = self.messages[-30:]

        try:
            for _ in range(10):
                response = self.llm.chat(
                    messages=self.messages,
                    tools=self.tool_definitions,
                    tool_choice="auto",
                )
                content_preview = (response.get("content") or "").lower()
                if any(x in content_preview for x in ("timed out", "cannot reach ollama", "no local model", "model error")):
                    return "Main AI unavailable — using Little Brain.\n" + self._little_brain_act(user_input)

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
                return content or "Done."
        except Exception as e:
            return f"Main AI error ({e}). Little Brain:\n" + self._little_brain_act(user_input)

        return self._little_brain_act(user_input)

    def run(self):
        self.running = True
        console.print("[green]JagX text mode.[/green]")
        while self.running:
            try:
                text = input("[You] > ").strip()
                if not text:
                    continue
                if text.lower() in {"exit", "quit", "stop", "sleep"}:
                    break
                console.print("[bold orange1]JagX:[/bold orange1]")
                console.print(Markdown(self.think(text)))
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
        self.running = False
