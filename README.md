# O Último Livro — Brasil

Aplicativo de preparação e biblioteca offline em português, baseado no LastBook.
Alpha 0.4 disponível para Linux, Windows e macOS, com pacotes separados para Mac Intel e Apple Silicon.

**[Linux e Apple Silicon](https://github.com/Moises-mfg/lastbook/releases/tag/v0.4.0-alpha.5)** · **[Windows e Mac Intel](https://github.com/Moises-mfg/lastbook/releases/tag/v0.4.0-alpha.4)** ·
[Documentação em português](README.pt-BR.md) · [Projeto original](README.upstream.md)

IA local em CPU, Wikipedias selecionáveis, mapas de todos os 5.571 municípios
brasileiros e 27 unidades federativas, guias, checklist e diretório de fontes e
comunidades. Quatro perfis de instalação, downloads verificados, pausa e retomada.

Alvo do perfil Leve: notebook i3 com 8 GB; o benchmark no i3 físico continua
pendente. O pacote suporta Linux x86_64 com Python 3.12–3.14 e glibc 2.39+,
começando por Ubuntu 24.04–26.04. Sem conta e sem telemetria.

Modelos, Wikipedias e mapas são baixados separadamente quando você pedir.
Para usar uma cidade, o aplicativo recebe apenas seu recorte; não é necessário
baixar manualmente os sete volumes da release de dados. Os mapas não oferecem
rotas automáticas nem informações em tempo real. O leitor de ZIM apresenta texto.

O site tem comparador, checklist, diretório e plano JSON importável no aplicativo.
Seu código está em `site-brasil/`.

[Como começar com domínio e afiliados](docs/brasil/DOMINIO-E-AFILIADOS.md) ·
[Mapas: fontes, construção e validação](docs/brasil/MAPAS-OFFLINE.md) ·
[Instalação, requisitos e backups no desktop](docs/brasil/INSTALACAO-DESKTOP.md).

Código aberto. Enciclopédias, mapas, motores e modelos mantêm suas próprias licenças.
