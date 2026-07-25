"""
osm.py
------
Comunicação com o OpenStreetMap: busca de endereços (Nominatim) e matriz de
distâncias/tempos (OSRM), a mesma API pública já usada no notebook original.

A função `obter_matriz_osrm` é a função `get_osrm_matrix` do notebook,
apenas renomeada e com o tratamento de erro convertido em exceção (para que
o Streamlit possa capturar e exibir a mensagem), em vez de retornar
(None, None) silenciosamente. A lógica da requisição em si não foi alterada.
"""

from typing import List, Dict, Tuple
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving/{}"

# A Nominatim exige um User-Agent identificável (política de uso do serviço público).
_HEADERS = {"User-Agent": "projeto-academico-ils-streamlit/1.0"}


def buscar_endereco(query: str, limite: int = 5) -> List[Dict]:
    """
    Busca endereços via Nominatim (OpenStreetMap).

    Retorna a lista bruta de resultados (cada item contém, entre outros
    campos, 'display_name', 'lat' e 'lon'), na mesma estrutura devolvida
    pela API pública do Nominatim.
    """
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limite,
    }
    try:
        resposta = requests.get(NOMINATIM_URL, params=params, headers=_HEADERS, timeout=15)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Erro ao consultar o Nominatim (OpenStreetMap): {e}")


def obter_matriz_osrm(coordinates: List[Tuple[float, float]]):
    """
    Equivalente direto de get_osrm_matrix() do notebook original.

    coordinates: lista de tuplas (lon, lat), índice 0 = depósito.
    Retorna (distances, durations) em metros e segundos, exatamente como a
    API do OSRM devolve (nenhuma conversão é feita aqui — isso acontece em
    ils.montar_matrizes, igual ao notebook original).
    """
    coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
    url = OSRM_TABLE_URL.format(coords_str)
    params = {"annotations": "distance,duration"}

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(f"Erro HTTP ao consultar o OSRM: {response.status_code}")

        data = response.json()

        if data["code"] != "Ok":
            raise RuntimeError(f"Erro na resposta do OSRM: {data.get('message')}")

        return data["distances"], data["durations"]

    except requests.RequestException as e:
        raise RuntimeError(f"Erro na requisição ao OSRM: {e}")
