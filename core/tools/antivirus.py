"""
JagX Virus Guard — Windows Defender powered protection.
Scan files/folders, check status, remove threats, update signatures.
JRILICENSE
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _ps(script: str, timeout: int = 600) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = ((r.stdout or "") + ("\n" + r.stderr if r.stderr else "")).strip()
        return out[:8000] if out else "OK"
    except subprocess.TimeoutExpired:
        return "Scan is still running in the background (timed out waiting). Check Windows Security."
    except Exception as e:
        return str(e)


def defender_status() -> str:
    """Show Windows Defender real-time protection and signature status."""
    if os.name != "nt":
        return "Virus Guard works on Windows (Microsoft Defender)."
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$s = Get-MpComputerStatus
if (-not $s) { 'Defender status unavailable. Open Windows Security.'; return }
[PSCustomObject]@{
  AntivirusEnabled = $s.AntivirusEnabled
  RealTimeProtectionEnabled = $s.RealTimeProtectionEnabled
  IoavProtectionEnabled = $s.IoavProtectionEnabled
  AntispywareEnabled = $s.AntispywareEnabled
  BehaviorMonitorEnabled = $s.BehaviorMonitorEnabled
  NISEnabled = $s.NISEnabled
  AntivirusSignatureLastUpdated = $s.AntivirusSignatureLastUpdated
  QuickScanAge = $s.QuickScanAge
  FullScanAge = $s.FullScanAge
} | Format-List | Out-String
"""
    return "=== JagX Virus Guard (Windows Defender) ===\n" + _ps(script, timeout=30)


def enable_realtime_protection() -> str:
    if os.name != "nt":
        return "Windows only"
    # Requires admin for some policies; try and report
    script = r"""
$ErrorActionPreference='Stop'
try {
  Set-MpPreference -DisableRealtimeMonitoring $false
  'Real-time protection enabled (if permissions allow).'
} catch {
  'Could not change real-time protection (run JagX as Administrator). Opening Windows Security...'
  Start-Process 'windowsdefender:'
}
"""
    return _ps(script, timeout=30)


def update_virus_definitions() -> str:
    if os.name != "nt":
        return "Windows only"
    script = r"""
$ErrorActionPreference='SilentlyContinue'
Update-MpSignature
$s = Get-MpComputerStatus
"Signatures update requested. Last updated: $($s.AntivirusSignatureLastUpdated)"
"""
    return _ps(script, timeout=180)


def quick_virus_scan() -> str:
    if os.name != "nt":
        return "Windows only"
    script = r"""
$ErrorActionPreference='SilentlyContinue'
Start-MpScan -ScanType QuickScan
'Triggered Windows Defender Quick Scan. Results appear in Windows Security → Protection history.'
"""
    return _ps(script, timeout=900)


def full_virus_scan() -> str:
    if os.name != "nt":
        return "Windows only"
    script = r"""
$ErrorActionPreference='SilentlyContinue'
Start-MpScan -ScanType FullScan
'Triggered Windows Defender Full Scan (may take a long time). Check Windows Security for progress.'
"""
    return _ps(script, timeout=30)


def scan_path_for_viruses(path: str) -> str:
    """Scan a specific file or folder with Defender."""
    if os.name != "nt":
        return "Windows only"
    p = Path(path).expanduser()
    if not p.exists():
        # common shortcuts
        home = Path.home()
        candidates = {
            "downloads": home / "Downloads",
            "desktop": home / "Desktop",
            "documents": home / "Documents",
        }
        key = path.strip().lower()
        if key in candidates:
            p = candidates[key]
        else:
            return f"Path not found: {path}"
    target = str(p.resolve())
    # Prefer Start-MpScan -ScanPath when available; also try MpCmdRun
    script = f"""
$ErrorActionPreference='SilentlyContinue'
$path = '{target.replace("'", "''")}'
try {{
  Start-MpScan -ScanType CustomScan -ScanPath $path
  "Custom scan started for: $path"
}} catch {{
  $mp = "$env:ProgramFiles\Windows Defender\MpCmdRun.exe"
  if (Test-Path $mp) {{
    & $mp -Scan -ScanType 3 -File $path
    "MpCmdRun scan finished for: $path"
  }} else {{
    "Could not start scan. Open Windows Security and scan manually: $path"
  }}
}}
"""
    return _ps(script, timeout=900)


def list_detected_threats() -> str:
    if os.name != "nt":
        return "Windows only"
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$t = Get-MpThreatDetection | Select-Object -First 30 ThreatID, ThreatName, Resources, InitialDetectionTime, ProcessName
if (-not $t) { 'No recent threat detections found by Defender.' }
else { $t | Format-List | Out-String }
"""
    return _ps(script, timeout=45)


def remove_detected_threats() -> str:
    """Ask Defender to remove/quarantine known threats."""
    if os.name != "nt":
        return "Windows only"
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$threats = Get-MpThreat
if (-not $threats) {
  'No active threats listed. Running a quick scan is recommended.'
  return
}
foreach ($th in $threats) {
  try { Remove-MpThreat -ThreatID $th.ThreatID } catch {}
}
'Removal requested for listed threats. Check Windows Security → Protection history.'
"""
    return _ps(script, timeout=120)


def quarantine_file(path: str) -> str:
    """Scan then delete a suspicious file if user path is valid (after Defender preference)."""
    if os.name != "nt":
        return "Windows only"
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        return f"File not found: {path}"
    # First scan the file
    scan = scan_path_for_viruses(str(p))
    # Move to JagX quarantine folder instead of hard-delete when unsure
    qdir = Path.home() / "JagX_Quarantine"
    qdir.mkdir(parents=True, exist_ok=True)
    dest = qdir / p.name
    try:
        # Prefer Defender remove; also isolate by moving
        p.replace(dest)
        return f"{scan}\nIsolated file moved to quarantine: {dest}\n(Delete permanently from that folder if confirmed malware.)"
    except Exception as e:
        return f"{scan}\nCould not move file (in use or access denied): {e}"


def delete_quarantined_file(name: str) -> str:
    qdir = Path.home() / "JagX_Quarantine"
    target = qdir / name
    if not target.exists():
        files = list(qdir.glob("*")) if qdir.exists() else []
        listing = ", ".join(f.name for f in files[:30]) or "(empty)"
        return f"Not found in quarantine. Available: {listing}"
    try:
        target.unlink()
        return f"Permanently deleted: {target}"
    except Exception as e:
        return str(e)


def list_quarantine_folder() -> str:
    qdir = Path.home() / "JagX_Quarantine"
    if not qdir.exists():
        return "Quarantine folder is empty / not created yet."
    files = sorted(qdir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not files:
        return "Quarantine folder is empty."
    return "\n".join(f"{f.name}  ({f.stat().st_size} bytes)" for f in files[:50])


def open_windows_security() -> str:
    if os.name != "nt":
        return "Windows only"
    os.system("start windowsdefender:")
    return "Opened Windows Security"


def virus_guard_report() -> str:
    return (
        defender_status()
        + "\n\n--- Recent threats ---\n"
        + list_detected_threats()
        + "\n\nTip: say 'quick virus scan', 'scan downloads for viruses', or 'update virus definitions'."
    )


ANTIVIRUS_TOOLS = [
    {"type": "function", "function": {"name": "defender_status", "description": "Show Windows Defender protection status.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "enable_realtime_protection", "description": "Enable Defender real-time protection.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "update_virus_definitions", "description": "Update antivirus signatures.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "quick_virus_scan", "description": "Run a quick virus scan.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "full_virus_scan", "description": "Run a full disk virus scan.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "scan_path_for_viruses", "description": "Scan a file or folder path (or downloads/desktop/documents).", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_detected_threats", "description": "List threats detected by Defender.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "remove_detected_threats", "description": "Remove/quarantine threats found by Defender.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "quarantine_file", "description": "Scan a suspicious file and isolate it in JagX_Quarantine.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "delete_quarantined_file", "description": "Permanently delete a file from JagX quarantine by name.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "list_quarantine_folder", "description": "List files in JagX quarantine folder.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "open_windows_security", "description": "Open Windows Security app.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "virus_guard_report", "description": "Full virus protection status report.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_FUNCTIONS = {
    "defender_status": defender_status,
    "enable_realtime_protection": enable_realtime_protection,
    "update_virus_definitions": update_virus_definitions,
    "quick_virus_scan": quick_virus_scan,
    "full_virus_scan": full_virus_scan,
    "scan_path_for_viruses": scan_path_for_viruses,
    "list_detected_threats": list_detected_threats,
    "remove_detected_threats": remove_detected_threats,
    "quarantine_file": quarantine_file,
    "delete_quarantined_file": delete_quarantined_file,
    "list_quarantine_folder": list_quarantine_folder,
    "open_windows_security": open_windows_security,
    "virus_guard_report": virus_guard_report,
}
