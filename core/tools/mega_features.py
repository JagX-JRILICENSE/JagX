"""
JagX Mega Feature Pack — 200+ callable everyday tools.
Windows-first. Opens sites/apps, system panels, notes, clipboard, files.
JRILICENSE
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

DATA = Path(__file__).resolve().parents[2] / "data" / "mega"
DATA.mkdir(parents=True, exist_ok=True)
NOTES = DATA / "notes.md"
TASKS = DATA / "tasks.json"
HABITS = DATA / "habits.json"
CLIP = DATA / "clips.json"


def _start(cmd: str) -> str:
    try:
        if os.name == "nt":
            os.system(f"start \"\" {cmd}")
        else:
            subprocess.Popen(cmd, shell=True)
        return f"Started: {cmd}"
    except Exception as e:
        return f"Failed: {e}"


def _url(url: str) -> str:
    try:
        webbrowser.open(url)
        return f"Opened {url}"
    except Exception as e:
        return str(e)


def _ps(script: str) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=40,
        )
        return (r.stdout or r.stderr or "OK").strip()[:4000]
    except Exception as e:
        return str(e)


def _json_load(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _json_save(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


# ---------- custom data tools ----------
def add_note(text: str) -> str:
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    with NOTES.open("a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().isoformat(timespec='minutes')}\n{text}\n")
    return "Note saved"


def list_notes() -> str:
    if not NOTES.exists():
        return "No notes yet"
    return NOTES.read_text(encoding="utf-8")[-6000:]


def add_task(title: str) -> str:
    items = _json_load(TASKS, [])
    items.append({"title": title, "done": False, "t": time.time()})
    _json_save(TASKS, items)
    return f"Task added: {title}"


def list_tasks() -> str:
    items = _json_load(TASKS, [])
    if not items:
        return "No tasks"
    lines = []
    for i, t in enumerate(items, 1):
        mark = "x" if t.get("done") else " "
        lines.append(f"{i}. [{mark}] {t.get('title')}")
    return "\n".join(lines)


def complete_task(index: int) -> str:
    items = _json_load(TASKS, [])
    i = int(index) - 1
    if i < 0 or i >= len(items):
        return "Bad task number"
    items[i]["done"] = True
    _json_save(TASKS, items)
    return f"Completed: {items[i]['title']}"


def add_habit(name: str) -> str:
    h = _json_load(HABITS, {})
    h.setdefault(name, {"days": []})
    _json_save(HABITS, h)
    return f"Habit tracked: {name}"


def check_habit(name: str) -> str:
    h = _json_load(HABITS, {})
    day = datetime.now().date().isoformat()
    rec = h.setdefault(name, {"days": []})
    if day not in rec["days"]:
        rec["days"].append(day)
    _json_save(HABITS, h)
    return f"Checked {name} for {day} ({len(rec['days'])} days)"


def save_clip(text: str) -> str:
    clips = _json_load(CLIP, [])
    clips.append({"t": datetime.now().isoformat(), "text": text[:2000]})
    _json_save(CLIP, clips[-100:])
    return "Clip saved"


def list_clips() -> str:
    clips = _json_load(CLIP, [])
    return json.dumps(clips[-20:], indent=2)


def now_clock() -> str:
    return datetime.now().strftime("%A %Y-%m-%d %H:%M:%S")


def timer_seconds(seconds: int = 60) -> str:
    s = max(1, min(int(seconds), 3600))
    time.sleep(s)
    return f"Timer finished after {s}s"


def disk_free() -> str:
    usage = shutil.disk_usage(os.environ.get("SystemDrive", "C:\\"))
    gb = lambda n: round(n / (1024 ** 3), 1)
    return f"Disk total {gb(usage.total)} GB  used {gb(usage.used)} GB  free {gb(usage.free)} GB"


def env_summary() -> str:
    keys = ["USERNAME", "USERPROFILE", "COMPUTERNAME", "OS", "NUMBER_OF_PROCESSORS"]
    return "\n".join(f"{k}={os.environ.get(k, '?')}" for k in keys)


def list_desktop() -> str:
    d = Path.home() / "Desktop"
    if not d.exists():
        return "No Desktop folder"
    names = [p.name for p in d.iterdir()][:80]
    return "\n".join(names) or "Empty desktop"


def list_downloads() -> str:
    d = Path.home() / "Downloads"
    if not d.exists():
        return "No Downloads folder"
    files = sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:40]
    return "\n".join(p.name for p in files)


def open_path(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"Missing: {p}"
    return _start(f'"{p}"')


def make_folder(path: str) -> str:
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return f"Folder ready: {p}"


def write_text_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {p}"


def read_text_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"Missing: {p}"
    return p.read_text(encoding="utf-8", errors="replace")[:8000]


CUSTOM: Dict[str, Callable[..., Any]] = {
    "add_note": add_note,
    "list_notes": list_notes,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "add_habit": add_habit,
    "check_habit": check_habit,
    "save_clip": save_clip,
    "list_clips": list_clips,
    "now_clock": now_clock,
    "timer_seconds": timer_seconds,
    "disk_free": disk_free,
    "env_summary": env_summary,
    "list_desktop": list_desktop,
    "list_downloads": list_downloads,
    "open_path": open_path,
    "make_folder": make_folder,
    "write_text_file": write_text_file,
    "read_text_file": read_text_file,
}

# ---------- 180+ openers: sites, windows, apps ----------
SITES = [
    ("open_google", "https://www.google.com"),
    ("open_bing", "https://www.bing.com"),
    ("open_duckduckgo", "https://duckduckgo.com"),
    ("open_maps", "https://maps.google.com"),
    ("open_translate", "https://translate.google.com"),
    ("open_drive", "https://drive.google.com"),
    ("open_docs", "https://docs.google.com"),
    ("open_sheets", "https://sheets.google.com"),
    ("open_slides", "https://slides.google.com"),
    ("open_calendar_web", "https://calendar.google.com"),
    ("open_keep", "https://keep.google.com"),
    ("open_photos_web", "https://photos.google.com"),
    ("open_meet", "https://meet.google.com"),
    ("open_outlook_web", "https://outlook.live.com"),
    ("open_onedrive_web", "https://onedrive.live.com"),
    ("open_office_web", "https://www.office.com"),
    ("open_notion", "https://www.notion.so"),
    ("open_trello", "https://trello.com"),
    ("open_asana", "https://app.asana.com"),
    ("open_todoist", "https://todoist.com/app"),
    ("open_slack", "https://app.slack.com"),
    ("open_discord", "https://discord.com/app"),
    ("open_teams_web", "https://teams.microsoft.com"),
    ("open_zoom_web", "https://zoom.us"),
    ("open_telegram_web", "https://web.telegram.org"),
    ("open_messenger", "https://www.messenger.com"),
    ("open_tiktok", "https://www.tiktok.com"),
    ("open_pinterest", "https://www.pinterest.com"),
    ("open_snapchat_web", "https://web.snapchat.com"),
    ("open_threads", "https://www.threads.net"),
    ("open_medium", "https://medium.com"),
    ("open_substack", "https://substack.com"),
    ("open_devto", "https://dev.to"),
    ("open_stackoverflow", "https://stackoverflow.com"),
    ("open_github_new", "https://github.com/new"),
    ("open_gist", "https://gist.github.com"),
    ("open_gitlab", "https://gitlab.com"),
    ("open_bitbucket", "https://bitbucket.org"),
    ("open_huggingface", "https://huggingface.co"),
    ("open_kaggle", "https://www.kaggle.com"),
    ("open_colab", "https://colab.research.google.com"),
    ("open_replit", "https://replit.com"),
    ("open_codesandbox", "https://codesandbox.io"),
    ("open_codepen", "https://codepen.io"),
    ("open_jsfiddle", "https://jsfiddle.net"),
    ("open_npm", "https://www.npmjs.com"),
    ("open_pypi", "https://pypi.org"),
    ("open_dockerhub", "https://hub.docker.com"),
    ("open_aws_console", "https://console.aws.amazon.com"),
    ("open_azure_portal", "https://portal.azure.com"),
    ("open_gcp_console", "https://console.cloud.google.com"),
    ("open_digitalocean", "https://cloud.digitalocean.com"),
    ("open_cloudflare_dash", "https://dash.cloudflare.com"),
    ("open_netlify", "https://app.netlify.com"),
    ("open_railway", "https://railway.app"),
    ("open_render", "https://dashboard.render.com"),
    ("open_heroku", "https://dashboard.heroku.com"),
    ("open_supabase", "https://supabase.com/dashboard"),
    ("open_firebase", "https://console.firebase.google.com"),
    ("open_stripe", "https://dashboard.stripe.com"),
    ("open_paypal", "https://www.paypal.com"),
    ("open_paystack", "https://dashboard.paystack.com"),
    ("open_flutterwave", "https://dashboard.flutterwave.com"),
    ("open_shopify", "https://www.shopify.com/admin"),
    ("open_amazon", "https://www.amazon.com"),
    ("open_ebay", "https://www.ebay.com"),
    ("open_aliexpress", "https://www.aliexpress.com"),
    ("open_jumia", "https://www.jumia.com.ng"),
    ("open_konga", "https://www.konga.com"),
    ("open_jiji", "https://jiji.ng"),
    ("open_canva", "https://www.canva.com"),
    ("open_figma", "https://www.figma.com"),
    ("open_photopea", "https://www.photopea.com"),
    ("open_removebg", "https://www.remove.bg"),
    ("open_capcut", "https://www.capcut.com"),
    ("open_spotify_web", "https://open.spotify.com"),
    ("open_soundcloud", "https://soundcloud.com"),
    ("open_apple_music", "https://music.apple.com"),
    ("open_netflix", "https://www.netflix.com"),
    ("open_prime_video", "https://www.primevideo.com"),
    ("open_disney", "https://www.disneyplus.com"),
    ("open_twitch", "https://www.twitch.tv"),
    ("open_wikipedia", "https://www.wikipedia.org"),
    ("open_wolfram", "https://www.wolframalpha.com"),
    ("open_archive", "https://archive.org"),
    ("open_wayback", "https://web.archive.org"),
    ("open_news_google", "https://news.google.com"),
    ("open_bbc", "https://www.bbc.com"),
    ("open_cnn", "https://www.cnn.com"),
    ("open_reuters", "https://www.reuters.com"),
    ("open_techcrunch", "https://techcrunch.com"),
    ("open_theverge", "https://www.theverge.com"),
    ("open_hn", "https://news.ycombinator.com"),
    ("open_producthunt", "https://www.producthunt.com"),
    ("open_linkedin_jobs", "https://www.linkedin.com/jobs"),
    ("open_indeed", "https://www.indeed.com"),
    ("open_upwork", "https://www.upwork.com"),
    ("open_fiverr", "https://www.fiverr.com"),
    ("open_freelancer", "https://www.freelancer.com"),
    ("open_coursera", "https://www.coursera.org"),
    ("open_udemy", "https://www.udemy.com"),
    ("open_khan", "https://www.khanacademy.org"),
    ("open_duolingo", "https://www.duolingo.com"),
    ("open_chatgpt_web", "https://chatgpt.com"),
    ("open_claude_web", "https://claude.ai"),
    ("open_gemini_web", "https://gemini.google.com"),
    ("open_grok_web", "https://grok.com"),
    ("open_perplexity", "https://www.perplexity.ai"),
    ("open_weather", "https://weather.com"),
    ("open_timeanddate", "https://www.timeanddate.com"),
    ("open_speedtest", "https://www.speedtest.net"),
    ("open_downdetector", "https://downdetector.com"),
    ("open_whois", "https://who.is"),
    ("open_namecheap_search", "https://www.namecheap.com/domains/domain-name-search/"),
    ("open_godaddy_search", "https://www.godaddy.com/domainsearch"),
    ("open_fontawesome", "https://fontawesome.com"),
    ("open_google_fonts", "https://fonts.google.com"),
    ("open_unsplash", "https://unsplash.com"),
    ("open_pexels", "https://www.pexels.com"),
    ("open_iconify", "https://icon-sets.iconify.design"),
    ("open_colorhunt", "https://colorhunt.co"),
    ("open_coolors", "https://coolors.co"),
    ("open_regex101", "https://regex101.com"),
    ("open_jsonlint", "https://jsonlint.com"),
    ("open_jwt_io", "https://jwt.io"),
    ("open_excalidraw", "https://excalidraw.com"),
    ("open_miro", "https://miro.com"),
    ("open_obsidian_help", "https://help.obsidian.md"),
    ("open_mdn", "https://developer.mozilla.org"),
    ("open_w3schools", "https://www.w3schools.com"),
    ("open_leetcode", "https://leetcode.com"),
    ("open_hackerrank", "https://www.hackerrank.com"),
    ("open_codewars", "https://www.codewars.com"),
    ("open_fitness_web", "https://www.nike.com/ntc-app"),
    ("open_myfitnesspal", "https://www.myfitnesspal.com"),
    ("open_strava", "https://www.strava.com"),
    ("open_youtube_music", "https://music.youtube.com"),
    ("open_youtube_studio", "https://studio.youtube.com"),
    ("open_analytics", "https://analytics.google.com"),
    ("open_search_console", "https://search.google.com/search-console"),
    ("open_adsense", "https://www.google.com/adsense"),
    ("open_mailchimp", "https://mailchimp.com"),
    ("open_convertkit", "https://app.convertkit.com"),
]

WIN_URI = [
    ("open_windows_settings", "ms-settings:"),
    ("open_wifi_settings", "ms-settings:network-wifi"),
    ("open_bluetooth_settings", "ms-settings:bluetooth"),
    ("open_display_settings", "ms-settings:display"),
    ("open_sound_settings", "ms-settings:sound"),
    ("open_privacy_settings", "ms-settings:privacy"),
    ("open_camera_privacy", "ms-settings:privacy-webcam"),
    ("open_mic_privacy", "ms-settings:privacy-microphone"),
    ("open_update_settings", "ms-settings:windowsupdate"),
    ("open_apps_settings", "ms-settings:appsfeatures"),
    ("open_storage_settings", "ms-settings:storagesense"),
    ("open_power_settings", "ms-settings:powersleep"),
    ("open_time_settings", "ms-settings:dateandtime"),
    ("open_language_settings", "ms-settings:regionlanguage"),
    ("open_accounts_settings", "ms-settings:yourinfo"),
    ("open_backup_settings", "ms-settings:backup"),
    ("open_theme_settings", "ms-settings:personalization-background"),
    ("open_taskbar_settings", "ms-settings:taskbar"),
    ("open_nightlight_settings", "ms-settings:nightlight"),
    ("open_focus_settings", "ms-settings:quiethours"),
    ("open_gaming_settings", "ms-settings:gaming-gamebar"),
    ("open_printer_settings", "ms-settings:printers"),
    ("open_keyboard_settings", "ms-settings:easeofaccess-keyboard"),
    ("open_mouse_settings", "ms-settings:mousetouchpad"),
    ("open_about_pc", "ms-settings:about"),
    ("open_activation", "ms-settings:activation"),
    ("open_developer_settings", "ms-settings:developers"),
]

WIN_EXE = [
    ("open_task_manager", "taskmgr"),
    ("open_control_panel", "control"),
    ("open_device_manager", "devmgmt.msc"),
    ("open_disk_mgmt", "diskmgmt.msc"),
    ("open_services", "services.msc"),
    ("open_event_viewer", "eventvwr.msc"),
    ("open_regedit", "regedit"),
    ("open_msconfig", "msconfig"),
    ("open_resource_monitor", "resmon"),
    ("open_perfmon", "perfmon"),
    ("open_snipping_tool", "snippingtool"),
    ("open_paint", "mspaint"),
    ("open_wordpad", "wordpad"),
    ("open_cmd", "cmd"),
    ("open_powershell", "powershell"),
    ("open_wt", "wt"),
    ("open_calc", "calc"),
    ("open_notepad_plus", "notepad"),
    ("open_char_map", "charmap"),
    ("open_magnifier", "magnify"),
    ("open_osk", "osk"),
    ("open_recycle_bin_explorer", "shell:RecycleBinFolder"),
    ("open_startup_folder", "shell:startup"),
    ("open_sendto_folder", "shell:sendto"),
    ("open_fonts_folder", "shell:Fonts"),
    ("open_pictures", "shell:My Pictures"),
    ("open_videos", "shell:My Video"),
    ("open_music", "shell:My Music"),
    ("open_documents", "shell:Personal"),
]

PS_CMDS = [
    ("empty_recycle_bin_safe", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; 'Recycle Bin cleared'"),
    ("list_startup_apps", "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command | Format-Table -AutoSize | Out-String"),
    ("list_printers", "Get-Printer | Select-Object Name,DriverName | Format-Table -AutoSize | Out-String"),
    ("list_hotspot_adapters", "Get-NetAdapter | Select-Object Name,Status,MacAddress | Format-Table -AutoSize | Out-String"),
    ("ip_config_brief", "Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress | Format-Table -AutoSize | Out-String"),
    ("dns_flush", "Clear-DnsClientCache; 'DNS cache flushed'"),
    ("list_large_temp", "Get-ChildItem $env:TEMP -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 15 Name,Length | Format-Table -AutoSize | Out-String"),
    ("battery_report_text", "(Get-WmiObject Win32_Battery | Select-Object EstimatedChargeRemaining,BatteryStatus | Format-List | Out-String)"),
    ("uptime_info", "(get-date) - (gcim Win32_OperatingSystem).LastBootUpTime | Out-String"),
    ("list_users_local", "Get-LocalUser | Select-Object Name,Enabled | Format-Table -AutoSize | Out-String"),
]

TOOL_FUNCTIONS: Dict[str, Callable[..., Any]] = dict(CUSTOM)
MEGA_TOOLS: List[dict] = []


def _reg(name: str, desc: str, fn: Callable, props: dict | None = None, required: list | None = None):
    TOOL_FUNCTIONS[name] = fn
    MEGA_TOOLS.append({
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": props or {}, "required": required or []},
        },
    })


for name, fn in CUSTOM.items():
    # already in TOOL_FUNCTIONS; add schema
    import inspect
    sig = inspect.signature(fn)
    props, req = {}, []
    for p, prm in sig.parameters.items():
        props[p] = {"type": "string" if prm.annotation in (str, inspect._empty) else "integer"}
        if prm.default is inspect._empty:
            req.append(p)
    MEGA_TOOLS.append({
        "type": "function",
        "function": {
            "name": name,
            "description": f"JagX feature: {name.replace('_', ' ')}",
            "parameters": {"type": "object", "properties": props, "required": req},
        },
    })

for name, url in SITES:
    _reg(name, f"Open {url}", lambda u=url: _url(u))

for name, uri in WIN_URI:
    _reg(name, f"Open Windows panel {uri}", lambda u=uri: _start(u))

for name, exe in WIN_EXE:
    _reg(name, f"Launch {exe}", lambda e=exe: _start(e))

for name, script in PS_CMDS:
    _reg(name, f"Windows info/action: {name.replace('_', ' ')}", lambda s=script: _ps(s))


def mega_feature_count() -> str:
    return f"Mega pack tools: {len(TOOL_FUNCTIONS)}"


_reg("mega_feature_count", "How many mega features are loaded", mega_feature_count)
