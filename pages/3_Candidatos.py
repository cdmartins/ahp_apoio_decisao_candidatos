import math
import textwrap

import pandas as pd
import streamlit as st

from ahp.estado import (
    inicializar_estado,
    sincronizar_avaliacoes,
    sincronizar_matriz_criterios,
    novo_candidato_id,
    novo_criterio_id,
    cabecalho_processo,
)
from ahp.navegacao import renderizar_navegacao

COLUNAS_FIXAS = ("Nome",)

inicializar_estado()

criterios = st.session_state.criterios

if "form_cand_versao" not in st.session_state:
    st.session_state.form_cand_versao = 0
if "mostrar_importar" not in st.session_state:
    st.session_state.mostrar_importar = False


def chave(campo: str) -> str:
    return f"{campo}_{st.session_state.form_cand_versao}"


def limpar_formulario() -> None:
    st.session_state.editando_candidato_id = None
    st.session_state.form_cand_versao += 1


def carregar_candidato_no_formulario(cand: dict) -> None:
    st.session_state.editando_candidato_id = cand["id"]
    st.session_state.form_cand_versao += 1
    st.session_state[chave("form_nome_cand")] = cand["nome"]
    for criterio in criterios:
        st.session_state[chave(f"form_nota_{criterio['id']}")] = st.session_state.avaliacoes[criterio["id"]].get(
            cand["id"], criterio["escala_min"]
        )


def excluir_candidato(cand_id: str) -> None:
    st.session_state.candidatos = [c for c in st.session_state.candidatos if c["id"] != cand_id]
    if st.session_state.editando_candidato_id == cand_id:
        limpar_formulario()
    sincronizar_avaliacoes()


def colunas_de_criterio(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in COLUNAS_FIXAS]


def sugestao_escala(valores: pd.Series, escala_atual: tuple[float, float] | None = None) -> tuple[float, float]:
    """Sugere uma escala mín-máx a partir dos valores observados numa coluna.

    Se o critério já existir (escala_atual informado), a sugestão nunca fica mais estreita
    que a escala já cadastrada — só amplia o suficiente para cobrir as notas da planilha.
    """
    numeros = pd.to_numeric(valores, errors="coerce").dropna()

    candidatos_min = [0.0]
    candidatos_max = []
    if escala_atual is not None:
        candidatos_min.append(escala_atual[0])
        candidatos_max.append(escala_atual[1])
    if not numeros.empty:
        candidatos_min.append(math.floor(numeros.min()))
        candidatos_max.append(math.ceil(numeros.max()))

    if not candidatos_max:
        return 0, 10

    minimo = min(candidatos_min)
    maximo = max(candidatos_max)
    if maximo <= minimo:
        maximo = minimo + 1
    return minimo, maximo


def validar_importacao(df: pd.DataFrame, criterios_atuais: list[dict]):
    """Retorna (regras, colunas_existentes, colunas_novas, colunas_fora_da_escala). Colunas que não
    batem com nenhum critério cadastrado não reprovam a validação — elas viram critérios novos.
    Colunas de um critério já cadastrado cuja escala não cobre as notas da planilha também não
    reprovam mais: entram em colunas_fora_da_escala para o usuário ampliar a escala antes de importar."""
    regras = []
    if "Nome" not in df.columns:
        regras.append((False, "Coluna 'Nome' não encontrada no arquivo"))
        return regras, [], [], []
    regras.append((len(df) > 0, f"{len(df)} candidatos encontrados"))

    por_nome = {c["nome"]: c for c in criterios_atuais}
    colunas_criterio = colunas_de_criterio(df)
    existentes = [c for c in colunas_criterio if c in por_nome]
    novos = [c for c in colunas_criterio if c not in por_nome]

    if novos:
        regras.append(
            (True, f"{len(colunas_criterio)} critérios na planilha ({len(existentes)} já cadastrados, {len(novos)} serão criados)")
        )
    else:
        regras.append((len(colunas_criterio) > 0, f"{len(colunas_criterio)} critérios encontrados"))

    fora_da_escala = []
    if colunas_criterio:
        preenchidas = not df[colunas_criterio].isna().any().any()
        regras.append((preenchidas, "Todas as notas preenchidas"))

        for nome_coluna in existentes:
            criterio = por_nome[nome_coluna]
            coluna = pd.to_numeric(df[nome_coluna], errors="coerce")
            if (coluna < criterio["escala_min"]).any() or (coluna > criterio["escala_max"]).any():
                fora_da_escala.append(nome_coluna)

    sem_duplicados = not df["Nome"].astype(str).str.strip().duplicated().any()
    regras.append((sem_duplicados, "Nenhum candidato duplicado"))

    return regras, existentes, novos, fora_da_escala


titulo_col, botoes_col = st.columns([3, 2])
with titulo_col:
    st.title("Candidatos e Avaliações")
    st.caption(cabecalho_processo())
    st.caption("Importe uma planilha ou cadastre manualmente as notas de cada candidato em cada critério")
with botoes_col:
    st.write("")
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Importar Planilha", use_container_width=True):
        st.session_state.mostrar_importar = True
    if col_btn2.button("Cadastrar Manualmente", type="primary", use_container_width=True):
        limpar_formulario()

with st.expander("Formato aceito pela aplicação", expanded=st.session_state.mostrar_importar):
    st.caption("Arquivo .csv com cabeçalho — uma linha por candidato: Nome e uma coluna por critério.")
    st.caption("Processo seletivo e cargo são definidos uma vez para todos, na página inicial (Nova Decisão).")

    modelo_df = pd.DataFrame([{"Nome": "Exemplo Candidato", **{c["nome"]: c["escala_min"] for c in criterios}}])
    st.download_button(
        "Baixar modelo",
        data=modelo_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="modelo_candidatos.csv",
        mime="text/csv",
    )

    arquivo = st.file_uploader("Selecione o arquivo CSV", type=["csv"], label_visibility="collapsed")

    if arquivo is not None:
        try:
            df_importado = pd.read_csv(arquivo)
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo: {e}")
            df_importado = None

        if df_importado is not None:
            # Aceita tanto "3.5" (ponto) quanto "3,5" (vírgula, comum em planilhas em pt-BR)
            for coluna in colunas_de_criterio(df_importado):
                df_importado[coluna] = pd.to_numeric(
                    df_importado[coluna].astype(str).str.strip().str.replace(",", ".", regex=False),
                    errors="coerce",
                )
            st.markdown("**Validação da importação**")
            regras, colunas_existentes, colunas_novas, colunas_fora_da_escala = validar_importacao(df_importado, criterios)
            for ok, mensagem in regras:
                st.markdown(f"{':green[✓]' if ok else ':red[✗]'} {mensagem}")

            criterios_por_nome = {c["nome"]: c for c in criterios}
            colunas_para_ajustar = colunas_novas + colunas_fora_da_escala

            escalas_ok = True
            if colunas_para_ajustar:
                st.markdown("**Escala dos critérios**")
                st.caption(
                    "Critérios novos ou com notas fora do intervalo já cadastrado aparecem aqui. "
                    "A sugestão é calculada a partir das notas desta planilha (e, para critérios já "
                    "existentes, da escala atual) — ajuste se necessário, lembrando que nota 0 é um "
                    "valor válido."
                )
                col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
                col_h1.caption("Critério")
                col_h2.caption("Mín.")
                col_h3.caption("Máx.")
                for nome_coluna in colunas_para_ajustar:
                    chave_min = f"import_escala_min_{nome_coluna}"
                    chave_max = f"import_escala_max_{nome_coluna}"
                    if chave_min not in st.session_state or chave_max not in st.session_state:
                        escala_atual = None
                        if nome_coluna in criterios_por_nome:
                            criterio_existente = criterios_por_nome[nome_coluna]
                            escala_atual = (criterio_existente["escala_min"], criterio_existente["escala_max"])
                        sugestao_min, sugestao_max = sugestao_escala(df_importado[nome_coluna], escala_atual)
                        st.session_state.setdefault(chave_min, sugestao_min)
                        st.session_state.setdefault(chave_max, sugestao_max)

                    col_nome_esc, col_min_esc, col_max_esc = st.columns([3, 1, 1])
                    rotulo = nome_coluna if nome_coluna in colunas_novas else f"{nome_coluna} (já cadastrado)"
                    col_nome_esc.write(rotulo)
                    col_min_esc.number_input("Mín.", step=1.0, key=chave_min, label_visibility="collapsed")
                    col_max_esc.number_input("Máx.", step=1.0, key=chave_max, label_visibility="collapsed")

                    minimo_atual = st.session_state[chave_min]
                    maximo_atual = st.session_state[chave_max]
                    coluna_valores = pd.to_numeric(df_importado[nome_coluna], errors="coerce")
                    if maximo_atual <= minimo_atual:
                        col_nome_esc.caption("O máximo deve ser maior que o mínimo.")
                        escalas_ok = False
                    elif ((coluna_valores < minimo_atual) | (coluna_valores > maximo_atual)).any():
                        col_nome_esc.caption(f"Há notas fora do intervalo {minimo_atual:g}–{maximo_atual:g} nesta coluna.")
                        escalas_ok = False

            valido = all(ok for ok, _ in regras) and escalas_ok
            if st.button("Processar avaliações", type="primary", disabled=not valido):
                id_por_nome_coluna = {nome_coluna: criterios_por_nome[nome_coluna]["id"] for nome_coluna in colunas_existentes}
                for nome_coluna in colunas_novas:
                    escala_min = st.session_state[f"import_escala_min_{nome_coluna}"]
                    escala_max = st.session_state[f"import_escala_max_{nome_coluna}"]
                    novo_id = novo_criterio_id()
                    st.session_state.criterios.append(
                        {
                            "id": novo_id,
                            "nome": nome_coluna,
                            "tipo": "Técnico",
                            "escala_min": escala_min,
                            "escala_max": escala_max,
                        }
                    )
                    id_por_nome_coluna[nome_coluna] = novo_id
                for nome_coluna in colunas_fora_da_escala:
                    criterio_existente = criterios_por_nome[nome_coluna]
                    criterio_existente["escala_min"] = st.session_state[f"import_escala_min_{nome_coluna}"]
                    criterio_existente["escala_max"] = st.session_state[f"import_escala_max_{nome_coluna}"]
                if colunas_novas:
                    sincronizar_matriz_criterios()

                for _, linha in df_importado.iterrows():
                    nome = str(linha["Nome"]).strip()

                    existente = next(
                        (c for c in st.session_state.candidatos if c["nome"].strip().lower() == nome.lower()), None
                    )
                    if existente:
                        existente.update({"origem": "Planilha"})
                        candidato_id = existente["id"]
                    else:
                        candidato_id = novo_candidato_id()
                        st.session_state.candidatos.append({"id": candidato_id, "nome": nome, "origem": "Planilha"})

                    for nome_coluna in colunas_existentes + colunas_novas:
                        criterio_id = id_por_nome_coluna[nome_coluna]
                        st.session_state.avaliacoes.setdefault(criterio_id, {})[candidato_id] = float(linha[nome_coluna])

                for nome_coluna in colunas_para_ajustar:
                    st.session_state.pop(f"import_escala_min_{nome_coluna}", None)
                    st.session_state.pop(f"import_escala_max_{nome_coluna}", None)

                sincronizar_avaliacoes()
                st.session_state.mostrar_importar = False
                partes_mensagem = []
                if colunas_novas:
                    partes_mensagem.append(f"{len(colunas_novas)} critério(s) criado(s)")
                if colunas_fora_da_escala:
                    partes_mensagem.append(f"{len(colunas_fora_da_escala)} critério(s) com escala ampliada")
                mensagem_criterios = " e " + " e ".join(partes_mensagem) if partes_mensagem else ""
                st.toast(f"{len(df_importado)} candidato(s) importado(s){mensagem_criterios}!")
                st.rerun()

if len(criterios) < 2:
    st.info(
        "Cadastre pelo menos 2 critérios (na página **Critérios** ou importando uma planilha acima) "
        "para cadastrar candidatos manualmente."
    )
    renderizar_navegacao("pages/3_Candidatos.py")
    st.stop()

col_form, col_lista = st.columns([1, 2], gap="large")

with col_form:
    with st.container(border=True):
        editando = st.session_state.editando_candidato_id is not None
        st.subheader("Editar candidato" if editando else "Cadastro manual")
        st.caption("Nome e notas por critério")

        st.text_input("Nome do candidato", placeholder="Ex.: Marina Alves", key=chave("form_nome_cand"))

        st.write("Notas nos critérios")
        for criterio in criterios:
            col_nome, col_faixa, col_valor = st.columns([3, 2, 2])
            col_nome.write(criterio["nome"])
            col_faixa.markdown(
                f"<div style='text-align:right; color:gray; padding-top:8px;'>{criterio['escala_min']}–{criterio['escala_max']}</div>",
                unsafe_allow_html=True,
            )
            col_valor.number_input(
                criterio["nome"],
                min_value=float(criterio["escala_min"]),
                max_value=float(criterio["escala_max"]),
                step=0.5,
                key=chave(f"form_nota_{criterio['id']}"),
                label_visibility="collapsed",
            )

        col_salvar, col_limpar = st.columns(2)
        salvar = col_salvar.button("Salvar", type="primary", use_container_width=True)
        limpar = col_limpar.button("Limpar", use_container_width=True)

        if limpar:
            limpar_formulario()
            st.rerun()

        if salvar:
            nome = (st.session_state.get(chave("form_nome_cand")) or "").strip()
            if not nome:
                st.error("Informe o nome do candidato.")
            else:
                editando_id = st.session_state.editando_candidato_id

                if editando_id:
                    candidato = next(c for c in st.session_state.candidatos if c["id"] == editando_id)
                    candidato.update({"nome": nome})
                    candidato_id = editando_id
                else:
                    candidato_id = novo_candidato_id()
                    st.session_state.candidatos.append({"id": candidato_id, "nome": nome, "origem": "Manual"})

                for criterio in criterios:
                    nota = st.session_state.get(chave(f"form_nota_{criterio['id']}"), criterio["escala_min"])
                    st.session_state.avaliacoes.setdefault(criterio["id"], {})[candidato_id] = float(nota)

                sincronizar_avaliacoes()
                limpar_formulario()
                st.rerun()

CORES_ORIGEM = {
    "Manual": ("#dcfce7", "#15803d"),
    "Planilha": ("#dbeafe", "#1d4ed8"),
}


def renderizar_card_candidato(candidato: dict) -> None:
    bg_badge, cor_badge = CORES_ORIGEM.get(candidato["origem"], ("#f3f4f6", "#6b7280"))

    linhas_criterio = []
    for criterio in criterios:
        nota = st.session_state.avaliacoes[criterio["id"]].get(candidato["id"], criterio["escala_min"])
        amplitude = criterio["escala_max"] - criterio["escala_min"]
        pct = min(1.0, max(0.0, (nota - criterio["escala_min"]) / amplitude if amplitude > 0 else 0)) * 100
        linhas_criterio.append(
            textwrap.dedent(f"""\
                <div style="margin-bottom:5px;">
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#374151;">
                <span>{criterio['nome']}</span><span>{nota:g}/{criterio['escala_max']:g}</span>
                </div>
                <div style="background:#f3f4f6; border-radius:4px; height:5px; margin-top:2px;">
                <div style="background:#16a34a; width:{pct:.1f}%; height:5px; border-radius:4px;"></div>
                </div>
                </div>
                """)
        )

    st.markdown(
        textwrap.dedent(f"""\
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:600; font-size:13px;">{candidato['nome']}</span>
            <span style="background:{bg_badge}; color:{cor_badge}; font-size:10px; font-weight:600; padding:2px 8px; border-radius:10px;">{candidato['origem']}</span>
            </div>
            """)
        + "".join(linhas_criterio),
        unsafe_allow_html=True,
    )


with col_lista:
    st.subheader("Candidatos cadastrados")
    st.caption(f"{len(st.session_state.candidatos)} candidato(s)")

    if not st.session_state.candidatos:
        st.info("Nenhum candidato cadastrado ainda. Use o formulário ao lado ou importe uma planilha.")
    else:
        colunas = st.columns(3)
        for i, candidato in enumerate(st.session_state.candidatos):
            with colunas[i % 3]:
                with st.container(border=True):
                    renderizar_card_candidato(candidato)

                    col_alt, col_exc = st.columns(2)
                    if col_alt.button("Alterar", key=f"alterar_cand_{candidato['id']}", use_container_width=True):
                        carregar_candidato_no_formulario(candidato)
                        st.rerun()
                    if col_exc.button("Excluir", key=f"excluir_cand_{candidato['id']}", use_container_width=True):
                        excluir_candidato(candidato["id"])
                        st.rerun()

renderizar_navegacao("pages/3_Candidatos.py")
