# O Último Livro — edição brasileira

Adaptação independente e aberta do [LastBook](https://github.com/Immortal-Protocols/lastbook).
**Versão alpha em desenvolvimento, não um produto pronto para emergências.**

Alvo inicial: Linux x86_64, Ubuntu 24.04 ou posterior, notebook i3 com 8 GB de RAM.
O pacote `.deb` publicado tem como alvo Ubuntu 24.04 e Python 3.12.
A geração do i3 e o desempenho da IA ainda precisam ser validados em equipamento real.

## O que já funciona

- Janela Linux usando o transporte local sem porta do LastBook.
- Busca em várias enciclopédias ZIM, com artigos em texto e prioridade para títulos exatos.
- Catálogo fixado de Wikipedia PT mini/nopic/maxi, inglês mini e espanhol mini.
- Downloads por ação explícita, com SHA-256, pausa e retomada após reabrir.
- Visualização de mapas MBTiles raster locais, com zoom e deslocamento.
- Cinco guias iniciais em português, com referências, e busca sem internet.
- Checklist persistente, salvo em SQLite no computador.
- Seleção dos quatro perfis, idiomas e estados, salva localmente.
- IA local em CPU: Qwen3 0.6B Q8, 4B Q4 e 14B Q4, com reservas de memória por modelo.
- Site com comparador, tamanhos reais, checklist e plano JSON importável no aplicativo.

A distribuição de mapas brasileiros ainda está pendente. O assistente recupera trechos
dos guias e das enciclopédias instaladas e oferece botões para consultar as referências.
As respostas continuam experimentais. O catálogo não exige downloads de gigabytes
para abrir o aplicativo; a pessoa escolhe os arquivos e vê o espaço necessário.

## Executar no Linux

Requisitos de sistema: Python 3.11+, PyGObject, GTK3, WebKitGTK 4.1 e Soup3.
Em Ubuntu, instale as dependências pelo gerenciador de pacotes:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-soup-3.0
/usr/bin/python3 -B brasil/main.py
```

O aplicativo não exige instalação da IA para abrir. Para compilar o motor opcional,
instale Git, CMake, compiladores C/C++ e OpenMP e execute:

```bash
bash brasil/build_runtime.sh
```

O motor compilado é `llama-completion`, que executa por pipes. São incluídos os
backends oficiais de CPU com seleção automática por instruções disponíveis;
a variante genérica permanece para processadores antigos. O `llama-cli` da
revisão atual abre um serviço local e por isso não é usado nesta adaptação.
Não enviamos perguntas para uma IA na nuvem. Downloads começam por ação explícita
em Minha instalação, Downloads ou Assistente local. O catálogo inclui as fontes
oficiais Qwen e o espelho Kiwix `ftpmirror.your.org`, com HTTPS, tamanho e SHA-256 fixados. O modelo e seus dados não entram no Git.

Dados: `${XDG_DATA_HOME:-~/.local/share}/ultimo-livro`. Desinstalar o pacote não
apaga sua preparação. Telemetria e cadastro não existem nesta versão.

## Testar e empacotar

```bash
python3 -B -m unittest discover -s brasil/tests -v
node --check brasil/web/app.js
python3 site-brasil/build.py
npm ci --prefix site-brasil --ignore-scripts --no-bin-links
npm test --prefix site-brasil
bash brasil/build_deb.sh
```

O `.deb` é gerado em `derived/brasil-build/`. Para distribuição Ubuntu 24.04,
compile o motor nessa versão do Ubuntu. Um binário compilado em versão mais nova
pode depender de bibliotecas indisponíveis na mais antiga. A automação brasileira
usa Ubuntu 24.04. Guias e checklist funcionam em pacotes sem o motor. O pacote completo também inclui
python-libzim 3.13.1, com licença GPL e componentes indicados em THIRD_PARTY_NOTICES.md.
Para executar a leitura de ZIM pelo código-fonte, instale libzim==3.13.1 em um
ambiente Python compatível ou em brasil/vendor.

Mapas aceitos: `.mbtiles` raster com metadado format=png/jpg/jpeg/webp; mapas vetoriais
ainda não são aceitos. A atribuição do pacote é exibida. Não baixamos tiles públicos
do OpenStreetMap. Enciclopédias: baixe pelo catálogo ou importe seus arquivos `.zim`;
os artigos aparecem em texto e seus scripts não são executados. Arquivos importados
permanecem no disco de origem, que precisa continuar conectado. Downloads do catálogo
ficam em `encyclopedias/` e `models/` na pasta de dados do aplicativo.

Para usar o plano do site, exporte o JSON e escolha **Minha instalação → Importar
plano do site**. A importação valida as escolhas e não inicia downloads. Depois,
confira os tamanhos e pressione **Baixar modelos e enciclopédias**. O andamento,
a pausa e a retomada ficam na seção **Downloads**.

O catálogo é gerado por uma ação do mantenedor com `tools/atualizar_catalogo_br.py`.
Ele consulta metadados oficiais e fixa versões; o aplicativo não consulta a rede
ao abrir. A interface do site usa os mesmos dados para evitar tamanhos divergentes.

## Documentação

- [Decisões e andamento](docs/brasil/ANDAMENTO.md)
- [Planejamento pesquisado](docs/brasil/PLANEJAMENTO.md)
- [Como começar com domínio e afiliados](docs/brasil/DOMINIO-E-AFILIADOS.md)
- [Código e documentação originais](README.upstream.md)

Nome provisório; não há vínculo oficial com os autores do LastBook.
O código original continua MIT. Conteúdo, mapas, motores e modelos mantêm suas
próprias licenças. Não redistribuímos a biblioteca de terceiros do LastBook.

## Interface da alpha

Imagem da própria janela Linux em teste, com dados descartáveis:

![Biblioteca brasileira na janela Linux](docs/brasil/interface-alpha.png)
