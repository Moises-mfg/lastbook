'use strict';
// Habilite uma plataforma somente após validar o pacote e publicar uma URL real.
const release10 = 'https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/v0.4.0-alpha.10';
const files10 = 'https://github.com/Moises-mfg/o-ultimo-livro/releases/download/v0.4.0-alpha.10';
const release08 = 'https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/v0.4.0-alpha.8';
const files08 = 'https://github.com/Moises-mfg/o-ultimo-livro/releases/download/v0.4.0-alpha.8';
window.ULTIMO_LIVRO_DOWNLOADS = [
  {
    id: 'linux', name: 'Linux', architecture: 'Intel / AMD x86_64',
    version: 'v0.4.0-alpha.10', available: true, releaseUrl: release10, checksumUrl: files10 + '/SHA256SUMS', evidenceUrl: release10,
    downloadUrl: files10 + '/ultimo-livro_0.4.0-alpha10_amd64.deb',
    requirements: 'Ubuntu 24.04–26.04 x86_64; Python 3.12–3.14 e glibc 2.39 ou posterior.',
    instructions: 'Baixe o pacote .deb, confira o SHA-256 na página da versão e instale pelo gerenciador do Ubuntu.'
  },
  {
    id: 'macos-arm64', name: 'macOS · Apple Silicon', architecture: 'ARM64',
    version: 'v0.4.0-alpha.8', available: true, releaseUrl: release08, checksumUrl: files08 + '/SHA256SUMS', evidenceUrl: release08,
    downloadUrl: files08 + '/ultimo-livro_0.4.0-alpha8_macos-arm64.dmg',
    requirements: 'macOS 13.3 ou posterior, em Mac com Apple Silicon.',
    instructions: 'A alpha 10 para Apple Silicon aguarda teste. A alpha 8 está disponível. Abra o DMG e mova o aplicativo para Aplicativos.'
  },
  {
    id: 'macos-x64', name: 'macOS · Intel', architecture: 'x86_64',
    version: 'v0.4.0-alpha.10', available: true, releaseUrl: release10, checksumUrl: files10 + '/SHA256SUMS', evidenceUrl: release10,
    downloadUrl: files10 + '/ultimo-livro_0.4.0-alpha10_macos-x64.dmg',
    requirements: 'macOS 13.3 ou posterior, em Mac com processador Intel.',
    instructions: 'Confira o processador em Sobre Este Mac. Abra o DMG e mova o aplicativo para Aplicativos.'
  },
  {
    id: 'windows-x64', name: 'Windows', architecture: 'x64',
    version: 'v0.4.0-alpha.10', available: true, releaseUrl: release10, checksumUrl: files10 + '/SHA256SUMS', evidenceUrl: release10, downloadUrl: null,
    requirements: 'Windows 10 versão 1809 ou posterior, x64.',
    instructions: 'Na página da versão, escolha o instalador por usuário ou o ZIP portátil. O ZIP requer WebView2 instalado.'
  }
];
