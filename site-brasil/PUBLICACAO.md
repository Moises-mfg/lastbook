# Publicação do site

Site de avaliação: https://ultimo-livro-brasil.genuineoffer32.chatgpt.site

- Hospedagem: plugin Sites.
- Acesso inicial: privado, para avaliação do proprietário; nenhum acesso público foi habilitado.
- Identificador: `appgprj_6afbb4c3c63881918a07ae21d93b17fa` (não é credencial).
- Fonte versionada neste GitHub: `site-brasil/`.
- Gerar saída: `python3 site-brasil/build.py`; a saída `dist/` é reproduzível e ignorada pelo Git.
- A publicação usa um checkout de hospedagem separado, sem enviar modelos, dados pessoais ou o restante da biblioteca.
- Atualizar a publicação existente, preservando seu identificador, em vez de criar outro site a cada edição.
- Não guardar credenciais de hospedagem ou do GitHub nos arquivos do projeto.

O navegador integrado não estava disponível para revisão visual. A publicação foi
confirmada pelo serviço de hospedagem. Os controles do configurador, checklist,
exportação e formato aceito pelo aplicativo são verificados por testes DOM
(`npm test --prefix site-brasil`); eles não verificam layout nem renderização.
O site é estático, não usa formulário de cadastro nem scripts/fontes externos.

A compra do domínio e a abertura do acesso público ficam para decisão do responsável.
