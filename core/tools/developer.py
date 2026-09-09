"""JagX developer tools for building and inspecting projects on the user's computer."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Iterable


def _root(path: str) -> Path:
    return Path(path).expanduser().resolve()


def inspect_project(path: str = ".") -> str:
    root = _root(path)
    if not root.exists(): return f"Project path not found: {root}"
    files = []
    ignored = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
    for p in root.rglob("*"):
        if any(part in ignored for part in p.parts): continue
        if p.is_file():
            try: files.append(str(p.relative_to(root)))
            except ValueError: pass
        if len(files) >= 500: break
    return json.dumps({"root": str(root), "files": files}, indent=2)


def run_project_tests(path: str = ".", command: str = "") -> str:
    """Run a user-specified project test command in the project directory."""
    root = _root(path)
    if not root.exists(): return f"Project path not found: {root}"
    if not command:
        if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists() or (root / "tests").exists(): command = "python -m pytest"
        elif (root / "package.json").exists(): command = "npm test"
        else: return "No test command was inferred. Provide the command explicitly."
    try:
        r = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=300)
        return f"Exit code: {r.returncode}\nSTDOUT:\n{r.stdout[-12000:]}\nSTDERR:\n{r.stderr[-12000:]}"
    except subprocess.TimeoutExpired: return "Project test command timed out after 300 seconds."
    except Exception as e: return f"Test execution failed: {e}"


def open_project(path: str) -> str:
    root = _root(path)
    if not root.exists(): return f"Project path not found: {root}"
    if os.name == "nt": os.startfile(str(root))
    elif os.name == "darwin": subprocess.Popen(["open", str(root)])
    else: subprocess.Popen(["xdg-open", str(root)])
    return f"Opened project folder: {root}"


def create_project_structure(path: str, files: list[dict]) -> str:
    """Create a project scaffold from a list of relative file paths and text contents."""
    root = _root(path); root.mkdir(parents=True, exist_ok=True)
    created = []
    for item in files[:100]:
        rel = str(item.get("path", "")).strip()
        content = str(item.get("content", ""))
        if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts: continue
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        created.append(rel)
    return f"Created {len(created)} project files under {root}:\n" + "\n".join(created)


DEVELOPER_TOOLS = [
    {"type":"function","function":{"name":"inspect_project","description":"Inspect a local software project and return its file tree, excluding build/cache folders.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"."}},"required":[]}}},
    {"type":"function","function":{"name":"run_project_tests","description":"Run the project's tests in its local folder. Sensitive because it executes a command; ask the user for approval first.","parameters":{"type":"object","properties":{"path":{"type":"string","default":"."},"command":{"type":"string","default":""}},"required":[]}}},
    {"type":"function","function":{"name":"open_project","description":"Open a local project folder in the file manager.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"create_project_structure","description":"Create a software project scaffold from relative paths and file contents.","parameters":{"type":"object","properties":{"path":{"type":"string"},"files":{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},"required":["path","files"]}}},
]

TOOL_FUNCTIONS = {"inspect_project": inspect_project, "run_project_tests": run_project_tests, "open_project": open_project, "create_project_structure": create_project_structure}
