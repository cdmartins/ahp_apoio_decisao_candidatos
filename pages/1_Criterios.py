import streamlit as st

from ahp.estado import (
    inicializar_estado,
    sincronizar_matriz_criterios,
    sincronizar_avaliacoes,
    novo_criterio_id,
    cabecalho_processo,
    TIPOS_CRITERIO,
    OPCOES_ESCALA,
)
from ahp.navegacao import renderizar_navegacao

inicializar_estado()

if "form_versao" not in st.session_state:
    st.session_state.form_versao = 0


def chave(campo: str) -> str:
    return f"{campo}_{st.session_state.form_versao}"


def limpar_formulario() -> None:
    st.session_state.editando_criterio_id = None
    st.session_state.form_versao += 1


def carregar_criterio_no_formulario(criterio: dict) -> None:
    st.session_state.editando_criterio_id = criterio["id"]
    st.session_state.form_versao += 1
    escala_atual = f'{criterio["escala_min"]} a {criterio["escala_max"]}'
    opcao = escala_atual if escala_atual in ("1 a 5", "1 a 10") else "Personalizada"
    st.session_state[chave("form_nome")] = criterio["nome"]
    st.session_state[chave("form_tipo")] = criterio["tipo"]
    st.session_state[chave("form_escala_opcao")] = opcao
    st.session_state[chave("form_escala_min")] = criterio["escala_min"]
    st.session_state[chave("form_escala_max")] = criterio["escala_max"]


def excluir_criterio(criterio_id: str) -> None:
    st.session_state.criterios = [c for c in st.session_state.criterios if c["id"] != criterio_id]
    if st.session_state.editando_criterio_id == criterio_id:
        limpar_formulario()
    sincronizar_matriz_criterios()
    sincronizar_avaliacoes()


titulo_col, botao_col = st.columns([3, 2])
with titulo_col:
    st.title("Gerenciar Critérios")
    st.caption(cabecalho_processo())
    st.caption("Cadastre os critérios que serão usados na avaliação dos candidatos.")
with botao_col:
    st.write("")
    st.write("")
    if st.button("Importar Critérios e Candidatos", use_container_width=True):
        st.session_state.mostrar_importar = True
        st.switch_page("pages/3_Candidatos.py")
    st.caption("Pula direto para a importação por planilha, que cria critérios e candidatos juntos.")

col_form, col_lista = st.columns([1, 2], gap="large")

with col_form:
    with st.container(border=True):
        editando = st.session_state.editando_criterio_id is not None
        st.subheader("Editar critério" if editando else "Novo critério")
        st.caption("Nome, tipo e escala de pontuação")

        st.text_input("Nome do critério", placeholder="Ex.: Experiência Técnica", key=chave("form_nome"))

        st.write("Tipo")
        st.segmented_control(
            "Tipo", options=TIPOS_CRITERIO, key=chave("form_tipo"), label_visibility="collapsed"
        )

        st.selectbox("Escala", options=OPCOES_ESCALA, key=chave("form_escala_opcao"))

        if st.session_state.get(chave("form_escala_opcao")) == "Personalizada":
            col_min, col_max = st.columns(2)
            col_min.number_input("Mínimo", step=1, key=chave("form_escala_min"))
            col_max.number_input("Máximo", step=1, key=chave("form_escala_max"))

        col_salvar, col_limpar = st.columns(2)
        salvar = col_salvar.button("Salvar", type="primary", use_container_width=True)
        limpar = col_limpar.button("Limpar", use_container_width=True)

        if limpar:
            limpar_formulario()
            st.rerun()

        if salvar:
            nome = (st.session_state.get(chave("form_nome")) or "").strip()
            tipo = st.session_state.get(chave("form_tipo"))
            opcao_escala = st.session_state.get(chave("form_escala_opcao"))

            if not nome:
                st.error("Informe o nome do critério.")
            elif not tipo:
                st.error("Selecione o tipo do critério (Técnico ou Comportamental).")
            else:
                if opcao_escala == "1 a 5":
                    escala_min, escala_max = 1, 5
                elif opcao_escala == "1 a 10":
                    escala_min, escala_max = 1, 10
                else:
                    escala_min = st.session_state.get(chave("form_escala_min"), 1)
                    escala_max = st.session_state.get(chave("form_escala_max"), 5)

                if escala_min >= escala_max:
                    st.error("O valor mínimo da escala deve ser menor que o máximo.")
                else:
                    dados = {"nome": nome, "tipo": tipo, "escala_min": escala_min, "escala_max": escala_max}
                    editando_id = st.session_state.editando_criterio_id
                    if editando_id:
                        for c in st.session_state.criterios:
                            if c["id"] == editando_id:
                                c.update(dados)
                    else:
                        st.session_state.criterios.append({"id": novo_criterio_id(), **dados})

                    sincronizar_matriz_criterios()
                    sincronizar_avaliacoes()
                    limpar_formulario()
                    st.rerun()

with col_lista:
    st.subheader("Critérios cadastrados")
    st.caption(f"{len(st.session_state.criterios)} critério(s)")

    if not st.session_state.criterios:
        st.info("Nenhum critério cadastrado ainda. Use o formulário ao lado para adicionar o primeiro.")
    else:
        cor_badge = {"Técnico": "blue", "Comportamental": "violet"}
        colunas = st.columns(2)
        for i, criterio in enumerate(st.session_state.criterios):
            with colunas[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{criterio['nome']}**")
                    st.badge(criterio["tipo"], color=cor_badge.get(criterio["tipo"], "gray"))
                    st.caption(f'Escala **{criterio["escala_min"]} a {criterio["escala_max"]}**')
                    col_alt, col_exc = st.columns(2)
                    if col_alt.button("Alterar", key=f"alterar_{criterio['id']}", use_container_width=True):
                        carregar_criterio_no_formulario(criterio)
                        st.rerun()
                    if col_exc.button("Excluir", key=f"excluir_{criterio['id']}", use_container_width=True):
                        excluir_criterio(criterio["id"])
                        st.rerun()

renderizar_navegacao("pages/1_Criterios.py")
