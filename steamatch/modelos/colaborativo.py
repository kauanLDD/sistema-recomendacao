"""Filtragem colaborativa item-based usando horas jogadas como sinal de preferência."""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def construir_modelo_colaborativo(df_horas):
    """Cria a matriz item-item a partir do comportamento de horas jogadas. Retorna (matriz_item_item, indice_itens)."""
    jogos_unicos   = df_horas['nome_jogo'].unique()
    usuarios_unicos = df_horas['usuario_id'].unique()

    indice_itens    = {jogo: idx for idx, jogo in enumerate(jogos_unicos)}
    indice_usuarios = {user: idx for idx, user in enumerate(usuarios_unicos)}

    n_jogos    = len(jogos_unicos)
    n_usuarios = len(usuarios_unicos)

    # Constrói matriz esparsa jogo x usuário
    linhas  = df_horas['nome_jogo'].map(indice_itens).values
    colunas = df_horas['usuario_id'].map(indice_usuarios).values
    valores = df_horas['horas'].values.astype(np.float32)

    matriz_esparsa = csr_matrix(
        (valores, (linhas, colunas)),
        shape=(n_jogos, n_usuarios)
    )

    matriz_item_item = cosine_similarity(matriz_esparsa, dense_output=True)

    return matriz_item_item, indice_itens


def recomendar_colaborativo(nomes_curtidos, matriz_item_item,
                             indice_itens, df_enriquecido,
                             excluir_nomes=None, n=10):
    """Agrega similaridades item-based dos jogos curtidos e retorna os N mais similares."""
    if excluir_nomes is None:
        excluir_nomes = []

    n_itens = matriz_item_item.shape[0]
    pontuacoes_agregadas = np.zeros(n_itens)

    curtidos_validos = 0
    for nome in nomes_curtidos:
        if nome in indice_itens:
            idx = indice_itens[nome]
            pontuacoes_agregadas += matriz_item_item[idx]
            curtidos_validos += 1

    if curtidos_validos == 0:
        return []

    pontuacoes_agregadas /= curtidos_validos

    indice_para_nome = {idx: nome for nome, idx in indice_itens.items()}
    indices_ordenados = np.argsort(pontuacoes_agregadas)[::-1]

    mapa_df = df_enriquecido.set_index('Nome_Jogo')

    jogos = []
    for idx in indices_ordenados:
        if len(jogos) >= n:
            break

        nome = indice_para_nome.get(idx)
        if nome is None:
            continue
        if nome in excluir_nomes:
            continue
        if nome in nomes_curtidos:
            continue

        if nome in mapa_df.index:
            linha = mapa_df.loc[nome]
            jogos.append({
                'nome':                    nome,
                'generos':                 linha['generos'],
                'tags':                    linha['tags'],
                'descricao':               linha['descricao'],
                'total_horas':             linha.get('total_horas', 0),
                'total_usuarios_jogaram':  linha.get('total_usuarios_jogaram', 0),
                'pontuacao_ponderada':     float(linha.get('pontuacao_ponderada', 0)),
                'pontuacao_colaborativa':  float(pontuacoes_agregadas[idx]),
                'motivo':                  '🤝 Usuários similares',
            })

    # Reordena combinando colaborativo (60%) + popularidade (40%)
    if len(jogos) > 1:
        colabs = np.array([j['pontuacao_colaborativa'] for j in jogos])
        pops   = np.array([j['pontuacao_ponderada']    for j in jogos])

        colab_min, colab_max = colabs.min(), colabs.max()
        pop_min,   pop_max   = pops.min(),   pops.max()

        colab_norm = (colabs - colab_min) / (colab_max - colab_min + 1e-9)
        pop_norm   = (pops   - pop_min)   / (pop_max   - pop_min   + 1e-9)

        for i, jogo in enumerate(jogos):
            jogo['pontuacao_colaborativa'] = float(0.6 * colab_norm[i] + 0.4 * pop_norm[i])

        jogos.sort(key=lambda x: x['pontuacao_colaborativa'], reverse=True)

    return jogos
