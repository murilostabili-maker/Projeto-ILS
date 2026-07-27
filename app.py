"""
app.py
------
Interface Streamlit. .
"""

import math as mt
import time

import pandas as pd
import streamlit as st

import ils
import importacao
import mapa as mapa_mod
import osm
from dados import Cliente, Deposito, construir_coordenadas, construir_dem

st.set_page_config(page_title="Roteirização de Veículos - ILS", layout="wide")

# ---------------------------------------------------------------------------
# Estado da sessão
# ---------------------------------------------------------------------------
if "deposito" not in st.session_state:
    st.session_state.deposito = None
if "clientes" not in st.session_state:
    st.session_state.clientes = []
if "proximo_id" not in st.session_state:
    st.session_state.proximo_id = 1
if "resultado_busca_deposito" not in st.session_state:
    st.session_state.resultado_busca_deposito = []
if "resultado_busca_cliente" not in st.session_state:
    st.session_state.resultado_busca_cliente = []
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "mapa_path" not in st.session_state:
    st.session_state.mapa_path = None
if "tempo_execucao" not in st.session_state:
    st.session_state.tempo_execucao = None

st.title("Roteirização de Veículos com ILS")
st.caption(
    "Interface para o projeto de Pesquisa Operacional")

# ---------------------------------------------------------------------------
# Sidebar: parâmetros do algoritmo
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Parâmetros do algoritmo")
    cap_max = st.number_input("Capacidade do veículo", min_value=1, value=2000, step=50)
    tempo_max = st.number_input("Tempo máximo por rota (horas)", min_value=0.1, value=4.0, step=0.5)
    max_iteracoes_sem_melhoras = st.number_input(
        "ILS: iterações sem melhora até parar", min_value=1, value=10, step=1
    )

    st.divider()
    total_demanda = sum(c.demanda for c in st.session_state.clientes)
    veiculos_sugeridos = mt.ceil(total_demanda / cap_max) if total_demanda > 0 else 0
    st.metric("Demanda total cadastrada", total_demanda)
    st.metric("Nº de Rotas necessárias", veiculos_sugeridos)

    st.divider()
    with st.expander("🗑️ Limpar tudo"):
        st.warning("Isso apaga o depósito, todos os clientes e o resultado gerado. Não pode ser desfeito.")
        if st.button("Confirmar limpeza", key="btn_limpar_tudo", type="primary", use_container_width=True):
            st.session_state.deposito = None
            st.session_state.clientes = []
            st.session_state.proximo_id = 1
            st.session_state.resultado_busca_deposito = []
            st.session_state.resultado_busca_cliente = []
            st.session_state.resultado = None
            st.session_state.mapa_path = None
            st.session_state.tempo_execucao = None
            st.success("Tudo foi limpo.")
            st.rerun()


# ---------------------------------------------------------------------------
# 1. Depósito
# ---------------------------------------------------------------------------
st.header("1. Depósito")

col_dep1, col_dep2 = st.columns([2, 1])

with col_dep1:
    busca_deposito = st.text_input("Buscar endereço do depósito", key="busca_deposito_input")
    if st.button("Pesquisar", key="btn_busca_deposito"):
        if busca_deposito.strip():
            with st.spinner("Consultando OpenStreetMap..."):
                try:
                    st.session_state.resultado_busca_deposito = osm.buscar_endereco(busca_deposito)
                    if not st.session_state.resultado_busca_deposito:
                        st.warning("Nenhum resultado encontrado para esse endereço.")
                except RuntimeError as e:
                    st.error(str(e))
                    st.session_state.resultado_busca_deposito = []
        else:
            st.warning("Digite um endereço para pesquisar.")

    if st.session_state.resultado_busca_deposito:
        opcoes = {r["display_name"]: r for r in st.session_state.resultado_busca_deposito}
        escolha = st.selectbox("Resultados encontrados", list(opcoes.keys()), key="select_deposito")
        if st.button("Definir como depósito", key="btn_definir_deposito"):
            r = opcoes[escolha]
            st.session_state.deposito = Deposito(
                nome=r["display_name"], latitude=float(r["lat"]), longitude=float(r["lon"])
            )
            st.session_state.resultado_busca_deposito = []
            st.success("Depósito definido.")
            st.rerun()

with col_dep2:
    if st.session_state.deposito:
        d = st.session_state.deposito
        st.info(f"**Depósito atual**\n\n{d.nome}\n\nLat: {d.latitude:.6f}  \nLon: {d.longitude:.6f}")
    else:
        st.warning("Nenhum depósito definido ainda.")

st.divider()

# ---------------------------------------------------------------------------
# 2. Clientes
# ---------------------------------------------------------------------------
st.header("2. Clientes")

col_cli1, col_cli2 = st.columns([2, 1])

with col_cli1:
    busca_cliente = st.text_input("Buscar endereço do cliente", key="busca_cliente_input")
    if st.button("Pesquisar endereço", key="btn_busca_cliente"):
        if busca_cliente.strip():
            with st.spinner("Consultando OpenStreetMap..."):
                try:
                    st.session_state.resultado_busca_cliente = osm.buscar_endereco(busca_cliente)
                    if not st.session_state.resultado_busca_cliente:
                        st.warning("Nenhum resultado encontrado para esse endereço.")
                except RuntimeError as e:
                    st.error(str(e))
                    st.session_state.resultado_busca_cliente = []
        else:
            st.warning("Digite um endereço para pesquisar.")

    if st.session_state.resultado_busca_cliente:
        opcoes_cli = {r["display_name"]: r for r in st.session_state.resultado_busca_cliente}
        escolha_cli = st.selectbox("Resultados encontrados", list(opcoes_cli.keys()), key="select_cliente")
        r_sel = opcoes_cli[escolha_cli]
        st.write(f"Lat: {float(r_sel['lat']):.6f} | Lon: {float(r_sel['lon']):.6f}")

        nome_cliente = st.text_input(
            "Nome do cliente",
            value=r_sel["display_name"].split(",")[0],
            key="nome_cliente_input",
        )
        demanda_cliente = st.number_input("Demanda", min_value=0, value=0, step=1, key="demanda_cliente_input")

        if st.button("Adicionar cliente", key="btn_add_cliente"):
            novo = Cliente(
                id=st.session_state.proximo_id,
                nome=nome_cliente or f"Cliente {st.session_state.proximo_id}",
                latitude=float(r_sel["lat"]),
                longitude=float(r_sel["lon"]),
                demanda=int(demanda_cliente),
            )
            st.session_state.clientes.append(novo)
            st.session_state.proximo_id += 1
            st.session_state.resultado_busca_cliente = []
            st.success(f"{novo.nome} adicionado.")
            st.rerun()

with col_cli2:
    st.metric("Clientes cadastrados", len(st.session_state.clientes))

with st.expander("📥 Importar clientes em lote (CSV/Excel)"):
    st.write(
        "Baixe a planilha modelo, preencha uma linha por cliente e envie de volta. "
        "Cada linha precisa de **nome** e **demanda**"
        ", Preenchendo ou **endereco** ou **latitude** + **longitude**."
    )
    st.download_button(
        "📄 Baixar planilha modelo (.xlsx)",
        data=importacao.gerar_template_bytes(),
        file_name="modelo_clientes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_template",
    )

    arquivo_importado = st.file_uploader(
        "Enviar planilha preenchida (.csv ou .xlsx)", type=["csv", "xlsx", "xls"], key="upload_clientes"
    )

    if arquivo_importado is not None and st.button("Processar planilha", key="btn_processar_planilha"):
        try:
            df_importado = importacao.ler_planilha(arquivo_importado)
        except ValueError as e:
            st.error(str(e))
        else:
            with st.spinner("Processando linhas (geocodificando endereços quando necessário)..."):
                novos_clientes, erros_importacao = importacao.processar_linhas(
                    df_importado, st.session_state.proximo_id
                )

            if novos_clientes:
                st.session_state.clientes.extend(novos_clientes)
                st.session_state.proximo_id += len(novos_clientes)
                st.success(f"{len(novos_clientes)} cliente(s) importado(s) com sucesso.")

            if erros_importacao:
                st.warning(f"{len(erros_importacao)} linha(s) com problema (ignoradas):")
                for msg in erros_importacao:
                    st.text(f"• {msg}")

            if novos_clientes:
                st.rerun()
                
if st.session_state.clientes:
    df_clientes = pd.DataFrame(
        [
            {
                "ID": c.id,
                "Cliente": c.nome,
                "Demanda": c.demanda,
                "Latitude": c.latitude,
                "Longitude": c.longitude,
            }
            for c in st.session_state.clientes
        ]
    )
    st.dataframe(df_clientes, use_container_width=True, hide_index=True)

    with st.expander("✏️ Editar cliente"):
        id_editar = st.selectbox(
            "Selecione o cliente",
            options=[c.id for c in st.session_state.clientes],
            format_func=lambda i: next(c.nome for c in st.session_state.clientes if c.id == i),
            key="id_editar_cliente",
        )
        cliente_atual = next(c for c in st.session_state.clientes if c.id == id_editar)

        novo_nome = st.text_input("Nome", value=cliente_atual.nome, key=f"editar_nome_{id_editar}")
        nova_demanda = st.number_input(
            "Demanda", min_value=0, value=cliente_atual.demanda, step=1, key=f"editar_demanda_{id_editar}"
        )

        if st.button("Salvar alterações", key="btn_salvar_edicao"):
            cliente_atual.nome = novo_nome
            cliente_atual.demanda = int(nova_demanda)
            st.success(f"Cliente '{novo_nome}' atualizado.")
            st.rerun()

    ids_remover = st.multiselect(
        "Selecionar clientes para remover",
        options=[c.id for c in st.session_state.clientes],
        format_func=lambda i: next(c.nome for c in st.session_state.clientes if c.id == i),
        key="ids_remover",
    )
    if st.button("Remover selecionados", key="btn_remover") and ids_remover:
        st.session_state.clientes = [c for c in st.session_state.clientes if c.id not in ids_remover]
        st.success("Cliente(s) removido(s).")
        st.rerun()
else:
    st.info("Nenhum cliente cadastrado ainda.")

st.divider()

# ---------------------------------------------------------------------------
# 3. Gerar roteamento
# ---------------------------------------------------------------------------
st.header("3. Gerar roteamento")

pode_gerar = st.session_state.deposito is not None and len(st.session_state.clientes) >= 1
if not pode_gerar:
    st.warning("Defina o depósito e cadastre pelo menos um cliente para gerar o roteamento.")

if st.button("🚀 Gerar Roteamento", type="primary", disabled=not pode_gerar):
    with st.spinner("Consultando matriz de distâncias (OSRM) e executando o ILS..."):
        try:
            inicio = time.time()

            clientes_calculo = list(st.session_state.clientes)  # snapshot: fixa a ordem usada nos índices
            coordenadas = construir_coordenadas(st.session_state.deposito, clientes_calculo)
            osrm_distances, osrm_durations = osm.obter_matriz_osrm(coordenadas)

            distancia, tempo = ils.montar_matrizes(osrm_distances, osrm_durations)
            dem = construir_dem(clientes_calculo)

            log = []
            resultado = ils.rodar_algoritmo_completo(
                dem, distancia, tempo, cap_max, tempo_max,
                max_iteracoes_sem_melhoras=int(max_iteracoes_sem_melhoras), log=log,
            )
            resultado["log"] = log
            resultado["distancia"] = distancia
            resultado["tempo"] = tempo
            resultado["dem"] = dem

            caminho_mapa, _ = mapa_mod.gerar_mapa(
                st.session_state.deposito, clientes_calculo,
                resultado["rotas_final"], distancia, tempo, dem,
                caminho_saida="resultados/rota.html",
            )

            st.session_state.resultado = resultado
            st.session_state.mapa_path = caminho_mapa
            st.session_state.tempo_execucao = time.time() - inicio

            st.success("Roteamento gerado com sucesso!")
        except RuntimeError as e:
            st.error(f"Erro ao gerar roteamento: {e}")

# ---------------------------------------------------------------------------
# 4. Resultado
# ---------------------------------------------------------------------------
if st.session_state.resultado:
    st.divider()
    st.header("4. Resultado")

    resultado = st.session_state.resultado

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Custo total", f"{round(resultado['custo_final'], 1)} km")
    c2.metric("Rotas necessárias", resultado["num_rotas"])
    c3.metric("Tempo de execução", f"{st.session_state.tempo_execucao:.1f}s")
    c4.metric("Clientes atendidos", len(st.session_state.clientes))

    with st.expander("Detalhes das rotas"):
        for idx, rota in enumerate(resultado["rotas_final"], start=1):
            carga = sum(resultado["dem"][c] for c in rota if c != 0)
            dist_rota = sum(resultado["distancia"][rota[i]][rota[i + 1]] for i in range(len(rota) - 1))
            tempo_rota = sum(resultado["tempo"][rota[i]][rota[i + 1]] for i in range(len(rota) - 1))
            st.write(
                f"**Rota {idx}**: {rota} — {round(dist_rota, 1)} km | "
                f"carga {carga}/{cap_max} | tempo {round(tempo_rota, 2)}h"
            )

    with st.expander("Log de execução"):
        for linha in resultado["log"]:
            st.text(linha)

    st.subheader("Mapa")
    with open(st.session_state.mapa_path, "r", encoding="utf-8") as f:
        html_mapa = f.read()
    st.components.v1.html(html_mapa, height=600, scrolling=True)

    with open(st.session_state.mapa_path, "rb") as f:
        st.download_button("⬇️ Baixar rota.html", data=f, file_name="rota.html", mime="text/html")
