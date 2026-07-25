"""
dados.py
--------
Estruturas de dados usadas pela interface Streamlit.

Este módulo NÃO contém lógica de otimização. Ele apenas define como um
"depósito" e um "cliente" são representados na interface, e converte a lista
de clientes cadastrados no formato que o algoritmo original (ils.py) espera:
um dicionário de demandas (`dem`) e uma lista de coordenadas (lon, lat),
ambos indexados pela MESMA ordem usada para montar a matriz OSRM (índice 0 =
depósito, índices 1..n = clientes, na ordem em que aparecem na lista).

Importante: usamos a POSIÇÃO do cliente na lista (1, 2, 3, ...) como índice
do nó no algoritmo — não o `id` do cliente. Isso evita inconsistências caso
um cliente seja removido no meio da lista (o `id` seria descontínuo, mas a
matriz de distâncias precisa de índices contínuos 0..n).
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class Deposito:
    nome: str
    latitude: float
    longitude: float


@dataclass
class Cliente:
    id: int          # identificador estável só para a interface (tabela / remoção)
    nome: str
    latitude: float
    longitude: float
    demanda: int


def construir_dem(clientes: List[Cliente]) -> Dict[int, int]:
    """
    Monta o dicionário de demandas no formato esperado pelo algoritmo original
    (dem[0] = 0 para o depósito; dem[i] = demanda do i-ésimo cliente da lista).
    """
    dem = {0: 0}
    for i, cliente in enumerate(clientes, start=1):
        dem[i] = cliente.demanda
    return dem


def construir_coordenadas(deposito: Deposito, clientes: List[Cliente]) -> List[Tuple[float, float]]:
    """
    Monta a lista de coordenadas (longitude, latitude) na ordem esperada pela
    função original get_osrm_matrix / obter_matriz_osrm: índice 0 = depósito,
    índices 1..n = clientes, na mesma ordem da lista `clientes`.
    """
    coordenadas = [(deposito.longitude, deposito.latitude)]
    for cliente in clientes:
        coordenadas.append((cliente.longitude, cliente.latitude))
    return coordenadas
