"""Motor de cálculo do método AHP (Analytic Hierarchy Process)."""
import numpy as np

# Índice aleatório (RI) de Saaty para matrizes de ordem 1 a 10
# Está tabelado para uma matriz de até 10 critérios. Para matrizes maiores, o valor de RI é aproximado.
_RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12,
       6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def normalizar_matriz(matriz: np.ndarray) -> np.ndarray:
    """Normaliza cada coluna da matriz pela soma da coluna."""
    soma_colunas = matriz.sum(axis=0)
    return matriz / soma_colunas


def calcular_pesos(matriz: np.ndarray) -> np.ndarray:
    """Calcula o vetor de pesos (prioridades) pela média das linhas da matriz normalizada."""
    normalizada = normalizar_matriz(matriz)
    return normalizada.mean(axis=1)


def calcular_razao_consistencia(matriz: np.ndarray, pesos: np.ndarray) -> tuple[float, float, float]:
    """Retorna (lambda_max, IC, CR) para avaliar a consistência da matriz de comparação."""
    n = matriz.shape[0]
    if n <= 2:
        return 1.0, 0.0, 0.0
    autovetor_ponderado = matriz @ pesos
    lambda_max = float(np.mean(autovetor_ponderado / pesos))
    ic = (lambda_max - n) / (n - 1)
    ri = _RI.get(n, 1.49)
    cr = ic / ri if ri > 0 else 0.0
    return lambda_max, ic, cr


def matriz_identidade(n: int) -> np.ndarray:
    """Matriz de comparação inicial neutra (todos os pares igualmente importantes)."""
    return np.ones((n, n))


def contar_pares_julgados(matriz: np.ndarray) -> int:
    """Conta quantos pares da matriz de comparação já foram julgados (diferentes de 'igual importância')."""
    n = matriz.shape[0]
    return sum(1 for i in range(n) for j in range(i + 1, n) if matriz[i][j] != 1)


def intensidade_saaty(nota_maior: float, nota_menor: float, escala_min: float, escala_max: float) -> int:
    """Converte a diferença entre duas notas (numa escala min-max) numa intensidade de 1 a 9.

    A diferença é tomada como proporção da amplitude total da escala e mapeada
    linearmente para o intervalo [1, 9] da escala fundamental de Saaty.
    """
    amplitude = escala_max - escala_min
    if amplitude <= 0:
        return 1
    proporcao = abs(nota_maior - nota_menor) / amplitude
    intensidade = 1 + proporcao * 8
    return int(round(min(9, max(1, intensidade))))


def matriz_comparacao_por_notas(notas: list[float], escala_min: float, escala_max: float) -> np.ndarray:
    """Deriva a matriz de comparação par a par entre alternativas a partir de suas notas.

    Quem tem a nota maior é considerado preferível, com intensidade calculada por
    intensidade_saaty; notas iguais resultam em comparação neutra (1).
    """
    n = len(notas)
    matriz = np.ones((n, n))
    for i in range(n):
        for j in range(n):
            if i == j or notas[i] == notas[j]:
                continue
            if notas[i] > notas[j]:
                matriz[i][j] = float(intensidade_saaty(notas[i], notas[j], escala_min, escala_max))
            else:
                matriz[i][j] = 1.0 / intensidade_saaty(notas[j], notas[i], escala_min, escala_max)
    return matriz


def calcular_prioridades_locais(criterios: list[dict], candidatos: list[dict], avaliacoes: dict) -> dict[str, np.ndarray]:
    """Para cada critério, deriva a prioridade local de cada candidato a partir das notas.

    Retorna {id_criterio: array de prioridades, na mesma ordem de `candidatos`}. Usa o id (não o
    nome) como chave para que renomear um critério não perca ou desalinhe as notas já lançadas.
    """
    ids_candidatos = [c["id"] for c in candidatos]
    prioridades = {}
    for criterio in criterios:
        notas = [avaliacoes[criterio["id"]][cid] for cid in ids_candidatos]
        matriz = matriz_comparacao_por_notas(notas, criterio["escala_min"], criterio["escala_max"])
        prioridades[criterio["id"]] = calcular_pesos(matriz)
    return prioridades


def calcular_ranking(
    criterios: list[dict], candidatos: list[dict], avaliacoes: dict, pesos_criterios: np.ndarray
) -> list[tuple[str, float]]:
    """Combina as prioridades locais de cada critério (derivadas das notas) com os pesos dos
    critérios, retornando [(nome_candidato, pontuação), ...] ordenado do maior para o menor."""
    prioridades_locais = calcular_prioridades_locais(criterios, candidatos, avaliacoes)
    pontuacao_final = np.zeros(len(candidatos))
    for peso, criterio in zip(pesos_criterios, criterios):
        pontuacao_final = pontuacao_final + peso * prioridades_locais[criterio["id"]]

    nomes_candidatos = [c["nome"] for c in candidatos]
    ranking = sorted(zip(nomes_candidatos, pontuacao_final), key=lambda item: item[1], reverse=True)
    return [(nome, float(pontuacao)) for nome, pontuacao in ranking]
