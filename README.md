# CodeRank

Aplicacao educacional em Flet para praticar programacao em grupos, resolver
desafios em conteineres isolados e acompanhar a pontuacao em um ranking.

## Funcionalidades do MVP

- cadastro, login e encerramento de sessao;
- consulta, formatacao e validacao obrigatoria de CEP pela API ViaCEP;
- criacao de grupos e entrada por codigo de convite;
- listagem e remocao protegida de membros por administradores;
- desafios em Python e Java;
- execucao isolada com limites de CPU, memoria, processos, rede e tempo;
- registro de submissoes, pontuacao unica por desafio e ranking por grupo;
- perfil com pontuacao e quantidade de desafios concluidos;
- edicao de perfil e endereco, historico de submissoes e notificacoes de pontuacao;
- backend Supabase com Auth, PostgreSQL, RLS e funcoes transacionais;
- modo demonstracao local para testes sem credenciais externas.

## Pre-requisitos

- Python 3.13 ou superior;
- Docker Desktop com o motor Docker em execucao.

## Executar em modo demonstracao

No PowerShell, a partir da raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose build
python main.py
```

Sem um arquivo `.env`, o aplicativo abre em modo demonstracao. Use:

```text
E-mail: demo@coderank.local
Senha:  demo1234
```

Os dados desse modo ficam apenas na memoria e sao apagados quando o aplicativo
e fechado.

## Conectar ao Supabase

1. Crie um projeto no Supabase.
2. Abra o SQL Editor e execute todo o arquivo `schema.sql`.
3. Copie `.env.example` para `.env`.
4. Preencha somente a URL e a chave publica `anon`/`publishable` do projeto.
5. Reinicie `python main.py`.

```env
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_ANON_KEY=SUA_CHAVE_PUBLICA
```

Nunca coloque a chave `service_role`, uma secret key ou senha do banco no
aplicativo. O arquivo `.env` esta ignorado pelo Git.

Se a confirmacao de e-mail estiver ativada no Supabase, o usuario deve abrir o
link recebido antes do primeiro login.

O servidor de e-mail padrao do Supabase possui limites baixos. Clique em
`Criar conta` apenas uma vez; se a conta ja foi criada, use o primeiro e-mail
de confirmacao recebido em vez de repetir o cadastro.

## Execucao do codigo

O editor envia o codigo pela entrada padrao para um conteiner novo e
descartavel. Cada execucao:

- usa uma imagem previamente construida, sem montar diretorios do computador;
- nao possui acesso a rede;
- executa com usuario sem privilegios e capabilities removidas;
- usa sistema de arquivos somente leitura, exceto por area temporaria limitada;
- possui limites de CPU, memoria, processos, tamanho do codigo e tempo;
- remove o conteiner ao finalizar ou exceder o timeout.

Python e executado em modo isolado. Java exige uma classe publica chamada
`Main` e e compilado com Java 21 antes da execucao.

> Para uma demonstracao local, a interface compara a saida com o resultado
> esperado e registra a submissao. Em producao publica, a execucao e a
> validacao devem ficar em um servico de backend dedicado, nunca no cliente.

## Testes automatizados

Os testes unitarios nao precisam do motor Docker:

```powershell
python -m unittest discover -s tests -v
```

Eles cobrem os limites do executor, tratamento de timeout, autenticacao local,
grupos, permissoes de membros, perfil, consulta e validacao de CEP, filtro de
desafios, historico e a regra que impede pontuacao duplicada.

## Teste manual do sandbox

Depois de iniciar o Docker Desktop:

```powershell
docker compose build
python -c "from src.services.code_runner import run_code; r=run_code('python', 'print(2 + 3)'); print(r.stdout, r.stderr, r.exit_code)"
python -c "from src.services.code_runner import run_code; s='public class Main { public static void main(String[] args) { System.out.println(2 + 3); } }'; r=run_code('java', s); print(r.stdout, r.stderr, r.exit_code)"
python -c "from src.services.code_runner import run_code; r=run_code('python', 'while True: pass', 2); print(r.stderr, r.timed_out, r.exit_code)"
```

Resultados esperados:

- Python imprime `5` e retorna codigo `0`;
- Java imprime `5` e retorna codigo `0`;
- o loop infinito e interrompido, `timed_out=True` e codigo `124`.

## Estrutura principal

```text
src/services/backend.py     Supabase e modo demonstracao
src/services/code_runner.py Execucao isolada Docker
src/services/viacep.py      Consulta de endereco
src/ui/                     Interface Flet
schema.sql                  Tabelas, funcoes e politicas RLS
tests/                      Testes automatizados
```
