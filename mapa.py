"""
mapa.py
-------
Geração do mapa Folium com depósito, clientes e rotas.

Esta é a mesma lógica de visualização do trecho Folium fornecido — os
mesmos elementos (marcador do depósito, CircleMarker + rótulo numérico para
cada cliente, PolyLine colorida por rota com tooltip de distância/carga/
tempo). A única mudança é a fonte dos dados: em vez dos dicionários fixos
`lats`/`lons`/`coords`, os pontos vêm da lista de clientes cadastrados na
interface (na mesma ordem usada para montar a matriz de distâncias).
"""

import os
from typing import Dict, List, Tuple

import folium

from dados import Cliente, Deposito

CORES = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink',
         'darkred', 'cadetblue', 'darkgreen', 'darkblue', 'gray']


def gerar_mapa(
    deposito: Deposito,
    clientes: List[Cliente],
    melhor_solucao: List[List[int]],
    distancia: Dict[int, Dict[int, float]],
    tempo: Dict[int, Dict[int, float]],
    dem: Dict[int, int],
    caminho_saida: str = "resultados/rota.html",
) -> Tuple[str, "folium.Map"]:
    """
    Gera e salva o mapa Folium com o depósito, os clientes e as rotas da
    melhor solução encontrada. Retorna (caminho_do_arquivo, objeto_mapa).

    Importante: `clientes` deve estar na MESMA ordem usada para montar a
    matriz de distâncias/tempos (é essa ordem que define o índice de nó
    1..n usado em `melhor_solucao`, `distancia`, `tempo` e `dem`).
    """
    mapa = folium.Map(location=[deposito.latitude, deposito.longitude], zoom_start=13)

    folium.Marker(
        location=[deposito.latitude, deposito.longitude],
        popup="Depósito",
        tooltip="Depósito",
        icon=folium.Icon(color='blue', icon='home', prefix='fa'),
    ).add_to(mapa)

    lat_por_indice = {0: deposito.latitude}
    lon_por_indice = {0: deposito.longitude}

    for indice, cliente in enumerate(clientes, start=1):
        lat_por_indice[indice] = cliente.latitude
        lon_por_indice[indice] = cliente.longitude

        folium.CircleMarker(
            location=[cliente.latitude, cliente.longitude],
            radius=8,
            color='orange',
            fill=True,
            fill_color='orange',
            fill_opacity=0.7,
            popup=f"{cliente.nome} | Demanda: {cliente.demanda}",
            tooltip=cliente.nome,
        ).add_to(mapa)

        folium.Marker(
            location=[cliente.latitude, cliente.longitude],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px; font-weight:bold; color:black;">{indice}</div>'
            ),
        ).add_to(mapa)

    for idx, rota in enumerate(melhor_solucao):
        cor = CORES[idx % len(CORES)]
        dist_rota = sum(distancia[rota[i]][rota[i + 1]] for i in range(len(rota) - 1))
        carga_rota = sum(dem[c] for c in rota if c != 0)
        tempo_rota = sum(tempo[rota[i]][rota[i + 1]] for i in range(len(rota) - 1))

        pontos = [[lat_por_indice[c], lon_por_indice[c]] for c in rota]

        folium.PolyLine(
            locations=pontos,
            color=cor,
            weight=3,
            opacity=0.8,
            tooltip=(
                f"Rota {idx + 1}: {round(dist_rota, 1)} km | "
                f"Carga: {carga_rota} | Tempo: {round(tempo_rota, 2)}h"
            ),
        ).add_to(mapa)

    os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)
    mapa.save(caminho_saida)

    return caminho_saida, mapa
