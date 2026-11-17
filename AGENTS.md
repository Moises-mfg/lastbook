# Roteamento de modelos — O Último Livro

Aplicar somente a este projeto e ao fork `Moises-mfg/lastbook`, incluindo site e
aplicativos Linux, macOS e Windows. Usar recursos nativos do Codex, sem contratar
APIs ou plugins pagos.

- Leve: GPT-6-Luna, esforço low; status de CI, inventários, leitura delimitada,
  textos curtos e tarefas determinísticas. Agente `ultimo_livro_leve`.
- Comum: GPT-6.1-Sol, esforço medium; implementação delimitada e testes comuns.
  Agente `ultimo_livro_implementacao`.
- Complexa: GPT-6-Astra, esforço high; arquitetura, falhas nativas difíceis,
  segurança, concorrência, risco de dados e auditoria final.
  Agente `ultimo_livro_complexo`.

O coordenador escolhe o nível mais leve suficiente. Escalonar quando houver
ambiguidade, risco ou falha não explicada. Não usar modelos pesados para tarefas
triviais nem todos os agentes em cada tarefa.

Fornecer apenas caminhos, objetivos e evidências necessários. Usar
`fork_turns="none"` quando disponível. Não duplicar trabalho. No máximo três
subagentes ativos; edição paralela somente em arquivos distintos. Git, integração
e publicação ficam com o coordenador.

Quando o cliente não recarregar agentes durante a conversa, especificar modelo e
esforço na ferramenta de delegação. Se um modelo estiver indisponível, informar e
usar alternativa adequada disponível. Nunca alegar troca que não ocorreu.

O modelo principal não muda automaticamente por este arquivo. O roteamento
ocorre nas subtarefas; a troca do principal depende do seletor do cliente.

Não alterar sandbox, aprovações, credenciais ou provedores para habilitar o
roteamento. Não declarar aplicativo usável somente por sintaxe ou testes de outro
sistema: conferir o pacote executado no sistema de destino.
