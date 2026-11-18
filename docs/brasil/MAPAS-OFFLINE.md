# Mapas brasileiros offline

O leitor vetorial oferece consulta local, busca de ruas e lugares, zoom e camadas.
O catálogo cobre 5.571 municípios, 27 unidades federativas, visão geral e Brasil
detalhado. Os arquivos de dados são distribuídos separadamente na
[release de mapas](https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/mapas-br-2026-11-16).
O aplicativo não consulta a rede ao abrir; downloads começam por ação explícita.

## Fontes e limites

- OpenStreetMap, extrato Geofabrik `brazil-261116.osm.pbf`, de 16/11/2026.
- IBGE, malha municipal 2025 e lista oficial de localidades, incluindo Boa
  Esperança do Norte/MT. O catálogo confere com os 5.571 códigos oficiais.
- Ruas, ferrovias, hidrografia, localidades e serviços registrados no extrato OSM.
- Recortes por retângulo envolvente, incluindo o entorno. Não são limites
  cadastrais exatos. Não há roteamento, relevo ou atendimento em tempo real.

Créditos: © contribuidores do OpenStreetMap, Geofabrik e IBGE. A base derivada
OSM é oferecida sob ODbL 1.0; créditos, URI de licença e proveniência ficam no mapa.
O código do aplicativo mantém suas próprias licenças.

Fontes primárias:

- https://download.geofabrik.de/south-america/brazil.html
- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/
- https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/
- https://servicodados.ibge.gov.br/api/v1/localidades/municipios

## Tamanhos e formato

Visão geral: 28.348.416 bytes. Campinas/SP: 16.523.264 bytes.
Boa Esperança do Norte/MT: 339.968 bytes. Brasil detalhado: 2.281.992.192 bytes.
A base nacional contém 9.598.609 feições, sem vias descartadas por falta de localização.

Os sete volumes `.ulpack` somam 11.750.383.616 bytes porque reúnem todos os
recortes. O aplicativo recebe somente os intervalos escolhidos: não é preciso
baixar todos para usar uma cidade. Cada mapa `.ulmap` é um SQLite independente,
com RTree, índice FTS5 de nomes e geometrias delta comprimidas com zlib.

Cada mapa mantém tamanho e SHA-256 próprios. Mapas maiores que um volume são
divididos, verificados por parte e montados com verificação final. O espaço
adicional de montagem do mapa nacional é mostrado antes do download.

## Reprodução pelo mantenedor

Em ambiente virtual, instale `tools/mapas-requisitos.txt`. Essas dependências
servem à construção; a leitura dos mapas usa apenas a biblioteca padrão Python.

```bash
python tools/baixar_fontes_mapas_br.py
python tools/construir_mapas_br.py master
python tools/construir_mapas_br.py regions
python tools/empacotar_mapas_br.py
```

Arquivos grandes ficam em `derived/mapas-br/`, fora do Git. A origem, tamanho e
hashes das fontes são registrados em proveniência. Recortes concluídos são
preservados ao retomar a construção. Um arquivo temporário evita publicar bases
incompletas. Não lançar um aplicativo com catálogo apontando para dados ausentes.

## Validação

- OSM sintético → SQLite → recorte: geometria, índice espacial e busca.
- HTTPS local: intervalos delimitados, retomada, recusa de intervalo incorreto,
  montagem de partes, checksum final e limpeza após ativação.
- Todos os SHA-256 e tamanhos dos volumes conferidos com os digests do GitHub.
- Download real por GitHub da visão geral, Campinas e Boa Esperança do Norte;
  Campinas foi pausada e retomada, e os três mapas foram verificados e ativados.
  Reproduzir com `python3 tools/validar_mapas_publicados.py`.
- Janela Linux com recorte real de Campinas: ruas, bairros, busca, zoom e camadas.
  [Captura do aplicativo](imagens/mapa-campinas.png).
- 28 testes brasileiros, 86 testes do instalador (dois específicos de macOS
  ignorados no Linux) e cinco testes DOM do site aprovados localmente.
- Bundle TLS restrito atualizado com Sectigo E46/R46 do Mozilla/certifi 2026.10.23.
  Todas as origens autorizadas passaram; a origem externa de controle foi recusada.
- Wheels oficiais libzim 3.13.1 para Python 3.12, 3.13 e 3.14, com hashes fixados
  e diretórios separados. A Wikipedia PT mini real abriu no Ubuntu 26.04/Python
  3.14. A compilação do motor permanece no Ubuntu 24.04.

O benchmark em i3 físico com 8 GB e a revisão visual do site em navegador completo
permanecem pendentes. Os testes da janela Linux e os testes DOM têm escopo distinto.
