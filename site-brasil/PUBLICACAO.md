# Como colocar o site O Último Livro no ar

A versão de avaliação fica no [site privado](https://ultimo-livro-brasil.genuineoffer32.chatgpt.site).
Para ter um endereço público sem comprar domínio, use o Cloudflare Pages e
comece pelo endereço `pages.dev` que ele fornecer. O código continua versionado
no seu GitHub.

## 1. Gere os arquivos do site

No Linux, com Git e Python 3 instalados, abra um terminal e execute:

```bash
git clone https://github.com/Moises-mfg/o-ultimo-livro.git
cd o-ultimo-livro
python3 site-brasil/build.py
```

Se já tiver o repositório, entre nele, atualize o branch `main` e execute só o
comando Python. A pasta gerada é `site-brasil/dist/`, com `index.html`,
`style.css`, `app.js`, `catalogo.js`, `downloads.js`, `plano-familiar.html`,
`plano-familiar.css` e `plano-familiar.js`. Os instaladores continuam
disponíveis nas releases do GitHub.

Para ver o resultado antes de publicar, execute
`python3 -m http.server 8000 --bind 127.0.0.1 --directory site-brasil/dist` e abra
`http://127.0.0.1:8000` no navegador. Encerre o servidor com **Ctrl+C**.

## 2. Publique sem domínio próprio

1. Entre na sua conta no [painel da Cloudflare](https://dash.cloudflare.com/).
2. Abra **Workers & Pages** e escolha **Create application**. Em **Get started**,
   selecione **Drag and drop your files** para criar um projeto Pages por envio de arquivos.
3. Escolha um nome para o projeto e arraste a pasta `site-brasil/dist` para a área
   de envio. Confira que `index.html` está na raiz dos arquivos enviados.
4. Clique em **Deploy site**. Quando a publicação terminar, copie do painel o
   endereço HTTPS que termina em `.pages.dev`. Esse é o endereço que você pode divulgar.
5. Abra o endereço em janela anônima e no celular. Confira os links dos instaladores
   e teste o configurador, a exportação do plano JSON e o checklist. Abra também
   o plano familiar pela seção de preparação, preencha campos e confira a prévia
   de impressão em A4 e a opção de salvar PDF do navegador.

O envio direto recebe os arquivos já gerados. Para publicar automaticamente a
cada alteração no GitHub, o Cloudflare Pages exige um projeto separado criado
com integração Git. [Envio direto](https://developers.cloudflare.com/pages/get-started/direct-upload/) ·
[Integração com Git](https://developers.cloudflare.com/pages/get-started/git-integration/)

## 3. Adicione um domínio próprio quando quiser

1. Escolha e registre um domínio em seu nome. Para `.br`, consulte a
   disponibilidade no [Registro.br](https://registro.br/).
2. No projeto Pages, abra **Custom domains → Set up a domain** e adicione
   `www.seudominio.com.br`, substituindo pelo seu nome real.
3. Se o DNS estiver fora da Cloudflare, abra o painel que administra o DNS e
   crie um registro **CNAME** para `www` apontando para o endereço `.pages.dev`
   do projeto, sem `https://`. Se o DNS já estiver na Cloudflare, confirme o
   registro sugerido pelo painel.
4. Aguarde o painel confirmar a ativação e abra o novo endereço com HTTPS. Se
   quiser usar o domínio sem `www`, o Pages exige que o DNS da zona seja
   administrado pela Cloudflare. [Domínios personalizados no Pages](https://developers.cloudflare.com/pages/configuration/custom-domains/)

## 4. Atualize o site depois da publicação

Atualize o código pelo GitHub e execute novamente `python3 site-brasil/build.py`.
No mesmo projeto do Cloudflare Pages, escolha **Create a new deployment**, use
o ambiente de produção e envie a pasta `site-brasil/dist` inteira. Abra o endereço
público para conferir a nova versão.

Para preparar a monetização depois da publicação, siga o
[guia de domínio e afiliados](../docs/brasil/DOMINIO-E-AFILIADOS.md).
