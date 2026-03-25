"""Carrega e prepara os dados do games.csv (FronkonGames) para o SteamMatch.

Nota sobre o dataset: as colunas do CSV estão deslocadas em +1 a partir da
posição 8 (há uma coluna extra "DLC count" não declarada no header). Por isso
os nomes usados no read_csv não correspondem ao conteúdo semântico esperado.
Mapeamento real após inspeção empírica:
  CSV "Supported languages"  → descrição do jogo (About the game)
  CSV "Tags"                 → gêneros do jogo  (Genres)
  CSV "Screenshots"          → tags Steam do usuário (Steam Tags)
  CSV "Negative"             → contagem de avaliações positivas
  CSV "Score rank"           → contagem de avaliações negativas
  CSV "Notes"                → número de recomendações Steam
"""

import pandas as pd
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

# Mínimo de avaliações positivas para incluir o jogo
MIN_POSITIVAS = 50


def carregar_dados(caminho_dados='./dados'):
    """Carrega games.csv e retorna df_jogos pronto para recomendação."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progresso:

        tarefa = progresso.add_task("🔄 Carregando games.csv...", total=100)

        caminho_csv = f"{caminho_dados}/games.csv"

        # Colunas pelo nome real no header (com o deslocamento documentado acima)
        colunas_csv = [
            'Name',
            'Supported languages',   # = About the game (descrição)
            'Tags',                  # = Genres
            'Screenshots',           # = Steam Tags
            'Negative',              # = avaliações positivas
            'Score rank',            # = avaliações negativas
            'Notes',                 # = recomendações Steam
        ]
        df = pd.read_csv(caminho_csv, usecols=colunas_csv, index_col=False)
        progresso.update(tarefa, advance=40)

        # Renomear para nomes semânticos internos
        df = df.rename(columns={
            'Name':                'Nome_Jogo',
            'Supported languages': 'descricao',
            'Tags':                'generos',
            'Screenshots':         'tags',
            'Negative':            'positivas',
            'Score rank':          'negativas',
            'Notes':               'recomendacoes',
        })
        progresso.update(tarefa, advance=15)

        # Limpeza
        df = df[df['Nome_Jogo'].notna() & (df['Nome_Jogo'].str.strip() != '')]
        df['positivas']    = pd.to_numeric(df['positivas'], errors='coerce').fillna(0).astype(int)
        df['negativas']    = pd.to_numeric(df['negativas'], errors='coerce').fillna(0).astype(int)
        df['recomendacoes'] = pd.to_numeric(df['recomendacoes'], errors='coerce').fillna(0).astype(int)

        # Filtrar jogos com avaliações suficientes
        df = df[df['positivas'] >= MIN_POSITIVAS]

        # Remover jogos sem gênero E sem tags
        df = df[df['generos'].notna() | df['tags'].notna()]
        df = df.drop_duplicates(subset='Nome_Jogo')

        df['descricao'] = df['descricao'].fillna('').astype(str)
        df['generos']   = df['generos'].fillna('desconhecido').astype(str)
        df['tags']      = df['tags'].fillna('desconhecido').astype(str)
        progresso.update(tarefa, advance=20)

        # Calcular popularidade estilo IMDb
        total_reviews = df['positivas'] + df['negativas']
        df['total_reviews'] = total_reviews

        ratio_positivo = np.where(
            total_reviews > 0,
            df['positivas'] / total_reviews,
            0.0
        )
        df['ratio_positivo'] = ratio_positivo

        v = df['positivas']
        m = v.quantile(0.70)
        R = df['ratio_positivo']
        C = float(R.mean())
        df['pontuacao_ponderada'] = (v / (v + m)) * R + (m / (v + m)) * C

        # Campo de conteúdo para TF-IDF: gêneros (peso duplo) + tags + descrição
        df['conteudo'] = (
            df['generos'] + ' ' + df['generos'] + ' ' +
            df['tags'] + ' ' +
            df['descricao']
        ).str.strip()

        df = df.reset_index(drop=True)
        progresso.update(tarefa, advance=25)

    total_jogos   = len(df)
    com_metadados = (
        (df['generos'] != 'desconhecido') |
        (df['tags'] != 'desconhecido')
    ).sum()

    console.print(f"✅ Jogos carregados: [bold green]{total_jogos:,}[/bold green]")
    console.print(f"✅ Com metadados completos: [bold cyan]{com_metadados:,}[/bold cyan]")
    console.print("✅ Pronto para recomendação")

    return df
