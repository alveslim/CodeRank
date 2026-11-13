"""Consulta de CEP usando a API pública ViaCEP."""

from __future__ import annotations

import logging
import re

import requests


logger = logging.getLogger(__name__)
CEP_PATTERN = re.compile(r"^\d{5}-?\d{3}$")


def consultar_cep(cep: str) -> dict | None:
    """Retorna o endereço do CEP ou None quando inválido/indisponível.

    Aceita somente CEP com oito dígitos, com ou sem hífen. Falhas de rede,
    respostas HTTP inválidas e JSON malformado não interrompem a interface.
    """

    if not isinstance(cep, str):
        return None

    cep_normalizado = cep.strip()
    if not CEP_PATTERN.fullmatch(cep_normalizado):
        return None

    cep_limpo = cep_normalizado.replace("-", "")
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        dados = response.json()
    except requests.exceptions.RequestException:
        logger.warning("Não foi possível consultar o ViaCEP.")
        return None
    except (ValueError, TypeError):
        logger.warning("O ViaCEP retornou uma resposta inválida.")
        return None

    if not isinstance(dados, dict) or str(dados.get("erro", "")).lower() == "true":
        return None

    return dados
