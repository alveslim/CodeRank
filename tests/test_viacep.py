import unittest
from unittest.mock import Mock, patch

import requests

from src.services.viacep import (
    CepError,
    consultar_cep,
    formatar_cep,
    limpar_cep,
)


class ViaCepTests(unittest.TestCase):
    def test_cleans_and_formats_cep(self):
        self.assertEqual("69005070", limpar_cep("69005-070"))
        self.assertEqual("69005-070", formatar_cep("69005070"))
        self.assertEqual("69005-070", formatar_cep("69abc005-070999"))

    @patch("src.services.viacep.requests.get")
    def test_returns_valid_address(self, get):
        response = Mock()
        response.json.return_value = {
            "cep": "69005-070",
            "localidade": "Manaus",
            "uf": "AM",
        }
        response.raise_for_status.return_value = None
        get.return_value = response

        address = consultar_cep("69005-070")

        self.assertEqual("Manaus", address["localidade"])
        get.assert_called_once_with(
            "https://viacep.com.br/ws/69005070/json/", timeout=5
        )

    @patch("src.services.viacep.requests.get")
    def test_rejects_incomplete_cep_without_network_call(self, get):
        with self.assertRaisesRegex(CepError, "exatamente 8"):
            consultar_cep("123")
        get.assert_not_called()

    @patch("src.services.viacep.requests.get")
    def test_rejects_nonexistent_cep(self, get):
        response = Mock()
        response.json.return_value = {"erro": "true"}
        response.raise_for_status.return_value = None
        get.return_value = response

        with self.assertRaisesRegex(CepError, "nao encontrado"):
            consultar_cep("00000-000")

    @patch(
        "src.services.viacep.requests.get",
        side_effect=requests.Timeout("timeout"),
    )
    def test_explains_timeout(self, get):
        with self.assertRaisesRegex(CepError, "demorou demais"):
            consultar_cep("69005-070")


if __name__ == "__main__":
    unittest.main()
