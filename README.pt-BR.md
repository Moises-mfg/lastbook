# O Último Livro — edição brasileira

Adaptação independente e aberta do [LastBook](https://github.com/Immortal-Protocols/lastbook).
**Versão alpha em desenvolvimento, não um produto pronto para emergências.**

Alvo inicial: Linux x86_64, Ubuntu 24.04 ou posterior, notebook i3 com 8 GB de RAM.
O pacote `.deb` publicado tem como alvo Ubuntu 24.04 e Python 3.12.
A geração do i3 e o desempenho da IA ainda precisam ser validados em equipamento real.

## O que já funciona

- Janela Linux usando o transporte local sem porta do LastBook.
- Leitura e busca em um ZIM local por vez, com artigos em texto.
- Visualização de mapas MBTiles raster locais, com zoom e deslocamento.
- Cinco guias iniciais em português, com referências, e busca sem internet.
- Checklist persistente, salvo em SQLite no computador.
- Seleção dos quatro perfis, idiomas e estados, salva localmente.
- IA pequena experimental em CPU: Qwen3 0.6B Q8, download voluntário com SHA-256.
- Site com comparador de perfis, exportação de plano e checklist local.

Mapas e pacotes brasileiros de Wikipedia ainda não estão publicados. Modelos 4B e
14B são escolhas planejadas; a integração inicial executa somente o 0.6B.
O assistente usa os guias incluídos; não pesquisa automaticamente toda a Wikipedia.

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

O motor compilado é `llama-completion`, que executa por pipes. O `llama-cli` da
revisão atual abre um serviço local e por isso não é usado nesta adaptação.
Não enviamos perguntas para uma IA na nuvem. O download do modelo só começa após
uma ação explícita na tela Assistente local. O modelo e seus dados não entram no Git.

Dados: `${XDG_DATA_HOME:-~/.local/share}/ultimo-livro`. Desinstalar o pacote não
apaga sua preparação. Telemetria e cadastro não existem nesta versão.

## Testar e empacotar

```bash
python3 -B -m unittest discover -s brasil/tests -v
node --check brasil/web/app.js
node --check site-brasil/app.js
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
do OpenStreetMap. Enciclopédias: selecione seu `.zim` já baixado; esta versão mostra
texto dos artigos e não executa seus scripts. Dados externos não são copiados: o
disco de origem precisa permanecer conectado.

## Documentação

- [Decisões e andamento](docs/brasil/ANDAMENTO.md)
- [Planejamento pesquisado](docs/brasil/PLANEJAMENTO.md)
- [Como começar com domínio e afiliados](docs/brasil/DOMINIO-E-AFILIADOS.md)
- [Código e documentação originais](README.upstream.md)

Nome provisório; não há vínculo oficial com os autores do LastBook.
O código original continua MIT. Conteúdo, mapas, motores e modelos mantêm suas
próprias licenças. Não redistribuímos a biblioteca de terceiros do LastBook.
