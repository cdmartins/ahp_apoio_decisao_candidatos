"""Cálculos AHP com AHPy; """
import ahpy
import numpy as np

PRECISAO = 10 


def _comparar(matriz: np.ndarray, nome: str, cr: bool = False) -> ahpy.Compare:    
    n = len(matriz)
    if not n:
        raise ValueError("A matriz de comparação não pode ser vazia.")
    if cr and n > 15:
        raise ValueError("O RI de Saaty no AHPy suporta CR para até 15 critérios.")
    comparacoes = {
        (str(i), str(j)): float(matriz[i][j])
        for i in range(n) for j in range(i + 1, n)
    } if n > 1 else {"0": 1.0}
    # Saaty (2005), tabela interna do AHPy
    return ahpy.Compare(nome, comparacoes, precision=PRECISAO, random_index="saaty", cr=cr)


def _pesos(resultado: ahpy.Compare, n: int) -> np.ndarray:    
    return np.array([resultado.local_weights[str(i)] for i in range(n)], dtype=float)


def calcular_pesos_e_consistencia(matriz: np.ndarray) -> tuple[np.ndarray, float]:
    resultado = _comparar(matriz, "Critérios", cr=True)
    return _pesos(resultado, len(matriz)), float(resultado.consistency_ratio)


def matriz_identidade(n: int) -> np.ndarray:
    return np.ones((n, n))


def contar_pares_julgados(matriz: np.ndarray) -> int:
    return sum(matriz[i][j] != 1 for i in range(len(matriz)) for j in range(i + 1, len(matriz)))


def intensidade_saaty(nota_maior: float, nota_menor: float, escala_min: float, escala_max: float) -> int:
    amplitude = escala_max - escala_min
    if amplitude <= 0:
        return 1
    intensidade = 1 + 8 * abs(nota_maior - nota_menor) / amplitude
    return int(round(min(9, max(1, intensidade))))


def matriz_comparacao_por_notas(notas: list[float], escala_min: float, escala_max: float) -> np.ndarray:
    """Compara as notas em pares e preenche o par inverso por reciprocidade."""
    matriz = np.ones((len(notas), len(notas)))
    for i in range(len(notas)):
        for j in range(i + 1, len(notas)):
            valor = intensidade_saaty(notas[i], notas[j], escala_min, escala_max)
            matriz[i, j] = valor if notas[i] >= notas[j] else 1 / valor
            matriz[j, i] = 1 / matriz[i, j]
    return matriz


def calcular_resultados(
    criterios: list[dict], candidatos: list[dict], avaliacoes: dict, matriz_criterios: np.ndarray
) -> tuple[np.ndarray, float, dict[str, np.ndarray], list[tuple[str, float]]]:
    if len(matriz_criterios) != len(criterios):
        raise ValueError("A matriz deve corresponder aos critérios cadastrados.")
    objetivo = _comparar(matriz_criterios, "Objetivo", cr=True)
    pesos = _pesos(objetivo, len(criterios))
    cr = float(objetivo.consistency_ratio)
    if not candidatos:
        return pesos, cr, {}, []
    filhos, prioridades = [], {}
    for i, criterio in enumerate(criterios):
        notas = [avaliacoes[criterio["id"]][c["id"]] for c in candidatos]
        matriz = matriz_comparacao_por_notas(notas, criterio["escala_min"], criterio["escala_max"])
        filho = _comparar(matriz, str(i))
        filhos.append(filho)
        prioridades[criterio["id"]] = _pesos(filho, len(candidatos))
    objetivo.add_children(filhos)
    ranking = [(c["nome"], float(objetivo.target_weights[str(i)])) for i, c in enumerate(candidatos)]
    return pesos, cr, prioridades, sorted(ranking, key=lambda item: item[1], reverse=True)
