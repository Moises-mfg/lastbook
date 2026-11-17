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
