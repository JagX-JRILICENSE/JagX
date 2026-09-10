"""JagX Agent — autonomous on your PC; only hard-blocks money/hacking."""
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
try:
    from core.tools.social_web import SOCIAL_WEB_TOOLS, TOOL_FUNCTIONS as SOCIAL_WEB_FUNCS
except Exception:
    SOCIAL_WEB_TOOLS, SOCIAL_WEB_FUNCS = [], {}
try:
    from core.tools.cloud_dev import CLOUD_DEV_TOOLS, TOOL_FUNCTIONS as CLOUD_DEV_FUNCS
except Exception:
    CLOUD_DEV_TOOLS, CLOUD_DEV_FUNCS = [], {}
try:
    from core.tools.developer import DEVELOPER_TOOLS, TOOL_FUNCTIONS as DEVELOPER_FUNCS
except Exception:
    DEVELOPER_TOOLS, DEVELOPER_FUNCS = [], {}
try:
    from core.tools.mega_features import MEGA_TOOLS, TOOL_FUNCTIONS as MEGA_FUNCS
except Exception:
    MEGA_TOOLS, MEGA_FUNCS = [], {}
try:
    from core.tools.games import GAME_TOOLS, TOOL_FUNCTIONS as GAME_FUNCS
except Exception:
    GAME_TOOLS, GAME_FUNCS = [], {}
try:
    from core.tools.streaming import STREAMING_TOOLS, TOOL_FUNCTIONS as STREAMING_FUNCS
except Exception:
    STREAMING_TOOLS, STREAMING_FUNCS = [], {}
try:
    from core.tools.web_builder import WEB_BUILDER_TOOLS, TOOL_FUNCTIONS as WEB_BUILDER_FUNCS
except Exception:
    WEB_BUILDER_TOOLS, WEB_BUILDER_FUNCS = [], {}
try:
    from core.tools.image import IMAGE_TOOLS, TOOL_FUNCTIONS as IMAGE_FUNCS
except Exception:
    IMAGE_TOOLS, IMAGE_FUNCS = [], {}
try:
    from core.tools.vision_privacy import VISION_PRIVACY_TOOLS, TOOL_FUNCTIONS as VISION_PRIVACY_FUNCS
except Exception:
    VISION_PRIVACY_TOOLS, VISION_PRIVACY_FUNCS = [], {}
try:
    from core.tools.power40 import POWER40_TOOLS, TOOL_FUNCTIONS as POWER40_FUNCS
except Exception:
    POWER40_TOOLS, POWER40_FUNCS = [], {}
try:
    from core.tools.antivirus import ANTIVIRUS_TOOLS, TOOL_FUNCTIONS as ANTIVIRUS_FUNCS
except Exception:
    ANTIVIRUS_TOOLS, ANTIVIRUS_FUNCS = [], {}

console = Console()

HIGH_RISK_PATTERNS = [
    r"hack", r"exploit", r"payload", r"metasploit", r"nmap", r"sqlmap",
    r"keylog", r"rat\b", r"backdoor", r"rootkit", r"reverse.?shell",
    r"mimikatz", r"credential.?dump", r"password.?crack",
    r"ddos", r"botnet", r"ransomware",
    r"format\s+c:", r"rm\s+-rf\s+/", r"mkfs", r"dd\s+if=",
]

CONFIRM_TOOLS = {
    "delete_path", "uninstall_app",
    "shutdown_windows", "restart_windows", "empty_recycle_bin",
    "format_drive", "wipe_disk",
    "delete_quarantined_file", "quarantine_file", "remove_detected_threats",
}

SHOW_RESULT_TOOLS = {
    "vercel_deploy", "generate_image", "build_animated_website",
    "capture_webcam_photo", "describe_webcam",
}

MONEY_BLOCK_PATTERNS = [
    r"\btransfer money\b", r"\bsend money\b", r"\bbank transfer\b",
    r"\bwire transfer\b", r"\benter (my )?pin\b", r"\baccount (number|no)\b",
    r"\brouting number\b", r"\botp\b", r"\b2fa code\b",
    r"\bpay with (my )?card\b", r"\bbuy (a )?domain with (my )?card\b",
    r"\benter (my )?card\b", r"\bcvv\b", r"\bcard number\b",
    r"\bauto.?trade\b", r"\bplace (a )?trade\b", r"\bbuy stock\b",
    r"\bsell stock\b", r"\bforex\b.*\b(execute|place|order)\b",
]


def _select_tools(all_defs: List[dict], user_text: str, cap: int = 24) -> List[dict]:
    low = (user_text or "").lower()
    tokens = set(re.findall(r"[a-z0-9]+", low))
    scored = []
    for d in all_defs:
        fn = (d.get("function") or {})
        name = (fn.get("name") or "").lower()
        desc = (fn.get("description") or "").lower()
        blob = name + " " + desc
        score = sum(1 for t in tokens if t in blob and len(t) > 2)
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [d for s, d in scored if s > 0][:cap]
    core_names = {
        "open_app", "screenshot_and_open", "quick_virus_scan",
        "privacy_guard_scan", "system_briefing",
    }
    core = [d for d in all_defs if (d.get("function") or {}).get("name") in core_names]
    seen, out = set(), []
    for d in core + picked:
        n = (d.get("function") or {}).get("name")
        if n and n not in seen:
            seen.add(n)
            out.append(d)
    return out[:cap] if out else all_defs[:16]


class JagXAgent:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.llm = create_llm_from_config(self.config)
        self.memory = Memory(self.config.get("memory", {}).get("path", "./data/memory"))
        self.messages: List[Dict[str, Any]] = []
        self.running = False
        self.gui_mode = False
        self.autonomous = True
        self.on_tool_start: Optional[Callable[[str, dict], None]] = None
        self.on_tool_end: Optional[Callable[[str, str], None]] = None
        self.confirm_callback: Optional[Callable[[str], bool]] = None

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
                preferred_model="qwen2.5:3b",
                auto_pull=False,
                auto_install_ollama=False,
            )
            if status.get("ok") and status.get("model"):
                self.llm.model = status["model"]
                self.llm.available_models = status.get("available") or []
            for m in getattr(self.llm, "available_models", []) or []:
                if "qwen2.5:3b" in m.lower() and "coder" not in m.lower():
                    self.llm.model = m
                    break
        except Exception:
            pass

        self.llm.system_prompt += "\nBe short. Call tools for actions. Greet briefly for hi/hello.\n"

        self.tool_functions = {
            **WEB_FUNCS, **SYSTEM_FUNCS, **DESKTOP_FUNCS, **PRIVACY_FUNCS, **EXTRA_FUNCS,
            **CREDENTIAL_FUNCS, **MEDIA_FUNCS, **PRODUCTIVITY_FUNCS, **BROWSER_FUNCS,
            **SCREEN_FUNCS, **SYSTEM_PLUS_FUNCS, **SYSTEM_PLUS2_FUNCS, **POWER_FUNCS,
            **POWER_FEATURE_FUNCS, **SOCIAL_WEB_FUNCS, **CLOUD_DEV_FUNCS, **DEVELOPER_FUNCS,
            **MEGA_FUNCS, **GAME_FUNCS, **STREAMING_FUNCS, **WEB_BUILDER_FUNCS, **IMAGE_FUNCS,
            **VISION_PRIVACY_FUNCS, **POWER40_FUNCS, **ANTIVIRUS_FUNCS,
        }
        self.tool_definitions = (
            WEB_TOOLS + SYSTEM_TOOLS + DESKTOP_TOOLS + PRIVACY_TOOLS + EXTRA_TOOLS +
            CREDENTIAL_TOOLS + MEDIA_TOOLS + PRODUCTIVITY_TOOLS + BROWSER_TOOLS +
            SCREEN_TOOLS + SYSTEM_PLUS_TOOLS + SYSTEM_PLUS2_TOOLS + POWER_TOOL_DEFINITIONS +
            POWER_FEATURE_TOOLS + SOCIAL_WEB_TOOLS + CLOUD_DEV_TOOLS + DEVELOPER_TOOLS +
            MEGA_TOOLS + GAME_TOOLS + STREAMING_TOOLS + WEB_BUILDER_TOOLS + IMAGE_TOOLS +
            VISION_PRIVACY_TOOLS + POWER40_TOOLS + ANTIVIRUS_TOOLS
        )

        console.print(f"[bold orange1]JagX ready[/bold orange1] — tools:{len(self.tool_functions)} model:{self.llm.model}")

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _is_money_block(self, text: str) -> bool:
        low = (text or "").lower()
        return any(re.search(p, low, re.I) for p in MONEY_BLOCK_PATTERNS)

    def _needs_confirm(self, name: str, arguments: Dict[str, Any]) -> bool:
        if name in CONFIRM_TOOLS:
            return True
        if name == "run_shell":
            cmd = str(arguments.get("command", "")).lower()
            if any(x in cmd for x in ("format ", "diskpart", "rm -rf /", "mkfs", "del /f /s /q")):
                return True
        blob = (name + " " + json.dumps(arguments)).lower()
        return any(re.search(p, blob, re.I) for p in HIGH_RISK_PATTERNS)

    def _ask_confirm(self, message: str) -> bool:
        if self.confirm_callback:
            try:
                return bool(self.confirm_callback(message))
            except Exception:
                return False
        return True if self.gui_mode else False

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        func = self.tool_functions.get(name)
        if not func:
            return f"Unknown tool: {name}"
        if self._needs_confirm(name, arguments):
            if not self._ask_confirm(f"Allow {name}?"):
                return "Cancelled."
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
            result = f"Tool error: {e}"
        if self.on_tool_end:
            try:
                self.on_tool_end(name, result)
            except Exception:
                pass
        return result

    def _little_brain_act(self, user_input: str) -> str:
        if not self.little:
            return "Try: open notepad | take a screenshot | quick virus scan"
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
        return content or "OK"

    def think(self, user_input: str) -> str:
        user_input = (user_input or "").strip()
        if not user_input:
            return "Tell me what you want me to do."
        if self._is_money_block(user_input):
            return "I will not automate bank/card payments."

        low = user_input.lower().strip()

        if low in {"hi", "hello", "hey", "good morning", "good evening", "how are you"}:
            return "Hey! I'm JagX. Try: open notepad · take a screenshot · quick virus scan"

        if self.little:
            hit = self.little.rules.interpret(user_input)
            if hit and hit.get("tool") is None:
                return hit["say"]
            if hit and hit.get("tool") and hit["tool"] in self.tool_functions:
                return f"{hit['say']}. {self._execute_tool(hit['tool'], hit.get('args') or {})}"

        slug = "open_" + re.sub(r"[^a-z0-9]+", "_", low.replace("open ", "", 1)).strip("_")
        if low.startswith("open ") and slug in self.tool_functions:
            return f"Done. {self._execute_tool(slug, {})}"

        fast = {
            "open notepad": ("open_app", {"app_name": "notepad"}),
            "take a screenshot": ("screenshot_and_open", {}),
            "screenshot": ("screenshot_and_open", {}),
            "open obs": ("open_obs", {}),
            "privacy scan": ("privacy_guard_scan", {}),
            "check ip": ("check_ip_reputation", {}),
            "quick virus scan": ("quick_virus_scan", {}),
            "virus status": ("virus_guard_report", {}),
            "system briefing": ("system_briefing", {}),
        }
        if low in fast:
            name, args = fast[low]
            if name in self.tool_functions:
                return f"Done. {self._execute_tool(name, args)}"

        self.messages.append({"role": "user", "content": user_input})
        if len(self.messages) > 30:
            self.messages = self.messages[-20:]

        tools = _select_tools(self.tool_definitions, user_input)
        try:
            for _ in range(8):
                response = self.llm.chat(messages=self.messages, tools=tools, tool_choice="auto")
                content_preview = (response.get("content") or "").lower()
                if any(x in content_preview for x in ("cannot reach ollama", "no local model")):
                    return self._little_brain_act(user_input)
                if "timed out" in content_preview or "still loading" in content_preview:
                    lb = self._little_brain_act(user_input)
                    if lb and "Try:" not in lb:
                        return lb
                    return "Model is warming up. Try: open notepad · take a screenshot"
                if "model error" in content_preview:
                    return self._little_brain_act(user_input)
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
        except Exception:
            return self._little_brain_act(user_input)
        return self._little_brain_act(user_input)

    def run(self):
        self.running = True
        while self.running:
            try:
                text = input("[You] > ").strip()
                if not text:
                    continue
                if text.lower() in {"exit", "quit", "stop"}:
                    break
                console.print("[bold orange1]JagX:[/bold orange1]")
                console.print(Markdown(self.think(text)))
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
        self.running = False
