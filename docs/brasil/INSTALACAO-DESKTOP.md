# Instalação dos aplicativos de desktop

## Estado e requisitos

A [página da alpha 9](https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/v0.4.0-alpha.9)
lista os pacotes já validados para download. Os sistemas suportados são Linux
x86_64 (Ubuntu 24.04–26.04), Mac Intel e Apple Silicon (macOS 13.3 ou posterior)
e Windows x64 (Windows 10 versão 1809 ou posterior).

O instalador Windows inclui o WebView2 Runtime. Os pacotes Mac e Windows
incluem Python e o motor local. Modelos GGUF, enciclopédias e mapas são baixados
por ação explícita no aplicativo. O perfil Leve recomenda 8 GB de RAM instalada.
A IA do perfil Leve exige 2,5 GiB livres no momento da resposta.

## Escolha do pacote

No macOS, confira em **Sobre Este Mac** se o processador é Apple Silicon (ARM) ou Intel e escolha o DMG da arquitetura correspondente. No Windows, use o instalador para a instalação comum por usuário ou extraia o ZIP portátil em uma pasta onde sua conta possa gravar. O ZIP não instala o WebView2 Runtime: se ele não estiver disponível no computador, a interface pode não iniciar até que o runtime seja instalado por um meio confiável.

## Primeira abertura e uso offline

**Minha instalação** mostra a memória detectada, o número de processadores
lógicos e o espaço livre. Confira a sugestão de perfil e escolha o modelo de IA,
as Wikipedias e o mapa. O download começa após sua confirmação. Você pode abrir
a biblioteca imediatamente e escolher os downloads depois.

A **Biblioteca** já inclui três PDFs em português. Leia as páginas no aplicativo
ou abra o PDF no leitor do sistema. O **Assistente local** retoma os turnos recentes
para responder a perguntas de seguimento. As conversas e as referências ficam no
computador. Use **Nova conversa** para limpar o histórico.

Na alpha 9, **Minha instalação** mostra os componentes da seleção,
seus tamanhos, o que já está instalado e o espaço necessário antes de baixar.
A **Biblioteca** reúne a busca em guias, PDFs, Wikipedia (enciclopédia) e lugares
dos mapas vetoriais instalados. Em **Verificar uso offline**, o aplicativo testa
a leitura local e executa uma inferência curta quando a IA está configurada.

O assistente mostra a RAM disponível para o modelo. Use **Parar resposta**
para interromper a geração e recuperar a pergunta sem gravar uma resposta parcial.

Na Biblioteca, **Guias por situação** reúne leituras por apagão, enchente,
falta de água, calor intenso e cuidados com alimentos. Os resumos e o texto
dos PDFs ficam disponíveis offline. Os botões de referência abrem as fontes
no navegador. Em **Minha preparação**, o botão do guia de compras abre
o site do projeto e pode pedir acesso.

## Preparação familiar e municipal

Em **Plano familiar**, combine dois pontos de encontro, um contato fora da área,
responsáveis pelo apoio e o que levar. Em **Salvar cópia HTML offline**,
selecione só os campos que deseja levar no celular ou imprimir. Em **Acesso
rápido**, ensaie abrir o plano, os contatos, o mapa e os guias com a rede desligada.

Cadastre pontos em **Lugares salvos** e confira a cobertura dos mapas
instalados. Em **Mapas locais**, use **Salvar recorte para impressão**. O recorte
pode incluir lugares pessoais, conforme o que estiver visível. Em **Minha
região**, selecione o município para consultar o histórico do Atlas Digital de
Desastres de 1991 a 2025 e guias temáticos. As contagens são registros históricos,
sem previsão ou indicação de rota. A amostra de Itajaí inclui cinco UBS no CNES
e sete locais de abrigo cadastrados no plano municipal. Confira o atendimento
e os abrigos em funcionamento com os serviços locais.

Para importar dados locais, use **Minha região → Importar camada GeoJSON**.
Arquivos em WGS84 (longitude e latitude, EPSG:4326) devem conter uma coleção de
pontos para saúde ou abrigos, ou de polígonos para risco. Informe a fonte e a
data de referência e ative a camada no mapa. Preserve o arquivo original para
reimportar quando necessário. A origem exibida é a informada na importação.

O botão **Recuperação** reúne um guia pós-enchente e registros pessoais com
datas, protocolos e fotos. Use **Inventário** para anotar quantidade, local e
data para revisão. O modelo do site pode ser preenchido no navegador e impresso
em A4, ou salvo pela opção PDF do navegador.

## Dados e backups

Os dados ficam em `~/Library/Application Support/UltimoLivro` no macOS, `%LOCALAPPDATA%\UltimoLivro` no Windows e, no Linux, em `$XDG_DATA_HOME/ultimo-livro` (ou `~/.local/share/ultimo-livro` se `XDG_DATA_HOME` não estiver definido). Se `ULTIMO_LIVRO_DATA` estiver definida, ela substitui o diretório padrão em qualquer sistema. Para fazer backup, feche o aplicativo e copie essa pasta para um local seguro; para restaurar, feche o aplicativo e recoloque os dados na pasta correspondente. Preserve os arquivos GGUF, Wikis e mapas se quiser manter os downloads locais. Arquivos importados permanecem na pasta ou no disco de origem: copie-os também e, se o caminho mudar, importe-os novamente no aplicativo.

Abra **Verificar uso offline → Backup e recuperação**. Escolha
**Exportar backup** e selecione a pasta do pendrive ou outro destino. O arquivo
inclui o checklist, as escolhas de instalação e os registros de preparação com fotos. A opção de incluir o chat
também grava perguntas e respostas. Ao restaurar, um backup com chat substitui
o histórico atual. Use os botões de importação para reconectar arquivos grandes
de enciclopédias ou mapas onde já estão salvos.

## Medir a IA em um i3 com 8 GB

Com o perfil Leve e o modelo de 0,6 bilhão de parâmetros já baixado, execute
a partir do repositório no notebook Linux:

```bash
python3 tools/medir_ia_linux.py \
  --raiz /opt/ultimo-livro \
  --modelo "${XDG_DATA_HOME:-$HOME/.local/share}/ultimo-livro/models/Qwen3-0.6B-Q8_0.gguf" \
  --saida /tmp/medicao-ultimo-livro-i3.json
```

O relatório registra processador, RAM instalada, RAM disponível, tempo até
concluir duas respostas e o maior RSS observado no motor de IA. A medição
usa dados de teste e um modelo já baixado. O RSS se refere ao motor de IA,
enquanto a janela e os demais processos ficam fora da medição. Anote também
se estava na tomada ou na bateria e confira manualmente as duas respostas.

## Assinatura e limites

Os pacotes macOS usam assinatura ad hoc; os instaladores Windows não têm certificado comercial. Gatekeeper ou SmartScreen podem mostrar avisos, e não há garantia de aprovação automática. Confira a origem e a integridade do pacote e siga as opções de análise disponíveis para aquele arquivo; não desative proteções globais.

## Licenças e fontes

Os pacotes 0.4 autocontidos incluem uma pasta `licenses` com textos, avisos e um
`MANIFESTO.json` de versões, origens e hashes. No Windows, ela fica em
`_internal/licenses` dentro da pasta do aplicativo. No macOS, integra o conteúdo
do aplicativo; use **Mostrar Conteúdo do Pacote** para inspecioná-la.

A release deve oferecer gratuitamente o arquivo `fontes` da plataforma e
arquitetura correspondente, além dos instaladores. Esse ZIP é destinado à
inspeção e reconstrução dos componentes; não é necessário para usar o aplicativo.
Modelos, enciclopédias e mapas não estão nesse arquivo. Os componentes Microsoft
continuam com seus próprios termos; a licença MIT do projeto não os relicencia.

Para empacotar localmente, `GITHUB_SHA` precisa apontar para o commit completo
publicado que corresponde ao código sob compilação, e `GITHUB_REPOSITORY` deve
identificar o fork. O CI fornece esses valores automaticamente. A coleta de
fontes é uma etapa do mantenedor com conexão, não uma atividade do aplicativo.
