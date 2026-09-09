"""JagX idle policy helpers.
The UI/agent can use this module to configure an idle timeout. The actual
power action remains confirmation-gated when invoked by the agent.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

DEFAULTS = {"enabled": False, "timeout_minutes": 30, "action": "sleep", "last_activity": time.time()}


def _path(root: str = "./data/jagx") -> Path:
    p = Path(root); p.mkdir(parents=True, exist_ok=True); return p / "idle_policy.json"


def get_idle_policy(root: str = "./data/jagx") -> str:
    p = _path(root)
    if not p.exists(): return json.dumps(DEFAULTS)
    try: return p.read_text(encoding="utf-8")
    except Exception: return json.dumps(DEFAULTS)


def set_idle_policy(enabled: bool = False, timeout_minutes: int = 30, action: str = "sleep", root: str = "./data/jagx") -> str:
    action = action.lower().strip()
    if action not in {"sleep", "hibernate", "shutdown"}: return "Invalid action. Choose sleep, hibernate, or shutdown."
    if timeout_minutes < 1 or timeout_minutes > 10080: return "timeout_minutes must be between 1 and 10080."
    data = {"enabled": bool(enabled), "timeout_minutes": int(timeout_minutes), "action": action, "last_activity": time.time()}
    p = _path(root); p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"Idle power policy saved: enabled={data['enabled']}, timeout={data['timeout_minutes']} minutes, action={action}."


def mark_activity(root: str = "./data/jagx") -> str:
    p = _path(root); data = json.loads(get_idle_policy(root)); data["last_activity"] = time.time(); p.write_text(json.dumps(data, indent=2), encoding="utf-8"); return "Activity timestamp updated."


def idle_due(root: str = "./data/jagx") -> str:
    data = json.loads(get_idle_policy(root)); due = bool(data.get("enabled")) and time.time() - float(data.get("last_activity", time.time())) >= int(data.get("timeout_minutes", 30))*60
    return json.dumps({"due": due, "action": data.get("action", "sleep")})

IDLE_TOOL_DEFINITIONS = [
 {"type":"function","function":{"name":"get_idle_policy","description":"Read JagX automatic idle power policy.","parameters":{"type":"object","properties":{},"required":[]}}},
 {"type":"function","function":{"name":"set_idle_policy","description":"Configure JagX to sleep, hibernate, or shut down after a period with no user activity. Use only when explicitly requested.","parameters":{"type":"object","properties":{"enabled":{"type":"boolean","default":False},"timeout_minutes":{"type":"integer","default":30},"action":{"type":"string","enum":["sleep","hibernate","shutdown"],"default":"sleep"}},"required":[]}}}
]
TOOL_FUNCTIONS={"get_idle_policy":get_idle_policy,"set_idle_policy":set_idle_policy}
