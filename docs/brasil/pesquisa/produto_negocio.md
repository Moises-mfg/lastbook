# Produto, site e monetização no Brasil

## Como aproveitar LastBook e estruturar produto e site?

### Takeaway
Recomendação: núcleo offline gratuito, voltado a preparação doméstica e resiliência no Brasil, com marca própria e site editorial público separado. Fazer primeiro uma auditoria de reaproveitamento do LastBook, antes de decidir entre fork e aplicativo novo.

### Cited Findings
- Código original e documentação LastBook usam MIT: permitem uso, modificação e venda, preservando avisos de copyright e licença. Isso não equivale a permissão automática de marca, vídeos, mapas, modelos ou biblioteca de terceiros. [Licença](https://github.com/Immortal-Protocols/lastbook/blob/main/LICENSE), [avisos terceiros](https://github.com/Immortal-Protocols/lastbook/blob/main/THIRD_PARTY_NOTICES.md).
- O repositório descreve desktop com vídeos, mapa e chat com fontes; Linux direcionado a Ubuntu 24.04 x86_64, versão exibida 1.1.9. [Repositório](https://github.com/Immortal-Protocols/lastbook). Não copiar promessa de compatibilidade universal.
- A página https://lastbook.org/library/ não abriu no leitor web desta pesquisa; não inventar avaliação visual ou catálogo desta página. Outro pesquisador pode conseguir acesso.

### Inferences
Propostas de produto, não fatos sobre LastBook:
- Posicionamento: “Conhecimento, mapas e preparação para consultar mesmo sem internet”. Evitar marketing que explora pânico ou promete sobrevivência garantida.
- Menu aplicativo: Início; Assistente local; Biblioteca; Mapas; Meu plano e estoque; Aprender e comunidades; Equipamentos; Downloads; Configurações. Busca textual deve funcionar mesmo sem IA e ser a rota mais rápida para instruções curtas.
- Inicialização: escolher pasta e disco externo; diagnóstico somente local de CPU/RAM/GPU/espaço; exibir quatro perfis; explicar tamanho real do catálogo, duração estimada usando velocidade medida, licença, data e idioma; confirmar downloads; teste offline; tutorial curto. Customizável escolhe modelo/quantização/contexto, wikis/coleções/idiomas, mapas/níveis de zoom, vídeos autorizados.
- Início: status “Pronto para uso sem internet”, componentes faltantes, armazenamento e bateria, acesso rápido a guias de emergência, favoritos, retomada downloads e data de última revisão. Cor alto contraste, tipografia legível, teclado, acessibilidade, modo claro/escuro, modo econômico. Não exigir login nem conexão para abrir app.
- Equipamentos: critérios e checklist offline, não catálogo comercial congelado; “já tenho”, “preciso”, quantidade, prioridade, validade. Link ao site editorial só após avaliação contratual da origem do tráfego; nenhuma abertura automática ou redirecionamento invisível.
- Site: páginas Início, Baixar para Linux, Compare instalações, Catálogo offline, Guias Brasil, Equipamentos, Comunidades, Documentação, Transparência/licenças, Privacidade, Contato. Cabeçalho com download e demonstração; quatro cartões claros; requisitos; exemplo de resposta com fonte; instrução sobre o que funciona offline. Site público estático acessível e rápido, sem conta no MVP; catálogo gerado de manifesto versionado; conteúdo editorial próprio revisado.
- Site não deve tentar executar modelos pesados no navegador nem ser requisito para o funcionamento do desktop. No celular deve oferecer guias, compras e planejamento, sem prometer aplicativo móvel ainda inexistente.
- Governança catálogo: registro por item com origem, autor, licença, redistribuição comercial, versão, checksum, tamanho, idioma, temas, revisor, data de revisão. Conservar atribuições junto aos arquivos; biblioteca pública não significa domínio público.

### Gaps
Marca e domínio precisam ser escolhidos e pesquisados. Auditoria técnica detalhada e inventário de dependências ainda são necessários. Não houve teste executando LastBook.

## Como monetizar sem comprometer o funcionamento offline?

### Takeaway
A ideia dos afiliados é viável no site público, mas os dois programas pesquisados trazem restrições decisivas para links embutidos no aplicativo offline. Não planejar receita desktop como se já estivesse contratualmente autorizada.

### Cited Findings
- Amazon Brasil proíbe links especiais/conteúdo do programa em software instalável, inclusive desktop, salvo aplicativos móveis aprovados. Seu contrato também regula preços e uso de conteúdo obtido por APIs. [Políticas, seção 5 e requisitos](https://associados.amazon.com.br/help/operating/policies).
- Amazon exige identificação próxima dos links e declaração de associado. Há duas traduções oficiais; usar a redação do contrato vigente no cadastro. [Identificação](https://associados.amazon.com.br/help/node/topic/GPXFHVYZMTGPUMPE).
- Mercado Livre informa que links não podem ser compartilhados em meios offline ou grupos fechados; meios válidos são redes sociais, sites e blogs públicos declarados. [Regra oficial](https://www.mercadolivre.com.br/l/afiliados-compartilhamento-de-publicacao). Proíbe abrir marketplace automaticamente sem clique. [Direcionamento](https://www.mercadolivre.com.br/l/afiliados-direcionamento-de-visitas).
- CDC art. 36 exige publicidade identificável; art. 37 proíbe publicidade enganosa e abusiva, inclusive exploração do medo. [CDC](https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm).
- CONAR publicou atualização do guia em 26/05/2026, com identificação publicitária, testemunhais, IA e governança. [Guia atualizado](https://www.conar.org.br/noticias/guia-de-marketing-e-publicidade-por-influenciadores-digitais).
- LGPD exige finalidade, necessidade e transparência; consentimento não é a única base possível, e coleta deve ser mínima. [ANPD perguntas](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes), [guia interesse legítimo](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-lanca-guia-orientativo-sobre-legitimo-interesse).

### Inferences
- Fluxo proposto: guia editorial público próprio → comparação real de critérios → clique voluntário identificado → lojista. Cadastro do site e aprovação do programa precedem publicação de links. Não presumir que app → página intermediária → Amazon contorna proibição de associação com software; obter resposta escrita descrevendo exatamente esse fluxo.
- Alternativa para compras dentro do app: contratos diretos com fabricantes/lojas permitindo explicitamente software desktop e recomendações offline. Até isso existir, checklist local sem links afiliados.
- Aviso de exemplo: “Publicidade: este conteúdo contém links de afiliado; podemos receber comissão por compras qualificadas”. Preservar também declaração específica exigida pelo programa. Não dizer “compre para apoiar o projeto” quando programa vedar incentivo desse tipo.
- Não gravar imagens e preços de marketplace no pacote offline sem licença. Usar imagens próprias/autorizadas e especificações editoriais. Exibir preço somente via forma autorizada e atualizada ou “consultar preço na loja”. Não deixar IA inventar preço, estoque, certificação ou substituto.
- Catálogo editorial ordenado por adequação, custo total, disponibilidade, reparabilidade e certificações; comissão não deve decidir segurança nem posição. Divulgar critérios e conflitos. Incluir opções sem comissão.
- Links podem expirar; checagem periódica no site, data de atualização e opção de relatar problema. Offline mostrar “compra e preço exigem internet”; nenhuma comissão acontece sem compra elegível atribuída e confirmada.
- Receita = visitas qualificadas × taxa de clique × conversão × ticket elegível × comissão efetiva, descontando cancelamentos, impostos e despesas. Exemplo SOMENTE HIPOTÉTICO: 10.000 visitas × 20% × 3% × R$250 × 4% = R$600 brutos/mês. Não são taxas atuais dos programas nem previsão.
- Receitas complementares propostas: doações voluntárias separadas dos links; suporte; oficinas; instalação e configuração; venda de SSD pronto apenas com conteúdos redistribuíveis; licenças institucionais de suporte e manutenção; patrocínios sinalizados. Não bloquear biblioteca já baixada por expiração de assinatura.
- Privacidade: sem login obrigatório, chats/localização/estoque no dispositivo, telemetria desativada por padrão, consentimentos e avisos adequados no site, retenção mínima, exportar/apagar dados. Conexão online sempre visível, inclusive atualização.

### Gaps
Termos completos Mercado Livre não puderam ser lidos por 403; páginas oficiais de ajuda sustentam restrições acima, mas não permitem afirmar aprovação para desktop. Comissões dependem de categoria, conta e campanha; não há taxa universal confiável para orçamento. Tributação/CNPJ/CNAE devem ser fechados com contador conforme operação concreta.

## Que sequência, modelos, orçamento e decisões são necessários?

### Takeaway
Executar por marcos verificáveis; começar Linux Ubuntu x86_64 e quatro configurações de conteúdo, sem quatro bases de código. IA é ferramenta de desenvolvimento; decisões médicas, direitos e engenharia de rádio precisam de revisores humanos.

### Cited Findings
- Anthropic documenta famílias Opus, Sonnet e Haiku e suas versões atuais em catálogo mutável. [Modelos](https://platform.claude.com/docs/en/models/overview). Google documenta famílias Gemini no catálogo igualmente mutável. [Modelos](https://aistudio.google.com/docs/models). Nenhuma dessas fontes prova superioridade neste projeto; recomendações abaixo são escolhas de trabalho, sujeitas a teste e orçamento, não ranking.

### Inferences
- Modelos por etapa: planejamento/requisitos/ameaças e arquitetura com modelo de raciocínio da categoria Claude Opus; implementação cotidiana e testes com categoria Claude Sonnet ou agente de código já contratado; importação em lote e classificação preliminar com Haiku ou Gemini Flash; leitura multimodal/inspeção de interfaces e documentos com Gemini Pro; revisão final de mudanças com outro modelo forte independente e humano. Fixar versão estável disponível na execução, realizar tarefa piloto e medir custo/qualidade. Não expor credenciais dos modelos de desenvolvimento no aplicativo distribuído. Modelos embarcados devem ser menores e separados: pesquisador técnico cobre escolha e hardware.
- Não escolher modelo por nome para criar conteúdo de emergência sem fonte. IA ajuda localizar e resumir; revisão humana qualificada e referência continuam obrigatórias.
- Fase 0, 1–2 semanas: requisitos com usuário, licença, auditoria LastBook, matriz hardware, política editorial, entrevistas e programas afiliados. Saída: decisão fork ou novo com motivo e escopo congelado.
- Fase 1, 1–2 semanas: protótipo UX e prova técnica: IA em CPU, ZIM, mapa local, interrupção de download e teste sem rede. Saída: validar máquina fraca antes de polir UI.
- Fase 2, 4–8 semanas: MVP instalável, catálogo, quatro perfis, busca, fontes, gerenciador armazenamento, biblioteca, mapas de visualização e checklist. Roteamento e rádio ao vivo podem vir depois.
- Fase 3, 2–4 semanas: testes em máquinas reais, acessibilidade, atualização assinada/rollback, pacotes Linux, revisão conteúdo e site editorial. Beta com 10–30 pessoas se houver participantes.
- Fase 4, contínua: curadoria e revisão, distribuição novos pacotes, suporte, afiliados aprovados, métricas agregadas e contratos diretos.
- Estimativa própria total: 8–16 semanas para MVP enxuto com pessoa experiente em tempo integral; equipe e escopo podem alterar. Não prazo contratado.
- Orçamento próprio: 300–600 horas × valor hora informado; exemplo R$100/h → R$30–60 mil de trabalho. Não é cotação de mercado. Acrescentar curadoria, advogado/contador quando necessários, revisores, máquinas e mídias de teste, domínio, hospedagem, APIs desenvolvimento e banda.
- Banda pode dominar custos: 1.000 downloads de 30 GB = 30 TB de transferência. Cotar CDN/armazenamento com teto e aproveitar downloads diretos autorizados do fornecedor; não espelhar conteúdo sem permissão. Custo recorrente deve usar cotação antes do compromisso.
- Critérios de aceite: inicia sem rede; busca funciona sem modelo; IA mostra fonte e ausência de informação; não excede orçamento RAM; downloads retomam e verificam hash; falta de disco e queda de energia não corrompem catálogo; atualização preserva dados; conteúdo e links comerciais têm licença/autorização; tarefas essenciais acessíveis por teclado.
- Indicadores: instalação concluída, uso offline bem-sucedido, percentual com fonte correta em conjunto de perguntas em português, tempo até primeira resposta, consumo RAM/energia, falhas e solicitações de suporte. Receita afiliada é indicador separado da utilidade do aplicativo.
- Inputs PRIORIDADE 1 antes implementação: público principal e cenários (urbano, rural, enchente, apagão etc.); região piloto; orçamento e horas disponíveis; desenvolvedor/equipe e conhecimento; especificações das máquinas alvo e sua máquina de teste; distribuição Linux e arquitetura; fork ou independência/aceitação MIT; nome/marca; escopo MVP e data desejada.
- Inputs PRIORIDADE 2 antes pacote conteúdo: limite download/armazenamento; idiomas; wikis e coleções prioritárias; regiões de mapas e necessidade real de roteamento; uso disco externo; perfis familiares e necessidades especiais opcionais sem coleta excessiva; autorização/revisores conteúdos; canais e grupos que já acompanha; permissão dos criadores para offline; interesse em comunicar com LoRa real ou somente aprender.
- Inputs PRIORIDADE 3 antes monetização/publicação: contas afiliadas existentes e programas; site/domínio/empresa/CPF-CNPJ; orçamento e categorias de compra; aceitação de publicidade clara e opções sem comissão; parceiros diretos; termos/privacidade; política telemetria; contato suporte e responsável manutenção; modelo gratuito/doação/suporte pago; logo e identidade visual. Nunca pedir senhas ou tokens pelo chat; configurar segredos localmente quando autorizado.

### Gaps
Disponibilidade exata, preço e identificação dos modelos de desenvolvimento mudam: revalidar ao iniciar. Sem respostas do usuário não fechar prazo, taxa de comissão, lista de SKUs, capacidade de downloads ou custos de distribuição.
