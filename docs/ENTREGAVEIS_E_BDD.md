# Entregáveis do produto CodeRank

> **Status:** proposta de trabalho baseada no repositório. O README descreve o CodeRank como uma plataforma educacional competitiva de programação. Não foi encontrada uma decisão registrada do squad sobre personas, recorte de público ou priorização final. Portanto, o público-alvo abaixo é uma **proposta para validação**, não uma decisão já aprovada.

## 1. O negócio: tema, problema e público-alvo

### Tema do aplicativo
**CodeRank — plataforma educacional para prática competitiva de programação.**

O produto reúne desafios de lógica e programação, editor para escrever soluções em Python e Java, execução isolada de código, grupos de estudo/competição e ranking de participantes. A proposta é oferecer um ambiente no qual estudantes possam praticar, receber avaliação objetiva das soluções e acompanhar sua evolução.

### Problema que o produto pretende resolver
Estudantes iniciantes e intermediários precisam de um ambiente único para praticar programação, testar soluções com segurança, comparar resultados e manter a motivação por meio de metas e atividades em grupo.

### Público-alvo proposto

| Segmento | Necessidade | Prioridade proposta |
|---|---|---|
| Estudantes de programação em cursos técnicos, graduação ou formação livre | Praticar lógica e linguagens, receber retorno sobre soluções e acompanhar progresso | Primário |
| Grupos de estudo e equipes acadêmicas | Resolver desafios em conjunto e acompanhar desempenho do grupo | Secundário |
| Professores, tutores e mentores | Recomendar exercícios e acompanhar a evolução dos estudantes | Secundário/futuro |

**Validação pendente do squad:** confirmar faixa de conhecimento (iniciante, intermediário ou ambos), contexto prioritário (ensino técnico, superior ou cursos livres), papel de professores/mentores e se a competição é individual, em grupo ou ambas.

### Proposta de valor
Praticar programação em um só lugar, com desafios avaliados por casos de teste, execução isolada, progresso individual e dinâmica de grupos/ranking.

## 2. Escopo do produto

### Funcionalidades mapeadas

O código atual contém protótipos de interface para as áreas abaixo. A existência de uma tela não significa que a funcionalidade esteja concluída: várias ações ainda são simuladas ou usam dados estáticos.

| Área | Escopo esperado para o MVP | Situação observada no repositório |
|---|---|---|
| Cadastro e autenticação | Criar conta, entrar, manter sessão e sair | Login/cadastro simulados; Supabase ainda não integrado |
| Desafios | Listar desafios, visualizar enunciado, dificuldade e casos de teste | Lista estática com exemplo Two Sum |
| Editor e execução | Escrever Python/Java, executar em sandbox e visualizar saída/erros | Editor e chamada Docker implementados; avaliação automática ainda não existe |
| Avaliação de submissões | Executar casos de teste e classificar resultado | Não implementada |
| Grupos | Criar grupo, gerar convite, entrar por código e abrir grupo | Interface existe; dados e códigos são locais/simulados |
| Membros e permissões | Listar membros, identificar administrador e permitir remoção autorizada | Lista fixa; remoção apenas imprime mensagem |
| Perfil | Consultar e editar dados do usuário | Dados fixos; edição não persiste |
| Histórico | Consultar submissões anteriores e seus resultados | Histórico estático de demonstração |
| Ranking | Exibir classificação calculada com pontuação persistida | Dados fixos; posições atualmente repetidas |
| Persistência | Salvar usuários, desafios, grupos, submissões e pontuação | Arquivo schema.sql está vazio |

### Escopo proposto para o MVP
1. Cadastro, login, sessão e logout reais.
2. Catálogo de desafios com enunciados e casos de teste.
3. Editor com suporte inicial a Python e Java.
4. Execução isolada com limites de tempo, memória e saída.
5. Avaliação automática usando casos de teste.
6. Cadastro de grupos, convites e controle de participantes.
7. Perfil com histórico de submissões.
8. Ranking global calculado com base em resultados persistidos.
9. Testes automatizados e documentação de execução.

### Fora do escopo inicial (proposta)
- Aplicativo nativo para iOS/Android.
- Competições ao vivo com cronômetro e sala em tempo real.
- Mensagens/chat entre participantes.
- Monetização, assinaturas ou pagamentos.
- Suporte a linguagens além de Python e Java.

Esses itens devem ser reavaliados pelo squad antes de entrarem no backlog do MVP.

## 3. Critérios de aceite e tarefas do board

As Issues do GitHub são a fonte de acompanhamento das tarefas. Cada Issue deve conter contexto, critérios verificáveis e testes relacionados. O quadro GitHub Projects/Trello deve usar, no mínimo, as colunas **Backlog**, **Pronto para desenvolvimento**, **Em andamento**, **Em revisão** e **Concluído**.

| Entrega | Critérios de aceite resumidos | Issue |
|---|---|---|
| Banco de dados e segurança | Tabelas versionadas; chaves e relacionamentos; políticas de acesso por usuário/grupo; instruções de setup | [#2](../issues/2) |
| Autenticação | Cadastro/login/logout reais; validação de sessão; erros apresentados sem expor detalhes internos | [#3](../issues/3) |
| Catálogo de desafios | Desafios e casos de teste persistidos; listagem vem do banco; dados inválidos/inativos não são oferecidos | [#4](../issues/4) |
| Executor e avaliação | Execução isolada; timeout e limites de saída; comparação de casos de teste; resultado padronizado | [#5](../issues/5) · [#7](../issues/7) |
| Arquitetura do executor | Aplicação web não depende de Docker Engine local no ambiente serverless; serviço de execução tem contrato autenticado | [#6](../issues/6) |
| Grupos e convites | Criar/listar grupos persistidos; códigos únicos; entrada válida; código inválido gera retorno claro | [#8](../issues/8) |
| Permissões de grupo | Apenas administrador executa ações administrativas; remoção persistida; interface atualiza a lista | [#9](../issues/9) |
| Perfil e histórico | Dados carregados do usuário autenticado; edição persistida; histórico obtido das submissões reais | [#10](../issues/10) |
| Ranking | Pontos derivados de submissões aceitas; ordenação decrescente; desempate documentado; sem posições repetidas | [#11](../issues/11) |
| Navegação e estados da UI | Rotas válidas; erros/loading/empty states visíveis; navegação de grupo corrigida | [#12](../issues/12) |
| Qualidade e CI | Testes de unidade/integração; workflow executa em PR; instruções de teste atualizadas | [#13](../issues/13) |

## 3.1 Quadro de acompanhamento no Trello

O backlog também está espelhado no Trello, com um cartão por Issue do GitHub e uma checklist marcável de critérios de aceite em cada cartão.

**[Abrir quadro CodeRank — Backlog do MVP](https://trello.com/b/fF1h14Cc/coderank-backlog-do-mvp)**

Listas do fluxo: Backlog, Pronto para desenvolvimento, Em andamento, Em revisão e Concluído. Os cartões estão inicialmente no Backlog; mova-os conforme o trabalho avançar e marque os critérios à medida que forem validados.

### Definition of Done (DoD)
Uma tarefa só pode ser marcada como concluída quando:
- [ ] Todos os critérios de aceite da Issue forem atendidos.
- [ ] O comportamento principal e os fluxos de erro estiverem cobertos por testes.
- [ ] Não houver credenciais ou segredos versionados.
- [ ] A documentação necessária estiver atualizada.
- [ ] O pipeline de CI estiver verde.
- [ ] A alteração tiver sido revisada por pelo menos uma pessoa do squad, conforme o processo combinado.
- [ ] A Issue estiver vinculada ao Pull Request correspondente.

## 4. Contrato de comportamento — BDD (Gherkin)

Os cenários abaixo descrevem o comportamento esperado do MVP. Eles são especificações de aceite; ainda precisam ser automatizados e executados no projeto.

### Feature: Cadastro e autenticação

~~~gherkin
# language: pt

Funcionalidade: Cadastro e autenticação
  Como estudante
  Quero criar uma conta e acessar a plataforma
  Para salvar meu progresso e participar dos desafios

  Cenário: Cadastro com dados válidos
    Dado que não existe uma conta cadastrada com o e-mail informado
    Quando eu preencher os dados obrigatórios corretamente
    E confirmar o cadastro
    Então minha conta deve ser criada pelo serviço de autenticação
    E devo receber confirmação do resultado
    E não devo acessar áreas privadas sem uma sessão válida

  Cenário: Cadastro com e-mail já utilizado
    Dado que já existe uma conta com o e-mail informado
    Quando eu tentar cadastrar outra conta com esse e-mail
    Então o cadastro deve ser recusado
    E uma mensagem compreensível deve ser apresentada

  Cenário: Login com credenciais válidas
    Dado que possuo uma conta ativa
    Quando eu informar e-mail e senha corretos
    Então uma sessão autenticada deve ser iniciada
    E devo ser direcionado para a área principal

  Cenário: Login com credenciais inválidas
    Dado que estou na tela de login
    Quando eu informar credenciais incorretas
    Então o acesso deve ser recusado
    E uma mensagem genérica de autenticação deve ser apresentada

  Cenário: Encerrar sessão
    Dado que estou autenticado
    Quando eu selecionar a opção de sair
    Então a sessão deve ser encerrada
    E devo voltar para a tela de login
~~~

### Feature: Catálogo e resolução de desafios

~~~gherkin
# language: pt

Funcionalidade: Resolver desafios de programação
  Como estudante autenticado
  Quero consultar desafios e enviar soluções
  Para praticar programação e medir meu desempenho

  Cenário: Consultar desafios disponíveis
    Dado que estou autenticado
    Quando eu abrir a área de desafios
    Então devo visualizar os desafios ativos cadastrados
    E cada desafio deve apresentar título e dificuldade

  Cenário: Enviar solução aceita
    Dado que selecionei um desafio ativo
    E escrevi uma solução que atende a todos os casos de teste
    Quando eu enviar a solução em uma linguagem suportada
    Então a execução deve ocorrer no ambiente isolado
    E o resultado deve ser "Aceito"
    E a submissão deve ser registrada no meu histórico

  Cenário: Enviar solução com resposta incorreta
    Dado que selecionei um desafio ativo
    E escrevi uma solução que falha em pelo menos um caso de teste
    Quando eu enviar a solução
    Então o resultado deve ser "Resposta Incorreta"
    E o histórico deve registrar a submissão e seu resultado

  Cenário: Execução excede o tempo permitido
    Dado que enviei uma solução para um desafio
    Quando a execução ultrapassar o limite de tempo configurado
    Então a execução deve ser interrompida
    E o resultado deve ser "Tempo Excedido"

  Cenário: Código ultrapassa o limite permitido
    Dado que estou no editor de um desafio
    Quando eu tentar enviar código acima do limite configurado
    Então a submissão deve ser recusada antes da execução
    E devo receber uma mensagem informando o limite

  Cenário: Selecionar linguagem suportada
    Dado que estou no editor
    Quando eu selecionar Python ou Java
    Então o editor deve apresentar um exemplo compatível com a linguagem escolhida
    E a submissão deve ser encaminhada ao executor correspondente
~~~

### Feature: Grupos e convites

~~~gherkin
# language: pt

Funcionalidade: Gerenciar grupos de estudo
  Como estudante autenticado
  Quero criar ou ingressar em grupos
  Para praticar programação com outras pessoas

  Cenário: Criar grupo com nome válido
    Dado que estou autenticado
    Quando eu informar um nome válido e confirmar a criação
    Então o grupo deve ser salvo no banco
    E deve ser gerado um código de convite único
    E eu devo constar como administrador do grupo

  Cenário: Tentar criar grupo sem nome
    Dado que estou no formulário de criação de grupo
    Quando eu confirmar sem informar um nome
    Então o grupo não deve ser criado
    E o campo de nome deve apresentar uma validação

  Cenário: Entrar com código de convite válido
    Dado que existe um grupo com o código informado
    Quando eu solicitar entrada usando esse código
    Então devo ser associado ao grupo
    E o grupo deve aparecer na minha lista

  Cenário: Entrar com código inválido
    Dado que não existe grupo com o código informado
    Quando eu solicitar entrada
    Então não devo ser associado a nenhum grupo
    E devo receber uma mensagem de código inválido

  Cenário: Administrador remove um membro
    Dado que sou administrador de um grupo
    E existe outro usuário membro desse grupo
    Quando eu solicitar a remoção desse membro
    Então a associação deve ser removida no banco
    E a lista de membros deve ser atualizada

  Cenário: Membro comum tenta remover outro membro
    Dado que sou membro comum de um grupo
    Quando eu tentar executar uma ação exclusiva de administrador
    Então a operação deve ser recusada no backend
    E nenhuma associação deve ser alterada
~~~

### Feature: Perfil e histórico

~~~gherkin
# language: pt

Funcionalidade: Consultar e editar perfil
  Como estudante autenticado
  Quero consultar e atualizar meus dados
  Para manter meu perfil correto e acompanhar minha evolução

  Cenário: Consultar o próprio perfil
    Dado que estou autenticado
    Quando eu abrir meu perfil
    Então devo visualizar os dados associados à minha conta
    E devo visualizar meu histórico real de submissões

  Cenário: Atualizar dados do perfil
    Dado que estou autenticado
    Quando eu alterar os campos editáveis com dados válidos
    E salvar as alterações
    Então os dados devem ser persistidos
    E ao reabrir o perfil devo visualizar os dados atualizados

  Cenário: Consultar histórico sem submissões
    Dado que ainda não enviei nenhuma solução
    Quando eu abrir meu histórico
    Então devo visualizar uma mensagem de estado vazio
    E a aplicação não deve exibir submissões fictícias
~~~

### Feature: Ranking

~~~gherkin
# language: pt

Funcionalidade: Consultar ranking
  Como participante
  Quero visualizar a classificação
  Para acompanhar meu desempenho em relação aos demais participantes

  Cenário: Exibir ranking ordenado
    Dado que existem usuários com pontuações registradas
    Quando eu abrir o ranking global
    Então os usuários devem aparecer em ordem decrescente de pontos
    E cada posição deve ser única
    E a pontuação exibida deve corresponder aos dados persistidos

  Cenário: Empate de pontuação
    Dado que dois usuários possuem a mesma pontuação
    Quando o ranking for calculado
    Então o critério de desempate documentado deve ser aplicado
    E a classificação deve permanecer estável
~~~

## 5. Checklist de entregáveis para apresentação do squad

- [ ] **O negócio:** tema, problema, proposta de valor e público-alvo apresentados.
- [ ] Público-alvo e personas validados formalmente pelo squad.
- [ ] **O escopo:** funcionalidades do MVP, itens fora de escopo e situação atual apresentados.
- [ ] **Board:** tarefas cadastradas no GitHub Issues e organizadas em GitHub Projects ou Trello.
- [ ] Cada tarefa possui descrição, prioridade, critérios de aceite e responsável definido.
- [ ] **Contrato BDD:** cenários Gherkin revisados pelo squad.
- [ ] Cenários BDD convertidos em testes automatizados quando aplicável.
- [ ] **Evidências:** execução dos testes, capturas de tela e links dos Pull Requests anexados.
- [ ] **Revisão final:** squad aprova negócio, escopo, critérios de aceite e BDD.

## 6. Decisões que precisam de validação do squad

1. Confirmar o público prioritário e o nível de conhecimento esperado.
2. Confirmar se professores/mentores terão perfil e permissões próprias no MVP.
3. Definir regra de pontuação e desempate do ranking.
4. Definir limites de tempo, memória, tamanho de código e saída das submissões.
5. Definir quais campos de perfil são obrigatórios e editáveis.
6. Confirmar se grupos terão desafios próprios ou apenas acesso ao catálogo global.
7. Definir o fluxo de revisão, responsáveis e política de aprovação das entregas.

---

**Referência técnica:** este documento foi elaborado a partir da estrutura e dos arquivos presentes no repositório CodeRank. Ele descreve o estado observado e uma proposta de MVP; não substitui a validação das decisões de produto pelo squad.
