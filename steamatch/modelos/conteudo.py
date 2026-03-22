"""Recomendação baseada em conteúdo via TF-IDF e similaridade cosseno entre jogos."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def construir_modelo_conteudo(df_enriquecido):
    """Constrói a matriz TF-IDF e retorna (matriz_similaridade, indice_jogos)."""
    df = df_enriquecido.reset_index(drop=True)

    def montar_texto(linha):
        partes = []
        if linha['generos'] != 'desconhecido':
            # Gêneros com peso 2x
            partes.append(linha['generos'])
            partes.append(linha['generos'])
        if linha['tags'] != 'desconhecido':
            partes.append(linha['tags'])
        if linha['descricao']:
            partes.append(linha['descricao'])
        return ' '.join(partes)

    df['texto_completo'] = df.apply(montar_texto, axis=1)

    vetorizador = TfidfVectorizer(
        max_features=5000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
    )
    matriz_tfidf = vetorizador.fit_transform(df['texto_completo'])

    matriz_similaridade = cosine_similarity(matriz_tfidf, dense_output=True)

    indice_jogos = {nome: idx for idx, nome in enumerate(df['Nome_Jogo'])}

    return matriz_similaridade, indice_jogos


def recomendar_por_conteudo(nomes_curtidos, df_enriquecido,
                             matriz_similaridade, indice_jogos,
                             excluir_nomes=None, n=10):
    """Agrega similaridades dos jogos curtidos e retorna os N mais próximos por conteúdo."""
    if excluir_nomes is None:
        excluir_nomes = []

    n_jogos = matriz_similaridade.shape[0]
    pontuacoes_agregadas = np.zeros(n_jogos)

    curtidos_validos = 0
    for nome in nomes_curtidos:
        if nome in indice_jogos:
            idx = indice_jogos[nome]
            pontuacoes_agregadas += matriz_similaridade[idx]
            curtidos_validos += 1

    if curtidos_validos == 0:
        return []

    pontuacoes_agregadas /= curtidos_validos

    indice_para_nome = {idx: nome for nome, idx in indice_jogos.items()}
    indices_ordenados = np.argsort(pontuacoes_agregadas)[::-1]

    jogos = []
    df_idx = df_enriquecido.reset_index(drop=True)
    mapa_df = df_idx.set_index('Nome_Jogo')

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
                'nome':                   nome,
                'generos':                linha['generos'],
                'tags':                   linha['tags'],
                'descricao':              linha['descricao'],
                'total_horas':            linha.get('total_horas', 0),
                'total_usuarios_jogaram': linha.get('total_usuarios_jogaram', 0),
                'pontuacao_ponderada':    float(linha.get('pontuacao_ponderada', 0)),
                'pontuacao_conteudo':     float(pontuacoes_agregadas[idx]),
                'motivo':                 'Baseado no seu gosto (conteúdo)',
            })

    # Reordena combinando similaridade (60%) + popularidade (40%)
    if len(jogos) > 1:
        sims = np.array([j['pontuacao_conteudo']  for j in jogos])
        pops = np.array([j['pontuacao_ponderada'] for j in jogos])

        sim_min, sim_max = sims.min(), sims.max()
        pop_min, pop_max = pops.min(), pops.max()

        sim_norm = (sims - sim_min) / (sim_max - sim_min + 1e-9)
        pop_norm = (pops - pop_min) / (pop_max - pop_min + 1e-9)

        for i, jogo in enumerate(jogos):
            jogo['pontuacao_conteudo'] = float(0.6 * sim_norm[i] + 0.4 * pop_norm[i])

        jogos.sort(key=lambda x: x['pontuacao_conteudo'], reverse=True)

    return jogos
