# CodeRank

Aplicação educacional em Flet com execução isolada de submissões Python e Java.

## Pré-requisitos

- Python 3.13 ou superior
- Docker Desktop com o motor Docker em execução

## Configuração do ambiente

No PowerShell, a partir da raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose build
python main.py
```

O comando `docker compose build` cria as imagens locais:

- `coderank-python:latest`
- `coderank-java:latest`

## Como funciona a execução

O editor envia o código pela entrada padrão para um contêiner novo e descartável. Cada execução:

- usa uma imagem previamente construída, sem montar diretórios do computador;
- não possui acesso à rede;
- executa com usuário sem privilégios e todas as capabilities removidas;
- usa sistema de arquivos somente leitura, exceto por uma área temporária limitada;
- possui limites de CPU, memória, processos, tamanho do código e tempo de execução;
- remove o contêiner ao finalizar ou exceder o timeout.

Python é executado com o interpretador em modo isolado. Java exige uma classe pública chamada `Main` e é compilado com Java 21 antes da execução.

> O isolamento reduz o risco de executar código não confiável, mas não substitui uma infraestrutura de sandbox dedicada para uso público em produção.

## Testes

Os testes unitários não precisam do motor Docker:

```powershell
python -m unittest discover -s tests -v
```

Para conferir manualmente as imagens depois de iniciar o Docker Desktop:

```powershell
'print("sandbox python ok")' | docker run --rm -i --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m coderank-python:latest

@'
public class Main {
    public static void main(String[] args) {
        System.out.println("sandbox java ok");
    }
}
'@ | docker run --rm -i --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m coderank-java:latest
```
