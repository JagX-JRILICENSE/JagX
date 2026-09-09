"""JagX advanced coding/build tools.

JRILICENSE
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path


def _root(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _safe_relative(root: Path, rel: str) -> Path | None:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        return None
    target = (root / p).resolve()
    try:
        target.relative_to(root)
        return target
    except ValueError:
        return None


def search_code(path: str, query: str, extensions: list[str] | None = None, max_results: int = 50) -> str:
    """Search source files for a string, returning file/line matches."""
    root = _root(path)
    if not root.is_dir(): return f"Project path not found: {root}"
    exts = {e.lower() if e.startswith(".") else "." + e.lower() for e in (extensions or [])}
    ignored = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}
    hits = []
    needle = query.lower()
    for p in root.rglob("*"):
        if not p.is_file() or any(part in ignored for part in p.parts): continue
        if exts and p.suffix.lower() not in exts: continue
        try: text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        for n, line in enumerate(text.splitlines(), 1):
            if needle in line.lower():
                hits.append(f"{p.relative_to(root)}:{n}: {line.strip()[:500]}")
                if len(hits) >= max_results: return "\n".join(hits)
    return "No matches found." if not hits else "\n".join(hits)


def inspect_python_file(path: str) -> str:
    """Parse a Python file and report syntax errors plus classes/functions/imports."""
    p = _root(path)
    if not p.is_file(): return f"Python file not found: {p}"
    try: tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
    except SyntaxError as e: return json.dumps({"valid": False, "error": f"line {e.lineno}: {e.msg}"}, indent=2)
    data = {"valid": True, "imports": [], "functions": [], "classes": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): data["imports"].extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom): data["imports"].append(node.module or "")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): data["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef): data["classes"].append(node.name)
    return json.dumps(data, indent=2)


def git_status(path: str = ".") -> str:
    """Show git status and recent commit for a project."""
    root = _root(path)
    try:
        a = subprocess.run(["git", "status", "--short", "--branch"], cwd=root, capture_output=True, text=True, timeout=30)
        b = subprocess.run(["git", "log", "-1", "--oneline"], cwd=root, capture_output=True, text=True, timeout=30)
        return f"STATUS:\n{a.stdout or a.stderr}\nLATEST COMMIT:\n{b.stdout or b.stderr}"
    except Exception as e: return f"Git inspection failed: {e}"


def build_project(path: str, command: str = "") -> str:
    """Build a project using an explicit command or safe common build inference."""
    root = _root(path)
    if not root.is_dir(): return f"Project path not found: {root}"
    if not command:
        if (root / "pyproject.toml").exists(): command = "python -m build"
        elif (root / "package.json").exists(): command = "npm run build"
        elif (root / "build_windows.bat").exists(): command = "build_windows.bat"
        else: return "No build command inferred. Provide the build command explicitly."
    try:
        r = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=900)
        return f"Exit code: {r.returncode}\nSTDOUT:\n{r.stdout[-16000:]}\nSTDERR:\n{r.stderr[-16000:]}"
    except subprocess.TimeoutExpired: return "Build timed out after 900 seconds."
    except Exception as e: return f"Build failed: {e}"


def apply_file_patch(path: str, old_text: str, new_text: str, expected_matches: int = 1) -> str:
    """Replace an exact text fragment in a local file; refuses ambiguous matches."""
    p = _root(path)
    if not p.is_file(): return f"File not found: {p}"
    text = p.read_text(encoding="utf-8")
    count = text.count(old_text)
    if count != expected_matches:
        return f"Patch refused: expected {expected_matches} matches but found {count}."
    p.write_text(text.replace(old_text, new_text), encoding="utf-8")
    return f"Applied exact patch to {p} ({count} match)."


def create_backup(path: str) -> str:
    """Create a timestamp-free .bak copy beside a file before editing it."""
    p = _root(path)
    if not p.is_file(): return f"File not found: {p}"
    backup = p.with_suffix(p.suffix + ".bak")
    shutil.copy2(p, backup)
    return f"Backup created: {backup}"


CODING_TOOLS = [
    {"type":"function","function":{"name":"search_code","description":"Search source code for a text pattern and return file/line matches.","parameters":{"type":"object","properties":{"path":{"type":"string"},"query":{"type":"string"},"extensions":{"type":"array","items":{"type":"string"}},"max_results":{"type":"integer","default":50}},"required":["path","query"]}}},
    {"type":"function","function":{"name":"inspect_python_file","description":"Statically inspect a Python file for syntax validity, imports, functions, and classes.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"git_status","description":"Inspect git branch/status and latest commit in a project.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"."}},"required":[]}}},
    {"type":"function","function":{"name":"build_project","description":"Build a local software project using an explicit command or common project build inference. Requires user confirmation because it executes a build command.","parameters":{"type":"object","properties":{"path":{"type":"string"},"command":{"type":"string","default":""}},"required":["path"]}}},
    {"type":"function","function":{"name":"apply_file_patch","description":"Apply an exact text replacement to a local file. Refuses if the expected match count is wrong.","parameters":{"type":"object","properties":{"path":{"type":"string"},"old_text":{"type":"string"},"new_text":{"type":"string"},"expected_matches":{"type":"integer","default":1}},"required":["path","old_text","new_text"]}}},
    {"type":"function","function":{"name":"create_backup","description":"Create a .bak backup of a file before editing it.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
]

TOOL_FUNCTIONS = {"search_code": search_code, "inspect_python_file": inspect_python_file, "git_status": git_status, "build_project": build_project, "apply_file_patch": apply_file_patch, "create_backup": create_backup}
