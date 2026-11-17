# Mapas brasileiros — construção em andamento

O ramo de mapas acrescenta leitor vetorial local, busca de ruas e lugares,
controle de camadas e catálogo por município, estado e Brasil. A versão 0.2
publicada continua sendo a referência enquanto os dados novos não forem
publicados e verificados. Não há downloads automáticos ao abrir o aplicativo.

## Fontes e escopo

- OpenStreetMap, extrato Geofabrik `brazil-261116.osm.pbf` de 16/11/2026.
- IBGE, malha municipal 2025 e lista oficial de localidades, 5.571 municípios.
- 27 unidades federativas; inclui Boa Esperança do Norte/MT.
- Ruas, ferrovias, hidrografia, localidades e serviços registrados no OSM.
- Recortes por retângulo envolvente, incluindo o entorno. Não são limites
  cadastrais exatos. Não há roteamento, relevo ou atendimento em tempo real.

Créditos: © contribuidores do OpenStreetMap, Geofabrik e IBGE.
A base derivada OSM é disponibilizada sob ODbL 1.0. Os créditos e fontes ficam
no próprio mapa e no manifesto, sem remover as licenças dos materiais originais.

Fontes primárias:

- https://download.geofabrik.de/south-america/brazil.html
- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/
- https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/
- https://servicodados.ibge.gov.br/api/v1/localidades/municipios

## Reprodução pelo mantenedor

Em ambiente virtual, instale `tools/mapas-requisitos.txt`. São ferramentas de
construção; o aplicativo final usa apenas SQLite e a biblioteca padrão Python.

```bash
python tools/baixar_fontes_mapas_br.py
python tools/construir_mapas_br.py master
python tools/construir_mapas_br.py regions
python tools/empacotar_mapas_br.py
```

Os arquivos grandes ficam em `derived/mapas-br/`, fora do Git. A origem,
tamanho e hashes das fontes são registrados em proveniência. A base nacional
construída contém 9.598.609 feições, sem vias descartadas por falta de localização.
Os recortes concluídos são preservados ao retomar a construção.

O formato `.ulmap` é SQLite com RTree e índice de nomes FTS5. Geometrias são
comprimidas com zlib. `.ulpack` é apenas transporte por intervalos HTTP; cada
mapa mantém tamanho e SHA-256 próprios. Mapas maiores que um volume são divididos,
verificados por parte e montados com verificação final. A montagem nacional
precisa de espaço temporário adicional, mostrado antes do download.

Não lançar uma versão do aplicativo que aponte para arquivos indisponíveis. O ramo de desenvolvimento e seu PR de rascunho podem conter o catálogo para executar o CI enquanto os volumes sobem. A entrega só
pode ser considerada concluída após upload, teste HTTP Range no GitHub e
instalação real de ao menos um recorte com busca e desenho offline.

## Verificação já realizada neste ramo

- Geometria, SQLite, RTree, busca e recorte de fonte OSM sintética.
- HTTPS local: intervalos delimitados, pausa e retomada, recusa de intervalo
  incorreto, montagem de múltiplas partes e limpeza após verificação.
- Janela Linux real: leitura vetorial, busca, zoom e controle de camadas.
- A versão de IA continua dependente de benchmark em i3 físico com 8 GB.

A geração e distribuição nacional ainda estão em andamento. Este arquivo é
atualizado conforme a validação, sem tratar o leitor pronto como dados publicados.

### Validação com dados reais

O recorte de Campinas/SP abriu na janela Linux. A busca encontrou Campinas, o
zoom exibiu ruas e bairros e o controle de camadas alterou o desenho.
[Captura do aplicativo](imagens/mapa-campinas.png). Isso valida o leitor com dados
reais; o teste de download por GitHub ainda será feito após publicar os volumes.

A suíte brasileira passou 27 testes; o instalador original passou 86 testes
(com dois específicos de macOS ignorados no Linux); o site passou quatro testes
DOM. O primeiro CI do PR #6 passou nos testes e na compilação/teste do pacote.

### Distribuição

Os recortes foram concluídos: 5.600 entradas e sete volumes, somando
11.750.383.616 bytes de transporte. O catálogo confere com os 5.571 códigos
municipais oficiais. O envio para a release de dados está em andamento; o app
0.3 ainda não foi lançado. O ramo de desenvolvimento inclui o catálogo para
validar a integração completa pelo CI.

O diretório de fontes acrescenta 11 referências revisadas, com descrições locais
e abertura da página original somente por ação explícita. Inclui fontes oficiais,
projetos LoRa, grupos regionais, LABRE e criadores, com identificação comercial.
Nenhum vídeo, página completa ou conversa foi redistribuído.

### Publicação e teste do transporte real

A release `mapas-br-2026-11-16` foi publicada após conferir os SHA-256 dos sete
volumes com os digests retornados pelo GitHub. O downloader do próprio aplicativo
baixou a visão geral, Campinas/SP e Boa Esperança do Norte/MT; pausou e retomou
Campinas, verificou hashes e ativou os três mapas. A busca offline encontrou
Campinas. O teste é reproduzível por `python3 tools/validar_mapas_publicados.py`.

O teste identificou a ausência das raízes Sectigo usadas pelo GitHub no bundle
herdado. Foram acrescentadas E46/R46 a partir do Mozilla/certifi 2026.10.23;
continuam permitidas somente as 13 raízes explícitas, com TLS 1.2+, hostname
verificado e recusa de certificado fora da lista. Todas as origens autorizadas
passaram na verificação de TLS; a origem externa de controle foi recusada.

O pacote agora inclui os wheels oficiais libzim 3.13.1 para CPython 3.12, 3.13
e 3.14 em diretórios separados, com SHA-256 fixado. Apenas a variante do Python
em uso é carregada. A Wikipedia PT mini real abriu e foi pesquisada na janela
do Ubuntu 26.04/Python 3.14. A compilação do motor permanece no Ubuntu 24.04.
