'use strict';
// Habilite uma plataforma somente após validar o pacote e publicar uma URL real.
// Linux usa sua página de versão existente; URLs de binários não publicados ficam vazias.
window.ULTIMO_LIVRO_DOWNLOADS = [
  {
    id: 'linux', name: 'Linux', architecture: 'Intel / AMD x86_64',
    version: 'v0.3.0-alpha.3', available: true,
    releaseUrl: 'https://github.com/Moises-mfg/lastbook/releases/tag/v0.3.0-alpha.3',
    downloadUrl: null,
    requirements: 'Ubuntu 24.04–26.04 x86_64; Python 3.12–3.14 e glibc 2.39 ou posterior.',
    instructions: 'Na página da versão, baixe o pacote .deb e confira a integridade. Instale o pacote pelo gerenciador do Ubuntu para resolver as dependências.'
  },
  {
    id: 'macos-arm64', name: 'macOS · Apple Silicon', architecture: 'ARM64',
    version: 'v0.4', available: false, releaseUrl: null, downloadUrl: null,
    requirements: 'Previsto: macOS 13.3 ou posterior, em Mac com Apple Silicon.',
    instructions: 'Confira o chip em Sobre Este Mac. O DMG correspondente será disponibilizado após a validação.'
  },
  {
    id: 'macos-x64', name: 'macOS · Intel', architecture: 'x86_64',
    version: 'v0.4', available: false, releaseUrl: null, downloadUrl: null,
    requirements: 'Previsto: macOS 13.3 ou posterior, em Mac com processador Intel.',
    instructions: 'Confira o processador em Sobre Este Mac. Aguarde a validação do DMG para Intel.'
  },
  {
    id: 'windows-x64', name: 'Windows', architecture: 'x64',
    version: 'v0.4', available: false, releaseUrl: null, downloadUrl: null,
    requirements: 'Previsto: Windows 10 versão 1809 ou posterior, x64.',
    instructions: 'Estão previstos instalador por usuário com WebView2 e ZIP portátil. O ZIP precisará do WebView2 instalado. Aguarde a validação antes de baixar.'
  }
];
