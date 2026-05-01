; Inno Setup 6 - builds one installer EXE from the PyInstaller onefile executable.
; Prerequisite: run scripts\build_release.ps1 first.

#define MyAppName "Lucid Net"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LucidNet"
#define MyAppExeName "LucidNet.exe"
#define DistExe SourcePath + "..\dist\" + MyAppExeName

#if !FileExists(DistExe)
  #error Missing dist\LucidNet.exe. Run scripts\build_release.ps1 first, or run scripts\build_release.ps1 -SkipInstaller before compiling installer\LucidNet.iss directly.
#endif

[Setup]
AppId={{B8E4C9A1-6F2D-4E1B-9C0A-7D3E5F1A2B6C}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=LucidNet-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\app.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""if (-not [System.Diagnostics.EventLog]::SourceExists('LucidNet')) {{ New-EventLog -LogName Application -Source 'LucidNet' }}"""; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function ShouldPurgeUserData(): Boolean;
begin
  Result := Pos('/PURGEUSERDATA', UpperCase(GetCmdTail)) > 0;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and ShouldPurgeUserData() then
    DelTree(ExpandConstant('{localappdata}\LucidNet'), True, True, True);
end;
