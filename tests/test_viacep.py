import unittest
from unittest.mock import Mock, patch

import requests

from src.services.viacep import consultar_cep


class ViaCepTests(unittest.TestCase):
    @patch("src.services.viacep.requests.get")
    def test_returns_valid_address_and_normalizes_cep(self, get):
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
            "https://viacep.com.br/ws/69005070/json/",
            timeout=5,
        )

    @patch("src.services.viacep.requests.get")
    def test_accepts_cep_without_hyphen(self, get):
        response = Mock()
        response.json.return_value = {"localidade": "Manaus", "uf": "AM"}
        response.raise_for_status.return_value = None
        get.return_value = response

        self.assertEqual("Manaus", consultar_cep("69005070")["localidade"])

    @patch("src.services.viacep.requests.get")
    def test_rejects_invalid_cep_without_network_call(self, get):
        for cep in ("123", "abc69005070", "6900-5070", "69005 070", None):
            with self.subTest(cep=cep):
                self.assertIsNone(consultar_cep(cep))
        get.assert_not_called()

    @patch("src.services.viacep.requests.get")
    def test_returns_none_for_nonexistent_cep(self, get):
        response = Mock()
        response.json.return_value = {"erro": "true"}
        response.raise_for_status.return_value = None
        get.return_value = response

        self.assertIsNone(consultar_cep("00000-000"))

    @patch(
        "src.services.viacep.requests.get",
        side_effect=requests.Timeout("timeout"),
    )
    def test_returns_none_on_timeout(self, get):
        self.assertIsNone(consultar_cep("69005-070"))

    @patch("src.services.viacep.requests.get")
    def test_returns_none_on_http_error(self, get):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("503")
        get.return_value = response

        self.assertIsNone(consultar_cep("69005-070"))

    @patch("src.services.viacep.requests.get")
    def test_returns_none_on_invalid_json(self, get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.side_effect = ValueError("invalid JSON")
        get.return_value = response

        self.assertIsNone(consultar_cep("69005-070"))


if __name__ == "__main__":
    unittest.main()
