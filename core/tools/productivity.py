"""JagX everyday productivity tools."""
from __future__ import annotations

import ast
import datetime as dt
import json
import math
import os
import subprocess
import webbrowser
from pathlib import Path


def calculate(expression: str) -> str:
    """Safely evaluate basic arithmetic and math functions."""
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Expression, ast.Constant, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Call, ast.Name, ast.Load, ast.Tuple, ast.List)):
            raise ValueError("Only basic arithmetic/math expressions are allowed.")
    return str(eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}}, allowed))


def get_time_date() -> str:
    return dt.datetime.now().astimezone().strftime("%A, %d %B %Y, %I:%M:%S %p %Z")


def create_note(title: str, content: str, folder: str = "data/notes") -> str:
    target_dir = Path(folder).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in title).strip() or "note"
    target = target_dir / f"{safe}.md"
    target.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return f"Note saved to {target}"


def list_folder(path: str = ".") -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists(): return f"Folder not found: {p}"
    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    return json.dumps([{"name": x.name, "type": "folder" if x.is_dir() else "file"} for x in items[:200]], indent=2)


def read_text_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists(): return f"File not found: {p}"
    if p.stat().st_size > 2_000_000: return "File is too large for direct reading."
    return p.read_text(encoding="utf-8", errors="replace")


def write_text_file(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {p}"


def open_folder(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists(): return f"Path not found: {p}"
    if os.name == "nt": os.startfile(str(p))
    elif os.name == "darwin": subprocess.Popen(["open", str(p)])
    else: subprocess.Popen(["xdg-open", str(p)])
    return f"Opened {p}"


def search_web(query: str) -> str:
    url = "https://www.google.com/search?q=" + __import__("urllib.parse", fromlist=["quote_plus"]).quote_plus(query)
    webbrowser.open(url)
    return f"Opened Google search for: {query}"


def productivity_tools():
    return [
        {"type":"function","function":{"name":"calculate","description":"Calculate a basic arithmetic or math expression.","parameters":{"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"]}}},
        {"type":"function","function":{"name":"get_time_date","description":"Get the current local date and time.","parameters":{"type":"object","properties":{},"required":[]}}},
        {"type":"function","function":{"name":"create_note","description":"Create a local Markdown note.","parameters":{"type":"object","properties":{"title":{"type":"string"},"content":{"type":"string"},"folder":{"type":"string","default":"data/notes"}},"required":["title","content"]}}},
        {"type":"function","function":{"name":"list_folder","description":"List files and folders in a directory.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"."}},"required":[]}}},
        {"type":"function","function":{"name":"read_text_file","description":"Read a local text file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
        {"type":"function","function":{"name":"write_text_file","description":"Create or overwrite a local text file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
        {"type":"function","function":{"name":"open_folder","description":"Open a local folder in the file manager.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
        {"type":"function","function":{"name":"search_web","description":"Open a Google web search.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    ]

PRODUCTIVITY_TOOLS = productivity_tools()
TOOL_FUNCTIONS = {"calculate": calculate, "get_time_date": get_time_date, "create_note": create_note, "list_folder": list_folder, "read_text_file": read_text_file, "write_text_file": write_text_file, "open_folder": open_folder, "search_web": search_web}
