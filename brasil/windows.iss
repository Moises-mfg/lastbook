#ifndef Version
#define Version "0.4.0-alpha4"
#endif
[Setup]
AppId={{4A9BBFE6-A72F-4D48-9BBE-852F62733423}
AppName=O Último Livro
AppVersion={#Version}
AppPublisher=Projeto O Último Livro
AppPublisherURL=https://github.com/Moises-mfg/lastbook
DefaultDirName={localappdata}\Programs\UltimoLivro
DefaultGroupName=O Último Livro
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\derived\desktop-release
OutputBaseFilename=ultimo-livro_{#Version}_windows-x64-instalar
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\UltimoLivro.exe
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
[Files]
Source: "..\derived\desktop-dist\UltimoLivro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\derived\webview-runtime.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
[Icons]
Name: "{group}\O Último Livro"; Filename: "{app}\UltimoLivro.exe"
Name: "{autodesktop}\O Último Livro"; Filename: "{app}\UltimoLivro.exe"
[Run]
Filename: "{tmp}\webview-runtime.exe"; Parameters: "/silent /install"; StatusMsg: "Preparando o componente WebView2 da Microsoft..."; Flags: waituntilterminated; Check: NeedsWebView
Filename: "{app}\UltimoLivro.exe"; Description: "Abrir O Último Livro"; Flags: nowait postinstall skipifsilent
[Code]
function NeedsWebView: Boolean;
var VersionValue: String;
begin
  Result := not ((RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', VersionValue) or RegQueryStringValue(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', VersionValue)) and (VersionValue <> '') and (VersionValue <> '0.0.0.0'));
end;
