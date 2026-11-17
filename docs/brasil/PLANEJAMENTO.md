# Planeje uma central brasileira de preparação

**Recomendação: criar uma central offline em português para Linux, começando por uma adaptação auditada do LastBook, com quatro perfis configuráveis e núcleo gratuito.** A biblioteca, os mapas, a busca e os planos pessoais devem funcionar mesmo quando a IA não puder rodar. A IA será escolhida pelo hardware e por testes em português; a menor opção útil importa mais que o menor modelo existente. O diferencial brasileiro será conteúdo revisado, mapas locais, preparação familiar e recomendações de compras adequadas ao risco e ao orçamento. Os afiliados exigem uma estratégia própria: as regras pesquisadas da Amazon restringem software desktop e as do Mercado Livre restringem meios offline. O site editorial pode gerar receita após aprovação, mas não deve servir como uma forma presumida de contornar essas regras. Este relatório apresenta planejamento, escolhas propostas e decisões pendentes; nenhum aplicativo, site, parceria ou instalação foi criado.

Pesquisa realizada em **16 de novembro de 2026**. As especificações dos fornecedores são fatos documentais, não resultados de testes deste projeto. Faixas de armazenamento, cronograma e orçamento abaixo são estimativas de planejamento. Não foram executados o LastBook nem benchmarks físicos de modelos, rádios ou equipamentos.

## 1. Aproveitar o LastBook reduz trabalho, mas exige auditoria

O LastBook reúne boa parte da proposta: leitura de documentos, vídeos, enciclopédias, mapas e conversa com fontes. Seu repositório publica suporte Linux direcionado ao Ubuntu 24.04 x86_64, mas a documentação consultada relata testes em WSL2 com CPU; isso não valida automaticamente distribuições diferentes ou aceleração por GPU em Linux nativo. O código usa Python, interface Linux GTK/WebKitGTK e frontend HTML/CSS/JavaScript. Minha recomendação é **testar um fork com marca própria antes de considerar uma reescrita**. Reaproveitar a base concentra o esforço nas diferenças que interessam: português, Brasil, IA menor, conteúdo selecionável e manutenção. ([Repositório LastBook](https://github.com/Immortal-Protocols/lastbook))

A página da biblioteca oferece conjuntos Small, Medium e All, apresentados na consulta com aproximadamente 7,7 GB, 67,5 GB e 387,9 GB. Esses números ajudam a compreender a escala do produto original; **não são tamanhos das instalações brasileiras propostas**. O catálogo tem forte referência aos Estados Unidos e não deve ser simplesmente traduzido e redistribuído inteiro. ([Biblioteca LastBook](https://www.lastbook.org/library/))

A licença MIT do código permite adaptação e uso comercial, preservados os avisos exigidos. Ela não transforma livros, vídeos, modelos, mapas ou marca em material livre para qualquer uso. Há também dependências com GPL, incluindo componentes ZIM. Antes de distribuir, precisamos inventariar versões e obrigações e decidir como cumprir a disponibilização de código e os avisos aplicáveis. Afiliados e software aberto podem coexistir; minha preferência inicial é manter o aplicativo aberto e financiar curadoria, suporte e distribuição. ([Licença do projeto](https://github.com/Immortal-Protocols/lastbook/blob/main/LICENSE), [Avisos de terceiros](https://github.com/Immortal-Protocols/lastbook/blob/main/THIRD_PARTY_NOTICES.md), [Créditos da biblioteca](https://www.lastbook.org/credits/))

**Critério para continuar com o fork:** uma prova técnica deve abrir uma enciclopédia, executar uma IA pequena, mostrar um mapa brasileiro e instalar/atualizar com segurança em Ubuntu nativo. Também deve ser possível organizar modelos e pacotes sem depender de uma IA fixa. Se essa adaptação custar mais que substituir módulos específicos, mantemos o que funciona e substituímos esses módulos. Uma reescrita integral só deve ser escolhida com evidência de bloqueio técnico ou de licenciamento incompatível com a estratégia desejada.

O primeiro lançamento deve ter suporte declarado para Ubuntu 24.04 LTS x86_64, com pacote `.deb` e testes em hardware real. Linux Mint compatível pode entrar na matriz após validação. Flatpak, AppImage, ARM64 e outras distribuições ficam para uma segunda etapa. Cada formato adicional amplia a manutenção, especialmente de vídeo, permissões de disco externo e GPU.

### O aplicativo deve oferecer uma rotina clara

A proposta de posicionamento é: **“Conhecimento, mapas e preparação para consultar mesmo sem internet.”** A interface deve ser inteiramente em português, com linguagem acessível, fonte ajustável, alto contraste, navegação por teclado, modo claro/escuro e modo econômico. A primeira tela deve mostrar se o conjunto está pronto para uso offline, o que falta baixar, espaço ocupado e atalhos para guias essenciais. Nenhum cadastro será necessário para consultar o que já está instalado.

| Área | O que entregar inicialmente | Evolução posterior |
|---|---|---|
| Início | Estado offline, favoritos, guias rápidos, downloads pendentes | Lembretes locais de revisão e validade |
| Assistente local | Perguntas em português, trechos e fontes abríveis | Comparação de modelos e respostas mais elaboradas |
| Biblioteca | Pesquisa, PDF, ZIM, vídeos autorizados, favoritos | Coleções temáticas e importadores adicionais |
| Mapas | Regiões baixadas, busca de locais, pontos e GPX | Geocodificação e roteamento próprios |
| Meu plano e estoque | Pessoas, contatos, listas, “já tenho”, validade | Planos compartilháveis por arquivo |
| Aprender e comunidades | Guias, diretório público, indicação de necessidade de internet | Integração experimental com rádios |
| Equipamentos | Critérios, prioridades e lista de necessidades | Compras autorizadas contratualmente |
| Downloads e configurações | Quatro perfis, pacotes, discos, privacidade | Distribuição local e mais plataformas |

Planos, estoque, coordenadas e conversas ficam no dispositivo. A exportação deve ser opcional e explicar quando um arquivo inclui dados pessoais. O modelo de receitas não precisa de histórico de perguntas ou localização residencial.

## 2. Quatro perfis devem compartilhar um instalador e um catálogo

A instalação deve começar pelo aplicativo pequeno, seguido dos pacotes escolhidos. No assistente inicial, a pessoa escolhe a pasta, recebe um diagnóstico local e vê os quatro perfis. Antes de confirmar, o programa mostra tamanho de download, tamanho final, espaço temporário, idiomas, datas, licenças e uma estimativa de tempo baseada na conexão medida. O perfil será uma recomendação editável; não haverá quatro aplicativos independentes.

### IA local: escolher pela utilidade e pelo computador

Minha linha inicial de candidatos é Qwen3, pela disponibilidade de tamanhos pequenos e licenças Apache 2.0 nos modelos citados. Não se trata de um ranking dos melhores modelos disponíveis. A escolha final precisa comparar qualidade em português, citações corretas, latência e memória no hardware alvo. A frase “menor IA disponível” deve virar **“menor IA aprovada nos nossos testes”**: um modelo muito pequeno que inventa instruções não atende ao objetivo. ([Qwen3 0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), [Qwen3 4B Instruct](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [Qwen3 14B](https://huggingface.co/Qwen/Qwen3-14B))

| Perfil proposto | IA candidata inicial | Hardware alvo, sujeito a teste | Conteúdo sugerido | Meta inicial de espaço instalado |
|---|---|---|---|---|
| **Leve** | Qwen3 0.6B; priorizar consulta e resumos simples | CPU; 4 GB RAM experimental, 8 GB recomendado | Wikipedia PT mini, guias essenciais, mapa do município ou entorno | 5–12 GB |
| **Moderada** | Qwen3 4B Instruct; comparar 8B quando couber | 16 GB RAM; GPU opcional | Wikipedia PT sem imagens, mapas de um estado, alguns vídeos licenciados | 25–60 GB |
| **Parruda** | Qwen3 14B Q4; oferecer 8B como alternativa rápida | 32 GB RAM; GPU com 12–16 GB VRAM desejável, conforme contexto e driver | Wikipedia PT completa, outros idiomas opcionais, Brasil vetorial e coleções maiores | 100–250 GB ou mais |
| **Personalizada** | Modelo aprovado, quantização e contexto escolhidos | Diagnóstico e estimativa por configuração | Wikis, idiomas, mapas, camadas e vídeos independentes | Soma calculada pelo catálogo |

**As faixas acima são metas de produto, não tamanhos de downloads já disponíveis.** O tamanho e a data dos arquivos portugueses atuais do Kiwix não foram confirmados nesta pesquisa. Se o conjunto real exceder a faixa, o instalador precisa mostrar o valor real e oferecer escolhas menores. Não prometer “Wikipedia portuguesa completa em X GB” sem congelar a edição utilizada.

Como referência dos pesos, os repositórios oficiais consultados apresentam arquivos de aproximadamente 639 MB para 0.6B Q8, 2,5 GB para 4B Q4, 5,03 GB para 8B Q4 e 9 GB para 14B Q4. **Arquivo do modelo não é memória total necessária.** Contexto, cache, interface, busca e sistema operacional também consomem RAM; a VRAM disponível e os drivers determinam a aceleração possível. A versão Instruct e a quantização escolhidas devem ser conferidas como um par compatível, sem trocar automaticamente arquivos entre variantes. ([GGUF 0.6B](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/main), [GGUF 4B](https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/main), [GGUF 8B](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main), [GGUF 14B](https://huggingface.co/Qwen/Qwen3-14B-GGUF/tree/main))

O diagnóstico deve identificar arquitetura e instruções da CPU, RAM disponível, GPU, VRAM, driver, espaço e sistema de arquivos. Um teste curto opcional mede o desempenho real. O aplicativo precisa permitir redução de contexto, troca de modelo e execução só em CPU. Falha na GPU deve levar a uma alternativa explicada; falta de memória não pode bloquear a biblioteca. Não somar RAM e VRAM como se fossem sempre intercambiáveis, sobretudo em GPU integrada.

Sugiro integrar **llama.cpp** como motor controlado pelo aplicativo e testar seus backends no Linux. Ollama pode ser uma integração opcional para usuários que já o utilizam; não elimina a necessidade de verificar GPU e drivers. No perfil leve, começar com contexto pequeno e carregar o gerador só quando solicitado reduz consumo e libera memória para leitura. ([llama.cpp](https://github.com/ggml-org/llama.cpp), [Backends e compilação](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md), [Hardware do Ollama](https://docs.ollama.com/gpu))

### Wikipedia, busca e mapas precisam funcionar por conta própria

O catálogo de enciclopédias deve deixar escolher idioma, coleção e variante, além de importar `.zim` existente. No Kiwix, **mini** contém introduções e infoboxes, **nopic** oferece artigos sem imagens e **maxi** é a variante completa. Essa diferença precisa estar na tela de escolha: “pequena” não pode parecer sinônimo de “completa”. Wikipedia em português, outros idiomas e projetos complementares entram conforme disponibilidade e licença da edição concreta. ([Explicação oficial das variantes](https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/), [Catálogo Kiwix](https://get.kiwix.org/en/solutions/catalog/))

A busca textual é a primeira camada. A IA recupera trechos e responde com referências locais verificáveis, técnica conhecida como RAG. Cada citação deve abrir o documento ou artigo correto sem internet. Para busca semântica portuguesa, multilingual-e5-small é um candidato de baixo custo a testar; não reutilizar um índice inglês presumindo a mesma qualidade. Indexar toda a Wikipedia pode exigir muito armazenamento e processamento: começar com guias curados e indexação progressiva é mais prudente. ([Multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small))

O assistente deve distinguir resposta fundamentada de ausência de evidência, evitar inventar certificações e usar material revisado em temas críticos. Em saúde, água, incêndios e eletricidade, a versão oficial revisada deve ficar acessível diretamente, sem exigir que a pessoa converse com a IA. O modo econômico pode desativar geração e manter busca, leitura e fichas imprimíveis.

Nos mapas, recomendo MapLibre com pacotes PMTiles ou MBTiles regionais, incluindo estilos, fontes, ícones e demais recursos locais. O OpenStreetMap exige atribuição e obrigações ODbL; os tiles públicos não são uma fonte autorizada para download em massa. Dados OSM brutos também não equivalem a um mapa pronto. O Brasil `.pbf` consultado na Geofabrik estava na ordem de 2 GB, mas pacotes renderizados, relevo, índices e roteamento têm tamanhos próprios. ([MapLibre e PMTiles](https://docs.protomaps.com/pmtiles/maplibre), [Recursos locais e privacidade](https://docs.protomaps.com/guide/security-privacy), [OSM direitos](https://www.openstreetmap.org/copyright), [Política dos tiles](https://operations.osmfoundation.org/policies/tiles/), [Extratos Brasil](https://download.geofabrik.de/south-america/brazil.html))

O MVP deve mostrar mapas, procurar locais, salvar pontos, medir distância e importar/exportar GPX. Roteamento a pé ou carro exige motor e grafo adicionais, como Valhalla, e pode entrar depois. Mapas offline não informam se uma ponte caiu, se uma rua está inundada ou se um hospital está atendendo. Pontos de abrigo e serviços precisam ter fonte e data; não apresentar localização histórica como disponibilidade em tempo real. ([Valhalla](https://github.com/valhalla/valhalla))

### Arquitetura, distribuição e manutenção

| Camada | Decisão proposta | Motivo |
|---|---|---|
| Interface Linux | Aproveitar GTK/WebKitGTK e frontend local após prova técnica | Reduzir reescrita inicial |
| Serviço local | Python coordenando biblioteca, configurações, busca e processos | Separar regras da interface e dos motores |
| Inferência | Processo llama.cpp separado, versão fixada e limites de recursos | Encerrar/reiniciar IA sem derrubar leitura |
| Enciclopédias | Adaptador ZIM com licenças auditadas | Trocar coleções sem alterar aplicativo |
| Mapas | Adaptador MapLibre, pacotes locais e atribuições | Independência de serviços externos |
| Dados pessoais | Banco local separado dos pacotes | Atualizar biblioteca preservando planos |
| Distribuição | Aplicativo pequeno e manifesto versionado de dados | Evitar reinstalação de dezenas de GB |

Cada pacote deve registrar origem, versão, licença, idioma, tamanho de download/final/temporário, hash, dependências e data de revisão. O manifesto precisa de assinatura; hash sozinho não autentica um catálogo adulterado. Downloads devem pausar, retomar, verificar integridade e recuperar de falhas, preservando a versão anterior até concluir a troca. A importação por USB deve funcionar sem consulta obrigatória ao servidor.

É necessário testar falta de espaço, queda de energia, disco removido, caminhos com acentos e FAT32, que limita arquivos grandes. Arquivos importados não podem executar código arbitrário ou acessar a rede silenciosamente. PDFs, vídeos, ZIM e conteúdo recuperado pela IA são entradas potencialmente problemáticas; um documento não deve conseguir dar ordens ao programa ou abrir compras automaticamente. Atualizações serão voluntárias, com alterações e consumo de espaço explícitos. O núcleo instalado deve continuar útil se o projeto ou a hospedagem deixar de existir.

## 3. Conteúdo brasileiro e compras devem partir dos riscos reais

A prioridade editorial deve ser preparação doméstica para interrupções de água, energia e comunicação e para evacuação. Guias de Defesa Civil e Saúde sustentam o núcleo; agricultura, reparos e autonomia ampliada entram depois. O objetivo é ajudar a pessoa a usar e manter recursos que consegue ter, sem transformar preparação em uma lista interminável de compras. A Defesa Civil inclui água, alimentos, documentos, medicamentos, higiene, roupas e necessidades de crianças e animais em seus materiais. ([Kit pessoal da Defesa Civil PR](https://www.defesacivil.pr.gov.br/Pagina/Kit-de-Emergencia-pessoal), [Orientações antes, durante e depois](https://www.defesacivil.pr.gov.br/Noticia/O-que-fazer-em-desastres-Defesa-Civil-orienta-populacao-sobre-antes-durante-e-depois))

### Lista inicial do que comprar no Brasil

A tabela é uma **lista por especificação e prioridade**, não um ranking de marcas nem uma cesta com preços cotados. Quantidades e modelos finais dependem de cidade/CEP, pessoas, riscos, necessidades e orçamento. Primeiro registrar o que a casa já tem; depois cotar dois ou três fornecedores com frete, data e garantia.

| Prioridade | Item | Como selecionar e dimensionar |
|---|---|---|
| Essencial | Água potável lacrada e recipientes próprios com tampa | Calcular pessoas, animais e dias; separar consumo/cozinha de higiene. Calor e condições de saúde alteram a demanda. |
| Essencial | Alimentos habituais não perecíveis e abridor manual | Meta inicial proposta de três dias, ampliável; respeitar dietas e alergias, priorizar preparo simples e controlar validade. |
| Essencial | Lanterna frontal ou de mão e luz de ambiente | Uma luz individual por usuário e uma compartilhada como referência inicial; comparar autonomia em potência útil, pilhas/USB e resistência documentada. |
| Essencial | Pilhas, carregador, power bank e cabos | Confirmar portas e potência; comparar Wh e perdas, e não só mAh. Um power bank de celular pode não alimentar notebook. |
| Essencial | Rádio receptor AM/FM | Operação com pilhas ou recarga acessível; recepção local. Receptor não é transceptor. |
| Essencial | Kit de curativos e medicamentos de uso contínuo | Gaze, curativos, fita, atadura, luvas, termômetro e itens revisados por profissional; receitas, alergias e contatos. |
| Essencial | Proteção de documentos e higiene | Saco/pasta estanque, cópias e contatos impressos, dinheiro trocado, sabonete, papel, sacos, itens menstruais, fraldas e animais. |
| Conforme risco | Bota impermeável, luvas, óculos e PFF2 | Tamanho e proteção adequados; verificar CA quando aplicável. Bota de trilha não equivale a EPI para limpeza. |
| Conforme risco | Mochila, capa de chuva, roupas e cobertor | Conforto, clima e peso que a pessoa consegue transportar; reaproveitar itens existentes. |
| Conforme risco | Detector de fumaça e extintor adequado | Instalação, tipo e treinamento conforme orientação local e fabricante; verificar registro e integridade do extintor. |
| Conforme risco | Apito e ferramentas domésticas básicas | Selecionar por tarefas reais, evitando kits sem utilidade demonstrada. |
| Continuidade | SSD externo ou pendrive confiável | Instalação, biblioteca e backup; testar leitura e manter cópia independente do original. |
| Expansão | Estação de energia e painel/carregador solar | Comprar depois de calcular Wh/dia, potência e autonomia; dimensionar para equipamentos reais e sol disponível. |
| Expansão | Dois ou mais rádios LoRa e antenas compatíveis | Verificar homologação do produto exato, firmware, parâmetros e existência de pares para testar. |
| Expansão | Filtro portátil e método de desinfecção | Examinar manual e limitações; filtro de trilha não garante remoção de contaminantes de enchente. |

Não proponho uma quantidade universal de água nem instruções improvisadas de potabilização. A tela correspondente deve guardar orientação oficial revisada e identificar concentração e produto quando houver desinfecção. O Ministério da Saúde publica instruções próprias para água em emergências; a IA deve apontar a fonte em vez de inventar dosagens. ([Saúde: cuidados com água](https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes/cuidados-com-a-agua/cuidados-com-a-agua))

Como exemplo concreto para o catálogo de botas, a Marluvas publica a Vulcaflex 110VFLEX PR, em PVC, com características impermeáveis e CA informado 42291. É **candidata para comparação**, sem teste físico ou endosso nesta pesquisa. O CA, a proteção, a numeração e a situação atual do modelo precisam ser conferidos antes da publicação. Nenhuma bota torna seguro atravessar enchentes ou locais energizados; PFF2 não protege contra gases. ([Ficha do fabricante](https://www.marluvas.com/uploads/2022/05/110vflex-pr-700453.pdf), [MTE: EPI e CA](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/seguranca-e-saude-no-trabalho/equipamentos-de-protecao-individual-epi/perguntas_e_respostas), [Saúde: enchentes](https://miniapps.saude.gov.br/guia-clima/enchentes-e-inundacoes/o-que-comunicar-a-comunidade))

Extintores novos devem atender às exigências de certificação e registro; o aplicativo deve explicar o que verificar, sem decidir sozinho o dimensionamento da casa. Primeiros socorros, incêndios e instalações elétricas precisam de revisão humana qualificada e incentivo a formação prática. ([Inmetro: extintores](https://www.gov.br/inmetro/pt-br/acesso-a-informacao/perguntas-frequentes/avaliacao-da-conformidade/extintores-de-incendio/quais-as-exigencias-por-parte-do-inmetro-para-as-empresas-que-comercializam-extintores-de-incendio-novos))

### Canais, grupos e preparação enquanto há conexão

Sugiro uma área “Preparar enquanto há conexão”: cadastrar alertas, baixar mapas e guias, localizar serviços municipais, combinar contatos e pontos de encontro, fazer curso de primeiros socorros, testar rádios, verificar backups e simular um dia sem internet. O cadastramento de alertas da Defesa Civil por CEP via SMS 40199 consta em orientação oficial e deve ser ensinado antes da emergência. Alertas novos dependem dos canais e da conectividade disponíveis. ([MIDR: alertas](https://www.gov.br/mdr/pt-br/acesso-a-informacao/perguntas-frequentes/perguntas-frequentes-defesa-civil/alertas))

| Fonte ou comunidade verificável | Papel proposto no diretório | Cuidados editoriais |
|---|---|---|
| Defesa Civil e Ministério da Saúde | Referências centrais para preparação e emergência | Conferir data, contexto regional e direitos de redistribuição |
| Sobrevivencialismo/Portal SV e Julio Lobo | Candidatos para aprendizagem e parcerias | Revisar publicações individualmente e divulgar interesses comerciais |
| Meshtastic e MeshCore oficiais | Documentação dos respectivos ecossistemas | Fixar versão de firmware e revisar configuração brasileira |
| MeshBrasil | Comunidade e materiais em português | Conferir atualidade e regras oficiais antes de reproduzir parâmetros |
| LABRE estadual e redes de emergência | Formação e diretório de radioamadorismo | Verificar disponibilidade regional e exigências de habilitação |

Esses nomes são pontos de partida, não aprovação de todos os ensinamentos de um canal. Cada publicação deve registrar assunto, autor, fontes, revisão, riscos, vínculo comercial e permissão offline. O Portal SV e a página de Julio Lobo permitem verificar existência e atuação; MeshBrasil e LABRE-CE oferecem referências públicas para comunicação. ([Portal SV](https://membros.sobrevivencialismo.com/), [Julio Lobo](https://juliolobo.com.br/sobre), [MeshBrasil](https://meshbrasil.com/faq.html), [LABRE-CE e emergência](https://labre-ce.org.br/rener/))

Assistir a um vídeo ou ter YouTube Premium não concede direito de redistribuí-lo no aplicativo. O núcleo deve usar arquivos com licença compatível ou autorização documentada do criador; os demais aparecem como links que exigem internet. Convites privados e conversas de grupos não devem ser copiados. ([YouTube: downloads offline](https://support.google.com/youtube/answer/7381437/youtube-videos-offline-faqs))

### LoRa deve começar como conhecimento e diretório

LoRa é a tecnologia de rádio; LoRaWAN é uma arquitetura de rede IoT e não equivale a mensageiro autônomo em malha. Meshtastic e MeshCore são ecossistemas distintos; não presumir interoperabilidade. No início, incluir conceitos, checklist de dois nós, consumo, testes de cobertura e links públicos. Integração de mensagens no aplicativo fica depois do núcleo offline. Um rádio isolado não cria uma comunidade e LoRa não é meio para transportar Wikipedia, vídeos ou modelos de IA. ([LoRa Alliance](https://lora-alliance.org/about-lorawan-old/), [Meshtastic](https://meshtastic.org/docs/getting-started/initial-config/), [MeshCore](https://github.com/meshcore-dev/MeshCore))

Não proponho comprar qualquer placa anunciada como “915 MHz” e copiar um preset estrangeiro. A tabela atual do Meshtastic apresenta opções brasileiras que precisam ser confrontadas com versão, produto, antena, potência e regras nacionais. Preset não comprova homologação. Equipamentos de radiação restrita e radioamadorismo têm regimes diferentes; os requisitos de Anatel devem ser verificados no modelo exato antes da compra e publicação de instruções. Nenhum SKU Heltec, RAK ou Seeed foi confirmado como homologado nesta pesquisa. ([Meshtastic por país](https://meshtastic.org/docs/configuration/region-by-country/), [Anatel: Resolução 680 consolidada](https://informacoes.anatel.gov.br/legislacao/resolucoes/2017/936-resolucao-680), [Homologação por declaração](https://www.gov.br/anatel/pt-br/regulado/certificacao-de-produtos/declaracao-de-conformidade/), [Regras operacionais de radioamador](https://informacoes.anatel.gov.br/legislacao/atos-de-requisitos-operacionais-de-outorga-e-licenciamento/2148-ato-3448-26))

## 4. Afiliados precisam de autorização; o site deve explicar o produto

**O principal risco comercial encontrado é presumir que links de afiliados podem ser embutidos no desktop.** A política da Amazon Brasil restringe Links Especiais e conteúdo do programa em software instalável, com exceção específica para aplicativos móveis aprovados. O Mercado Livre informa restrições a meios offline e grupos fechados e lista meios públicos declarados no cadastro. Não planejar comissão dentro do aplicativo como receita já autorizada. ([Amazon: políticas, seção 5](https://associados.amazon.com.br/help/operating/policies), [Mercado Livre: compartilhamento](https://www.mercadolivre.com.br/l/afiliados-compartilhamento-de-publicacao))

Minha proposta é núcleo gratuito e site editorial público com guias, comparações e links aprovados. O fluxo app → site → loja precisa ser descrito ao programa e confirmado por escrito; uma página intermediária não é garantia de conformidade. Para compras diretamente associadas ao desktop, buscar contratos com fabricantes ou lojas que autorizem explicitamente esse uso. Até obter autorização, a área de equipamentos pode funcionar como checklist e orientação, preservando a utilidade offline.

A publicidade deve ser claramente identificada. Uma redação editorial possível é “Publicidade: este conteúdo contém links de afiliado; podemos receber comissão por compras qualificadas”, acompanhada da declaração específica exigida pelo programa. Não esconder o vínculo nem ordenar produtos pela comissão. O CDC exige publicidade identificável e proíbe publicidade enganosa ou abusiva, incluindo exploração do medo; preparação não deve ser vendida com promessas de sobrevivência garantida. ([Amazon: identificação](https://associados.amazon.com.br/help/node/topic/GPXFHVYZMTGPUMPE), [CDC, artigos 36 e 37](https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm))

Imagens, preços e conteúdo de marketplaces têm regras próprias. Não congelar fotos e preços no pacote offline sem licença. Usar material próprio/autorizado e especificações editoriais; preço, quando não houver integração autorizada, será consultado na loja. O clique deve ser voluntário, sem abertura automática, redirecionamento oculto ou compra iniciada pela IA. ([Amazon: políticas](https://associados.amazon.com.br/help/operating/policies), [Mercado Livre: direcionamento de visitas](https://www.mercadolivre.com.br/l/afiliados-direcionamento-de-visitas))

A conta financeira é **visitas qualificadas × cliques × conversão × ticket elegível × comissão efetiva**, descontados cancelamentos, tributos e despesas. Exemplo puramente hipotético: 10.000 visitas × 20% de clique × 3% de compra × R$250 × 4% = R$600 brutos. Não são taxas verificadas dos programas nem previsão de receita. Afiliados precisam de audiência e compras atribuídas; não sustentam automaticamente downloads grandes. Suporte, oficinas, instalação, doações, manutenção institucional e SSD preparado com conteúdo redistribuível são receitas complementares a avaliar.

### Como deve ser o site

O site deve ser leve, acessível e legível no celular, com demonstração real do aplicativo, requisitos claros e botão “Baixar para Linux”. A página inicial apresenta a proposta, o que funciona offline, os quatro perfis e uma resposta de exemplo com fonte. Não deve sugerir que uma IA grande roda em qualquer computador nem prometer aplicativo móvel antes de existir.

| Página | Conteúdo e objetivo |
|---|---|
| Início | Proposta, demonstração, privacidade e download |
| Baixar para Linux | Versão, distribuições testadas, requisitos, assinatura/hash e instruções |
| Compare instalações | Diferenças reais entre perfis, tamanhos e seleção personalizada |
| Catálogo offline | Pacotes, idiomas, datas, licenças e cobertura |
| Guias Brasil | Conteúdo editorial revisado e adequado aos riscos locais |
| Equipamentos | Critérios, comparações, alternativas e publicidade identificada |
| Comunidades | Diretório público com cidade/UF, protocolo e última verificação |
| Documentação e suporte | Instalação, offline, atualização, problemas e acessibilidade |
| Transparência e privacidade | Licenças, autores, revisores, afiliados e tratamento de dados |

Sugiro site estático e catálogo gerado do mesmo manifesto do aplicativo, evitando divergências. Sem conta no MVP, sem dependência do site para abrir dados locais e sem modelos pesados executando no navegador. A identidade visual pode usar fundo claro ou escuro, um tom de verde/azul e um destaque âmbar para ações, com pictogramas acompanhados de texto. A marca precisa ser própria, pesquisada e sem sugerir afiliação oficial com LastBook.

Na privacidade, minimizar dados e explicar finalidades; não coletar estoque, saúde, chats e coordenadas apenas para medir vendas. Telemetria do aplicativo deve começar desativada. O site precisa ter política compatível com os serviços realmente usados e controles adequados quando houver rastreamento. A LGPD exige necessidade e transparência; consentimento não é a única base legal e não substitui esse trabalho. ([ANPD: perguntas frequentes](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes))

## 5. Desenvolver por marcos e decidir o escopo antes de publicar

### Qual modelo deve ajudar em cada etapa

A IA de desenvolvimento é separada da IA embarcada. Modelos grandes na nuvem podem ajudar a construir o programa; isso não significa que o usuário precisará deles ou de assinatura para consultar a biblioteca. Não há benchmark deste projeto que justifique declarar um vencedor absoluto. A recomendação é escolher uma versão estável disponível, executar uma tarefa piloto e medir correção, custo e tempo, antes de contratar uso amplo. As famílias abaixo constam dos catálogos oficiais, que mudam com o tempo. ([Anthropic: modelos](https://platform.claude.com/docs/en/models/overview), [Google: modelos](https://aistudio.google.com/docs/models))

| Etapa | Modelo ou categoria sugerida | Responsabilidade humana |
|---|---|---|
| Requisitos, arquitetura e análise de riscos | GPT-6 Astra disponível nesta sessão, ou Claude Opus | Aprovar escopo, concessões e decisões técnicas |
| Implementação cotidiana e testes | GPT-6.1 Sol disponível nesta sessão, ou Claude Sonnet | Revisar mudanças e executar testes reais |
| Classificação de arquivos e metadados | Haiku ou Gemini Flash | Validar amostras, direitos e itens de risco |
| Inspeção de documentos e interfaces | Gemini Pro ou modelo multimodal equivalente | Verificar fontes, layout e acessibilidade |
| Revisão independente | Outro modelo forte, diferente do autor da mudança | Aprovar código, segurança e lançamento |
| Conteúdo de emergência | IA como auxílio de extração e redação com fontes | Revisão por pessoa qualificada; IA não certifica instruções |
| Assistente do usuário | Qwen3 0.6B/4B/8B/14B conforme testes e hardware | Governança do catálogo e das avaliações |

Os nomes GPT-6 Astra e GPT-6.1 Sol são exemplos disponíveis no ambiente desta conversa, não promessa de disponibilidade futura nem comparação de desempenho publicada. Se você quiser trabalhar com apenas uma ferramenta já contratada, ela pode cobrir várias etapas; a separação importante é de tarefas e revisão. Não há necessidade de pagar todos esses serviços. Chaves e credenciais de desenvolvimento jamais devem ser incluídas no aplicativo distribuído.

### Sequência de execução e critérios de aprovação

| Marco | Estimativa de esforço/calendário | Resultado exigido para continuar |
|---|---|---|
| Definição e auditoria | 1–2 semanas | Público, região, hardware, licenças, decisão sobre fork e escopo definidos |
| Prova técnica e UX | 1–2 semanas | IA em máquina fraca, ZIM, mapa e download interrompido funcionando sem rede |
| MVP | 4–8 semanas | Instalador, perfis, biblioteca, busca com fontes, mapas básicos, planos e armazenamento |
| Beta e publicação | 2–4 semanas | Testes Linux nativo, acessibilidade, recuperação, revisão de conteúdo e site |
| Manutenção | Contínua | Atualizações, correções, suporte, curadoria e contratos comerciais |

Uma hipótese inicial é **8–16 semanas** para um MVP enxuto com dedicação integral e experiência, com sobreposição de algumas atividades. Não é prazo contratado. Integração de rádio ao vivo, roteamento completo, satélite, sincronização entre dispositivos e múltiplas plataformas devem ficar fora do primeiro lançamento para preservar a entrega básica.

O orçamento deve separar desenvolvimento, revisão técnica/editorial, licenciamento, testes, identidade, hospedagem, suporte e distribuição. Um exercício de 300–600 horas multiplicado pelo valor/hora acordado é mais útil que um preço fechado sem requisitos; a R$100/h, daria R$30–60 mil apenas de trabalho, exemplo de cálculo e não cotação. Se você desenvolver com auxílio de IA, o desembolso muda, mas pesquisa, testes e manutenção continuam consumindo tempo.

A banda merece orçamento próprio: mil downloads de 30 GB representam 30 TB de transferência. Precisamos cotar armazenamento e distribuição com limites de gastos, aproveitar origens autorizadas e evitar espelhar material sem permissão. Domínio, API de desenvolvimento, equipamentos de teste e eventuais revisores entram separadamente. Não há custo mensal confiável sem prever usuários e tamanhos reais.

A aprovação do MVP precisa demonstrar abertura e consulta com rede desligada, leitura sem modelo, respostas em português com fontes corretas, comportamento seguro quando falta evidência, limites de RAM, falha de GPU com alternativa e uso em máquinas reais. Também precisa comprovar retomada de download, rejeição de hash inválido, recuperação após interrupção, preservação de planos e funcionamento integral dos mapas sem fontes externas. Testar teclado, ampliação de texto e legendas deve fazer parte do aceite, junto da conferência de licenças e publicidade.

Sugiro um conjunto revisado de 150–300 perguntas em português para avaliar citações, recuperação e respostas; esse número é uma proposta de avaliação, não uma norma. Medir tempo até primeira resposta, uso de memória, consumo em bateria e sucesso de instalação. A receita de afiliados deve ser medida separadamente da utilidade offline, para não incentivar recomendações comerciais inadequadas.

### Informações que preciso de você antes de implementar

Você pode responder primeiro às perguntas da primeira tabela; as demais podem ser fechadas antes de cada marco correspondente. Não preciso de senhas ou tokens pelo chat.

| Prioridade imediata | Sua resposta necessária |
|---|---|
| Público e cenário | Para quem é o produto: famílias urbanas, interior, trilha, preparação para enchentes, apagões ou outros? |
| Região piloto | Qual cidade/estado será a referência inicial de conteúdo e mapas? |
| Hardware | Qual CPU, RAM, GPU/VRAM e armazenamento da sua máquina e das máquinas mais fracas que deseja atender? |
| Linux | Você aceita começar por Ubuntu 24.04 x86_64? Precisa de outra distribuição desde o lançamento? |
| Orçamento e trabalho | Quanto pode investir inicialmente e por mês? Vai programar, contratar ou trabalhar em equipe? Quantas horas terá? |
| Prazo e escopo | Existe data alvo? Quais três funções são indispensáveis para a primeira versão? |
| Base e licença | Aceita uma adaptação aberta do LastBook, com marca própria e cumprimento das licenças? |
| Marca | Já tem nome, domínio, identidade ou prefere propostas? |

| Antes de montar os pacotes | Sua resposta necessária |
|---|---|
| Espaço e conexão | Qual limite aceitável de download e disco para leve, moderada e parruda? Haverá uso de SSD/USB? |
| Enciclopédias | Apenas português inicialmente? Quais outros idiomas e coleções têm prioridade? |
| Mapas | Município, estado ou Brasil? Precisa de rotas offline no primeiro lançamento ou visualização basta? |
| Conteúdo | Quais canais, autores e grupos você já acompanha? Tem contato ou autorização para uso offline? |
| Revisão | Há profissionais ou parceiros para revisar saúde, água, incêndios e comunicação? |
| Rádio | Quer ensinar LoRa ou controlar rádios no aplicativo? Já possui equipamento e comunidade local? |
| Compras | Qual cenário, faixa de gasto e perfil familiar orientarão a primeira cesta? Crianças, idosos e animais são relevantes? |

| Antes da monetização e publicação | Sua resposta necessária |
|---|---|
| Afiliados | Tem cadastro aprovado em algum programa? Qual site e canal foram declarados? |
| Parcerias | Conhece lojas/fabricantes interessados em autorizar recomendações no desktop? |
| Receita | Prefere gratuito com afiliados/doações, suporte pago, oficinas ou outro modelo? |
| Operação | Já possui CPF/CNPJ adequado, contador, domínio e responsável pelo suporte? |
| Transparência | Concorda com publicidade explícita, alternativas sem comissão e ordenação por adequação? |
| Privacidade | Aceita não exigir conta e manter telemetria desativada inicialmente? |
| Continuidade | Quem manterá pacotes, correções, links, respostas ao público e revisões? |

Com essas respostas, o próximo trabalho concreto será uma especificação fechada do MVP, a matriz de testes e a auditoria do fork. A primeira prova técnica deve demonstrar utilidade no computador mais fraco escolhido; ela determinará os limites dos perfis e evitará construir o produto em torno de uma promessa de IA que o hardware real não sustenta.

**Para responder agora, bastam quatro conjuntos de informações:** (1) público, riscos principais e cidade/estado; (2) orçamento, prazo e quem desenvolverá; (3) hardware mínimo e distribuição Linux; (4) aceitação de código aberto, modelo de receita e eventual nome. As outras decisões podem ser detalhadas nos marcos indicados, antes de implementarmos ou publicarmos cada parte.
