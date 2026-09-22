"""Inicialização e utilitários do estado compartilhado entre as páginas (st.session_state)."""
import uuid

import streamlit as st

from ahp.calculo import matriz_identidade

PROCESSO_PADRAO = {"nome": "", "cargo": ""}

TIPOS_CRITERIO = ["Técnico", "Comportamental"]
OPCOES_ESCALA = ["1 a 5", "1 a 10", "Personalizada"]


def nomes_criterios() -> list[str]:
    return [c["nome"] for c in st.session_state.criterios]


def gerar_id() -> str:
    return uuid.uuid4().hex[:8]


def novo_criterio_id() -> str:
    return gerar_id()


def novo_candidato_id() -> str:
    return gerar_id()


def cabecalho_processo() -> str:
    """Texto com o processo seletivo e o cargo da decisão em andamento, para exibir no topo das páginas."""
    if not st.session_state.get("decisao_iniciada"):
        return "Nenhum processo seletivo iniciado"
    processo = st.session_state.processo_atual
    return f"{processo['nome']} · {processo['cargo']}"


def iniciar_nova_decisao(nome_processo: str, cargo: str) -> None:
    """Começa uma decisão do zero: define processo/cargo e limpa critérios, candidatos e avaliações."""
    st.session_state.processo_atual = {"nome": nome_processo, "cargo": cargo}
    st.session_state.decisao_iniciada = True
    st.session_state.criterios = []
    st.session_state.candidatos = []
    st.session_state.avaliacoes = {}
    st.session_state.matriz_criterios = None
    st.session_state.matriz_criterios_ids = []
    st.session_state.editando_criterio_id = None
    st.session_state.editando_candidato_id = None
    sincronizar_matriz_criterios()
    sincronizar_avaliacoes()


def inicializar_estado() -> None:
    """Garante que todas as chaves de estado existam. Começa sempre vazio, sem dados de exemplo."""
    if "processo_atual" not in st.session_state:
        st.session_state.processo_atual = dict(PROCESSO_PADRAO)

    if "decisao_iniciada" not in st.session_state:
        st.session_state.decisao_iniciada = False

    if "criterios" not in st.session_state:
        st.session_state.criterios = []

    if "candidatos" not in st.session_state:
        st.session_state.candidatos = []

    if "editando_criterio_id" not in st.session_state:
        st.session_state.editando_criterio_id = None

    if "editando_candidato_id" not in st.session_state:
        st.session_state.editando_candidato_id = None

    sincronizar_matriz_criterios()
    sincronizar_avaliacoes()


def sincronizar_matriz_criterios() -> None:
    """Reconstrói a matriz de comparação a partir da identidade (id) de cada critério, preservando
    o julgamento de todo par cujos dois critérios ainda existem — mesmo que a ordem, a quantidade
    ou o nome tenham mudado. Pares novos (envolvendo um critério recém-criado) entram neutros (1);
    pares cujo critério foi excluído somem junto com ele."""
    criterios = st.session_state.criterios
    ids_atuais = [c["id"] for c in criterios]
    n = len(ids_atuais)

    matriz_antiga = st.session_state.get("matriz_criterios")
    ids_antigos = st.session_state.get("matriz_criterios_ids")

    nova_matriz = matriz_identidade(n)
    if matriz_antiga is not None and ids_antigos:
        posicao_antiga = {id_: i for i, id_ in enumerate(ids_antigos)}
        for nova_i, id_i in enumerate(ids_atuais):
            i_antigo = posicao_antiga.get(id_i)
            if i_antigo is None:
                continue
            for nova_j, id_j in enumerate(ids_atuais):
                j_antigo = posicao_antiga.get(id_j)
                if j_antigo is None:
                    continue
                nova_matriz[nova_i][nova_j] = matriz_antiga[i_antigo][j_antigo]

    st.session_state.matriz_criterios = nova_matriz
    st.session_state.matriz_criterios_ids = ids_atuais


def sincronizar_avaliacoes() -> None:
    """Garante que exista uma nota (por id de candidato) para cada critério, sem apagar as já
    preenchidas. Usa o id do critério (não o nome) como chave — renomear um critério não deve
    fazer as notas já lançadas para ele desaparecerem."""
    avaliacoes = st.session_state.get("avaliacoes", {})
    novas = {}
    for criterio in st.session_state.criterios:
        criterio_id = criterio["id"]
        antigas = avaliacoes.get(criterio_id, {})
        novas[criterio_id] = {}
        for candidato in st.session_state.candidatos:
            valor_default = (criterio["escala_min"] + criterio["escala_max"]) / 2
            novas[criterio_id][candidato["id"]] = antigas.get(candidato["id"], valor_default)
    st.session_state.avaliacoes = novas
