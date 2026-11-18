"""Diretório editorial local. Nenhum vídeo, página ou conversa é copiado."""
from urllib.parse import urlsplit

from .situacoes import SOURCES

RECURSOS = [
    {'id':'defesa-kit','nome':'Defesa Civil do Paraná · kit de emergência','categoria':'Preparação','tipo':'Fonte oficial','url':'https://www.defesacivil.pr.gov.br/Pagina/Kit-de-Emergencia-pessoal','resumo':'Lista de referência para organizar documentos, água, alimentação e itens pessoais. Adapte às pessoas e aos riscos da sua região.','observacao':'Orientação estadual; confira também a Defesa Civil do seu município.'},
    {'id':'midr-alertas','nome':'MIDR · alertas da Defesa Civil','categoria':'Preparação','tipo':'Fonte oficial','url':'https://www.gov.br/mdr/pt-br/acesso-a-informacao/perguntas-frequentes/perguntas-frequentes-defesa-civil/alertas','resumo':'Informações sobre recebimento de alertas. Conheça os canais e faça os cadastros enquanto houver conexão.','observacao':'O aplicativo offline não recebe nem atualiza alertas de risco.'},
    {'id':'saude-agua','nome':'Ministério da Saúde · cuidados com a água','categoria':'Preparação','tipo':'Fonte oficial','url':'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes/cuidados-com-a-agua/cuidados-com-a-agua','resumo':'Referência oficial sobre água para consumo em contexto de enchentes. Consulte as instruções para o produto e a concentração exatos.','observacao':'Esta referência não substitui avaliação das condições locais de água e saneamento.'},
    {'id':'meshtastic-docs','nome':'Meshtastic · documentação oficial','categoria':'LoRa e redes mesh','tipo':'Projeto aberto','url':'https://meshtastic.org/docs/getting-started/','resumo':'Primeiros passos, equipamentos e configuração da rede de mensagens por rádio LoRa. A documentação principal está em inglês.','observacao':'Confira a versão do firmware e a configuração adequada ao Brasil. Um nó isolado não cria cobertura.'},
    {'id':'meshtastic-grupo','nome':'Comunidade Meshtastic Brasil · Telegram','categoria':'LoRa e redes mesh','tipo':'Comunidade independente','url':'https://t.me/meshtastic_br','resumo':'Grupo brasileiro indicado no diretório de comunidades do projeto Meshtastic. Útil para conhecer participantes e iniciativas locais.','observacao':'A conversa depende do Telegram e da conexão. Não há integração de mensagens no aplicativo.'},
    {'id':'meshbrasil-regionais','nome':'MeshBrasil · grupos regionais','categoria':'LoRa e redes mesh','tipo':'Comunidade independente','url':'https://www.meshbrasil.com/grupos-regionais.html','resumo':'Diretório comunitário para procurar grupos por região e combinar testes de comunicação antes de depender da rede.','observacao':'O projeto comunitário também divulga serviços e equipamentos comerciais. Não temos comissão ou parceria.'},
    {'id':'meshcore-docs','nome':'MeshCore · projeto e documentação','categoria':'LoRa e redes mesh','tipo':'Projeto aberto','url':'https://github.com/meshcore-dev/MeshCore','resumo':'Documentação e código de outro ecossistema de comunicação mesh por rádio. Consulte o próprio projeto para firmware e suporte.','observacao':'MeshCore e Meshtastic são ecossistemas diferentes. Não presuma comunicação direta entre eles.'},
    {'id':'labre-estaduais','nome':'LABRE · entidades estaduais','categoria':'Radioamadorismo','tipo':'Entidade de radioamadores','url':'https://www.labre.org.br/estaduais-da-labre/','resumo':'Diretório das entidades estaduais para conhecer atividades e pessoas ligadas ao radioamadorismo na sua região.','observacao':'Conhecer um grupo não autoriza transmitir. Consulte os requisitos aplicáveis ao serviço e ao equipamento.'},
    {'id':'anatel-produtos','nome':'Anatel · certificação de produtos','categoria':'Radioamadorismo','tipo':'Fonte oficial','url':'https://www.gov.br/anatel/pt-br/regulado/certificacao-de-produtos','resumo':'Ponto de partida oficial para verificar informações sobre certificação e homologação antes da compra de equipamentos.','observacao':'O portal pode solicitar verificação no navegador. A homologação deve corresponder ao modelo exato.'},
    {'id':'sobrevivencialismo','nome':'Sobrevivencialismo · Portal SV','categoria':'Canais e formação','tipo':'Criador e plataforma comercial','url':'https://membros.sobrevivencialismo.com/','resumo':'Portal dos criadores de Sobrevivencialismo com conteúdos sobre preparo, atividades de campo e autossuficiência.','observacao':'Há assinatura e conteúdos pagos. A indicação identifica a fonte; não avalia ou aprova todos os ensinamentos. Não temos comissão.'},
    {'id':'julio-lobo','nome':'Julio Lobo · apresentação e projetos','categoria':'Canais e formação','tipo':'Criador independente','url':'https://juliolobo.com.br/sobre','resumo':'Apresentação do criador dos canais Julio Lobo, Sobrevivencialismo e Rancho SV, para conhecer a autoria e os temas publicados.','observacao':'Conteúdos e serviços podem ter finalidade comercial. Vídeos e cursos não estão incluídos na biblioteca offline.'},
]

for recurso in RECURSOS:
    recurso['revisado']='2026-11-17'
    recurso['offline']='Descrição e endereço disponíveis offline. A página original requer internet; nenhum material de terceiros foi redistribuído.'


def resource_url(ident):
    if not isinstance(ident,str):raise ValueError('Selecione uma referência válida.')
    item=next((r for r in RECURSOS if r['id']==ident),None)
    if item is None and ident not in SOURCES:raise ValueError('Referência não encontrada.')
    url = item['url'] if item is not None else SOURCES[ident][1]
    parsed = urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Endereço da referência inválido.')
    return url
