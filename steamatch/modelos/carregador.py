"""Carrega, enriquece e prepara os dados dos CSVs do SteamMatch."""

import re

import pandas as pd
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()


def _normalizar_nome(s: pd.Series) -> pd.Series:
    """Normaliza nomes para merge: lowercase, remove símbolos e colapsa espaços."""
    return (
        s.str.lower()
         .str.strip()
         .str.replace(r'[™®©]', '', regex=True)
         .str.replace(r"[:\-']", ' ', regex=True)
         .str.replace(r'\s+', ' ', regex=True)
         .str.strip()
    )


def _buscar_sugestoes(nome: str, df_steam: pd.DataFrame, n: int = 3) -> list:
    """Busca no df_steam nomes parecidos via str.contains nas primeiras palavras."""
    palavras = [p for p in nome.split() if len(p) > 3 and not p.isdigit()][:2]
    if not palavras:
        return []
    pattern = '|'.join(re.escape(p) for p in palavras)
    return (
        df_steam[df_steam['name'].str.contains(pattern, case=False, na=False, regex=True)]
        ['name'].head(n).tolist()
    )


def carregar_dados(caminho_dados='./dados'):
    """Carrega os dois CSVs e retorna df_enriquecido, df_horas, df_compras."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progresso:

        tarefa = progresso.add_task("🔄 Carregando steam-200k.csv...", total=100)

        caminho_200k = f"{caminho_dados}/steam-200k.csv"
        df_principal = pd.read_csv(
            caminho_200k,
            header=None,
            names=['usuario_id', 'nome_jogo', 'comportamento', 'valor', '_extra']
        )
        progresso.update(tarefa, advance=100)

        df_compras = df_principal[df_principal['comportamento'] == 'purchase'][
            ['usuario_id', 'nome_jogo']
        ].copy()

        df_horas = df_principal[df_principal['comportamento'] == 'play'][
            ['usuario_id', 'nome_jogo', 'valor']
        ].copy()
        df_horas = df_horas.rename(columns={'valor': 'horas'})

        tarefa2 = progresso.add_task("🔗 Enriquecendo com metadados...", total=100)

        caminho_games = f"{caminho_dados}/steam_games.csv"
        df_steam = pd.read_csv(caminho_games, usecols=['name', 'genre', 'popular_tags', 'desc_snippet'])
        progresso.update(tarefa2, advance=50)

        jogos_unicos = df_principal['nome_jogo'].unique()
        df_jogos = pd.DataFrame({'Nome_Jogo': jogos_unicos})

        # Merge exato por nome normalizado
        df_jogos['_chave'] = _normalizar_nome(df_jogos['Nome_Jogo'])
        df_steam['_chave'] = _normalizar_nome(df_steam['name'])

        df_steam_unico = df_steam.drop_duplicates(subset='_chave')

        df_enriquecido = df_jogos.merge(
            df_steam_unico[['_chave', 'genre', 'popular_tags', 'desc_snippet']],
            on='_chave',
            how='left'
        )

        # Etapa (b): tentar sem ano no final
        df_enriquecido['_chave_sem_ano'] = (
            df_enriquecido['_chave']
            .str.replace(r'\s+\d{4}$', '', regex=True)
            .str.strip()
        )
        df_steam_unico = df_steam_unico.copy()
        df_steam_unico['_chave_sem_ano'] = (
            df_steam_unico['_chave']
            .str.replace(r'\s+\d{4}$', '', regex=True)
            .str.strip()
        )
        df_steam_sem_ano = df_steam_unico.drop_duplicates(subset='_chave_sem_ano')

        sem_match_mask = df_enriquecido['genre'].isna()
        df_para_recuperar = (
            df_enriquecido[sem_match_mask][['Nome_Jogo', '_chave', '_chave_sem_ano']]
            .merge(
                df_steam_sem_ano[['_chave_sem_ano', 'genre', 'popular_tags', 'desc_snippet']],
                on='_chave_sem_ano',
                how='inner',
            )
            .set_index('_chave')
        )
        n_recuperados = len(df_para_recuperar)
        if n_recuperados > 0:
            df_enriquecido = df_enriquecido.set_index('_chave')
            df_enriquecido.update(df_para_recuperar[['genre', 'popular_tags', 'desc_snippet']])
            df_enriquecido = df_enriquecido.reset_index()

        # Top 30 mais jogados ainda sem metadados
        horas_por_jogo = (
            df_horas.groupby('nome_jogo')['horas']
            .sum()
            .reset_index()
            .rename(columns={'nome_jogo': 'Nome_Jogo', 'horas': 'total_horas'})
        )
        ainda_sem_meta = df_enriquecido[df_enriquecido['genre'].isna()][
            ['Nome_Jogo', '_chave_sem_ano']
        ].copy()
        top30_sem_meta = (
            ainda_sem_meta
            .merge(horas_por_jogo, on='Nome_Jogo', how='left')
            .sort_values('total_horas', ascending=False)
            .head(30)
        )

        df_enriquecido = df_enriquecido.rename(columns={
            'genre':        'generos',
            'popular_tags': 'tags',
            'desc_snippet': 'descricao',
        })
        df_enriquecido['generos']   = df_enriquecido['generos'].fillna('desconhecido')
        df_enriquecido['tags']      = df_enriquecido['tags'].fillna('desconhecido')
        df_enriquecido['descricao'] = df_enriquecido['descricao'].fillna('')

        df_enriquecido = df_enriquecido.drop(columns=['_chave', '_chave_sem_ano'])

        progresso.update(tarefa2, advance=50)

        total_jogos    = len(df_enriquecido)
        com_metadados  = (df_enriquecido['generos'] != 'desconhecido').sum()
        taxa_cobertura = (com_metadados / total_jogos) * 100

    console.print(f"✅ Pronto! [bold green]{total_jogos}[/bold green] jogos carregados.")
    console.print(
        f"   Cobertura de metadados: [bold cyan]{com_metadados}/{total_jogos}[/bold cyan] "
        f"([bold]{taxa_cobertura:.1f}%[/bold])"
    )
    console.print(
        f"   Etapa (b) — remoção de ano: "
        f"[bold cyan]+{n_recuperados}[/bold cyan] jogos recuperados"
    )

    if not top30_sem_meta.empty:
        console.print(
            f"\n[bold yellow]🔍 {len(top30_sem_meta)} jogos mais jogados sem metadados "
            f"(possíveis grafias no steam_games.csv):[/bold yellow]"
        )
        for _, row in top30_sem_meta.iterrows():
            nome    = row['Nome_Jogo']
            total_h = row.get('total_horas') or 0
            sugestoes = _buscar_sugestoes(nome, df_steam)
            sug_str = ', '.join(f'"{s}"' for s in sugestoes) if sugestoes else 'nenhum encontrado'
            console.print(f"  [red]{nome}[/red] ({total_h:.0f}h) → steam_games: {sug_str}")
        console.print()

    return df_enriquecido, df_horas, df_compras


def calcular_popularidade(df_horas, df_compras, df_enriquecido):
    """Adiciona métricas de popularidade ao df_enriquecido e descarta jogos sem metadados. Retorna df_enriquecido, df_horas, df_compras filtrados."""
    stats_horas = df_horas.groupby('nome_jogo').agg(
        total_usuarios_jogaram=('usuario_id', 'nunique'),
        total_horas=('horas', 'sum'),
        media_horas=('horas', 'mean'),
    ).reset_index()

    stats_compras = df_compras.groupby('nome_jogo').agg(
        total_compras=('usuario_id', 'nunique')
    ).reset_index()

    df_enriquecido = df_enriquecido.merge(
        stats_horas.rename(columns={'nome_jogo': 'Nome_Jogo'}),
        on='Nome_Jogo', how='left'
    )
    df_enriquecido = df_enriquecido.merge(
        stats_compras.rename(columns={'nome_jogo': 'Nome_Jogo'}),
        on='Nome_Jogo', how='left'
    )

    df_enriquecido['total_usuarios_jogaram'] = df_enriquecido['total_usuarios_jogaram'].fillna(0)
    df_enriquecido['total_horas']            = df_enriquecido['total_horas'].fillna(0)
    df_enriquecido['media_horas']            = df_enriquecido['media_horas'].fillna(0)
    df_enriquecido['total_compras']          = df_enriquecido['total_compras'].fillna(0)

    # Calcula pontuação ponderada estilo IMDb
    v = df_enriquecido['total_usuarios_jogaram']
    m = df_enriquecido['total_usuarios_jogaram'].quantile(0.60)
    R = df_enriquecido['media_horas']
    C = df_enriquecido['media_horas'].mean()

    df_enriquecido['pontuacao_ponderada'] = (v / (v + m)) * R + (m / (v + m)) * C

    total_antes = len(df_enriquecido)
    df_enriquecido = df_enriquecido[
        (df_enriquecido['generos'] != 'desconhecido') &
        (df_enriquecido['tags'] != 'desconhecido') &
        (df_enriquecido['generos'].notna()) &
        (df_enriquecido['tags'].notna())
    ].reset_index(drop=True)
    descartados = total_antes - len(df_enriquecido)

    console.print(
        f"✅ Jogos com metadados completos: [bold green]{len(df_enriquecido)}[/bold green] "
        f"(descartados [bold red]{descartados}[/bold red] sem gênero/tags)"
    )

    # Sincroniza df_horas e df_compras com os jogos remanescentes
    jogos_validos = set(df_enriquecido['Nome_Jogo'])
    df_horas   = df_horas[df_horas['nome_jogo'].isin(jogos_validos)].reset_index(drop=True)
    df_compras = df_compras[df_compras['nome_jogo'].isin(jogos_validos)].reset_index(drop=True)

    return df_enriquecido, df_horas, df_compras
