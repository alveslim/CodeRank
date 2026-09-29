"""Validacao e consulta de enderecos brasileiros pelo ViaCEP."""

from __future__ import annotations

from typing import Any

import requests


class CepError(ValueError):
    """Erro apresentavel ao usuario durante a validacao do CEP."""


def limpar_cep(valor: object) -> str:
    """Retorna apenas os digitos de um CEP, limitado a oito posicoes."""

    return "".join(filter(str.isdigit, str(valor or "")))[:8]


def formatar_cep(valor: object) -> str:
    """Formata um CEP parcial ou completo como ``00000-000``."""

    digitos = limpar_cep(valor)
    if len(digitos) <= 5:
        return digitos
    return f"{digitos[:5]}-{digitos[5:]}"


def consultar_cep(cep: object) -> dict[str, Any]:
    """Consulta um CEP real e levanta ``CepError`` com mensagem amigavel."""

    cep_limpo = limpar_cep(cep)
    if len(cep_limpo) != 8:
        raise CepError("O CEP deve conter exatamente 8 numeros.")

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        dados = response.json()
    except requests.Timeout as exc:
        raise CepError("A consulta do CEP demorou demais. Tente novamente.") from exc
    except (requests.RequestException, ValueError) as exc:
        raise CepError("Nao foi possivel consultar o CEP. Verifique sua internet.") from exc

    if dados.get("erro"):
        raise CepError("CEP nao encontrado. Informe um CEP real dos Correios.")

    cidade = str(dados.get("localidade") or "").strip()
    estado = str(dados.get("uf") or "").strip()
    if not cidade or not estado:
        raise CepError("O servico de CEP retornou um endereco incompleto.")
    return dados
