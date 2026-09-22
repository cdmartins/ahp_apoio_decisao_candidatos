"""Definição das páginas do app e navegação sequencial (anterior/próxima) entre elas."""
import streamlit as st

DEFINICOES_PAGINAS = [
    {"path": "inicio.py", "title": "Início"},
    {"path": "pages/0_Resumo.py", "title": "Resumo do Processo"},
    {"path": "pages/1_Criterios.py", "title": "Critérios"},
    {"path": "pages/2_Comparacao_Criterios.py", "title": "Definir Importância"},
    {"path": "pages/3_Candidatos.py", "title": "Candidatos e Avaliações"},
    {"path": "pages/4_Resultado.py", "title": "Resultado"},
]


def renderizar_navegacao(caminho_atual: str) -> None:
    """Mostra botões "← anterior" / "próxima →" para navegar entre as páginas, seguindo o fluxo."""
    indice = next(i for i, p in enumerate(DEFINICOES_PAGINAS) if p["path"] == caminho_atual)
    anterior = DEFINICOES_PAGINAS[indice - 1] if indice > 0 else None
    proxima = DEFINICOES_PAGINAS[indice + 1] if indice < len(DEFINICOES_PAGINAS) - 1 else None

    st.divider()
    col_ant, col_prox = st.columns(2)
    with col_ant:
        if anterior and st.button(f"← {anterior['title']}", use_container_width=True):
            st.switch_page(anterior["path"])
    with col_prox:
        if proxima and st.button(f"{proxima['title']} →", type="primary", use_container_width=True):
            st.switch_page(proxima["path"])
