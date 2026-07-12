[Setup]
AppName=OmniStudio
AppVersion=1.0
DefaultDirName={autopf}\OmniStudio
DefaultGroupName=OmniStudio
OutputDir=c:\Users\icomp\PycharmProjects\OmniStudio\dist
OutputBaseFilename=OmniStudio_Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
SetupIconFile=c:\Users\icomp\PycharmProjects\OmniStudio\assets\icons\app_icon.ico

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "c:\Users\icomp\PycharmProjects\OmniStudio\dist\OmniStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OmniStudio"; Filename: "{app}\OmniStudio.exe"
Name: "{autodesktop}\OmniStudio"; Filename: "{app}\OmniStudio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OmniStudio.exe"; Description: "{cm:LaunchProgram,OmniStudio}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Force close any running instances of OmniStudio to prevent file locking
  Exec('taskkill', '/F /IM OmniStudio.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
