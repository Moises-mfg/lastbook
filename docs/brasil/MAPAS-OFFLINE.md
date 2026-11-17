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

Não publicar um manifesto que aponte para arquivos indisponíveis. A entrega só
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
