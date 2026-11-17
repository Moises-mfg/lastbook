# Tecnologia Linux e conteúdos offline

Pesquisa em 16/11/2026. Planejamento, sem implementação. Valores propostos são metas de engenharia, não medições do aplicativo ainda inexistente.

## O que aproveitar do LastBook e o que precisa mudar?

### Takeaway
LastBook já cobre grande parte da ideia; a oportunidade é uma edição brasileira com português, conteúdo e mapas brasileiros, perfis de IA menores e curadoria comercial transparente. Começar por estudo de viabilidade de um fork é mais eficiente que reescrever tudo.

### Cited Findings
- LastBook é biblioteca offline com PDF, vídeo, enciclopédia ZIM, mapa e chat com fontes; código original MIT. Linux publicado para Ubuntu 24.04 x86_64, versão 1.1.9; README só declara testes em WSL2 com CPU, sem validação de GPU nativa ou demais distribuições. [Repositório](https://github.com/Immortal-Protocols/lastbook).
- Biblioteca publicada: Small 7,7 GB, Medium 67,5 GB, All 387,9 GB; IA, mapas estaduais e índices adicionais. Small possui 148 PDFs, 41 vídeos e duas enciclopédias; foco cartográfico EUA. Esses números não são tamanhos do futuro produto brasileiro. [Biblioteca](https://www.lastbook.org/library/).
- IA original fixada no código em Gemma 4 26B A4B Unsloth UD-Q4_K_M, 16.947.541.728 bytes; contexto 16.384, reserva 2,5 GiB; runner mede encaixe e encerra após inatividade. É diferente da ideia de escolher modelos pequenos por perfil. [Código de IA](https://raw.githubusercontent.com/Immortal-Protocols/lastbook/main/llm_local.py).
- Original organiza engine Python, shell GTK/WebKitGTK Linux, frontend HTML/CSS/JS sem build; comunicação por ponte e subprocesso, sem porta desktop. Downloads HTTPS com allowlist, SHA256, inspeção ZIP e atualização atômica. Busca semântica original usa modelo inglês BGE apenas em Windows; não presumir busca semântica portuguesa no Linux. [README técnico](https://raw.githubusercontent.com/Immortal-Protocols/lastbook/main/README.md).
- MIT do projeto não cobre biblioteca de terceiros; python-libzim listado GPL-3.0-or-later, libzim GPL-2.0, demais componentes têm termos próprios. [Licenças de dependências](https://raw.githubusercontent.com/Immortal-Protocols/lastbook/main/THIRD_PARTY_NOTICES.md). [Créditos e direitos](https://www.lastbook.org/credits/).

### Inferences
- Recomendação: fork/derivação com marca própria após auditoria técnica e de licenças; manter Python + WebKitGTK + frontend local inicialmente. Não adotar Tauri/Electron apenas para modernizar aparência: reescrita amplia risco e não resolve conteúdo, mapas e qualidade da IA.
- Código MIT permite uso comercial com preservação dos avisos; combinação/distribuição com bibliotecas GPL precisa de avaliação específica e disponibilização de código conforme obrigações. Um app aberto financiado por afiliados é compatível com estratégia comercial; software aberto não implica ausência de receita.
- Empacotamento inicial .deb Ubuntu 24.04 LTS x86_64; validar Ubuntu nativo e Mint baseado em 24.04; AppImage/Flatpak e ARM64 depois. Contêineres não validam áudio, vídeo, GPU e experiência desktop. Declarar matriz de suporte explicitamente.
- Não copiar marca, desenhos nem todos PDFs/vídeos do LastBook sem permissões. Conteúdo acessível na internet não equivale a direito de redistribuir.

### Gaps
- Não executei nem auditei toda a implementação LastBook. README e site apresentam pequenas diferenças de versões Mac; fixar commit/artefato na prova técnica, não prometer suporte a partir da documentação.

## Como dimensionar IA, Wikipedia e mapas?

### Takeaway
Os quatro perfis devem ser predefinições editáveis de um único instalador. Modelo, mapa e enciclopédia são escolhas independentes: muito armazenamento não significa memória suficiente para IA grande.

### Cited Findings
- Qwen3 0.6B, 4B, 8B e 14B oferecem opções Apache-2.0. São candidatos verificáveis, não garantia de melhor desempenho em português ou os menores existentes no mundo. [0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), [4B Instruct 2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507), [8B](https://huggingface.co/Qwen/Qwen3-8B), [14B](https://huggingface.co/Qwen/Qwen3-14B).
- Repositórios oficiais GGUF consultados mostram 0.6B Q8_0 639 MB; 4B Q4_K_M 2,5 GB; 8B Q4_K_M 5,03 GB; 14B Q4_K_M 9 GB. São arquivos específicos, não RAM total de execução. Baixar arquivo escolhido, não repositório com todas quantizações. [0.6B GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/tree/main), [4B GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/main), [8B GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main), [14B GGUF](https://huggingface.co/Qwen/Qwen3-14B-GGUF/tree/main).
- llama.cpp oferece inferência C/C++ e backends CPU/GPU, com builds distintos. [Projeto](https://github.com/ggml-org/llama.cpp), [Builds e backends](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md). Ollama tem requisitos concretos de drivers/GPUs e não elimina problemas de compatibilidade. [Suporte de hardware](https://docs.ollama.com/gpu).
- Kiwix: mini inclui introdução e infobox; nopic inclui artigos completos sem imagens; maxi inclui versão completa. Os percentuais de redução do FAQ são gerais, não tamanho da edição portuguesa. [FAQ oficial](https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/).
- Multilingual-e5-small tem licença MIT, embeddings de 384 dimensões e suporte multilíngue; candidato leve para busca portuguesa. [Modelo](https://huggingface.co/intfloat/multilingual-e5-small). Qwen3-Embedding-0.6B é alternativa a avaliar, não confundir com modelo gerador. [Modelo](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).
- Geofabrik disponibiliza Brasil OSM bruto .pbf de aproximadamente 2 GB em 15/11/2026 e recortes regionais. Esse tamanho NÃO é o mapa renderizado completo, nem inclui terreno, satélite, fontes ou índice de endereços. [Brasil](https://download.geofabrik.de/south-america/brazil.html).
- OSM exige atribuição e tem licença ODbL. Não baixar em massa os tiles públicos de tile.openstreetmap.org; construir pacotes próprios ou contratar provedor permitido. [Licença](https://www.openstreetmap.org/copyright), [Política de tiles](https://operations.osmfoundation.org/policies/tiles/).
- Protomaps/MapLibre podem trabalhar com arquivos PMTiles; offline exige também estilos, fontes, sprites, JS e CSS locais. MBTiles é alternativa SQLite. [Integração](https://docs.protomaps.com/pmtiles/maplibre), [Segurança e recursos](https://docs.protomaps.com/guide/security-privacy), [Formatos](https://docs.protomaps.com/pmtiles/).
- Exibição de mapa não oferece roteamento automaticamente; Valhalla é um motor separado para OSM. [Valhalla](https://github.com/valhalla/valhalla).

### Inferences
Proposta de perfis, todos sujeitos a benchmark e catálogo real:

| Perfil | IA candidata | Hardware alvo de projeto | Enciclopédia/mapa | Meta de armazenamento instalado |
|---|---|---|---|---|
| Leve | Qwen3-0.6B, começar com GGUF oficial Q8; quantização Q4 própria somente após validação | 4 GB RAM como limite experimental, 8 GB recomendado; CPU, GPU dispensável | Wikipedia portuguesa mini, guias essenciais e município/região escolhida | 5–12 GB |
| Moderada | Qwen3-4B Instruct; comparar 8B se memória/latência permitirem | 16 GB RAM; GPU opcional | Wikipedia portuguesa nopic, mapas de um estado, vídeos essenciais licenciados | 25–60 GB |
| Parruda | Qwen3-14B Q4; 8B como opção mais rápida | 32 GB RAM; 12–16 GB VRAM desejável para aceleração, sujeito a contexto/driver | Wikipedia portuguesa maxi, outros idiomas opcionais, Brasil vetorial, mais vídeos | 100–250 GB ou mais |
| Personalizada | catálogo de GGUF aprovados ou arquivo importado validado | calculado por modelo, contexto e backend | idiomas, variantes, regiões, camadas e vídeos escolhidos | soma exata do manifesto |

- Estes totais são orçamentos propostos, não tamanhos confirmados de Wikipedia PT. Não prometer faixa até congelar ZIMs e gerar mapas/pacotes. IA menor deve resumir fontes simples e encontrar páginas; não vender como conselheiro confiável em medicina ou engenharia.
- A frase “menor IA disponível” deve virar “menor IA aprovada que passa nos testes em português”; sempre haverá modelos menores inúteis para o caso. Explicar isso ao usuário.
- Seleção automática local: CPU/arquitetura/AVX, RAM total e disponível, GPU/VRAM/driver, espaço e filesystem; benchmark curto opcional. Estimar pesos + KV cache + buffers + embeddings + interface + reserva OS. Não somar RAM e VRAM ingenuamente, nem ignorar memória compartilhada de iGPU.
- Configurar contexto inicial 2–4 mil tokens no Leve, 4–8 mil no Moderado e 8 mil no Parrudo; aumentar só com memória disponível. Mostrar tempo estimado medido, permitir CPU e redução de contexto. GPU falha -> CPU; RAM insuficiente -> modelo menor ou busca/leitura sem geração. Nunca travar o acesso à biblioteca porque IA falhou.
- Wikipedia escolhível por idioma e variante, mostrando claramente que mini não possui artigos integrais. Importar .zim existente. Não “traduzir a Wikipedia inteira” com IA para suprir lacunas.
- RAG: extrair texto com IDs de fonte/página, busca lexical primeiro, embeddings multilíngues opcionais, recuperação híbrida, trechos e citações verificáveis. Fontes têm data, autor, licença e revisão. Recusar afirmação quando não houver base; abrir página citada sem internet. Índices vetoriais da Wikipedia inteira podem crescer e custar dias para gerar: começar apenas com guias e artigos recuperados, distribuir índices de conjuntos curados.
- Mapa mínimo: visualizar, pesquisar locais, salvar pontos, importar/exportar GPX, distância. Fase posterior: geocodificação de endereços e roteamento a pé/carro com grafo offline próprio. Não prometer rotas seguras em enchentes ou hospitais funcionando a partir de dados estáticos.
- Mapas por município, estado e país; recortes sobrepostos com deduplicação, data de atualização, escala/zoom e aviso de cobertura. Relevo opcional; satélite fora do MVP por volume/licença.

### Gaps
- Catálogo Kiwix web sofreu bloqueio de confirmação e índice consultado não retornou entradas portuguesas via ferramenta. Não obtive tamanho/data exatos de ZIM português atual; usar catálogo oficial no congelamento, sem inventar GB. Catálogo: https://get.kiwix.org/en/solutions/catalog/ .
- Sem benchmarks locais de português, consumo energético, RAM mínima ou velocidades de geração. Modelos acima são candidatos conservadores, não ranking dos melhores em novembro de 2026.

## Como instalar, atualizar, proteger e validar?

### Takeaway
Distribuir um aplicativo pequeno com gerenciador de pacotes de dados é mais sustentável que quatro instaladores gigantes. Importação por USB e funcionamento completamente desconectado são critérios de aceitação centrais.

### Cited Findings
- LastBook já verifica SHA256, arquivos ZIP perigosos, faz troca atômica e não exige conta; vale reaproveitar o desenho após revisão. [Setup](https://raw.githubusercontent.com/Immortal-Protocols/lastbook/main/README.md).
- Recursos de mapa externos podem causar vazamentos e quebrar offline mesmo com tiles locais. [Protomaps](https://docs.protomaps.com/guide/security-privacy).

### Inferences
- Manifesto assinado com ID, versão, origem, licença, tamanho download/instalado/temporário, SHA256, dependências, idiomas e data de revisão; assinatura protege autenticidade, checksum isolado não protege manifesto comprometido.
- Downloads retomáveis HTTP Range e ETag, fila, pausa, seleção de pasta/disco externo, limitação de banda; verificar espaço para staging e rollback. Modelo/ZIM grandes devem permanecer como arquivo final quando possível, sem duplicação ZIP desnecessária.
- Detectar FAT32 e arquivo >4 GiB; explicar em português e oferecer destino compatível. Testar unidades removíveis, permissões, nomes com acentos, espaço cheio, desconexão e quedas de energia.
- Conteúdo carregado em renderizadores sem executar scripts arbitrários, bloqueio de acesso à rede embutida e paths; isolamento de PDF/vídeo, prevenção ZIP Slip/bombas, validação de arquivos importados, sem executar código de modelo remoto. Conversas e coordenadas locais, sem telemetria por padrão.
- Atualização voluntária; apresentar alterações e espaço necessário; manter dados pessoais separados dos pacotes; exportação/importação da biblioteca com metadados e manifesto. Core permanece usável se CDN/projeto desaparecer.
- Links comerciais devem abrir no navegador externo após ação explícita; vídeos/canais que são apenas links aparecem como “precisa de internet”. Dados offline disponíveis mesmo quando loja/link expira.
- Testes que aprovam MVP: rede fisicamente desligada; busca PT por acento/sinônimo, fontes clicáveis, resposta sem evidência, prompt malicioso no documento, compatibilidade CPU/GPU, retomada de download, hash inválido, interrupção de instalação e rollback, offline mapas/fontes/endereço, licença/atribuição visível, mídia com legenda, leitor teclado e fonte ampliada.
- Medir resposta em PT e citações num conjunto revisado de 150–300 perguntas com respostas verificadas. Conteúdo de saúde, eletricidade e potabilização requer revisor humano qualificado; uma IA não pode validar sozinha.
- Estimativa de execução sugerida: viabilidade/licenças 1–2 semanas; protótipo Linux e hardware 2–3; biblioteca e instalação 3–5; busca/RAG 2–4; mapas/curadoria/site 2–4; piloto 2–3. Etapas sobrepõem com equipe, mas um desenvolvedor sozinho deve prever 3–6 meses ou mais, sobretudo curadoria. São estimativas, não compromissos.

### Gaps
- Custos reais de armazenamento/CDN e distribuição precisam de número de usuários e média de download. Fórmula: usuários novos × GB por instalação + atualizações; o app offline não elimina custo de distribuição inicial.
