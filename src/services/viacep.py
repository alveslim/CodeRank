# Ficheiro: src/services/viacep.py
import requests

def consultar_cep(cep: str) -> dict | None:
    """Busca o CEP na API ViaCEP e retorna um dicionário com os dados ou None se falhar."""
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    
    if len(cep_limpo) == 8:
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        try:
            response = requests.get(url, timeout=5) # Timeout é uma boa prática
            if response.status_code == 200:
                dados = response.json()
                if "erro" not in dados:
                    return dados
        except requests.exceptions.RequestException as e:
            print(f"Erro de rede ao consultar ViaCEP: {e}")
            
    return None