"""JagX Personal Memory — durable, searchable, privacy-aware memory."""
from __future__ import annotations
import json, re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class Memory:
    """Persistent local memory for facts, preferences, notes, and conversation context."""
    def __init__(self, path: str = "./data/memory"):
        self.path=Path(path).expanduser(); self.path.mkdir(parents=True,exist_ok=True); self.file=self.path/"memory.json"; self.data=self._load()
    def _load(self):
        default={"version":2,"facts":[],"preferences":{},"notes":[],"conversations":[]}
        try:
            d=json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else default
            if not isinstance(d,dict): d=default
            for k,v in default.items(): d.setdefault(k,v)
            return d
        except Exception: return default
    def _save(self):
        tmp=self.file.with_suffix(".tmp"); tmp.write_text(json.dumps(self.data,indent=2,ensure_ascii=False),encoding="utf-8"); tmp.replace(self.file)
    @staticmethod
    def _redact(text):
        return re.sub(r"(?i)(password|passcode|otp|one[- ]time code|secret|api[_ -]?key)\s*[:=]\s*[^\s,;]+",r"\1=[REDACTED]",str(text))
    def add_note(self,text,tags=None):
        text=str(text).strip()
        if text and text not in [n.get("text","") for n in self.data["notes"]]:
            self.data["notes"].append({"text":self._redact(text),"tags":tags or [],"timestamp":datetime.now().isoformat(timespec="seconds")}); self.data["notes"]=self.data["notes"][-200:]; self._save()
    def add_fact(self,fact,tags=None):
        fact=self._redact(str(fact).strip())
        if fact and fact not in self.data["facts"]: self.data["facts"].append(fact); self.data["facts"]=self.data["facts"][-200:]; self._save()
    def set_preference(self,key,value): self.data["preferences"][str(key).strip()]=value; self._save()
    def get_preference(self,key,default=None): return self.data["preferences"].get(key,default)
    def record_conversation(self,user_text,assistant_text,tags=None):
        self.data["conversations"].append({"user":self._redact(user_text)[:2000],"assistant":self._redact(assistant_text)[:3000],"tags":tags or [],"timestamp":datetime.now().isoformat(timespec="seconds")}); self.data["conversations"]=self.data["conversations"][-100:]; self._save()
    def search(self,query,limit=8):
        terms=[x for x in re.findall(r"[\w'-]+",str(query).lower()) if len(x)>1]; candidates=[]
        for x in self.data["facts"]: candidates.append((x,"fact",""))
        for k,v in self.data["preferences"].items(): candidates.append((f"{k}={v}","preference",""))
        for x in self.data["notes"]: candidates.append((x.get("text",""),"note",x.get("timestamp","")))
        for x in self.data["conversations"]: candidates.append((f"User: {x.get('user','')}\nJagX: {x.get('assistant','')}","conversation",x.get("timestamp","")))
        scored=[]
        for text,kind,stamp in candidates:
            score=sum(text.lower().count(t) for t in terms)
            if score: scored.append((score,stamp,kind,text))
        scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
        return "\n\n".join(f"[{k}] {t}" for _,_,k,t in scored[:max(1,limit)]) if scored else "No relevant memories found."
    def forget(self,query):
        q=str(query).strip().lower(); removed=0
        if not q:return 0
        old=self.data["facts"]; self.data["facts"]=[x for x in old if q not in x.lower()]; removed+=len(old)-len(self.data["facts"])
        old=self.data["notes"]; self.data["notes"]=[x for x in old if q not in x.get("text","").lower()]; removed+=len(old)-len(self.data["notes"])
        for k in list(self.data["preferences"]):
            if q in k.lower() or q in str(self.data["preferences"][k]).lower(): del self.data["preferences"][k]; removed+=1
        old=self.data["conversations"]; self.data["conversations"]=[x for x in old if q not in json.dumps(x,ensure_ascii=False).lower()]; removed+=len(old)-len(self.data["conversations"])
        if removed:self._save()
        return removed
    def get_context_summary(self,max_notes=8,max_conversations=4):
        p=[]; f=self.data["facts"]
        if f:p.append("Known facts about the user:\n- " + "\n- ".join(f[-12:]))
        if self.data["preferences"]:p.append("Preferences:\n- " + "\n- ".join(f"{k}={v}" for k,v in list(self.data["preferences"].items())[-20:]))
        n=self.data["notes"][-max_notes:]
        if n:p.append("Recent notes:\n- " + "\n- ".join(x.get("text","") for x in n))
        c=self.data["conversations"][-max_conversations:]
        if c:p.append("Recent conversation context:\n- " + "\n- ".join(x.get("user","") for x in c))
        return "\n\n".join(p) if p else "No long-term memory yet."
    def clear(self): self.data={"version":2,"notes":[],"preferences":{},"facts":[],"conversations":[]}; self._save()
