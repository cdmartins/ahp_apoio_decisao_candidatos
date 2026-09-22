import streamlit as st

from ahp.navegacao import DEFINICOES_PAGINAS

st.set_page_config(page_title="AHP-Qualifica", layout="wide")

paginas = [
    st.Page(p["path"], title=p["title"], default=(p["path"] == "inicio.py"))
    for p in DEFINICOES_PAGINAS
]

pg = st.navigation(paginas)
pg.run()
