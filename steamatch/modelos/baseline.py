"""Recomendação por popularidade usada nas primeiras interações da sessão."""


def recomendar_mais_avaliados(df_jogos, n=10, excluir_nomes=None):
    """Retorna os N jogos com maior número total de reviews (positivas + negativas)."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_jogos[~df_jogos['Nome_Jogo'].isin(excluir_nomes)].copy()
    df_ordenado = df_filtrado.sort_values('total_reviews', ascending=False)

    return _montar_lista(df_ordenado, n, motivo='📈 Baseado em popularidade')


def recomendar_melhor_avaliados(df_jogos, n=10, excluir_nomes=None):
    """Retorna os N jogos com maior ratio de avaliações positivas (mínimo 100 reviews)."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_jogos[
        (~df_jogos['Nome_Jogo'].isin(excluir_nomes)) &
        (df_jogos['total_reviews'] >= 100)
    ].copy()
    df_ordenado = df_filtrado.sort_values('ratio_positivo', ascending=False)

    return _montar_lista(df_ordenado, n, motivo='📈 Baseado em popularidade')


def recomendar_pontuacao_ponderada(df_jogos, n=10, excluir_nomes=None):
    """Retorna os N jogos com maior pontuação ponderada estilo IMDb."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_jogos[~df_jogos['Nome_Jogo'].isin(excluir_nomes)].copy()
    df_ordenado = df_filtrado.sort_values('pontuacao_ponderada', ascending=False)

    return _montar_lista(df_ordenado, n, motivo='📈 Baseado em popularidade')


def obter_jogos_populares(df_jogos, n=50, excluir_nomes=None):
    """Retorna os N jogos mais populares por pontuacao_ponderada excluindo já vistos."""
    return recomendar_pontuacao_ponderada(df_jogos, n=n, excluir_nomes=excluir_nomes)


def obter_jogo_aleatorio(df_jogos, excluir_nomes=None):
    """Retorna um jogo aleatório do df_jogos para introduzir diversidade na fila."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_jogos[~df_jogos['Nome_Jogo'].isin(excluir_nomes)]

    if df_filtrado.empty:
        return None

    linha = df_filtrado.sample(n=1).iloc[0]
    return _linha_para_dict(linha, motivo='🎲 Exploração aleatória')


def _linha_para_dict(linha, motivo: str) -> dict:
    """Converte uma linha do DataFrame em dicionário para o sistema de swipe."""
    return {
        'nome':            linha['Nome_Jogo'],
        'generos':         linha['generos'],
        'tags':            linha['tags'],
        'descricao':       linha['descricao'],
        'positivas':       int(linha.get('positivas', 0)),
        'total_reviews':   int(linha.get('total_reviews', 0)),
        'pontuacao_ponderada': float(linha.get('pontuacao_ponderada', 0)),
        'motivo':          motivo,
    }


def _montar_lista(df_ordenado, n: int, motivo: str) -> list[dict]:
    """Converte as N primeiras linhas do DataFrame ordenado em lista de dicts."""
    jogos = []
    for _, linha in df_ordenado.head(n).iterrows():
        jogos.append(_linha_para_dict(linha, motivo))
    return jogos
