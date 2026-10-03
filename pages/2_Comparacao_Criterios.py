import textwrap

import pandas as pd
import streamlit as st

from ahp.calculo import calcular_pesos_e_consistencia, matriz_identidade
from ahp.estado import inicializar_estado, nomes_criterios, cabecalho_processo
from ahp.navegacao import renderizar_navegacao

inicializar_estado()

ESCALA_SAATY = [
    (1, "Igual", "Mesma importância"),
    (2, "Leve", "Pequena tendência"),
    (3, "Moderada", "Leve preferência"),
    (4, "Moderada+", "Preferência moderada"),
    (5, "Forte", "Preferência clara"),
    (6, "Forte+", "Preferência forte"),
    (7, "Muito Forte", "Forte preferência"),
    (8, "No limite", "Quase absoluta"),
    (9, "Extrema", "Preferência absoluta"),
]


def mostrar_escala_saaty() -> None:
    st.markdown(
        textwrap.dedent("""\
            <style>
            .metric-card {
                background-color: #ffffff;
                padding: 14px;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                text-align: center;
                transition: 0.2s;
                height: 120px;
            }
            .metric-card:hover {
                border: 1px solid #16a34a;
                transform: translateY(-2px);
            }
            .metric-num {
                width: 32px;
                height: 32px;
                margin: 0 auto 10px auto;
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                font-weight: bold;
            }
            .metric-num.low {
                background: linear-gradient(135deg, #2563EB, #60A5FA);
            }
            .metric-num.medium {
                background: linear-gradient(135deg, #D97706, #FBBF24);
            }
            .metric-num.high {
                background: linear-gradient(135deg, #DC2626, #F87171);
            }
            .metric-title {
                font-size: 13px;
                font-weight: 600;
                color: #111827;
                margin-bottom: 6px;
            }
            .metric-desc {
                font-size: 11px;
                color: #6b7280;
                line-height: 1.3;
            }
            </style>
            """),
        unsafe_allow_html=True,
    )

    colunas = st.columns(9)
    for col, (numero, titulo, desc) in zip(colunas, ESCALA_SAATY):
        nivel = "low" if numero <= 3 else ("medium" if numero <= 6 else "high")
        with col:
            st.markdown(
                textwrap.dedent(f"""\
                    <div class="metric-card">
                    <div class="metric-num {nivel}">{numero}</div>
                    <div class="metric-title">{titulo}</div>
                    <div class="metric-desc">{desc}</div>
                    </div>
                    """),
                unsafe_allow_html=True,
            )


def formatar_celula(valor: float) -> str:
    if valor == 1:
        return "1"
    if valor > 1:
        return str(round(valor))
    return f"1/{round(1 / valor)}"


def cor_celula(valor: float) -> str:
    if valor == 1:
        return "color: gray;"
    if valor > 1:
        return "color: #16a34a; font-weight: 700;"
    return "color: gray;"


titulo_col, botao_col = st.columns([4, 1])
with titulo_col:
    st.title("Definir Importância")
    st.caption(cabecalho_processo())
    st.caption("Comparação par a par dos critérios pela escala de Saaty — os pesos são calculados automaticamente")
with botao_col:
    st.write("")
    if st.button("Reiniciar", use_container_width=True):
        st.session_state.matriz_criterios = matriz_identidade(len(st.session_state.criterios))
        st.rerun()

st.warning("Evite usar muitos valores extremos, como 9, para não prejudicar a consistência da matriz.")

mostrar_escala_saaty()

nomes = nomes_criterios()
ids_criterios = [c["id"] for c in st.session_state.criterios]

if len(nomes) < 2:
    st.warning("Cadastre pelo menos 2 critérios na página **Critérios** antes de continuar.")
    st.stop()

matriz = st.session_state.matriz_criterios.copy()
pares = [(i, j) for i in range(len(nomes)) for j in range(i + 1, len(nomes))]

col_principal, col_lateral = st.columns([2, 1], gap="large")

with col_principal:
    titulo_col2, contagem_col = st.columns([3, 1])
    titulo_col2.subheader("Comparação par a par")
    contagem_col.markdown(f"<div style='text-align:right; color:gray;'>{len(pares)} pares</div>", unsafe_allow_html=True)

    for i, j in pares:
        nome_i, nome_j = nomes[i], nomes[j]
        valor_atual = matriz[i][j]
        p_atual = 0
        if valor_atual > 1:
            p_atual = -round(valor_atual)
        elif valor_atual < 1:
            p_atual = round(1 / valor_atual)

        with st.container(border=True):
            col_i, col_vs, col_j = st.columns([4, 1, 4])
            with col_i.container(border=True):
                if p_atual < 0:
                    st.markdown(f":green[**{nome_i}**]")
                else:
                    st.markdown(f"**{nome_i}**")
            col_vs.markdown("<div style='text-align:center; padding-top:10px; color:gray;'>vs</div>", unsafe_allow_html=True)
            with col_j.container(border=True):
                if p_atual > 0:
                    st.markdown(f":green[**{nome_j}**]")
                else:
                    st.markdown(f"**{nome_j}**")

            p_escolhido = st.slider(
                f"{nome_i} vs {nome_j}",
                min_value=-9,
                max_value=9,
                value=p_atual,
                step=1,
                label_visibility="collapsed",
                # Chave pelo id dos dois critérios (não pela posição i/j): assim, se um critério for
                # excluído e a lista reordenar, este controle não herda o valor de um par diferente.
                key=f"comp_{ids_criterios[i]}_{ids_criterios[j]}",
            )
            leg_esq, leg_meio, leg_dir = st.columns(3)
            leg_esq.caption("← mais importante")
            leg_meio.markdown("<div style='text-align:center; color:gray;'>igual</div>", unsafe_allow_html=True)
            leg_dir.markdown("<div style='text-align:right; color:gray;'>mais importante →</div>", unsafe_allow_html=True)

            if p_escolhido > 0:
                valor = 1.0 / p_escolhido
                descricao = f"**{p_escolhido}**  {nome_j} é {p_escolhido}× mais importante"
                espelho = f"1/{p_escolhido}"
            elif p_escolhido < 0:
                valor = float(-p_escolhido)
                descricao = f"**{-p_escolhido}**  {nome_i} é {-p_escolhido}× mais importante"
                espelho = str(-p_escolhido)
            else:
                valor = 1.0
                descricao = "**Igual importância**"
                espelho = "1"

            matriz[i][j] = valor
            matriz[j][i] = 1 / valor

            col_desc, col_esp = st.columns([3, 1])
            col_desc.markdown(descricao)
            col_esp.markdown(f"<div style='text-align:right; color:gray;'>espelho: {espelho}</div>", unsafe_allow_html=True)

    st.session_state.matriz_criterios = matriz

with col_lateral:
    pesos, cr = calcular_pesos_e_consistencia(matriz)
    st.session_state.pesos_criterios = pesos
    st.session_state.cr_criterios = cr

    with st.container(border=True):
        st.markdown("**Pesos calculados**")
        st.caption("Pesos calculados pelo AHPy a partir do autovetor principal da matriz de comparação")
        for nome, peso in zip(nomes, pesos):
            col_nome, col_pct = st.columns([3, 1])
            col_nome.write(nome)
            col_pct.markdown(f"<div style='text-align:right;'>{peso:.1%}</div>", unsafe_allow_html=True)
            st.progress(float(peso))

    with st.container(border=True):
        st.markdown("**Consistência**")
        st.metric("CR", f"{cr:.3f}")
        if cr > 0.1:
            st.error("Julgamentos inconsistentes (CR > 0,10). Revise as comparações.")
        else:
            st.success("Julgamentos consistentes (CR ≤ 0,10).")

    if st.button("Salvar pesos", type="primary", use_container_width=True):
        st.session_state.pesos_salvos = True
        st.toast("Pesos salvos com sucesso!")

st.subheader("Matriz de comparação")
st.caption("Preenchida automaticamente pelo AHP: aⱼᵢ = 1 / aᵢⱼ")

df_valores = pd.DataFrame(matriz, index=nomes, columns=nomes)
estilo = df_valores.style.apply(lambda col: [cor_celula(v) for v in col], axis=0).format(formatar_celula)
st.dataframe(estilo, use_container_width=True)

renderizar_navegacao("pages/2_Comparacao_Criterios.py")
