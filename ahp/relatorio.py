"""Geração do relatório em PDF da página Resultado, com todas as informações exibidas na tela."""

import io
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

COR_TITULO = (17, 24, 39)
COR_TEXTO_CLARO = (107, 114, 128)
COR_VERDE = (22, 163, 74)
COR_VERMELHO = (220, 38, 38)

PALETA_CRITERIOS = ["#16a34a", "#2563eb", "#7c3aed", "#f59e0b", "#dc2626", "#0891b2", "#db2777"]
CORES_PODIO = ["#f59e0b", "#9ca3af", "#b45309"]
COR_BARRA_PADRAO = "#93c5fd"

plt.rcParams["font.family"] = "DejaVu Sans"


def _grafico_ranking_segmentado(ranking, criterios, pesos_criterios, prioridades_locais, nomes_candidatos) -> io.BytesIO:
    """Barras horizontais empilhadas: a contribuição de cada critério na pontuação final de cada
    candidato (mesma composição visual do card "Ranking final" da tela)."""
    indices = [nomes_candidatos.index(nome) for nome, _ in ranking]
    nomes_ordenados = [nome for nome, _ in ranking]
    y_pos = list(range(len(nomes_ordenados)))
    esquerda = [0.0] * len(nomes_ordenados)

    fig, ax = plt.subplots(figsize=(6.5, 0.55 * len(nomes_ordenados) + 1.1))
    for i, criterio in enumerate(criterios):
        peso = pesos_criterios[i]
        cor = PALETA_CRITERIOS[i % len(PALETA_CRITERIOS)]
        valores = [peso * prioridades_locais[criterio["id"]][idx] * 100 for idx in indices]
        ax.barh(y_pos, valores, left=esquerda, color=cor, height=0.6, label=criterio["nome"], zorder=3)
        esquerda = [e + v for e, v in zip(esquerda, valores)]

    ax.set_yticks(y_pos)
    ax.set_yticklabels(nomes_ordenados, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, max(esquerda) * 1.18 if esquerda else 1)
    ax.set_xlabel("Pontuação final (%)", fontsize=9)
    for i, total in enumerate(esquerda):
        ax.text(total + max(esquerda) * 0.015, i, f"{total:.1f}%", va="center", fontsize=9, fontweight="bold", color="#111827")
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(left=False)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.6, zorder=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=min(len(criterios), 3), fontsize=8, frameon=False)
    fig.tight_layout()
    return _figura_para_bytes(fig)


def _grafico_pesos(criterios, pesos_criterios) -> io.BytesIO:
    """Barras horizontais com o peso AHP de cada critério."""
    nomes = [c["nome"] for c in criterios]
    cores = [PALETA_CRITERIOS[i % len(PALETA_CRITERIOS)] for i in range(len(nomes))]
    maximo = max(pesos_criterios) if len(pesos_criterios) else 1.0

    fig, ax = plt.subplots(figsize=(6.5, 0.55 * len(nomes) + 0.6))
    y_pos = range(len(nomes))
    ax.barh(y_pos, [p * 100 for p in pesos_criterios], color=cores, height=0.6, zorder=3)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(nomes, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, maximo * 100 * 1.2)
    ax.set_xlabel("Peso do critério (%)", fontsize=9)
    for i, p in enumerate(pesos_criterios):
        ax.text(p * 100 + maximo * 2, i, f"{p:.1%}", va="center", fontsize=9, fontweight="bold", color="#111827")
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(left=False)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.6, zorder=0)
    fig.tight_layout()
    return _figura_para_bytes(fig)


def _grafico_prioridades(criterios, pesos_criterios, prioridades_locais, nomes_candidatos) -> io.BytesIO:
    """Grade com um gráfico de barras por critério, mostrando a prioridade de cada candidato nele."""
    n = len(criterios)
    ncols = 2 if n > 1 else 1
    nrows = -(-n // ncols)

    fig, eixos = plt.subplots(nrows, ncols, figsize=(6.5, 2.5 * nrows))
    eixos = eixos.flatten() if hasattr(eixos, "flatten") else [eixos]

    for i, criterio in enumerate(criterios):
        ax = eixos[i]
        cor = PALETA_CRITERIOS[i % len(PALETA_CRITERIOS)]
        valores = prioridades_locais[criterio["id"]]
        x_pos = range(len(nomes_candidatos))
        ax.bar(x_pos, [v * 100 for v in valores], color=cor, width=0.5, zorder=3)
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(nomes_candidatos, fontsize=8, rotation=20, ha="right")
        ax.set_title(f"{criterio['nome']}  (peso {pesos_criterios[i]:.1%})", fontsize=9, fontweight="bold", color="#111827")
        ax.set_ylim(0, 100)
        for j, v in enumerate(valores):
            ax.text(j, v * 100 + 3, f"{v:.0%}", ha="center", fontsize=8, color="#111827")
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.grid(axis="y", color="#e5e7eb", linewidth=0.6, zorder=0)

    for k in range(n, len(eixos)):
        eixos[k].axis("off")

    fig.tight_layout()
    return _figura_para_bytes(fig)


def _figura_para_bytes(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _inserir_imagem(pdf: FPDF, buf: io.BytesIO) -> None:
    from PIL import Image

    largura = pdf.epw
    largura_px, altura_px = Image.open(buf).size
    altura = largura * altura_px / largura_px
    buf.seek(0)

    # fpdf2 não quebra a página sozinho ao inserir uma imagem (diferente de cell/multi_cell);
    # sem essa checagem, uma imagem alta perto do rodapé fica cortada silenciosamente.
    espaco_disponivel = pdf.h - pdf.b_margin - pdf.get_y()
    if altura > espaco_disponivel:
        pdf.add_page()

    y_antes = pdf.get_y()
    pdf.image(buf, x=pdf.l_margin, y=y_antes, w=largura)
    pdf.set_y(y_antes + altura + 4)


def _titulo_secao(pdf: FPDF, texto: str) -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*COR_TITULO)
    pdf.cell(0, 9, texto, new_x="LMARGIN", new_y="NEXT")


def _tabela_prioridades(pdf: FPDF, criterios, prioridades_locais, nomes_candidatos) -> None:
    """Tabela candidato x critério com a prioridade local de cada um (a mesma do expander
    "Ver tabela completa" na tela)."""
    largura_nome = 48
    largura_col = (pdf.epw - largura_nome) / len(criterios)

    def cabecalho():
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*COR_TITULO)
        pdf.set_fill_color(243, 244, 246)
        pdf.cell(largura_nome, 8, "Candidato", new_x="RIGHT", new_y="TOP", fill=True)
        for criterio in criterios:
            pdf.cell(largura_col, 8, criterio["nome"], border=0, align="C", new_x="RIGHT", new_y="TOP", fill=True)
        pdf.ln(8)

    espaco_disponivel = pdf.h - pdf.b_margin - pdf.get_y()
    if espaco_disponivel < 8 * (len(nomes_candidatos) + 2):
        pdf.add_page()
    cabecalho()

    pdf.set_font("Helvetica", "", 9)
    for i, nome in enumerate(nomes_candidatos):
        if pdf.get_y() + 7 > pdf.h - pdf.b_margin:
            pdf.add_page()
            cabecalho()
            pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COR_TITULO)
        pdf.cell(largura_nome, 7, nome, new_x="RIGHT", new_y="TOP")
        for criterio in criterios:
            valor = prioridades_locais[criterio["id"]][i]
            pdf.cell(largura_col, 7, f"{valor:.1%}", align="C", new_x="RIGHT", new_y="TOP")
        pdf.ln(7)


def gerar_relatorio_pdf(
    processo,
    criterios,
    pesos_criterios,
    cr_criterios,
    ranking,
    pares_julgados,
    prioridades_locais,
    nomes_candidatos,
    candidatos,
    calculado_em=None,
) -> bytes:
    """Gera o relatório em PDF da página Resultado, com todas as informações exibidas na tela:
    gráficos de ranking, pesos, prioridades por critério, e as tabelas completas."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COR_TITULO)
    pdf.cell(0, 12, "Relatório do Processo Seletivo", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*COR_TEXTO_CLARO)
    pdf.cell(0, 7, f"Processo: {processo['nome']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Cargo: {processo['cargo']}", new_x="LMARGIN", new_y="NEXT")
    if calculado_em is not None:
        pdf.cell(0, 7, f"Resultado calculado em: {calculado_em.strftime('%d/%m/%Y às %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if pares_julgados == 0:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*COR_TEXTO_CLARO)
        pdf.multi_cell(
            0,
            6,
            "Nenhuma comparação de importância foi feita entre os critérios - todos têm peso igual. "
            "O resultado abaixo equivale a somar as notas de cada critério com o mesmo peso, sem uso "
            "efetivo do método AHP.",
        )
        pdf.ln(2)

    _titulo_secao(pdf, "Ranking final")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COR_TEXTO_CLARO)
    pdf.cell(0, 6, "Soma das prioridades ponderadas pelos pesos dos critérios, por candidato", new_x="LMARGIN", new_y="NEXT")
    _inserir_imagem(pdf, _grafico_ranking_segmentado(ranking, criterios, pesos_criterios, prioridades_locais, nomes_candidatos))

    pdf.set_font("Helvetica", "", 10)
    for posicao, (nome, pontuacao) in enumerate(ranking, start=1):
        pdf.set_text_color(*COR_TITULO)
        pdf.cell(130, 7, f"{posicao}º  {nome}", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "B", 10)
        cor = COR_VERDE if posicao == 1 else COR_TITULO
        pdf.set_text_color(*cor)
        pdf.cell(0, 7, f"{pontuacao:.1%}", new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.set_font("Helvetica", "", 10)
    pdf.ln(4)

    _titulo_secao(pdf, "Aplicação dos pesos AHP")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COR_TEXTO_CLARO)
    pdf.cell(0, 6, "Peso de cada critério vindo da matriz de comparação", new_x="LMARGIN", new_y="NEXT")
    _inserir_imagem(pdf, _grafico_pesos(criterios, pesos_criterios))

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*COR_TITULO)
    pdf.cell(70, 7, "Candidatos comparados:", new_x="RIGHT", new_y="TOP")
    pdf.cell(0, 7, str(len(candidatos)), new_x="LMARGIN", new_y="NEXT")
    cor_cr = COR_VERDE if cr_criterios <= 0.1 else COR_VERMELHO
    pdf.cell(70, 7, "CR da matriz:", new_x="RIGHT", new_y="TOP")
    pdf.set_text_color(*cor_cr)
    pdf.cell(0, 7, f"{cr_criterios:.3f}", new_x="LMARGIN", new_y="NEXT")
    if cr_criterios > 0.1:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*COR_TEXTO_CLARO)
        pdf.cell(0, 6, "Acima de 0,10 - revise as comparações em Definir Importância.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    _titulo_secao(pdf, "Prioridades por critério")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COR_TEXTO_CLARO)
    pdf.cell(0, 6, "Notas normalizadas dentro de cada critério - soma 100% por critério", new_x="LMARGIN", new_y="NEXT")
    _inserir_imagem(pdf, _grafico_prioridades(criterios, pesos_criterios, prioridades_locais, nomes_candidatos))

    _titulo_secao(pdf, "Critérios e pesos")
    pdf.set_font("Helvetica", "", 10)
    for criterio, peso in zip(criterios, pesos_criterios):
        pdf.set_text_color(*COR_TITULO)
        texto = f"{criterio['nome']} ({criterio['tipo']}, escala {criterio['escala_min']}-{criterio['escala_max']})"
        pdf.cell(130, 6, texto, new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"{peso:.1%}", new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.set_font("Helvetica", "", 10)
    pdf.ln(4)

    _titulo_secao(pdf, "Prioridade de cada candidato por critério")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COR_TEXTO_CLARO)
    pdf.cell(0, 6, "Soma de cada coluna (critério) = 100%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    _tabela_prioridades(pdf, criterios, prioridades_locais, nomes_candidatos)

    return bytes(pdf.output())
