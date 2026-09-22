import textwrap
from datetime import datetime

import pandas as pd
import streamlit as st

from ahp.calculo import (
    calcular_pesos,
    calcular_razao_consistencia,
    calcular_prioridades_locais,
    calcular_ranking,
    contar_pares_julgados,
)
from ahp.estado import inicializar_estado, cabecalho_processo
from ahp.navegacao import renderizar_navegacao
from ahp.relatorio import gerar_relatorio_pdf, PALETA_CRITERIOS

inicializar_estado()

CORES_PODIO = {
    1: {"bg": "#fffbeb", "border": "#f59e0b", "circulo": "#f59e0b"},
    2: {"bg": "#ffffff", "border": "#e5e7eb", "circulo": "#9ca3af"},
    3: {"bg": "#ffffff", "border": "#e5e7eb", "circulo": "#b45309"},
}

criterios = st.session_state.criterios
candidatos = st.session_state.candidatos
processo = st.session_state.processo_atual

titulo_col, botoes_col = st.columns([3, 2])
with titulo_col:
    st.title("Resultados")
    st.caption(cabecalho_processo())

if len(criterios) < 2 or len(candidatos) < 2:
    with titulo_col:
        st.caption("Comparação automática dos candidatos com os pesos AHP")
    st.warning("Complete as páginas anteriores (Critérios, Definir Importância e Candidatos) antes de ver o resultado.")
    renderizar_navegacao("pages/4_Resultado.py")
    st.stop()

matriz_criterios = st.session_state.matriz_criterios
pesos_criterios = calcular_pesos(matriz_criterios)
_, _, cr_criterios = calcular_razao_consistencia(matriz_criterios, pesos_criterios)
pares_julgados = contar_pares_julgados(matriz_criterios)

nomes_candidatos = [c["nome"] for c in candidatos]

prioridades_locais = calcular_prioridades_locais(criterios, candidatos, st.session_state.avaliacoes)
ranking = calcular_ranking(criterios, candidatos, st.session_state.avaliacoes, pesos_criterios)
cores_criterio = {c["id"]: PALETA_CRITERIOS[i % len(PALETA_CRITERIOS)] for i, c in enumerate(criterios)}

if "resultado_calculado_em" not in st.session_state:
    st.session_state.resultado_calculado_em = datetime.now()

with titulo_col:
    st.caption(
        "Comparação automática dos candidatos com os pesos AHP — calculado em "
        f"{st.session_state.resultado_calculado_em.strftime('%d/%m/%Y às %H:%M')}"
    )

with botoes_col:
    st.write("")
    col_recalc, col_export = st.columns(2)
    if col_recalc.button("Recalcular", use_container_width=True):
        st.session_state.resultado_calculado_em = datetime.now()
        st.rerun()
    col_export.download_button(
        "Exportar Relatório",
        data=gerar_relatorio_pdf(
            processo, criterios, pesos_criterios, cr_criterios, ranking, pares_julgados,
            prioridades_locais, nomes_candidatos, candidatos, st.session_state.resultado_calculado_em,
        ),
        file_name=f"relatorio_{processo['nome']}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

if pares_julgados == 0:
    st.info(
        "Nenhuma comparação de importância foi feita entre os critérios — todos estão com o mesmo peso "
        f"({1 / len(criterios):.1%} cada), e é por isso que a CR abaixo aparece 0,000. Volte a "
        "**Definir Importância** e julgue os pares, ou, se os critérios forem mesmo igualmente importantes, "
        "pode seguir assim: o AHP deixa de ser necessário e o resultado equivale a somar as notas de cada "
        "critério com peso igual."
    )

# --- Pódio (top 3) ---------------------------------------------------------
top3 = ranking[:3]
colunas_podio = st.columns(len(top3))
for col, (posicao, (nome, pontuacao)) in zip(colunas_podio, enumerate(top3, start=1)):
    idx = nomes_candidatos.index(nome)
    estilo = CORES_PODIO[posicao]

    rotulo_topo = (
        f"""<div style="display:inline-block; background:{estilo['circulo']}; color:white; font-size:10px; font-weight:700; padding:3px 10px; border-radius:10px; margin-bottom:10px;">MELHOR CANDIDATO</div>"""
        if posicao == 1
        else f"""<div style="font-size:11px; color:#9ca3af; font-weight:600; margin-bottom:10px;">{posicao}° COLOCADO</div>"""
    )

    itens_criterio = "".join(
        f'<div style="text-align:left;">'
        f'<div style="font-size:10px; color:#6b7280;">{c["nome"]}</div>'
        f'<div style="font-size:13px; font-weight:600; margin-top:2px;">{prioridades_locais[c["id"]][idx]:.1%}</div>'
        f'</div>'
        for c in criterios
    )

    with col:
        st.markdown(
            textwrap.dedent(f"""\
                <div style="background:{estilo['bg']}; border:1px solid {estilo['border']}; border-radius:12px; padding:16px;">
                {rotulo_topo}
                <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:28px; height:28px; border-radius:50%; background:{estilo['circulo']}; color:white; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0;">{posicao}</div>
                <div>
                <div style="font-weight:700; font-size:15px;">{nome}</div>
                <div style="font-size:12px; color:#6b7280;">{processo['cargo']}</div>
                </div>
                </div>
                <div style="margin-top:12px;">
                <span style="font-size:26px; font-weight:700;">{pontuacao:.1%}</span>
                <span style="font-size:12px; color:#6b7280;"> score global</span>
                </div>
                <div style="background:#f3f4f6; border-radius:4px; height:6px; margin-top:8px;">
                <div style="background:{estilo['circulo']}; width:{pontuacao * 100:.1f}%; height:6px; border-radius:4px;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:14px; gap:6px; flex-wrap:wrap;">
                {itens_criterio}
                </div>
                </div>
                """),
            unsafe_allow_html=True,
        )

# --- Ranking final + Aplicação dos pesos -----------------------------------
col_ranking, col_pesos = st.columns(2, gap="large")

with col_ranking:
    with st.container(border=True):
        st.markdown("**Ranking final**")
        st.caption("Soma das prioridades ponderadas pelos pesos dos critérios")

        for posicao, (nome, pontuacao) in enumerate(ranking, start=1):
            idx = nomes_candidatos.index(nome)
            col_nome, col_pct = st.columns([3, 1])
            col_nome.markdown(f"**{posicao}°** {nome}")
            col_pct.markdown(f"<div style='text-align:right; font-weight:700;'>{pontuacao:.1%}</div>", unsafe_allow_html=True)

            segmentos = "".join(
                f"""<div style="background:{cores_criterio[c['id']]}; width:{peso * prioridades_locais[c['id']][idx] * 100:.2f}%; height:8px;"></div>"""
                for c, peso in zip(criterios, pesos_criterios)
            )
            st.markdown(
                textwrap.dedent(f"""\
                    <div style="display:flex; background:#f3f4f6; border-radius:4px; overflow:hidden; height:8px; margin-bottom:10px;">
                    {segmentos}
                    </div>
                    """),
                unsafe_allow_html=True,
            )

        legenda = "".join(
            f"""<span style="margin-right:14px;"><span style="color:{cores_criterio[c['id']]};">■</span> {c['nome']} · {peso:.1%}</span>"""
            for c, peso in zip(criterios, pesos_criterios)
        )
        st.markdown(
            f"<div style='font-size:11px; color:#374151; margin-top:4px;'>{legenda}</div>", unsafe_allow_html=True
        )

with col_pesos:
    with st.container(border=True):
        st.markdown("**Aplicação dos pesos AHP**")
        st.caption("Peso de cada critério vindo da matriz de comparação")

        for criterio, peso in zip(criterios, pesos_criterios):
            col_nome, col_pct = st.columns([3, 1])
            col_nome.write(criterio["nome"])
            col_pct.markdown(f"<div style='text-align:right; font-weight:600;'>{peso:.1%}</div>", unsafe_allow_html=True)
            st.markdown(
                textwrap.dedent(f"""\
                    <div style="background:#f3f4f6; border-radius:4px; height:6px; margin-bottom:10px;">
                    <div style="background:{cores_criterio[criterio['id']]}; width:{peso * 100:.2f}%; height:6px; border-radius:4px;"></div>
                    </div>
                    """),
                unsafe_allow_html=True,
            )

        col_cand, col_cr = st.columns(2)
        with col_cand:
            with st.container(border=True):
                st.caption("Candidatos comparados")
                st.markdown(f"### {len(candidatos)}")
        with col_cr:
            with st.container(border=True):
                st.caption("CR da matriz")
                cor_cr = "#16a34a" if cr_criterios <= 0.1 else "#dc2626"
                st.markdown(
                    f"<div style='font-size:24px; font-weight:700; color:{cor_cr};'>{cr_criterios:.3f}</div>",
                    unsafe_allow_html=True,
                )
        if cr_criterios > 0.1:
            st.caption("Acima de 0,10 — revise as comparações em Definir Importância.")

# --- Prioridades por critério ------------------------------------------------
with st.container(border=True):
    col_titulo, col_nota = st.columns([3, 1])
    with col_titulo:
        st.markdown("**Prioridades por critério**")
        st.caption("Notas normalizadas dentro de cada critério — soma 100% por critério")
    with col_nota:
        st.markdown(
            "<div style='text-align:right; color:#9ca3af; font-size:12px; padding-top:8px;'>valores em % da coluna</div>",
            unsafe_allow_html=True,
        )

    ALTURA_MAXIMA = 100
    for criterio, peso in zip(criterios, pesos_criterios):
        cor = cores_criterio[criterio["id"]]
        col_nome_c, col_peso_c = st.columns([4, 1])
        col_nome_c.markdown(f"<span style='color:{cor};'>■</span> **{criterio['nome']}**", unsafe_allow_html=True)
        col_peso_c.markdown(
            f"<div style='text-align:right; color:#9ca3af; font-size:12px;'>peso {peso:.1%}</div>", unsafe_allow_html=True
        )

        valores = prioridades_locais[criterio["id"]]
        maximo = max(valores) if len(valores) else 0
        barras = "".join(
            f'<div style="display:flex; flex-direction:column; align-items:center; flex:1;">'
            f'<div style="font-size:12px; font-weight:600; margin-bottom:4px;">{valor:.0%}</div>'
            f'<div style="width:60%; height:{(valor / maximo * ALTURA_MAXIMA) if maximo > 0 else 0:.1f}px; background:{cor}; border-radius:4px 4px 0 0;"></div>'
            f'<div style="font-size:11px; color:#6b7280; margin-top:6px; text-align:center;">{nome_c}</div>'
            f'</div>'
            for nome_c, valor in zip(nomes_candidatos, valores)
        )
        st.markdown(
            textwrap.dedent(f"""\
                <div style="display:flex; align-items:flex-end; height:{ALTURA_MAXIMA + 40}px; gap:12px; padding-top:6px;">
                {barras}
                </div>
                """),
            unsafe_allow_html=True,
        )
        st.divider()

with st.expander("Ver tabela completa"):
    df_ranking = pd.DataFrame(ranking, columns=["Candidato", "Pontuação"])
    df_ranking.index = df_ranking.index + 1
    df_ranking.index.name = "Posição"
    st.dataframe(df_ranking.style.format({"Pontuação": "{:.1%}"}), use_container_width=True)

    df_prioridades = pd.DataFrame(
        {c["nome"]: prioridades_locais[c["id"]] for c in criterios}, index=nomes_candidatos
    )
    st.caption("Prioridade de cada candidato dentro de cada critério (soma de cada coluna = 100%).")
    st.dataframe(df_prioridades.style.format("{:.1%}"), use_container_width=True)

renderizar_navegacao("pages/4_Resultado.py")
