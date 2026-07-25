"""
ils.py
------
"""

import copy
import math as mt
import random as rd
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Matrizes de distância/tempo (equivalente ao trecho do notebook que convertia
# osrm_distances/osrm_durations para `distancia` e `tempo`)
# ---------------------------------------------------------------------------

def montar_matrizes(osrm_distances, osrm_durations):
    """
    Converte as matrizes cruas do OSRM (metros / segundos) para as matrizes
    `distancia` (km) e `tempo` (horas) usadas pelo algoritmo, com a diagonal
    marcada como infinito — exatamente como no notebook original.
    """
    n_vert = len(osrm_distances)
    vertices = list(range(n_vert))

    distancia: Dict[int, Dict[int, float]] = {}
    tempo: Dict[int, Dict[int, float]] = {}

    for i in vertices:
        distancia[i] = {}
        tempo[i] = {}
        for j in vertices:
            if i == j:
                distancia[i][j] = mt.inf
                tempo[i][j] = mt.inf
            else:
                distancia[i][j] = round(osrm_distances[i][j] / 1000, 1)   # km
                tempo[i][j] = round(osrm_durations[i][j] / 3600, 4)       # horas

    return distancia, tempo


# ---------------------------------------------------------------------------
# Heurística construtiva (vizinho mais próximo, respeitando capacidade e tempo)
# ---------------------------------------------------------------------------

def construir_rotas_iniciais(ids_clientes: List[int], dem, distancia, tempo, cap_max, tempo_max):
    """
    Heurística construtiva gulosa do notebook original: enquanto houver
    clientes não atendidos, inicia uma nova rota no depósito (0) e vai
    inserindo, a cada passo, o cliente viável mais próximo do último
    visitado, até não haver mais candidato que caiba em capacidade e tempo.
    """
    candidatos = list(ids_clientes)
    rotas = []

    while candidatos:
        rota = [0]
        carga_atual = 0
        tempo_atual = 0
        atual = 0

        while True:
            melhor_viz = -1
            menor_distancia = mt.inf

            for j in candidatos:
                nova_carga = carga_atual + dem[j]
                novo_tempo = tempo_atual + tempo[atual][j] + tempo[j][0]

                if nova_carga <= cap_max and novo_tempo <= tempo_max:
                    if distancia[atual][j] < menor_distancia:
                        melhor_viz = j
                        menor_distancia = distancia[atual][j]

            if melhor_viz == -1:
                break

            rota.append(melhor_viz)
            carga_atual += dem[melhor_viz]
            tempo_atual += tempo[atual][melhor_viz]
            atual = melhor_viz
            candidatos.remove(melhor_viz)

        rota.append(0)
        rotas.append(rota)

    return rotas


# ---------------------------------------------------------------------------
# Vizinhanças intra-rota (cópia literal das funções do notebook)
# ---------------------------------------------------------------------------

def swap(rota, custo_total, distancia, tempo, tempo_max):
    n = len(rota)
    melhor_s     = copy.deepcopy(rota)
    melhor_custo = custo_total
    melhor_i = melhor_j = -1

    for i in range(1, n - 2):
        for j in range(i + 2, n - 1):
            custo_mov = custo_total \
                - distancia[rota[i - 1]][rota[i]] - distancia[rota[i]][rota[i + 1]] \
                + distancia[rota[i - 1]][rota[j]] + distancia[rota[j]][rota[i + 1]] \
                - distancia[rota[j - 1]][rota[j]] - distancia[rota[j]][rota[j + 1]] \
                + distancia[rota[j - 1]][rota[i]] + distancia[rota[i]][rota[j + 1]]

            rota[i], rota[j] = rota[j], rota[i]
            tempo_teste = sum(tempo[rota[x]][rota[x + 1]] for x in range(len(rota) - 1))
            rota[i], rota[j] = rota[j], rota[i]

            if custo_mov < melhor_custo and tempo_teste <= tempo_max:
                melhor_custo = custo_mov
                melhor_i, melhor_j = i, j

    if melhor_i != -1:
        melhor_s[melhor_i], melhor_s[melhor_j] = melhor_s[melhor_j], melhor_s[melhor_i]

    return melhor_s, melhor_custo


def re_insertion(rota, custo_total, distancia, tempo, tempo_max):
    n = len(rota)
    melhor_s     = copy.deepcopy(rota)
    melhor_custo = custo_total
    melhor_i = melhor_p = -1

    for i in range(1, n - 1):
        for p in range(1, n):
            if i != p and p != i + 1:
                custo_mov = custo_total \
                    - distancia[rota[i - 1]][rota[i]] - distancia[rota[i]][rota[i + 1]] \
                    - distancia[rota[p - 1]][rota[p]] \
                    + distancia[rota[i - 1]][rota[i + 1]] \
                    + distancia[rota[p - 1]][rota[i]] + distancia[rota[i]][rota[p]]

                elemento = rota.pop(i)
                rota.insert(p, elemento)
                tempo_teste = sum(tempo[rota[x]][rota[x + 1]] for x in range(len(rota) - 1))
                rota.insert(i, rota.pop(p))

                if custo_mov < melhor_custo and tempo_teste <= tempo_max:
                    melhor_custo = custo_mov
                    melhor_i, melhor_p = i, p

    if melhor_i != -1:
        if melhor_i < melhor_p:
            melhor_s.insert(melhor_p, rota[melhor_i])
            melhor_s.pop(melhor_i)
        else:
            melhor_s.insert(melhor_p, rota[melhor_i])
            melhor_s.pop(melhor_i + 1)

    return melhor_s, melhor_custo


def dois_opt(rota, custo_total, distancia, tempo, tempo_max):
    n = len(rota)
    melhor_s     = copy.deepcopy(rota)
    melhor_custo = custo_total
    melhor_i = melhor_j = -1

    for i in range(1, n - 4):
        for j in range(i + 4, n):
            custo_mov = custo_total \
                - distancia[rota[i - 1]][rota[i]] \
                - distancia[rota[j - 1]][rota[j]] \
                + distancia[rota[i - 1]][rota[j - 1]] \
                + distancia[rota[i]][rota[j]]

            for x in range(i, j - 1):
                custo_mov -= distancia[rota[x]][rota[x + 1]]
                custo_mov += distancia[rota[x + 1]][rota[x]]

            rota[i:j] = rota[i:j][::-1]

            tempo_teste = sum(
                tempo[rota[x]][rota[x + 1]]
                for x in range(len(rota) - 1)
            )

            rota[i:j] = rota[i:j][::-1]

            if custo_mov < melhor_custo and tempo_teste <= tempo_max:
                melhor_custo = custo_mov
                melhor_i, melhor_j = i, j

    if melhor_i != -1:
        melhor_s[melhor_i:melhor_j] = (
            melhor_s[melhor_i:melhor_j][::-1]
        )

    return melhor_s, melhor_custo


def vnd_intra_uma_rota(rota, distancia, tempo, tempo_max):
    """
    Aplica o VND (Swap -> Re-insertion -> 2-opt, voltando para Swap a cada
    melhora) em UMA rota, até não haver mais melhora em nenhuma vizinhança.
    Usado tanto na varredura inicial quanto dentro do laço do ILS (o
    notebook original tinha essa mesma lógica duplicada nos dois pontos).
    """
    vizinhancas = [swap, re_insertion, dois_opt]

    rota_vnd = copy.deepcopy(rota)
    custo_vnd = sum(distancia[rota_vnd[i]][rota_vnd[i + 1]] for i in range(len(rota_vnd) - 1))
    k = 0

    while k < len(vizinhancas):
        rota_linha, custo_linha = vizinhancas[k](rota_vnd, custo_vnd, distancia, tempo, tempo_max)

        if custo_linha < custo_vnd:
            rota_vnd, custo_vnd = rota_linha, custo_linha
            k = 0
        else:
            k += 1

    return rota_vnd, custo_vnd


def vnd_intra_rotas(rotas, distancia, tempo, tempo_max, log: Optional[List[str]] = None):
    """
    Varredura VND intra-rota inicial (equivalente ao bloco 'VND INTRA' do
    notebook), aplicada a cada rota da solução construtiva.
    """
    rotas_vnd = []
    custo_total_geral = 0
    custo_final_geral = 0

    for idx, rota in enumerate(rotas, start=1):
        custo_inicial = sum(distancia[rota[i]][rota[i + 1]] for i in range(len(rota) - 1))
        custo_total_geral += custo_inicial

        rota_vnd, custo_vnd = vnd_intra_uma_rota(rota, distancia, tempo, tempo_max)

        rotas_vnd.append(rota_vnd)
        custo_final_geral += custo_vnd

        if log is not None:
            log.append(
                f"Rota {idx}: custo inicial {round(custo_inicial, 1)} km -> "
                f"custo final {round(custo_vnd, 1)} km "
                f"(melhora {round(custo_inicial - custo_vnd, 1)} km)"
            )

    return rotas_vnd, custo_total_geral, custo_final_geral


# ---------------------------------------------------------------------------
# Vizinhanças entre rotas (cópia literal das funções do notebook)
# ---------------------------------------------------------------------------

def swap_entre_rotas(rota_1, rota_2, distancia, tempo, tempo_max, dem, cap_max):
    melhor_1 = copy.deepcopy(rota_1)
    melhor_2 = copy.deepcopy(rota_2)
    melhor_custo = sum(distancia[rota_1[i]][rota_1[i + 1]] for i in range(len(rota_1) - 1)) \
                 + sum(distancia[rota_2[i]][rota_2[i + 1]] for i in range(len(rota_2) - 1))
    melhor_i = melhor_j = -1

    for i in range(1, len(rota_1) - 1):
        for j in range(1, len(rota_2) - 1):
            custo_mov = melhor_custo \
                - distancia[rota_1[i - 1]][rota_1[i]] - distancia[rota_1[i]][rota_1[i + 1]] \
                + distancia[rota_1[i - 1]][rota_2[j]] + distancia[rota_2[j]][rota_1[i + 1]] \
                - distancia[rota_2[j - 1]][rota_2[j]] - distancia[rota_2[j]][rota_2[j + 1]] \
                + distancia[rota_2[j - 1]][rota_1[i]] + distancia[rota_1[i]][rota_2[j + 1]]

            Carga_1 = sum(dem[c] for c in rota_1 if c != 0)
            Carga_2 = sum(dem[c] for c in rota_2 if c != 0)
            nova_carga_1 = Carga_1 - dem[rota_1[i]] + dem[rota_2[j]]
            nova_carga_2 = Carga_2 - dem[rota_2[j]] + dem[rota_1[i]]

            if nova_carga_1 > cap_max or nova_carga_2 > cap_max:
                continue

            rota_1[i], rota_2[j] = rota_2[j], rota_1[i]
            tempo_1 = sum(tempo[rota_1[x]][rota_1[x + 1]] for x in range(len(rota_1) - 1))
            tempo_2 = sum(tempo[rota_2[x]][rota_2[x + 1]] for x in range(len(rota_2) - 1))
            rota_1[i], rota_2[j] = rota_2[j], rota_1[i]

            if custo_mov < melhor_custo and tempo_1 <= tempo_max and tempo_2 <= tempo_max:
                melhor_custo = custo_mov
                melhor_i, melhor_j = i, j

    if melhor_i != -1:
        melhor_1[melhor_i], melhor_2[melhor_j] = melhor_2[melhor_j], melhor_1[melhor_i]

    return melhor_1, melhor_2, melhor_custo


def reinsert_entre_rotas(rota_1, rota_2, distancia, tempo, tempo_max, dem, cap_max):
    melhor_1 = copy.deepcopy(rota_1)
    melhor_2 = copy.deepcopy(rota_2)
    melhor_custo = sum(distancia[rota_1[i]][rota_1[i + 1]] for i in range(len(rota_1) - 1)) \
                 + sum(distancia[rota_2[i]][rota_2[i + 1]] for i in range(len(rota_2) - 1))
    melhor_i = -1
    melhor_j = -1

    for i in range(1, len(rota_1) - 1):
        for j in range(1, len(rota_2)):
            custo_mov = melhor_custo \
                - distancia[rota_1[i - 1]][rota_1[i]] - distancia[rota_1[i]][rota_1[i + 1]] \
                + distancia[rota_1[i - 1]][rota_1[i + 1]] \
                - distancia[rota_2[j - 1]][rota_2[j]] \
                + distancia[rota_2[j - 1]][rota_1[i]] + distancia[rota_1[i]][rota_2[j]]

            Carga_2 = sum(dem[c] for c in rota_2 if c != 0)
            nova_carga_2 = Carga_2 + dem[rota_1[i]]
            if nova_carga_2 > cap_max:
                continue

            cliente = rota_1[i]
            nova_rota_1 = rota_1[:i] + rota_1[i + 1:]
            nova_rota_2 = rota_2[:j] + [cliente] + rota_2[j:]
            tempo_1 = sum(tempo[nova_rota_1[x]][nova_rota_1[x + 1]] for x in range(len(nova_rota_1) - 1))
            tempo_2 = sum(tempo[nova_rota_2[x]][nova_rota_2[x + 1]] for x in range(len(nova_rota_2) - 1))

            if custo_mov < melhor_custo and tempo_1 <= tempo_max and tempo_2 <= tempo_max:
                melhor_custo = custo_mov
                melhor_i, melhor_j = i, j

    if melhor_i != -1:
        cliente = melhor_1.pop(melhor_i)
        melhor_2.insert(melhor_j, cliente)

    return melhor_1, melhor_2, melhor_custo


def vnd_entre_rotas(rotas, distancia, tempo, tempo_max, dem, cap_max, log: Optional[List[str]] = None):
    """
    Busca local entre rotas usada ANTES do ILS (bloco 'VND ENTRE ROTAS' do
    notebook). Ao encontrar uma melhora, reinicia a varredura a partir da
    rota `a` seguinte (mesmo comportamento do `Reiniciar`/`break` original).
    """
    vizinhancas_entre = [swap_entre_rotas, reinsert_entre_rotas]
    nomes_entre = ["Swap-entre-rotas (N4)", "reinsert_entre_rotas (N5)"]

    rotas_vnd = copy.deepcopy(rotas)
    melhorou = True

    while melhorou:
        melhorou = False
        reiniciar = False
        for a in range(len(rotas_vnd)):
            for b in range(len(rotas_vnd)):
                if a == b:
                    continue

                k = 0
                while k < len(vizinhancas_entre):
                    custo_antes = sum(distancia[rotas_vnd[a][i]][rotas_vnd[a][i + 1]]
                                       for i in range(len(rotas_vnd[a]) - 1)) \
                        + sum(distancia[rotas_vnd[b][i]][rotas_vnd[b][i + 1]]
                              for i in range(len(rotas_vnd[b]) - 1))

                    nova_rota_1, nova_rota_2, novo_custo = vizinhancas_entre[k](
                        rotas_vnd[a], rotas_vnd[b], distancia, tempo, tempo_max, dem, cap_max
                    )

                    if novo_custo < custo_antes:
                        if log is not None:
                            log.append(
                                f"{nomes_entre[k]} | Rotas {a + 1} e {b + 1}: "
                                f"melhorou {round(custo_antes - novo_custo, 1)} km"
                            )
                        rotas_vnd[a] = nova_rota_1
                        rotas_vnd[b] = nova_rota_2
                        melhorou = True
                        reiniciar = True
                        k = 0
                        break
                    else:
                        k += 1

            if reiniciar:
                break

    return rotas_vnd


def vnd_entre_rotas_ils(rotas, distancia, tempo, tempo_max, dem, cap_max):
    """
    Busca local entre rotas usada DENTRO do laço do ILS (bloco 'Etapa: Busca
    local entre rotas' do notebook). No original essa versão NÃO interrompe
    o par (a, b) ao melhorar — ela reavalia a mesma vizinhança a partir de
    K=0 repetidamente até não haver mais melhora naquele par, sem reiniciar
    a varredura pela rota `a`. Mantida separada de `vnd_entre_rotas` de
    propósito, para não alterar o comportamento original do ILS.
    """
    vizinhancas_entre = [swap_entre_rotas, reinsert_entre_rotas]

    rotas_vnd = copy.deepcopy(rotas)
    melhorou = True

    while melhorou:
        melhorou = False
        for a in range(len(rotas_vnd)):
            for b in range(len(rotas_vnd)):
                if a == b:
                    continue

                k = 0
                while k < len(vizinhancas_entre):
                    custo_antes = sum(distancia[rotas_vnd[a][i]][rotas_vnd[a][i + 1]]
                                       for i in range(len(rotas_vnd[a]) - 1)) \
                        + sum(distancia[rotas_vnd[b][i]][rotas_vnd[b][i + 1]]
                              for i in range(len(rotas_vnd[b]) - 1))

                    nova_rota_1, nova_rota_2, novo_custo = vizinhancas_entre[k](
                        rotas_vnd[a], rotas_vnd[b], distancia, tempo, tempo_max, dem, cap_max
                    )

                    if novo_custo < custo_antes:
                        rotas_vnd[a] = nova_rota_1
                        rotas_vnd[b] = nova_rota_2
                        melhorou = True
                        k = 0
                    else:
                        k += 1

    return rotas_vnd


# ---------------------------------------------------------------------------
# Perturbação (cópia literal, apenas com dem/tempo/cap_max/tempo_max como
# parâmetros em vez de globais)
# ---------------------------------------------------------------------------

def Perturbacao(melhor_solucao, dem, tempo, cap_max, tempo_max):
    rotas_perturbadas = copy.deepcopy(melhor_solucao)

    for _ in range(2):
        rotas_validas = [i for i in range(len(rotas_perturbadas)) if len(rotas_perturbadas[i]) > 3]

        if len(rotas_validas) < 2:
            break

        a, b = rd.sample(rotas_validas, 2)

        rota_a = rotas_perturbadas[a]
        rota_b = rotas_perturbadas[b]

        pos_i = rd.randint(1, len(rota_a) - 2)
        pos_j = rd.randint(1, len(rota_b) - 2)

        Carga_a = sum(dem[c] for c in rota_a if c != 0)
        Carga_b = sum(dem[c] for c in rota_b if c != 0)
        nova_carga_a = Carga_a - dem[rota_a[pos_i]] + dem[rota_b[pos_j]]
        nova_carga_b = Carga_b - dem[rota_b[pos_j]] + dem[rota_a[pos_i]]

        if nova_carga_a > cap_max or nova_carga_b > cap_max:
            continue

        rota_a[pos_i], rota_b[pos_j] = rota_b[pos_j], rota_a[pos_i]
        tempo_a = sum(tempo[rota_a[x]][rota_a[x + 1]] for x in range(len(rota_a) - 1))
        tempo_b = sum(tempo[rota_b[x]][rota_b[x + 1]] for x in range(len(rota_b) - 1))

        if tempo_a > tempo_max or tempo_b > tempo_max:
            rota_a[pos_i], rota_b[pos_j] = rota_b[pos_j], rota_a[pos_i]

    return rotas_perturbadas


# ---------------------------------------------------------------------------
# Laço principal do ILS (equivalente ao bloco final do notebook)
# ---------------------------------------------------------------------------

def executar_ils(rotas_iniciais, distancia, tempo, dem, cap_max, tempo_max,
                  max_iteracoes_sem_melhoras=10, log: Optional[List[str]] = None):
    """
    Reproduz o laço principal do ILS: perturba a melhor solução, aplica
    busca local intra e entre rotas, aceita se o custo total melhorar, e
    encerra após `max_iteracoes_sem_melhoras` iterações consecutivas sem
    melhora — mesmo critério de parada do notebook original.
    """
    melhor_solucao = copy.deepcopy(rotas_iniciais)
    custo_melhor = sum(sum(distancia[r[i]][r[i + 1]] for i in range(len(r) - 1)) for r in melhor_solucao)

    iteracao_ILS = 0
    iteracao_total = 0

    while iteracao_ILS < max_iteracoes_sem_melhoras:
        rotas_perturbadas = Perturbacao(melhor_solucao, dem, tempo, cap_max, tempo_max)

        rotas_pos_bl = []
        for rota in rotas_perturbadas:
            rota_final, _ = vnd_intra_uma_rota(rota, distancia, tempo, tempo_max)
            rotas_pos_bl.append(rota_final)

        rotas_pos_bl = vnd_entre_rotas_ils(rotas_pos_bl, distancia, tempo, tempo_max, dem, cap_max)

        custo_pos_bl = sum(sum(distancia[r[i]][r[i + 1]] for i in range(len(r) - 1)) for r in rotas_pos_bl)

        iteracao_total += 1

        if custo_pos_bl < custo_melhor:
            melhor_solucao = copy.deepcopy(rotas_pos_bl)
            custo_melhor = custo_pos_bl
            iteracao_ILS = 0
            if log is not None:
                log.append(f"Iteração {iteracao_total}: novo melhor custo = {round(custo_melhor, 1)} km")
        else:
            iteracao_ILS += 1
            if log is not None:
                log.append(f"Iteração {iteracao_total}: sem melhora (custo atual = {round(custo_melhor, 1)} km)")

    return melhor_solucao, custo_melhor, iteracao_total


# ---------------------------------------------------------------------------
# Orquestrador: liga heurística construtiva -> VND intra -> VND entre -> ILS
# ---------------------------------------------------------------------------

def rodar_algoritmo_completo(dem, distancia, tempo, cap_max, tempo_max,
                              max_iteracoes_sem_melhoras=10, log: Optional[List[str]] = None) -> Dict:
    """
    Função única chamada pelo app.py. Executa exatamente a sequência do
    notebook original: heurística construtiva -> VND intra-rota -> VND
    entre rotas -> ILS, e devolve um dicionário com a solução final e as
    métricas usadas na interface.
    """
    n = len(distancia) - 1  # não conta o depósito (índice 0)
    ids_clientes = list(range(1, n + 1))

    if log is not None:
        log.append("Etapa 1/4: heurística construtiva (vizinho mais próximo)")
    rotas = construir_rotas_iniciais(ids_clientes, dem, distancia, tempo, cap_max, tempo_max)

    if log is not None:
        log.append("Etapa 2/4: VND intra-rota (Swap, Re-insertion, 2-opt)")
    rotas_vnd, custo_construcao, _ = vnd_intra_rotas(rotas, distancia, tempo, tempo_max, log=log)

    if log is not None:
        log.append("Etapa 3/4: VND entre rotas (Swap-entre-rotas, Re-insertion-entre-rotas)")
    rotas_vnd = vnd_entre_rotas(rotas_vnd, distancia, tempo, tempo_max, dem, cap_max, log=log)

    if log is not None:
        log.append(f"Etapa 4/4: Iterated Local Search (até {max_iteracoes_sem_melhoras} iterações sem melhora)")
    melhor_solucao, custo_melhor, iteracoes_ils = executar_ils(
        rotas_vnd, distancia, tempo, dem, cap_max, tempo_max,
        max_iteracoes_sem_melhoras=max_iteracoes_sem_melhoras, log=log
    )

    return {
        "rotas_construcao": rotas,
        "custo_construcao": custo_construcao,
        "rotas_final": melhor_solucao,
        "custo_final": custo_melhor,
        "iteracoes_ils": iteracoes_ils,
        "num_rotas": len(melhor_solucao),
    }
