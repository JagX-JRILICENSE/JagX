"""
JagX cloud + GitHub helpers
- GitHub CLI for your repos (improve code, push, PRs)
- Vercel CLI for deploy
- Open domain registrars (you complete payment yourself)
JRILICENSE
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _run(cmd: str, cwd: Optional[str] = None, timeout: int = 180) -> str:
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or os.path.expanduser("~"),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        return f"Exit {r.returncode}\n{out}\n{err}".strip()
    except Exception as e:
        return f"Error: {e}"


def github_cli_status() -> str:
    if not shutil.which("gh"):
        return "GitHub CLI (gh) not installed. Install from https://cli.github.com then run: gh auth login"
    return _run("gh auth status")


def github_list_repos(limit: int = 15) -> str:
    if not shutil.which("gh"):
        return "Install GitHub CLI: https://cli.github.com"
    return _run(f"gh repo list --limit {int(limit)}")


def github_clone_repo(repo: str, dest: str = "") -> str:
    """Clone owner/name into dest folder."""
    if not shutil.which("gh") and not shutil.which("git"):
        return "Need git or gh installed"
    target = dest.strip() or str(Path.home() / "Projects" / repo.replace("/", "_"))
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("gh"):
        return _run(f'gh repo clone {repo} "{target}"', timeout=300)
    return _run(f'git clone https://github.com/{repo}.git "{target}"', timeout=300)


def github_git_status(path: str = ".") -> str:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return f"Path not found: {root}"
    return _run("git status -sb && git remote -v", cwd=str(root))


def github_commit_all(path: str, message: str) -> str:
    """Stage all and commit in a local repo (does not push)."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return f"Path not found: {root}"
    msg = (message or "Update by JagX").replace('"', "'")
    return _run(f'git add -A && git commit -m "{msg}"', cwd=str(root))


def github_push(path: str = ".", branch: str = "") -> str:
    root = Path(path).expanduser().resolve()
    if branch:
        return _run(f"git push -u origin {branch}", cwd=str(root), timeout=180)
    return _run("git push", cwd=str(root), timeout=180)


def github_create_pr(path: str, title: str, body: str = "") -> str:
    if not shutil.which("gh"):
        return "Install GitHub CLI and run gh auth login"
    root = Path(path).expanduser().resolve()
    t = (title or "JagX update").replace('"', "'")
    b = (body or "Automated improvement via JagX").replace('"', "'")
    return _run(f'gh pr create --title "{t}" --body "{b}"', cwd=str(root), timeout=120)


def vercel_status() -> str:
    if not shutil.which("vercel"):
        return "Vercel CLI not installed. Run: npm i -g vercel  then: vercel login"
    return _run("vercel whoami")


def vercel_deploy(path: str = ".", prod: bool = False) -> str:
    """Deploy a project folder with Vercel CLI (user must be logged in)."""
    if not shutil.which("vercel"):
        return "Install: npm i -g vercel && vercel login"
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return f"Path not found: {root}"
    flag = "--prod" if prod else ""
    return _run(f"vercel {flag} --yes", cwd=str(root), timeout=300)


def open_domain_registrar(provider: str = "namecheap") -> str:
    """Open a domain shop so YOU can buy with your card. JagX will not store or enter card data."""
    urls = {
        "namecheap": "https://www.namecheap.com/",
        "godaddy": "https://www.godaddy.com/",
        "cloudflare": "https://www.cloudflare.com/products/registrar/",
        "google": "https://domains.google/",
        "vercel": "https://vercel.com/domains",
    }
    key = (provider or "namecheap").lower().strip()
    url = urls.get(key, urls["namecheap"])
    try:
        from core.tools.social_web import open_any_url

        return open_any_url(url) + " | Complete payment yourself — JagX will not enter card numbers."
    except Exception:
        import os as _os

        if _os.name == "nt":
            _os.system(f'start {url}')
        return f"Opened {url}. Pay yourself; card details stay with you."


def open_vercel_dashboard() -> str:
    try:
        from core.tools.social_web import open_any_url

        return open_any_url("https://vercel.com/dashboard")
    except Exception:
        return "Open https://vercel.com/dashboard"


CLOUD_DEV_TOOLS = [
    {"type": "function", "function": {"name": "github_cli_status", "description": "Check if GitHub CLI is installed and authenticated.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "github_list_repos", "description": "List your GitHub repositories via gh.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "default": 15}}, "required": []}}},
    {"type": "function", "function": {"name": "github_clone_repo", "description": "Clone a GitHub repo (owner/name) to a local folder.", "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "dest": {"type": "string", "default": ""}}, "required": ["repo"]}}},
    {"type": "function", "function": {"name": "github_git_status", "description": "Show git status for a local project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}}, "required": []}}},
    {"type": "function", "function": {"name": "github_commit_all", "description": "git add -A and commit locally (no push).", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "message": {"type": "string"}}, "required": ["path", "message"]}}},
    {"type": "function", "function": {"name": "github_push", "description": "Push local commits to origin.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}, "branch": {"type": "string", "default": ""}}, "required": []}}},
    {"type": "function", "function": {"name": "github_create_pr", "description": "Create a GitHub pull request with gh.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string", "default": ""}}, "required": ["path", "title"]}}},
    {"type": "function", "function": {"name": "vercel_status", "description": "Check Vercel CLI login status.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "vercel_deploy", "description": "Deploy a folder with Vercel CLI.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "default": "."}, "prod": {"type": "boolean", "default": False}}, "required": []}}},
    {"type": "function", "function": {"name": "open_vercel_dashboard", "description": "Open Vercel dashboard in browser.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_domain_registrar", "description": "Open domain shop so user can buy a domain themselves (no card automation).", "parameters": {"type": "object", "properties": {"provider": {"type": "string", "default": "namecheap"}}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "github_cli_status": github_cli_status,
    "github_list_repos": github_list_repos,
    "github_clone_repo": github_clone_repo,
    "github_git_status": github_git_status,
    "github_commit_all": github_commit_all,
    "github_push": github_push,
    "github_create_pr": github_create_pr,
    "vercel_status": vercel_status,
    "vercel_deploy": vercel_deploy,
    "open_vercel_dashboard": open_vercel_dashboard,
    "open_domain_registrar": open_domain_registrar,
}
