"""Consent-based social communication controls for JagX.

The pack intentionally does not silently read private chats, impersonate the
user, or publish unsolicited content. It provides local scheduling, drafts,
approval queues and integration policy that a future authorized connector can
use safely.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path("./data/social_automation.json")
ALLOWED = {"whatsapp", "telegram", "discord", "facebook", "instagram", "x", "email", "teams"}

def _default(): return {"enabled":False,"platforms":{},"schedules":[],"auto_reply":False,"auto_post":False,"drafts":[],"quiet_hours":None,"call_policy":{}}
def _load():
    if not CONFIG_PATH.exists(): return _default()
    try:
        d=json.loads(CONFIG_PATH.read_text(encoding="utf-8")); base=_default(); base.update(d); return base
    except Exception: return _default()
def _save(d): CONFIG_PATH.parent.mkdir(parents=True,exist_ok=True); CONFIG_PATH.write_text(json.dumps(d,indent=2),encoding="utf-8")
def _platform(p): return str(p).strip().lower()

def communication_status() -> str:
    d=_load(); return json.dumps({"enabled":d["enabled"],"platforms":list(d["platforms"].keys()),"auto_reply":d["auto_reply"],"auto_post":d["auto_post"],"schedules":len(d["schedules"]),"drafts":len(d["drafts"]),"quiet_hours":d["quiet_hours"]},indent=2)

def configure_communication(platform:str,enabled:bool=True)->str:
    p=_platform(platform)
    if p not in ALLOWED:return "Unsupported integration: "+", ".join(sorted(ALLOWED))
    d=_load(); d["platforms"][p]=bool(enabled); d["enabled"]=any(d["platforms"].values()); _save(d)
    return f"{p} integration {'enabled' if enabled else 'disabled'}. Authorize it through its supported login/connector before sending."

def set_social_schedule(platform:str,interval_minutes:int=30,enabled:bool=True)->str:
    p=_platform(platform); n=int(interval_minutes)
    if p not in ALLOWED:return "Unsupported platform."
    if n<5 or n>10080:return "Interval must be 5 minutes to 7 days."
    d=_load()
    if not d["platforms"].get(p):return "Enable and authorize that platform first."
    d["auto_post"]=bool(enabled); d["schedules"]=[{"platform":p,"interval_minutes":n,"enabled":bool(enabled),"created_at":datetime.now().isoformat()}]; _save(d)
    return f"Schedule {'enabled' if enabled else 'disabled'} for {p}: every {n} minutes. It only processes explicitly approved drafts."

def queue_social_post(platform:str,text:str)->str:
    p=_platform(platform); text=str(text).strip(); d=_load()
    if not text:return "Post text cannot be empty."
    if not d["platforms"].get(p):return "Enable and authorize that platform first."
    d["drafts"].append({"id":len(d["drafts"])+1,"platform":p,"text":text,"created_at":datetime.now().isoformat(),"approved":False}); _save(d); return "Saved as an unapproved draft."

def list_social_drafts(platform:str="")->str:
    p=_platform(platform) if platform else ""; d=_load(); rows=[x for x in d["drafts"] if not p or x["platform"]==p]; return json.dumps(rows,indent=2)

def approve_social_draft(draft_id:int)->str:
    d=_load(); found=next((x for x in d["drafts"] if x.get("id")==int(draft_id)),None)
    if not found:return "Draft not found."
    found["approved"]=True; found["approved_at"]=datetime.now().isoformat(); _save(d); return "Draft approved for the configured publishing workflow."

def remove_social_draft(draft_id:int)->str:
    d=_load(); before=len(d["drafts"]); d["drafts"]=[x for x in d["drafts"] if x.get("id")!=int(draft_id)]; _save(d); return "Draft removed." if len(d["drafts"])<before else "Draft not found."

def set_auto_reply(enabled:bool=True)->str:
    d=_load(); d["auto_reply"]=bool(enabled); _save(d); return f"Auto-reply policy {'enabled' if enabled else 'disabled'}; replies remain review/send-controlled."

def prepare_reply(platform:str,conversation_hint:str,proposed_reply:str)->str:
    if not str(proposed_reply).strip():return "Reply cannot be empty."
    return json.dumps({"platform":_platform(platform),"conversation_hint":str(conversation_hint)[:200],"reply":str(proposed_reply),"send":False},indent=2)

def set_quiet_hours(start:str="22:00",end:str="07:00",enabled:bool=True)->str:
    import re
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",start) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",end):return "Use HH:MM times."
    d=_load(); d["quiet_hours"]={"enabled":bool(enabled),"start":start,"end":end}; _save(d); return f"Quiet hours {'enabled' if enabled else 'disabled'}: {start}–{end}."

def set_call_policy(auto_answer:bool=False,allowed_contacts:str="")->str:
    d=_load(); d["call_policy"]={"auto_answer":bool(auto_answer),"allowed_contacts":[x.strip() for x in str(allowed_contacts).split(",") if x.strip()]}; _save(d); return "Call policy saved. Actual call answering requires an authorized telephony integration."

def call_control(action:str,contact:str="")->str:
    a=str(action).strip().lower()
    if a not in {"dial","answer","decline","hangup"}:return "Action must be dial, answer, decline, or hangup."
    return f"Call action prepared: {a}"+(f" for {contact}" if contact else "")+". No call was placed or answered by this local policy tool."

def integration_check(platform:str)->str:
    p=_platform(platform); d=_load(); return json.dumps({"platform":p,"configured":p in ALLOWED,"enabled":bool(d["platforms"].get(p,False)),"authorized":False,"note":"Authorization must be completed through a supported connector/app login."},indent=2)

def open_social_site(platform:str)->str:
    import webbrowser
    p=_platform(platform); urls={"whatsapp":"https://web.whatsapp.com/","telegram":"https://web.telegram.org/","discord":"https://discord.com/app","facebook":"https://www.facebook.com/","instagram":"https://www.instagram.com/","x":"https://x.com/","email":"https://mail.google.com/","teams":"https://teams.microsoft.com/"}
    if p not in urls:return "Unsupported platform."
    webbrowser.open(urls[p]); return f"Opened {p} in the default browser."

def export_social_queue(path:str="./data/social_queue.json")->str:
    d=_load(); out=Path(path).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d["drafts"],indent=2),encoding="utf-8"); return f"Exported {len(d['drafts'])} drafts to {out}."

def clear_social_queue()->str:
    d=_load(); n=len(d["drafts"]); d["drafts"]=[]; _save(d); return f"Cleared {n} social drafts."

def communication_audit()->str:
    d=_load(); return json.dumps({"checked_at":datetime.now().isoformat(),"enabled_platforms":list(d["platforms"].keys()),"draft_count":len(d["drafts"]),"schedule_count":len(d["schedules"]),"auto_reply":d["auto_reply"],"auto_post":d["auto_post"],"private_chat_reading":"disabled by design","silent_impersonation":"disabled by design"},indent=2)

# 15 user-facing features/tools: status, integration, scheduling, drafts, approvals,
# auto-reply policy, reply preparation, quiet hours, call policy, call actions,
# integration checks, site opening, queue export, queue clearing, audit.
NAMES=["communication_status","configure_communication","set_social_schedule","queue_social_post","list_social_drafts","approve_social_draft","remove_social_draft","set_auto_reply","prepare_reply","set_quiet_hours","set_call_policy","call_control","integration_check","open_social_site","export_social_queue","clear_social_queue","communication_audit"]
SYSTEM_SOCIAL_TOOLS=[]
for n in NAMES:
    SYSTEM_SOCIAL_TOOLS.append({"type":"function","function":{"name":n,"description":globals()[n].__doc__ or n.replace("_"," ").title(),"parameters":{"type":"object","properties":{},"additionalProperties":True}}})
TOOL_FUNCTIONS={n:globals()[n] for n in NAMES}
