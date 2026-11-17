# Decisões e andamento

## Decisões confirmadas

- Público: todo o Brasil; conteúdo nacional com recortes locais, não uma região piloto exclusiva.
- Linux primeiro, x86_64; alvo mínimo de produto: notebook i3 com 8 GB RAM.
- Código aberto. Reaproveitar o LastBook, preservando origem, licença e upstream.
- Desenvolvimento conduzido pelo assistente; decisões rotineiras não exigem nova confirmação.
- Ainda não há domínio nem cadastro em programas de afiliados.
- Nome de trabalho: O Último Livro, provisório e baseado na pasta do projeto.

## Arquitetura desta primeira entrega

O aplicativo brasileiro está em `brasil/` e reutiliza a janela WebKitGTK e a bridge
sem porta do LastBook. Isso permite testar português e computadores modestos sem
baixar os pacotes americanos ou o modelo de 17 GB. O aplicativo original permanece
em `app/main.py`; seus dados não são migrados automaticamente.

## Critérios pendentes de lançamento estável

1. Testar i3 físico de 8 GB (geração ainda não informada), tempo de resposta e RAM.
2. Catálogo ZIM por idioma com tamanho/data/licença e downloads verificáveis.
3. Mapas nacionais por região, atribuições e recursos gráficos integralmente locais.
4. Importar e pesquisar múltiplas enciclopédias, com fontes acessíveis pela IA.
5. Revisão humana de conteúdo crítico e acessibilidade.
6. Testar instalação/desinstalação em Ubuntu 24.04 nativo, incluindo modo offline.
7. Infraestrutura de pacotes, assinaturas e recuperação de atualizações.
8. Contratos/programas de afiliados aprovados para os canais efetivamente usados.

## Decisões que realmente dependem do responsável

- Nome definitivo e compra de domínio (custos e titularidade).
- Identidade/CPF/CNPJ e aceitação dos contratos dos programas comerciais.
- Eventuais gastos, profissionais revisores e compromissos de prazo.
- Quando houver interesse em divulgar o site: abrir o acesso público; a primeira
  publicação Sites é privada para avaliação do responsável.

Nenhuma senha, documento de identidade, credencial ou informação bancária deve ser
adicionada a este repositório.

## Verificações realizadas nesta primeira implementação

- Testes automatizados de persistência, validação, API pela bridge sem servidor,
  leitura/busca de ZIM real criado para testes e coordenadas TMS de mapa raster.
- Janela WebKitGTK nativa abriu os cinco guias em português.
- Modelo oficial Qwen3 0.6B Q8 baixado e conferido por SHA-256; resposta real em CPU.
- Rastreamento da execução de inferência não registrou chamadas socket/connect/bind/listen.
- CI Ubuntu 24.04 compilou motor e pacote da primeira base com sucesso.
- Site publicado privadamente via Sites; navegador integrado indisponível neste
  ambiente, portanto a revisão visual do site no navegador permanece pendente.

A Wikipedia PT mini publicada no catálogo Kiwix em maio de 2026 aparece com cerca
  de 1,6 GB, nopic 6,6 GB e maxi 19 GB (valores arredondados do catálogo, consultado
  em 16/11/2026). Isso atualiza a incerteza de tamanhos registrada no planejamento
  original. O aplicativo ainda não baixa essas enciclopédias; abre arquivos locais.
  Fonte: https://download.kiwix.org/zim/wikipedia/

## Evolução 0.2 — 17/11/2026

- Catálogo fixado de cinco Wikipedias e três modelos Qwen, com tamanho, versão,
  fonte e SHA-256. Os dados são consultados por ação do mantenedor; abrir o app
  não consulta a rede.
- O plano de instalação usa esses tamanhos, calcula o restante e mostra a reserva
  de disco. Salvar preferências continua sem iniciar downloads.
- Downloads pausáveis e retomáveis após reabrir, com ativação só após verificação.
- Importação de múltiplos ZIM, busca conjunta ou por coleção e prioridade a títulos
  exatos. O assistente recupera trechos dessas coleções e oferece referências abríveis.
- O plano exportado pelo site agora usa o formato aceito pelo aplicativo.
- Testes DOM do site verificam os controles e a exportação/importação. Isso não é
  revisão visual de navegador; a ferramenta de navegador continua indisponível.
- Wikipedia PT mini real: 1.703.536.110 bytes, baixada por HTTPS, verificada com o
  digest oficial e pesquisada offline. Os outros tamanhos exatos estão no catálogo.
- Testes locais HTTPS comprovaram pausa, retomada por Range após reabrir e recusa
  de checksum incorreto. A interface Linux verificou navegação, perfis, gravação,
  oito pacotes, desativação da IA e checklist em dados descartáveis.

O teste inicial do 4B na compilação sem otimizações atingiu o limite de tempo.
A compilação está sendo atualizada para os backends oficiais com seleção automática
por instruções da CPU, preservando uma variante genérica para máquinas antigas.
O modelo 14B ainda precisa de teste em computador com memória suficiente; não há
benchmark de um i3 físico de 8 GB. Mapas brasileiros por região continuam pendentes.

### Resultado do motor com seleção automática de CPU

O novo motor concluiu a pergunta “Qual é a capital do Brasil?” usando os artigos
Capital e Brasil da Wikipedia PT mini instalada. Nesta máquina de teste (i5 de
13ª geração, cerca de 16 GB instalados), o perfil Leve levou 5,81 s e o Moderado
24,22 s. São amostras de uma pergunta, com carga de compilação concomitante; não
são previsões de velocidade nem benchmark do i3 alvo. Ambos retornaram Brasília e
metadados das referências que o leitor consegue abrir. O rastreamento de uma
execução curta do motor atualizado não registrou chamadas socket/connect/bind/listen.
O diagnóstico confirmou AVX2/AVX_VNNI no backend escolhido automaticamente.

Foram aprovados 18 testes Python, quatro testes DOM do site (incluindo o plano
exportado aceito pelo validador do aplicativo) e o teste de interações na janela
Linux. O teste visual completo do site e o benchmark de hardware alvo permanecem
pendentes. Nenhum modelo ou arquivo de enciclopédia foi enviado ao Git.

## Entrega 0.3 — 17/11/2026

- PR [#6](https://github.com/Moises-mfg/lastbook/pull/6) integrado ao `main`.
- [Instalador 0.3 alpha](https://github.com/Moises-mfg/lastbook/releases/tag/v0.3.0-alpha.3),
  cerca de 32 MB, produzido no Ubuntu 24.04 pelo CI e conferido por SHA-256.
- [Dados dos mapas](https://github.com/Moises-mfg/lastbook/releases/tag/mapas-br-2026-11-16):
  5.571 municípios, 27 UFs, visão geral e Brasil detalhado; créditos, licença e
  proveniência incluídos. Os sete volumes foram comparados aos digests do GitHub.
- Downloads reais de visão geral, Campinas e Boa Esperança do Norte, com pausa,
  retomada, SHA-256, ativação e consulta offline aprovados.
- Leitor vetorial com busca, zoom e camadas. Captura real de Campinas em
  `docs/brasil/imagens/mapa-campinas.png`.
- Diretório de 11 fontes e comunidades com descrições locais e abertura da fonte
  original por ação explícita; inclui LoRa, radioamadorismo e criadores brasileiros.
- Site atualizado e implantado com sucesso: https://ultimo-livro-brasil.genuineoffer32.chatgpt.site .
  Acesso permanece privado para o proprietário. Fonte da hospedagem:
  `1919f77e90e0aaa94274b8597a766a5088ca1a03`; fonte também versionada em `site-brasil/`.
- CI aprovado: 28 testes brasileiros, 86 do instalador (dois de macOS ignorados),
  cinco testes DOM, leitores ZIM em Python 3.12/3.13/3.14 e janela do pacote extraído.
- O mesmo instalador foi extraído e testado no Ubuntu 26.04/Python 3.14 com
  Wikipedia PT mini e mapa reais. A busca e leitura de artigos passaram.
- Motor incluído no instalador respondeu Brasília com referências da Wikipedia
  em 5,5 segundos no i5/16 GB usado para teste. Não é benchmark nem previsão para i3.

Limites atuais: leitor de artigos em texto; mapas sem roteamento ou estado em
tempo real; IA experimental. Pendem benchmark no i3 físico e revisão visual do
site em navegador completo. Domínio próprio e programas de afiliados dependem
das escolhas e cadastros pessoais do proprietário; há instruções em
`DOMINIO-E-AFILIADOS.md`. Nenhuma conta, comissão ou compra foi ativada.

## Validação 0.4 — aplicativos para três sistemas

Implementação em revisão no PR [#7](https://github.com/Moises-mfg/lastbook/pull/7).
As janelas macOS/WebKit e Windows/WebView2 reutilizam o transporte local sem porta;
Python, leitor ZIM e motor CPU são incluídos no pacote. Os dados permanecem locais
e o download dos conteúdos depende de uma ação explícita.

- Linux: os 33 testes brasileiros passaram localmente, incluindo leitura de ZIM em
  pastas com acentos, persistência, integridade e retomada de downloads. O CI gerou
  o pacote `0.4.0~alpha4` no commit `795bd1561971431033c365dbc7a6fe2a30a01bc9`.
- Esse `.deb`, extraído no Ubuntu 26.04/Python 3.14, passou no fluxo da janela:
  mapas, busca/leitura ZIM, preferências, checklist, pergunta enviada pelo formulário,
  resposta real do motor incluído e abertura da referência apresentada pela IA.
- macOS Intel passou em uma rodada anterior com janela e inferência reais. A rodada
  atual exige também execução da cópia montada diretamente do DMG somente leitura.
- macOS ARM e Windows seguem em validação: criação da amostra ZIM no Windows foi
  separada da leitura em caminho Unicode; o consumo do motor e a memória disponível
  agora são registrados. A reserva de memória do produto permanece ativa.
- A cópia instalada no Windows também precisa passar no fluxo completo. Os pacotes
  não serão apresentados como disponíveis antes dessas verificações.

Uma medição curta no Linux registrou pico de 943.054.848 bytes no processo do motor
0.6B. Esse valor não representa a RAM total do aplicativo nem certifica o alvo i3/8 GB.
Requisitos, locais de dados e limites de assinatura estão em `INSTALACAO-DESKTOP.md`.

### Verificações adicionais da 0.4

- Windows x64: o run [44131108762](https://github.com/Moises-mfg/lastbook/actions/runs/44131108762)
  passou no motor, na cópia empacotada e na cópia instalada em pasta com acentos.
  As 15 etapas da janela, a pergunta pelo formulário, a resposta real com Brasília,
  a abertura da referência ZIM e o retorno ao mapa passaram. A correção do CRT
  compartilhado resolveu a falha inicial na abertura do modelo.
- A captura da cópia instalada foi conferida e está em `imagens/windows-alpha.png`.
  O pico do processo do motor foi 943.079.424 bytes numa pergunta curta; não é
  medição de RAM total nem benchmark do i3 alvo.
- Linux: o run [44134607804](https://github.com/Moises-mfg/lastbook/actions/runs/44134607804)
  passou também no teste repetível `tools/testar_linux.py`, com pacote extraído,
  IA, referência e captura obrigatórias. O CI agora inclui o conversor GI/Cairo.
- Os jobs macOS da rodada Windows acima foram cancelados antes de iniciar, com
  annotations de indisponibilidade de runners hospedados. Não houve teste do DMG
  nessa rodada. A nova tentativa usará o runner padrão `macos-26-intel`, além do
  ARM já configurado; trocar a imagem não garante disponibilidade.
- Antes de disponibilizar a alpha 0.4, o empacotamento está sendo completado com
  textos de licença e fontes das versões efetivamente incorporadas. A aprovação
  funcional do Windows não equivale à conclusão dessa revisão da distribuição.

O site recebeu a seção de downloads por sistema, com requisitos e estados reais,
e passou nos sete testes DOM. Publicação privada confirmada; fonte da hospedagem
`b6f8b27c8d153aecabb651128a9e9af0b98f1771`. O roteamento dos subagentes também está
registrado em `AGENTS.md`; esse arquivo não troca automaticamente o modelo principal.
