"""Recomendação por popularidade usada nas primeiras interações da sessão."""


def obter_jogos_populares(df_enriquecido, n=50, excluir_nomes=None):
    """Retorna os N jogos mais populares por pontuacao_ponderada excluindo já vistos."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_enriquecido[
        ~df_enriquecido['Nome_Jogo'].isin(excluir_nomes)
    ].copy()

    df_ordenado = df_filtrado.sort_values('pontuacao_ponderada', ascending=False)

    jogos = []
    for _, linha in df_ordenado.head(n).iterrows():
        jogos.append({
            'nome':                   linha['Nome_Jogo'],
            'generos':                linha['generos'],
            'tags':                   linha['tags'],
            'descricao':              linha['descricao'],
            'total_horas':            linha.get('total_horas', 0),
            'total_usuarios_jogaram': linha.get('total_usuarios_jogaram', 0),
            'pontuacao_ponderada':    linha.get('pontuacao_ponderada', 0),
            'motivo':                 'Baseado em popularidade',
        })

    return jogos


def obter_jogo_aleatorio(df_enriquecido, excluir_nomes=None):
    """Retorna um jogo aleatório do df_enriquecido para introduzir diversidade na fila."""
    if excluir_nomes is None:
        excluir_nomes = []

    df_filtrado = df_enriquecido[
        ~df_enriquecido['Nome_Jogo'].isin(excluir_nomes)
    ]

    if df_filtrado.empty:
        return None

    linha = df_filtrado.sample(n=1).iloc[0]
    return {
        'nome':                   linha['Nome_Jogo'],
        'generos':                linha['generos'],
        'tags':                   linha['tags'],
        'descricao':              linha['descricao'],
        'total_horas':            linha.get('total_horas', 0),
        'total_usuarios_jogaram': linha.get('total_usuarios_jogaram', 0),
        'pontuacao_ponderada':    linha.get('pontuacao_ponderada', 0),
        'motivo':                 'Descoberta aleatória',
    }
