import textwrap

import streamlit as st

from ahp.calculo import calcular_pesos, calcular_razao_consistencia, calcular_ranking, contar_pares_julgados
from ahp.estado import inicializar_estado, cabecalho_processo
from ahp.navegacao import renderizar_navegacao

inicializar_estado()

criterios = st.session_state.criterios
candidatos = st.session_state.candidatos
processo = st.session_state.processo_atual
matriz_criterios = st.session_state.matriz_criterios
avaliacoes = st.session_state.avaliacoes

n_criterios = len(criterios)
n_candidatos = len(candidatos)

pesos_criterios = None
cr_criterios = None
if n_criterios >= 2:
    pesos_criterios = calcular_pesos(matriz_criterios)
    _, _, cr_criterios = calcular_razao_consistencia(matriz_criterios, pesos_criterios)

ranking = []
if n_criterios >= 2 and n_candidatos >= 2:
    ranking = calcular_ranking(criterios, candidatos, avaliacoes, pesos_criterios)

pesos_salvos = st.session_state.get("pesos_salvos", False)

pares_totais = n_criterios * (n_criterios - 1) // 2
pares_julgados = contar_pares_julgados(matriz_criterios) if n_criterios >= 2 else 0

etapa1_concluida = n_criterios >= 2
etapa2_concluida = etapa1_concluida and pesos_salvos
etapa3_andamento = etapa2_concluida and n_candidatos > 0

ETAPAS = [
    {
        "titulo": "Gerenciar Critérios",
        "descricao": "Nome, tipo e escala de cada critério",
        "status": "Concluída" if etapa1_concluida else ("Em andamento" if n_criterios > 0 else "Pendente"),
        "info": f"{n_criterios} critério(s) cadastrado(s)" if n_criterios > 0 else "nenhum critério ainda",
    },
    {
        "titulo": "Definir Importância",
        "descricao": "Comparação par a par pela escala de Saaty",
        "status": "Concluída" if etapa2_concluida else ("Em andamento" if etapa1_concluida else "Pendente"),
        "info": f"{pares_julgados} de {pares_totais} pares julgados" if n_criterios >= 2 else "aguardando critérios",
    },
    {
        "titulo": "Candidatos e Avaliações",
        "descricao": "Importação de planilha e notas por critério",
        "status": "Em andamento" if etapa3_andamento else "Pendente",
        "info": f"{n_candidatos} candidato(s) avaliado(s)" if n_candidatos > 0 else "nenhum candidato ainda",
    },
    {
        "titulo": "Resultados",
        "descricao": "Aplicação dos pesos e ranking final",
        "status": "Pendente",
        "info": "aguardando fechamento",
    },
]

etapas_concluidas = sum(1 for etapa in ETAPAS if etapa["status"] == "Concluída")
proxima_etapa = next((etapa["titulo"] for etapa in ETAPAS if etapa["status"] != "Concluída"), None)


st.title("Resumo do Processo")
st.caption(cabecalho_processo())
st.caption(f"Acompanhe o andamento geral do seu processo seletivo — {processo['nome']}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.caption("Candidatos avaliados")
        st.markdown(f"### {n_candidatos} de {n_candidatos}")
        st.caption("todos com notas lançadas" if n_candidatos > 0 else "nenhum candidato cadastrado ainda")
with col2:
    with st.container(border=True):
        st.caption("Critérios definidos")
        st.markdown(f"### {n_criterios} critérios")
        st.caption("pesos AHP calculados" if pesos_criterios is not None else "aguardando critérios suficientes")
with col3:
    with st.container(border=True):
        st.caption("Consistência (CR)")
        if cr_criterios is not None:
            st.markdown(f"### {cr_criterios:.2f}".replace(".", ","))
            if pares_julgados == 0:
                st.caption("nenhuma comparação feita")
            else:
                st.caption("consistência aceitável" if cr_criterios <= 0.1 else "revise as comparações")
        else:
            st.markdown("### —")
            st.caption("aguardando critérios")
with col4:
    with st.container(border=True):
        st.caption("Etapas concluídas")
        st.markdown(f"### {etapas_concluidas}/4")
        st.caption(f"próxima: {proxima_etapa}" if proxima_etapa else "processo concluído")

if n_criterios >= 2 and pares_julgados == 0:
    st.info(
        "Nenhuma comparação de importância foi feita entre os critérios — todos estão com o mesmo peso "
        f"({1 / n_criterios:.1%} cada). Volte a **Definir Importância** e julgue os pares, ou, se os critérios "
        "forem mesmo igualmente importantes, pode seguir assim: o AHP deixa de ser necessário e o resultado "
        "equivale a somar as notas de cada critério com peso igual."
    )

CORES_STATUS = {"Concluída": "#16a34a", "Em andamento": "#2563eb", "Pendente": "#d1d5db"}
CLASSES_STATUS = {"Concluída": "done", "Em andamento": "andamento", "Pendente": "pendente"}

col_etapas, col_lateral = st.columns([3, 2], gap="large")

with col_etapas:
    with st.container(border=True):
        st.markdown("**Etapas do processo**")
        st.caption("Fluxo do método AHP nesta aplicação")

        estilo_timeline = textwrap.dedent("""\
            <style>
            .timeline .step { display:flex; gap:16px; position:relative; padding-bottom:28px; }
            .timeline .step:last-child { padding-bottom:0; }
            .timeline .step-marker {
                flex:0 0 32px; width:32px; height:32px; border-radius:50%; color:white;
                display:flex; align-items:center; justify-content:center; font-weight:700; z-index:1;
            }
            .timeline .step-marker.pendente { color:#6b7280; }
            .timeline .step-line { position:absolute; left:15px; top:32px; bottom:-28px; width:2px; background:#e5e7eb; }
            .timeline .step:last-child .step-line { display:none; }
            .timeline .step-content { flex:1; }
            .timeline .step-header { display:flex; justify-content:space-between; align-items:center; gap:8px; }
            .timeline .step-desc { color:#6b7280; font-size:13px; margin-top:2px; }
            .timeline .step-info { color:#9ca3af; font-size:12px; margin-top:6px; }
            .timeline .badge { padding:2px 10px; border-radius:12px; font-size:12px; font-weight:600; white-space:nowrap; }
            .timeline .badge.done { background:#dcfce7; color:#15803d; }
            .timeline .badge.andamento { background:#dbeafe; color:#1d4ed8; }
            .timeline .badge.pendente { background:#f3f4f6; color:#6b7280; }
            </style>
            """)
        html = [estilo_timeline, '<div class="timeline">']
        for i, etapa in enumerate(ETAPAS, start=1):
            classe = CLASSES_STATUS[etapa["status"]]
            cor = CORES_STATUS[etapa["status"]]
            passo = textwrap.dedent(f"""\
                <div class="step">
                <div class="step-marker {classe}" style="background:{cor};">{i}</div>
                <div class="step-line"></div>
                <div class="step-content">
                <div class="step-header">
                <b>{etapa['titulo']}</b>
                <span class="badge {classe}">{etapa['status']}</span>
                </div>
                <div class="step-desc">{etapa['descricao']}</div>
                <div class="step-info">{etapa['info']}</div>
                </div>
                </div>
                """)
            html.append(passo)
        html.append("</div>")
        st.markdown("\n".join(html), unsafe_allow_html=True)

with col_lateral:
    with st.container(border=True):
        st.markdown("**Progresso das etapas**", help=None)
        st.markdown(
            "<div style='display:flex; gap:18px; justify-content:center; font-size:13px; color:#374151;'>"
            "<span><span style='color:#16a34a;'>●</span> Concluídas</span>"
            "<span><span style='color:#2563eb;'>●</span> Em andamento</span>"
            "<span><span style='color:#9ca3af;'>●</span> Pendentes</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        pct_concluida = etapas_concluidas / 4 * 100
        n_andamento = sum(1 for etapa in ETAPAS if etapa["status"] == "Em andamento")
        pct_andamento = n_andamento / 4 * 100
        fim_andamento = pct_concluida + pct_andamento

        st.markdown(
            textwrap.dedent(f"""\
                <div style='position:relative; width:200px; height:200px; margin:20px auto;'>
                <div style='width:200px; height:200px; border-radius:50%;
                background:conic-gradient(#16a34a 0% {pct_concluida:.4f}%,
                #2563eb {pct_concluida:.4f}% {fim_andamento:.4f}%,
                #e5e7eb {fim_andamento:.4f}% 100%);'>
                </div>
                <div style='position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
                width:128px; height:128px; background:white; border-radius:50%;
                display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                <div style='font-size:26px; font-weight:700;'>{pct_concluida:.0f}%</div>
                <div style='font-size:13px; color:gray;'>concluído</div>
                </div>
                </div>
                """),
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        col_rank_titulo, col_rank_link = st.columns([2, 1])
        with col_rank_titulo:
            st.markdown("**Ranking parcial**")
            st.caption("Score global com os pesos AHP atuais")
        with col_rank_link:
            st.write("")
            if st.button("Ver →", use_container_width=True, help="Ver resultados completos"):
                st.switch_page("pages/4_Resultado.py")

        if not ranking:
            st.info("Ainda não há dados suficientes para calcular o ranking.")
        else:
            cores_posicao = ["#f59e0b", "#9ca3af", "#b45309"]
            for posicao, (nome, pontuacao) in enumerate(ranking[:3], start=1):
                cor = cores_posicao[posicao - 1]
                col_nome, col_pct = st.columns([3, 1])
                col_nome.markdown(f"**{posicao}º** {nome}")
                col_pct.markdown(
                    f"<div style='text-align:right; color:{cor}; font-weight:700;'>{pontuacao:.1%}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    textwrap.dedent(f"""\
                        <div style='background:#f3f4f6; border-radius:6px; height:8px; margin-bottom:10px;'>
                        <div style='background:{cor}; width:{pontuacao * 100:.1f}%; height:8px; border-radius:6px;'></div>
                        </div>
                        """),
                    unsafe_allow_html=True,
                )

renderizar_navegacao("pages/0_Resumo.py")
