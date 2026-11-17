#ifndef Version
#define Version "0.4.0-alpha5"
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
Source: "..\derived\webview-runtime.exe"; Flags: dontcopy
[Icons]
Name: "{group}\O Último Livro"; Filename: "{app}\UltimoLivro.exe"
Name: "{autodesktop}\O Último Livro"; Filename: "{app}\UltimoLivro.exe"
[Run]
Filename: "{app}\UltimoLivro.exe"; Description: "Abrir O Último Livro"; Flags: nowait postinstall skipifsilent
[Code]
function HasRuntime(RootKey: Integer; const Key: String): Boolean;
var VersionValue: String;
begin
  Result := RegQueryStringValue(RootKey, Key, 'pv', VersionValue) and (VersionValue <> '') and (VersionValue <> '0.0.0.0');
end;

function NeedsWebView: Boolean;
begin
  Result := not (HasRuntime(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') or HasRuntime(HKCU, 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var ResultCode: Integer; Attempt: Integer;
begin
  Result := '';
  if not NeedsWebView then Exit;
  ExtractTemporaryFile('webview-runtime.exe');
  if not Exec(ExpandConstant('{tmp}\webview-runtime.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then begin
    Result := 'Não foi possível iniciar o componente WebView2 da Microsoft. Tente novamente.';
    Exit;
  end;
  Log(Format('Instalador WebView2: código %d', [ResultCode]));
  for Attempt := 1 to 40 do begin
    if not NeedsWebView then Exit;
    Sleep(500);
  end;
  Result := Format('O componente WebView2 não ficou disponível (código %d). Verifique as permissões do Windows e execute o instalador novamente.', [ResultCode]);
end;
