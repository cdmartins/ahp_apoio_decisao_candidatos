import streamlit as st

from ahp.estado import inicializar_estado, iniciar_nova_decisao, cabecalho_processo
from ahp.navegacao import renderizar_navegacao

inicializar_estado()

st.title("AHP-Qualifica")
st.write(
    "Sistema de apoio à decisão para seleção de candidatos usando o método AHP "
    "(Analytic Hierarchy Process)."
)

st.markdown("### Como usar")
st.markdown(
    """
    Siga as páginas na barra lateral, em ordem (ou use os botões no final de cada página):

    1. **Resumo do Processo** — acompanhe o andamento geral e exporte o relatório.
    2. **Critérios** — defina os critérios de avaliação (ex.: experiência, formação).
    3. **Definir Importância** — compare os critérios par a par para gerar os pesos.
    4. **Candidatos e Avaliações** — cadastre os candidatos (manualmente ou por planilha) e suas notas em cada critério.
    5. **Resultado** — veja o ranking final, os pesos calculados e a consistência (CR).
    """
)

st.info(
    "Não há dados de exemplo — comece iniciando um processo seletivo abaixo e depois vá "
    "preenchendo cada página na ordem: Critérios, Definir Importância, Candidatos e Avaliações."
)

st.divider()
st.markdown("### Processo seletivo")
st.caption(
    "Só é possível conduzir um processo seletivo por vez. Iniciar um processo define o nome e o "
    "cargo (usados no cabeçalho de todas as páginas) e limpa os critérios, candidatos e avaliações atuais."
)

if "mostrar_nova_decisao" not in st.session_state:
    st.session_state.mostrar_nova_decisao = False

col_status, col_botao = st.columns([3, 2])
with col_status:
    if st.session_state.decisao_iniciada:
        st.success(f":green[✓] Decisão ativa: {cabecalho_processo()}")
    else:
        st.warning("Nenhum processo seletivo iniciado ainda.")
with col_botao:
    if st.button("Iniciar processo seletivo", use_container_width=True):
        st.session_state.mostrar_nova_decisao = True

if st.session_state.mostrar_nova_decisao:
    with st.container(border=True):
        nome_processo = st.text_input(
            "Nome do Processo", value=st.session_state.processo_atual["nome"], placeholder="Ex.: Analista de Dados 2026"
        )
        cargo = st.text_input(
            "Cargo", value=st.session_state.processo_atual["cargo"], placeholder="Ex.: Analista de Dados"
        )

        col_iniciar, col_cancelar = st.columns(2)
        if col_iniciar.button("Iniciar", type="primary", use_container_width=True):
            if not nome_processo.strip() or not cargo.strip():
                st.error("Preencha o nome do processo e o cargo.")
            else:
                iniciar_nova_decisao(nome_processo.strip(), cargo.strip())
                st.session_state.mostrar_nova_decisao = False
                st.toast("Processo seletivo iniciado!")
                st.switch_page("pages/0_Resumo.py")
        if col_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.mostrar_nova_decisao = False
            st.rerun()

renderizar_navegacao("inicio.py")
