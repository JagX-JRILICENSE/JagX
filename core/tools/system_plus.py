"""Fifty lightweight local Windows utility capabilities for JagX."""
from __future__ import annotations
import os, platform, shutil, socket, subprocess, time
from pathlib import Path

def _run(cmd):
    try: return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=15).strip()
    except Exception as e: return f"Unavailable: {e}"
def system_info(): return f"{platform.system()} {platform.release()} ({platform.version()}); machine={platform.machine()}; processor={platform.processor()}"
def hostname(): return socket.gethostname()
def current_user():
    try: return os.getlogin()
    except Exception: return os.getenv("USERNAME") or os.getenv("USER") or "unknown"
def working_directory(): return str(Path.cwd())
def home_directory(): return str(Path.home())
def current_time(): return time.strftime("%Y-%m-%d %H:%M:%S")
def uptime(): return _run(["powershell","-NoProfile","-Command","(Get-CimInstance Win32_OperatingSystem).LastBootUpTime"])
def disk_usage(path=None):
    path = path or ("C:\\" if platform.system()=="Windows" else "/")
    try:
        d=shutil.disk_usage(path); return f"{path}: {d.used/2**30:.1f} GB used / {d.total/2**30:.1f} GB total ({d.free/2**30:.1f} GB free)"
    except Exception as e:return f"Disk info failed: {e}"
def path_exists(path): return str(Path(path).expanduser().exists())
def file_size(path):
    try:return f"{Path(path).expanduser().stat().st_size} bytes"
    except Exception as e:return f"Size unavailable: {e}"
def list_drives(): return _run(["powershell","-NoProfile","-Command","Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free | Format-Table -AutoSize | Out-String"])
def wifi_status(): return _run(["netsh","wlan","show","interfaces"])
def ip_addresses(): return _run(["powershell","-NoProfile","-Command","Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias | Format-Table -AutoSize | Out-String"])
def network_adapters(): return _run(["powershell","-NoProfile","-Command","Get-NetAdapter | Select-Object Name,Status,LinkSpeed | Format-Table -AutoSize | Out-String"])
def ping_host(host="8.8.8.8"): return _run(["ping","-n","1",host])
def dns_lookup(host): return _run(["nslookup",host])
def battery_status(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_Battery | Select-Object BatteryStatus,EstimatedChargeRemaining,EstimatedRunTime | Format-List | Out-String"])
def display_resolution(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_VideoController | Select-Object CurrentHorizontalResolution,CurrentVerticalResolution | Format-Table | Out-String"])
def gpu_info(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion | Format-Table -AutoSize | Out-String"])
def cpu_info(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Format-List | Out-String"])
def ram_info(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | Format-List | Out-String"])
def os_info(): return _run(["powershell","-NoProfile","-Command","Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,LastBootUpTime | Format-List | Out-String"])
def process_count(): return _run(["powershell","-NoProfile","-Command","(Get-Process).Count"])
def top_processes(): return _run(["powershell","-NoProfile","-Command","Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name,Id,CPU | Format-Table -AutoSize | Out-String"])
def services_summary(): return _run(["powershell","-NoProfile","-Command","Get-Service | Group-Object Status | Select Name,Count | Format-Table | Out-String"])
def firewall_status(): return _run(["powershell","-NoProfile","-Command","Get-NetFirewallProfile | Select Name,Enabled | Format-Table | Out-String"])
def windows_version(): return _run(["cmd","/c","ver"])
def environment_value(name):
    if name.upper() in {"PASSWORD","PASS","TOKEN","SECRET","API_KEY","APIKEY","AUTH"}: return "Blocked: sensitive environment variable."
    return os.getenv(name,"<not set>")
def python_version(): return platform.python_version()
def jagx_version(): return "0.5.0-dev"
def temp_directory(): return os.getenv("TEMP") or os.getenv("TMP") or "/tmp"
def desktop_directory(): return str(Path.home()/"Desktop")
def downloads_directory(): return str(Path.home()/"Downloads")
def documents_directory(): return str(Path.home()/"Documents")
def pictures_directory(): return str(Path.home()/"Pictures")
def videos_directory(): return str(Path.home()/"Videos")
def music_directory(): return str(Path.home()/"Music")
def open_folder(path):
    p=str(Path(path).expanduser())
    if platform.system()=="Windows": os.startfile(p)
    return f"Opened folder: {p}"
def open_control_panel():
    if platform.system()=="Windows": subprocess.Popen(["control"])
    return "Control Panel opened."
def open_task_manager():
    if platform.system()=="Windows": subprocess.Popen(["taskmgr"])
    return "Task Manager opened."
def open_settings():
    if platform.system()=="Windows": subprocess.Popen(["cmd","/c","start","ms-settings:"])
    return "Windows Settings opened."
def open_run_dialog():
    if platform.system()=="Windows": subprocess.Popen(["explorer.exe","shell:::{2559a1f3-21d7-11d4-bdaf-00c04f60b9f0}"])
    return "Run dialog requested."
def lock_workstation():
    if platform.system()=="Windows": subprocess.Popen(["rundll32.exe","user32.dll,LockWorkStation"])
    return "Workstation lock requested."
def empty_recycle_bin():
    if platform.system()=="Windows": subprocess.Popen(["powershell","-NoProfile","-Command","Clear-RecycleBin -Force"])
    return "Recycle Bin cleanup requested."
def copy_text_to_clipboard(text):
    try:
        import pyperclip; pyperclip.copy(text); return "Text copied to clipboard."
    except Exception as e:return f"Clipboard failed: {e}"
def get_clipboard_text():
    try:
        import pyperclip; return pyperclip.paste()
    except Exception as e:return f"Clipboard unavailable: {e}"
def mouse_position():
    try:
        import pyautogui; return str(pyautogui.position())
    except Exception as e:return f"Mouse position unavailable: {e}"
def screen_size():
    try:
        import pyautogui; return str(pyautogui.size())
    except Exception as e:return f"Screen size unavailable: {e}"
def scroll_mouse(clicks=3):
    try:
        import pyautogui; pyautogui.scroll(int(clicks)); return f"Scrolled {clicks} clicks."
    except Exception as e:return f"Scroll failed: {e}"
def double_click(x=None,y=None):
    try:
        import pyautogui; pyautogui.doubleClick(x=x,y=y); return "Double-click completed."
    except Exception as e:return f"Double-click failed: {e}"
def drag_mouse(x,y,duration=0.5):
    try:
        import pyautogui; pyautogui.dragTo(x,y,duration=duration); return f"Dragged cursor to ({x},{y})."
    except Exception as e:return f"Drag failed: {e}"

def _defs():
    specs=[
("system_info","Get Windows/system information",system_info,{}),("hostname","Get computer hostname",hostname,{}),("current_user","Get current local username",current_user,{}),("working_directory","Get JagX working directory",working_directory,{}),("home_directory","Get user home directory",home_directory,{}),("current_time","Get local computer time",current_time,{}),("uptime","Get system uptime",uptime,{}),("disk_usage","Get disk usage for a path",disk_usage,{"path":{"type":"string"}}),("path_exists","Check whether a path exists",path_exists,{"path":{"type":"string"}}),("file_size","Get file size",file_size,{"path":{"type":"string"}}),("list_drives","List filesystem drives",list_drives,{}),("wifi_status","Show Wi-Fi interface status",wifi_status,{}),("ip_addresses","Show local IPv4 addresses",ip_addresses,{}),("network_adapters","Show network adapter status",network_adapters,{}),("ping_host","Ping a host",ping_host,{"host":{"type":"string"}}),("dns_lookup","Resolve a hostname",dns_lookup,{"host":{"type":"string"}}),("battery_status","Show battery status",battery_status,{}),("display_resolution","Show display resolution",display_resolution,{}),("gpu_info","Show graphics adapter information",gpu_info,{}),("cpu_info","Show CPU information",cpu_info,{}),("ram_info","Show installed RAM information",ram_info,{}),("os_info","Show Windows OS information",os_info,{}),("process_count","Count running processes",process_count,{}),("top_processes","Show top processes by CPU",top_processes,{}),("services_summary","Summarize Windows services",services_summary,{}),("firewall_status","Show Windows firewall profile status",firewall_status,{}),("windows_version","Show Windows version",windows_version,{}),("environment_value","Read a non-secret environment variable",environment_value,{"name":{"type":"string"}}),("python_version","Show Python version",python_version,{}),("jagx_version","Show JagX version",jagx_version,{}),("temp_directory","Get Windows temp directory",temp_directory,{}),("desktop_directory","Get Desktop directory",desktop_directory,{}),("downloads_directory","Get Downloads directory",downloads_directory,{}),("documents_directory","Get Documents directory",documents_directory,{}),("pictures_directory","Get Pictures directory",pictures_directory,{}),("videos_directory","Get Videos directory",videos_directory,{}),("music_directory","Get Music directory",music_directory,{}),("open_folder","Open a folder in Explorer",open_folder,{"path":{"type":"string"}}),("open_control_panel","Open Control Panel",open_control_panel,{}),("open_task_manager","Open Task Manager",open_task_manager,{}),("open_settings","Open Windows Settings",open_settings,{}),("open_run_dialog","Open Windows Run dialog",open_run_dialog,{}),("lock_workstation","Lock the workstation",lock_workstation,{}),("empty_recycle_bin","Empty the Windows Recycle Bin",empty_recycle_bin,{}),("copy_text_to_clipboard","Copy text to clipboard",copy_text_to_clipboard,{"text":{"type":"string"}}),("get_clipboard_text","Read clipboard text",get_clipboard_text,{}),("mouse_position","Get current cursor position",mouse_position,{}),("screen_size","Get screen dimensions",screen_size,{}),("scroll_mouse","Scroll the mouse wheel",scroll_mouse,{"clicks":{"type":"integer","default":3}}),("double_click","Double-click at a screen position",double_click,{"x":{"type":"integer"},"y":{"type":"integer"}}),("drag_mouse","Drag the cursor to a screen position",drag_mouse,{"x":{"type":"integer"},"y":{"type":"integer"},"duration":{"type":"number","default":0.5}})]
    defs=[]
    for name,desc,fn,props in specs: defs.append({"type":"function","function":{"name":name,"description":desc,"parameters":{"type":"object","properties":props,"required":[k for k,v in props.items() if "default" not in v]}}})
    return defs,{name:fn for name,_,fn,_ in specs}
SYSTEM_PLUS_TOOLS,TOOL_FUNCTIONS=_defs()
