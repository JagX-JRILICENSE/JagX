"""Additional free local desktop, file, media and productivity capabilities for JagX."""
from __future__ import annotations
import ctypes, hashlib, os, platform, shutil, subprocess, time, zipfile
from pathlib import Path

def _ps(script):
    try: return subprocess.check_output(["powershell","-NoProfile","-Command",script],text=True,stderr=subprocess.STDOUT,timeout=20).strip()
    except Exception as e: return f"Unavailable: {e}"
def _hotkey(*keys):
    try:
        import pyautogui; pyautogui.hotkey(*keys); return f"Pressed {'+'.join(keys)}."
    except Exception as e:return f"Keyboard action failed: {e}"
def active_window(): return _ps("(Get-Process | Where-Object {$_.MainWindowHandle -ne 0} | Select-Object -First 1).MainWindowTitle")
def volume_up(steps=2): return _hotkey(*(["volumeup"]*max(1,int(steps))))
def volume_down(steps=2): return _hotkey(*(["volumedown"]*max(1,int(steps))))
def volume_mute(): return _hotkey("volumemute")
def play_pause(): return _hotkey("playpause")
def next_track(): return _hotkey("nexttrack")
def previous_track(): return _hotkey("prevtrack")
def minimize_window(): return _hotkey("win","down")
def maximize_window(): return _hotkey("win","up")
def show_desktop(): return _hotkey("win","d")
def switch_window(): return _hotkey("alt","tab")
def close_active_window(): return _hotkey("alt","f4")
def task_view(): return _hotkey("win","tab")
def open_notifications(): return _hotkey("win","n")
def open_quick_settings(): return _hotkey("win","a")
def open_file_search(): return _hotkey("win","e")
def open_system_search(): return _hotkey("win","s")
def open_clipboard_history(): return _hotkey("win","v")
def open_emoji_panel(): return _hotkey("win",".")
def open_desktop(): return _hotkey("win","d")
def take_screenshot(path="data/screenshots/jagx_screen.png"):
    try:
        import pyautogui
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); pyautogui.screenshot().save(p); return f"Screenshot saved: {p}"
    except Exception as e:return f"Screenshot failed: {e}"
def take_region_screenshot(x,y,width,height,path="data/screenshots/jagx_region.png"):
    try:
        import pyautogui
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); pyautogui.screenshot(region=(int(x),int(y),int(width),int(height))).save(p); return f"Region screenshot saved: {p}"
    except Exception as e:return f"Region screenshot failed: {e}"
def file_hash(path,algorithm="sha256"):
    try:
        h=hashlib.new(algorithm.lower());
        with open(Path(path).expanduser(),"rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
        return h.hexdigest()
    except Exception as e:return f"Hash failed: {e}"
def count_files(path="."):
    try:return str(sum(1 for p in Path(path).expanduser().rglob("*") if p.is_file()))
    except Exception as e:return f"Count failed: {e}"
def find_text(path,text,limit=50):
    out=[]
    try:
        for p in Path(path).expanduser().rglob("*"):
            if len(out)>=int(limit):break
            if p.is_file() and p.stat().st_size<5_000_000:
                try:
                    if text.lower() in p.read_text(errors="ignore").lower():out.append(str(p))
                except Exception:pass
        return "\n".join(out) or "No matching files."
    except Exception as e:return f"Search failed: {e}"
def recent_files(path=None,limit=20):
    try:
        root=Path(path or Path.home()).expanduser(); items=[p for p in root.rglob("*") if p.is_file()]; items.sort(key=lambda p:p.stat().st_mtime,reverse=True); return "\n".join(str(p) for p in items[:int(limit)]) or "No files found."
    except Exception as e:return f"Recent files unavailable: {e}"
def zip_path(source,destination):
    try:
        src=Path(source).expanduser(); dst=Path(destination).expanduser(); dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.make_archive(str(dst.with_suffix("")),"zip",root_dir=src if src.is_dir() else src.parent,base_dir=src.name); return f"Created archive: {dst.with_suffix('.zip')}"
    except Exception as e:return f"Archive failed: {e}"
def unzip_path(archive,destination):
    try:
        dst=Path(destination).expanduser(); dst.mkdir(parents=True,exist_ok=True); zipfile.ZipFile(Path(archive).expanduser()).extractall(dst); return f"Extracted archive to: {dst}"
    except Exception as e:return f"Extract failed: {e}"
def open_url(url):
    try:
        import webbrowser; webbrowser.open(url); return f"Opened URL: {url}"
    except Exception as e:return f"URL open failed: {e}"
def copy_file_path(source,destination):
    try:
        src,dst=Path(source).expanduser(),Path(destination).expanduser(); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); return f"Copied file to: {dst}"
    except Exception as e:return f"Copy failed: {e}"
def backup_file(path):
    try:
        src=Path(path).expanduser(); dst=src.with_name(src.name+".bak"); shutil.copy2(src,dst); return f"Backup created: {dst}"
    except Exception as e:return f"Backup failed: {e}"
def compare_files(a,b):
    try:return "Files identical." if Path(a).expanduser().read_bytes()==Path(b).expanduser().read_bytes() else "Files differ."
    except Exception as e:return f"Comparison failed: {e}"
def append_text_file(path,text):
    try:
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); p.open("a",encoding="utf-8").write(text); return f"Appended text to: {p}"
    except Exception as e:return f"Append failed: {e}"
def prepend_text_file(path,text):
    try:
        p=Path(path).expanduser(); old=p.read_text(encoding="utf-8") if p.exists() else ""; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text+old,encoding="utf-8"); return f"Prepended text to: {p}"
    except Exception as e:return f"Prepend failed: {e}"
def make_empty_file(path):
    try:
        p=Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); p.touch(); return f"Created file: {p}"
    except Exception as e:return f"Create failed: {e}"
def file_modified_time(path):
    try:return time.ctime(Path(path).expanduser().stat().st_mtime)
    except Exception as e:return f"Time unavailable: {e}"
def file_permissions(path):
    try:return oct(Path(path).expanduser().stat().st_mode & 0o777)
    except Exception as e:return f"Permissions unavailable: {e}"
def set_file_permissions(path,mode="644"):
    try:
        p=Path(path).expanduser(); os.chmod(p,int(str(mode),8)); return f"Permissions set to {mode}."
    except Exception as e:return f"Permission change failed: {e}"
def cpu_temperature(): return _ps("Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select CurrentTemperature | Format-Table -AutoSize | Out-String")
def windows_theme(): return _ps("Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name AppsUseLightTheme | Select -Expand AppsUseLightTheme")
def toggle_windows_theme(): return _ps("$p='HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'; $v=(Get-ItemProperty $p -Name AppsUseLightTheme).AppsUseLightTheme; Set-ItemProperty $p -Name AppsUseLightTheme -Value (1-$v); Set-ItemProperty $p -Name SystemUsesLightTheme -Value (1-$v); 'Theme toggled.'")
def screen_timeout(): return _ps("powercfg /query SCHEME_CURRENT SUB_VIDEO VIDEOIDLE")
def power_plan(): return _ps("powercfg /getactivescheme")
def list_startup_items(): return _ps("Get-CimInstance Win32_StartupCommand | Select Name,Command,Location | Format-Table -AutoSize | Out-String")
def list_windows_users(): return _ps("Get-LocalUser | Select Name,Enabled,LastLogon | Format-Table -AutoSize | Out-String")
def active_network_profile(): return _ps("Get-NetConnectionProfile | Select Name,InterfaceAlias,NetworkCategory,IPv4Connectivity | Format-Table -AutoSize | Out-String")
def default_browser(): return _ps("(Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice' -ErrorAction SilentlyContinue).ProgId")
def installed_app_count(): return _ps("$a=Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue; $b=Get-ItemProperty 'HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -ErrorAction SilentlyContinue; @($a+$b | Where DisplayName).Count")
def clear_temp_files():
    try:
        t=Path(os.getenv("TEMP",Path.home()/"AppData/Local/Temp")); n=0
        for p in t.iterdir():
            try:
                if p.is_file(): p.unlink(); n+=1
                elif p.is_dir(): shutil.rmtree(p,ignore_errors=True); n+=1
            except Exception: pass
        return f"Temporary cleanup attempted; removed {n} items."
    except Exception as e:return f"Temp cleanup failed: {e}"
def launch_startup_folder():
    p=Path(os.getenv("APPDATA",Path.home()))/"Microsoft/Windows/Start Menu/Programs/Startup"
    try: os.startfile(p); return f"Opened Startup folder: {p}"
    except Exception as e:return f"Startup folder failed: {e}"
def launch_task_scheduler():
    try: subprocess.Popen(["taskschd.msc"],shell=True); return "Task Scheduler opened."
    except Exception as e:return f"Task Scheduler failed: {e}"
def launch_services():
    try: subprocess.Popen(["services.msc"],shell=True); return "Services manager opened."
    except Exception as e:return f"Services manager failed: {e}"
def launch_device_manager():
    try: subprocess.Popen(["devmgmt.msc"],shell=True); return "Device Manager opened."
    except Exception as e:return f"Device Manager failed: {e}"
def launch_disk_management():
    try: subprocess.Popen(["diskmgmt.msc"],shell=True); return "Disk Management opened."
    except Exception as e:return f"Disk Management failed: {e}"
def launch_event_viewer():
    try: subprocess.Popen(["eventvwr.msc"],shell=True); return "Event Viewer opened."
    except Exception as e:return f"Event Viewer failed: {e}"
def open_start_menu(): return _hotkey("win")
def open_action_center(): return _hotkey("win","a")
def open_run(): return _hotkey("win","r")
def open_task_manager_shortcut(): return _hotkey("ctrl","shift","esc")
def lock_screen(): return _hotkey("win","l")
def show_window_menu(): return _hotkey("alt","space")
def move_cursor_to(x,y):
    try:
        import pyautogui; pyautogui.moveTo(int(x),int(y),duration=0.25); return f"Cursor moved to ({x},{y})."
    except Exception as e:return f"Cursor move failed: {e}"
def click_cursor(x=None,y=None,button="left"):
    try:
        import pyautogui; pyautogui.click(x=x,y=y,button=button); return f"Clicked {button}."
    except Exception as e:return f"Click failed: {e}"

def _defs():
    specs=[
("active_window","Get active-window information",active_window,{}),("volume_up","Increase system volume",volume_up,{"steps":{"type":"integer","default":2}}),("volume_down","Decrease system volume",volume_down,{"steps":{"type":"integer","default":2}}),("volume_mute","Mute or unmute system audio",volume_mute,{}),("play_pause","Play or pause media",play_pause,{}),("next_track","Skip to next media track",next_track,{}),("previous_track","Go to previous media track",previous_track,{}),("minimize_window","Minimize active window",minimize_window,{}),("maximize_window","Maximize active window",maximize_window,{}),("show_desktop","Show desktop",show_desktop,{}),("switch_window","Switch active window",switch_window,{}),("close_active_window","Close active window",close_active_window,{}),("task_view","Open Windows Task View",task_view,{}),("open_notifications","Open Windows notifications",open_notifications,{}),("open_quick_settings","Open Windows quick settings",open_quick_settings,{}),("open_file_search","Open File Explorer",open_file_search,{}),("open_system_search","Open Windows Search",open_system_search,{}),("open_clipboard_history","Open clipboard history",open_clipboard_history,{}),("open_emoji_panel","Open emoji panel",open_emoji_panel,{}),("open_desktop","Show desktop",open_desktop,{}),("take_screenshot","Capture full screen",take_screenshot,{"path":{"type":"string","default":"data/screenshots/jagx_screen.png"}}),("take_region_screenshot","Capture screen region",take_region_screenshot,{"x":{"type":"integer"},"y":{"type":"integer"},"width":{"type":"integer"},"height":{"type":"integer"},"path":{"type":"string","default":"data/screenshots/jagx_region.png"}}),("file_hash","Calculate a file hash",file_hash,{"path":{"type":"string"},"algorithm":{"type":"string","default":"sha256"}}),("count_files","Count files below a folder",count_files,{"path":{"type":"string","default":"."}}),("find_text","Search text inside local files",find_text,{"path":{"type":"string"},"text":{"type":"string"},"limit":{"type":"integer","default":50}}),("recent_files","List recently modified files",recent_files,{"path":{"type":"string"},"limit":{"type":"integer","default":20}}),("zip_path","Create a ZIP archive",zip_path,{"source":{"type":"string"},"destination":{"type":"string"}}),("unzip_path","Extract a ZIP archive",unzip_path,{"archive":{"type":"string"},"destination":{"type":"string"}}),("open_url","Open a URL",open_url,{"url":{"type":"string"}}),("copy_file_path","Copy a file",copy_file_path,{"source":{"type":"string"},"destination":{"type":"string"}}),("backup_file","Create a .bak backup",backup_file,{"path":{"type":"string"}}),("compare_files","Compare two files",compare_files,{"a":{"type":"string"},"b":{"type":"string"}}),("append_text_file","Append text to a file",append_text_file,{"path":{"type":"string"},"text":{"type":"string"}}),("prepend_text_file","Prepend text to a file",prepend_text_file,{"path":{"type":"string"},"text":{"type":"string"}}),("make_empty_file","Create an empty file",make_empty_file,{"path":{"type":"string"}}),("file_modified_time","Get file modification time",file_modified_time,{"path":{"type":"string"}}),("file_permissions","Get file permissions",file_permissions,{"path":{"type":"string"}}),("set_file_permissions","Set file permissions",set_file_permissions,{"path":{"type":"string"},"mode":{"type":"string","default":"644"}}),("cpu_temperature","Read available CPU thermal sensors",cpu_temperature,{}),("windows_theme","Get Windows app theme state",windows_theme,{}),("toggle_windows_theme","Toggle Windows light/dark theme",toggle_windows_theme,{}),("screen_timeout","Show display idle power settings",screen_timeout,{}),("power_plan","Show active Windows power plan",power_plan,{}),("list_startup_items","List Windows startup entries",list_startup_items,{}),("list_windows_users","List local Windows user accounts",list_windows_users,{}),("active_network_profile","Show active network profile",active_network_profile,{}),("default_browser","Show default browser identifier",default_browser,{}),("installed_app_count","Count installed applications",installed_app_count,{}),("clear_temp_files","Clean temporary files",clear_temp_files,{}),("launch_startup_folder","Open Startup folder",launch_startup_folder,{}),("launch_task_scheduler","Open Task Scheduler",launch_task_scheduler,{}),("launch_services","Open Services manager",launch_services,{}),("launch_device_manager","Open Device Manager",launch_device_manager,{}),("launch_disk_management","Open Disk Management",launch_disk_management,{}),("launch_event_viewer","Open Event Viewer",launch_event_viewer,{}),("open_start_menu","Open Start menu",open_start_menu,{}),("open_action_center","Open Windows quick settings",open_action_center,{}),("open_run","Open Run shortcut",open_run,{}),("open_task_manager_shortcut","Open Task Manager shortcut",open_task_manager_shortcut,{}),("lock_screen","Lock Windows",lock_screen,{}),("show_window_menu","Open active window menu",show_window_menu,{}),("move_cursor_to","Move the visible mouse cursor",move_cursor_to,{"x":{"type":"integer"},"y":{"type":"integer"}}),("click_cursor","Click the visible mouse cursor",click_cursor,{"x":{"type":"integer"},"y":{"type":"integer"},"button":{"type":"string","default":"left"}})]
    defs=[]
    for n,d,f,p in specs: defs.append({"type":"function","function":{"name":n,"description":d,"parameters":{"type":"object","properties":p,"required":[k for k,v in p.items() if "default" not in v]}}})
    return defs,{n:f for n,d,f,p in specs}
SYSTEM_PLUS2_TOOLS,TOOL_FUNCTIONS=_defs()
