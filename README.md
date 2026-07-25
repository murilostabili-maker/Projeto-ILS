# Interface Streamlit — Roteirização com ILS

Interface gráfica para o seu algoritmo de roteirização (heurística construtiva
+ VND + Iterated Local Search). **A lógica de otimização não foi reescrita** —
apenas reorganizada em funções, para poder ser chamada pela interface.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abra o endereço que o Streamlit mostrar no terminal (geralmente `http://localhost:8501`).

## Estrutura

```
app.py         -> Interface Streamlit (busca de endereço, cadastro de clientes, botão "Gerar Roteamento", resultado)
ils.py         -> Algoritmo original (construção + VND intra/entre rotas + ILS) — motor de otimização
mapa.py        -> Geração do mapa Folium (mesmo código do seu snippet, adaptado à lista de clientes da interface)
osm.py         -> Busca de endereço (Nominatim) e matriz de distâncias/tempos (OSRM) — mesma API do notebook
dados.py       -> Classes Deposito/Cliente e conversão para o formato esperado pelo algoritmo (dem, coordenadas)
resultados/    -> onde rota.html é salvo a cada execução
teste_pipeline.py -> script de teste com instância sintética (não usado pela interface; serviu para validar o pipeline)
```

## O que foi alterado em relação ao seu código original — e por quê

| Arquivo original | O que mudou | Por quê |
|---|---|---|
| Heurística construtiva (script 1) | Virou a função `construir_rotas_iniciais()` em `ils.py`. `dem` deixou de vir de uma planilha Excel e passou a ser montado a partir dos clientes cadastrados na interface (`dados.construir_dem`). As coordenadas hardcoded (`coords = {...}`) deram lugar à lista de clientes cadastrados. | A interface precisa alimentar o algoritmo com dados dinâmicos, não fixos. |
| `get_osrm_matrix` | Renomeada para `osm.obter_matriz_osrm`, mesma lógica de requisição; em vez de retornar `(None, None)` em caso de erro, agora lança uma exceção (`RuntimeError`) para o Streamlit poder mostrar uma mensagem de erro amigável. | Uma tupla `(None, None)` silenciosa quebraria o restante do pipeline sem explicação. |
| `swap`, `re_insertion`, `dois_opt`, `swap_entre_rotas`, `reinsert_entre_rotas` | **Copiadas exatamente como estavam.** Nenhuma linha de lógica foi tocada. | Já recebiam todos os parâmetros necessários (`distancia`, `tempo`, `tempo_max`, `dem`, `cap_max`) — nada a mudar. |
| `Perturbacao` | Passou a receber `dem`, `tempo`, `cap_max`, `tempo_max` como parâmetros em vez de ler variáveis globais do notebook. Corpo da função idêntico. | Sem essa mudança a função quebraria fora de um notebook (não existiriam variáveis globais). |
| Laços de `print()` do VND intra, VND entre rotas e ILS | Substituídos por `log.append(...)` (uma lista passada por parâmetro, opcional). | O Streamlit não exibe saída de console; o log é mostrado num expander na interface. |
| Duas versões da busca local entre rotas (uma antes do ILS, outra dentro do laço do ILS) | Mantive as **duas separadas** (`vnd_entre_rotas` e `vnd_entre_rotas_ils`), pois no notebook original elas têm uma diferença sutil de controle de fluxo (a primeira reinicia a varredura a partir da rota `a` após uma melhora; a segunda não). Unificá-las mudaria o comportamento do ILS. | Preservar o comportamento exato do algoritmo original, mesmo que a diferença pareça pequena. |
| Folium (seu snippet) | Vira `mapa.gerar_mapa()`. Mesma estrutura visual (marcador do depósito, `CircleMarker` + rótulo numérico por cliente, `PolyLine` colorida por rota com tooltip). A única mudança é a fonte dos pontos: em vez de `lats`/`lons` fixos, usa a lista de clientes cadastrados, na mesma ordem usada para montar a matriz de distâncias. | Os pontos agora são dinâmicos. |

## Ponto de atenção: "quantidade de veículos"

O seu algoritmo **não recebe um número máximo de veículos como restrição rígida** — ele
cria quantas rotas forem necessárias, respeitando apenas `cap_max` (capacidade) e
`tempo_max` (tempo máximo por rota). Por isso, na sidebar da interface, "quantidade de
veículos" aparece apenas como uma **estimativa informativa** (demanda total ÷ capacidade),
igual ao `num_veh = mt.ceil(total_demanda / cap)` do seu script original — que também não
era usado para limitar a construção das rotas, apenas informativo.

Se no futuro você quiser transformar isso em uma restrição real (por exemplo, impedir mais
de N rotas), isso exigiria uma mudança na lógica do algoritmo (não apenas na interface) —
avise se quiser que eu implemente isso.

## Limites do OSRM/Nominatim públicos

O projeto usa os servidores públicos e gratuitos `nominatim.openstreetmap.org` e
`router.project-osrm.org`, os mesmos do seu notebook. Eles têm limite de uso (poucas
requisições por segundo, sem SLA de disponibilidade) — adequados para uso acadêmico/teste,
mas não recomendados para produção com muitos usuários simultâneos. Se a matriz OSRM falhar
(erro HTTP ou timeout), a interface exibe uma mensagem de erro em vez de travar.

## Testes realizados

Não tenho acesso de rede ao Nominatim/OSRM neste ambiente de desenvolvimento, então validei
o pipeline (`construir_rotas_iniciais` → VND intra → VND entre rotas → ILS → geração do mapa)
com uma matriz de distâncias sintética (`teste_pipeline.py`), incluindo casos de borda (1
cliente, remoção de cliente no meio da lista). Todos os clientes foram atendidos, capacidade
e tempo máximo respeitados em todas as rotas, e o ILS melhorou o custo da solução construtiva
em todos os testes. Recomendo testar a busca de endereço real (Nominatim/OSRM) no seu
ambiente antes de usar em produção.
