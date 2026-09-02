; StudyApp, Windows installer (Inno Setup 6)
; Build:  powershell -File scripts\build_installer.ps1

#ifndef AppVersion
  #define AppVersion "4.5.1"
#endif

#define AppName "StudyApp"
#define AppPublisher "Or Dadshaev"
#define AppURL "mailto:dadshaev@gmail.com"
#define AppId "{{8F3C2A91-6B4E-4D17-9C5A-21B7E0D4A8F2}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppCopyright=Copyright (C) 2026 Or Dadshaev
VersionInfoVersion={#AppVersion}.0
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
SourceDir=..\..
OutputDir=dist
OutputBaseFilename=StudyApp-{#AppVersion}-setup
LicenseFile=LICENSE
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\StudyApp.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
AllowNoIcons=yes
CloseApplications=yes
RestartApplications=no
UsedUserAreasWarning=no

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\StudyApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\StudyApp.exe"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\StudyApp.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\StudyApp.exe"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
