"""SteamMatch — ponto de entrada do sistema de recomendação de jogos Steam."""

import sys
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from modelos.carregador import carregar_dados
from modelos.conteudo import construir_modelo_conteudo
from interface.sessao import SessaoUsuario
from interface.terminal import (
    exibir_boas_vindas,
    exibir_card_jogo,
    exibir_feedback_curtida,
    exibir_feedback_rejeicao,
    exibir_tela_match,
    exibir_resumo_final,
)

console = Console()

MINIMO_JOGOS_DISPONIVEIS = 5


def carregar_todos_os_modelos(caminho_dados: str = './dados') -> tuple:
    """Carrega games.csv e constrói todos os modelos. Retorna (modelos, sessao)."""
    try:
        df_jogos = carregar_dados(caminho_dados)
    except FileNotFoundError as erro:
        console.print(f'\n[bold red]Arquivo nao encontrado:[/bold red] {erro}')
        console.print(
            '[yellow]Verifique se o arquivo games.csv '
            f'está em [bold]{caminho_dados}/[/bold][/yellow]\n'
        )
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progresso:
        tarefa = progresso.add_task('Construindo modelo TF-IDF...', total=100)

        matriz_sim, indice_jogos = construir_modelo_conteudo(df_jogos)
        progresso.update(tarefa, advance=100)

    total_jogos = len(df_jogos)
    console.print(f'Pronto! [bold green]{total_jogos}[/bold green] jogos carregados.\n')

    modelos = {
        'df_jogos':     df_jogos,
        'matriz_sim':   matriz_sim,
        'indice_jogos': indice_jogos,
    }

    return modelos, SessaoUsuario()


def _jogos_restantes(sessao: SessaoUsuario, modelos: dict) -> int:
    """Retorna a quantidade de jogos ainda não vistos na sessão."""
    total = len(modelos['df_jogos'])
    return total - len(sessao.vistos)


def main():
    """Loop principal do SteamMatch: boas-vindas, carregamento, swipe e resumo final."""
    exibir_boas_vindas()

    _dir = os.path.dirname(os.path.abspath(__file__))
    modelos, sessao = carregar_todos_os_modelos(os.path.join(_dir, 'dados'))

    while True:
        if _jogos_restantes(sessao, modelos) < MINIMO_JOGOS_DISPONIVEIS:
            console.print('\n[yellow]Você viu todos os jogos disponíveis![/yellow]\n')
            break

        jogo = sessao.obter_proximo_jogo(modelos)

        if jogo is None:
            console.print('\n[yellow]Não há mais jogos para recomendar.[/yellow]\n')
            break

        acao = exibir_card_jogo(jogo, sessao)

        if acao == 'q':
            break

        elif acao == 'l':
            sessao.registrar_curtida(jogo['nome'])
            exibir_feedback_curtida()

            # Tela de match a cada 5 likes
            if len(sessao.curtidos) > 0 and len(sessao.curtidos) % 5 == 0:
                exibir_tela_match(sessao, modelos)

        elif acao == 'd':
            sessao.registrar_rejeicao(jogo['nome'])
            exibir_feedback_rejeicao()

    exibir_resumo_final(sessao, modelos)


if __name__ == '__main__':
    main()
