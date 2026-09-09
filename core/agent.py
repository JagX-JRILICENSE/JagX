"""JagX Agent - the brain of the jaguar."""
from __future__ import annotations
import json, re
from typing import Any, Dict, List
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
from core.llm import create_llm_from_config
from core.memory import Memory
from core.tools.web import WEB_TOOLS, TOOL_FUNCTIONS as WEB_FUNCS
from core.tools.system import SYSTEM_TOOLS, TOOL_FUNCTIONS as SYSTEM_FUNCS
from core.tools.desktop import DESKTOP_TOOLS, TOOL_FUNCTIONS as DESKTOP_FUNCS
from core.tools.privacy import PRIVACY_TOOLS, TOOL_FUNCTIONS as PRIVACY_FUNCS
from core.tools.extra import EXTRA_TOOLS, TOOL_FUNCTIONS as EXTRA_FUNCS
from core.tools.media import MEDIA_TOOLS, TOOL_FUNCTIONS as MEDIA_FUNCS
from core.tools.productivity import PRODUCTIVITY_TOOLS, TOOL_FUNCTIONS as PRODUCTIVITY_FUNCS
from core.tools.credentials import CREDENTIAL_TOOLS, TOOL_FUNCTIONS as CREDENTIAL_FUNCS
from core.tools.developer import DEVELOPER_TOOLS, TOOL_FUNCTIONS as DEVELOPER_FUNCS
from core.tools.ai import AI_TOOLS, TOOL_FUNCTIONS as AI_FUNCS
from core.tools.automation import AUTOMATION_TOOLS, TOOL_FUNCTIONS as AUTOMATION_FUNCS
console = Console()
HIGH_RISK_PATTERNS=[r"hack",r"exploit",r"payload",r"metasploit",r"nmap",r"sqlmap",r"keylog",r"rat\b",r"backdoor",r"rootkit",r"c2\b",r"reverse.?shell",r"bind.?shell",r"privilege.?escalation",r"mimikatz",r"credential.?dump",r"password.?crack",r"ddos",r"botnet",r"ransomware",r"format\s+c:",r"rm\s+-rf\s+/",r"mkfs",r"dd\s+if="]
SENSITIVE_TOOLS={"run_shell","run_project_tests","delete_path","uninstall_app","write_file","write_text_file","set_clipboard","save_credential","create_project_structure","kill_process_by_name","block_camera_access"}
class JagXAgent:
    """Main tool-calling agent for JagX."""
    def __init__(self,config_path="config/settings.yaml"):
        self.config=self._load_config(config_path); self.llm=create_llm_from_config(self.config)
        self.memory=Memory(self.config.get("memory",{}).get("path","./data/memory")); self.messages=[]; self.running=False
        context=self.memory.get_context_summary()
        if context and context!="No long-term memory yet.": self.llm.system_prompt+=f"\n\n### Personal Memory\n{context}"
        self.tool_functions={**WEB_FUNCS,**SYSTEM_FUNCS,**DESKTOP_FUNCS,**PRIVACY_FUNCS,**EXTRA_FUNCS,**MEDIA_FUNCS,**PRODUCTIVITY_FUNCS,**CREDENTIAL_FUNCS,**DEVELOPER_FUNCS,**AI_FUNCS,**AUTOMATION_FUNCS}
        self.tool_definitions=WEB_TOOLS+SYSTEM_TOOLS+DESKTOP_TOOLS+PRIVACY_TOOLS+EXTRA_TOOLS+MEDIA_TOOLS+PRODUCTIVITY_TOOLS+CREDENTIAL_TOOLS+DEVELOPER_TOOLS+AI_TOOLS+AUTOMATION_TOOLS
        console.print(f"[bold orange1]JagX initialized[/bold orange1] — {len(self.tool_definitions)} tools loaded — model: {self.llm.model}")
    def _load_config(self,path):
        try:
            with open(path,encoding="utf-8") as f:return yaml.safe_load(f) or {}
        except Exception:return {}
    def _needs_confirmation(self,name,arguments):
        text=(name+" "+json.dumps(arguments)).lower(); return name in SENSITIVE_TOOLS or any(re.search(p,text,re.I) for p in HIGH_RISK_PATTERNS)
    def _execute_tool(self,name,arguments):
        func=self.tool_functions.get(name)
        if not func:return f"Unknown tool: {name}"
        if self._needs_confirmation(name,arguments):
            console.print(f"[bold yellow]JagX wants to perform:[/bold yellow] {name}({arguments})")
            if not Confirm.ask("Allow this action?",default=False):return "Action cancelled by user."
        try:return str(func(**arguments))
        except TypeError as e:return f"Tool argument error: {e}"
        except Exception as e:return f"Tool execution error: {e}"
    def think(self,user_input):
        self.messages.append({"role":"user","content":user_input})
        for _ in range(12):
            response=self.llm.chat(self.messages,tools=self.tool_definitions,tool_choice="auto"); calls=response.get("tool_calls")
            if calls:
                self.messages.append(response)
                for call in calls:
                    fn=call["function"]; name=fn["name"]
                    try:args=json.loads(fn.get("arguments","{}"))
                    except json.JSONDecodeError:args={}
                    result=self._execute_tool(name,args)
                    if name=="request_password" and not result.startswith("PASSWORD_INPUT_ERROR"):result="PASSWORD_RECEIVED_SECURELY: the password is available only to the local tool flow and must not be repeated or stored in conversation memory."
                    self.messages.append({"role":"tool","tool_call_id":call.get("id",name),"name":name,"content":result})
                continue
            content=response.get("content") or ""; self.messages.append({"role":"assistant","content":content})
            if any(w in user_input.lower() for w in ["remember","my name is","i like","i prefer","note that"]):self.memory.add_note(user_input)
            return content
        return "I reached the maximum number of tool rounds. Please try a simpler request."
    def run(self):
        self.running=True; console.print("[green]JagX is awake. Type your request or 'exit'.[/green]")
        while self.running:
            try:
                text=input("[You] > ").strip()
                if not text:continue
                if text.lower() in {"exit","quit","stop","sleep"}:break
                console.print("[bold orange1]JagX:[/bold orange1]");console.print(Markdown(self.think(text)))
            except KeyboardInterrupt:break
            except Exception as e:console.print(f"[red]Error:[/red] {e}")
        self.running=False
