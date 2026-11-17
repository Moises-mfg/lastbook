# Instalação dos aplicativos de desktop

## Estado e requisitos

A versão **0.3 para Linux** está publicada. A versão **0.4 para macOS e Windows** ainda está em validação; ainda não há links finais para download. O macOS planejado requer macOS 13.3 ou posterior e terá imagens DMG para Apple Silicon (ARM) e Intel. No Windows, o alvo é Windows 10 versão 1809 ou posterior, x64, com instalador por usuário e ZIP portátil. O instalador incluirá o WebView2 Runtime standalone. Python e o motor do aplicativo serão incluídos nos pacotes; arquivos GGUF, Wikis e mapas serão baixados somente depois de uma ação explícita no aplicativo.

## Escolha do pacote

No macOS, confira em **Sobre Este Mac** se o processador é Apple Silicon (ARM) ou Intel e escolha o DMG correspondente; o pacote errado pode não abrir. No Windows, use o instalador para a instalação comum por usuário ou extraia o ZIP portátil em uma pasta onde sua conta possa gravar. O ZIP não instala o WebView2 Runtime: se ele não estiver disponível no computador, a interface pode não iniciar até que o runtime seja instalado por um meio confiável.

## Dados e backups

Os dados ficam em `~/Library/Application Support/UltimoLivro` no macOS, `%LOCALAPPDATA%\UltimoLivro` no Windows e, no Linux, em `$XDG_DATA_HOME/ultimo-livro` (ou `~/.local/share/ultimo-livro` se `XDG_DATA_HOME` não estiver definido). Se `ULTIMO_LIVRO_DATA` estiver definida, ela substitui o diretório padrão em qualquer sistema. Para fazer backup, feche o aplicativo e copie essa pasta para um local seguro; para restaurar, feche o aplicativo e recoloque os dados na pasta correspondente. Preserve os arquivos GGUF, Wikis e mapas se quiser manter os downloads locais. Arquivos importados permanecem na pasta ou no disco de origem: copie-os também e, se o caminho mudar, importe-os novamente no aplicativo.

## Assinatura e limites

Os pacotes macOS planejados usam assinatura ad hoc; os instaladores Windows não têm certificado comercial. Gatekeeper ou SmartScreen podem mostrar avisos, e não há garantia de aprovação automática. Confira a origem e a integridade do pacote e siga as opções de análise disponíveis para aquele arquivo; não desative proteções globais. Os pacotes 0.4 e seus links só serão anunciados após a validação.

## Licenças e fontes

Os pacotes 0.4 autocontidos incluem uma pasta `licenses` com textos, avisos e um
`MANIFESTO.json` de versões, origens e hashes. No Windows, ela fica em
`_internal/licenses` dentro da pasta do aplicativo. No macOS, integra o conteúdo
do aplicativo; use **Mostrar Conteúdo do Pacote** para inspecioná-la.

A release deve oferecer gratuitamente o arquivo `fontes` da plataforma e
arquitetura correspondente, além dos instaladores. Esse ZIP é destinado à
inspeção e reconstrução dos componentes; não é necessário para usar o aplicativo.
Modelos, enciclopédias e mapas não estão nesse arquivo. Os componentes Microsoft
continuam com seus próprios termos; a licença MIT do projeto não os relicencia.

Para empacotar localmente, `GITHUB_SHA` precisa apontar para o commit completo
publicado que corresponde ao código sob compilação, e `GITHUB_REPOSITORY` deve
identificar o fork. O CI fornece esses valores automaticamente. A coleta de
fontes é uma etapa do mantenedor com conexão, não uma atividade do aplicativo.
