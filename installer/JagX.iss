; ============================================================
;  JagX - Inno Setup Script
;  Creates a professional Windows installer (Setup.exe)
;
;  How to use:
;  1. Install Inno Setup from https://jrsoftware.org/isinfo.php
;  2. Build the app first with build_windows.bat
;  3. Open this file in Inno Setup Compiler and click Build
; ============================================================

#define MyAppName "JagX"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "JagX-JRILICENSE"
#define MyAppURL "https://github.com/JagX-JRILICENSE/JagX"
#define MyAppExeName "JagX.exe"

[Setup]
AppId={{A8F3C2D1-9E4B-4F7A-8C1D-2E5F6A7B8C9D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist_installer
OutputBaseFilename=JagX_Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start JagX automatically when Windows starts"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; Main application files produced by build_windows.bat
Source: "..\dist\JagX\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  MsgBox('Welcome to JagX Setup!' + #13#10 + #13#10 +
         'After installation:' + #13#10 +
         '1. Allow microphone access' + #13#10 +
         '2. Make sure Ollama is running' + #13#10 +
         '3. Say "JagX" to start talking', mbInformation, MB_OK);
end;
