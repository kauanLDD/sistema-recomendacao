"""Interface visual no terminal com Rich: cards, telas e feedback do SteamMatch."""

import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()

LARGURA_PAINEL = 55


def _barra_progresso_visual(valor: float, maximo: float, tamanho: int = 10) -> str:
    """Gera uma barra textual estilo █░ com base na proporção valor/maximo."""
    if maximo <= 0:
        proporcao = 0.0
    else:
        proporcao = min(valor / maximo, 1.0)
    blocos_cheios = int(proporcao * tamanho)
    blocos_vazios = tamanho - blocos_cheios
    return '█' * blocos_cheios + '░' * blocos_vazios


def _truncar(texto: str, limite: int = 120) -> str:
    """Trunca o texto no limite de caracteres adicionando reticências se necessário."""
    if not texto or not texto.strip():
        return 'Sem descrição disponível.'
    texto = texto.strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite].rstrip() + '...'


def _genero_curto(generos: str, max_generos: int = 2, limite: int = 16) -> str:
    """Extrai os primeiros max_generos e trunca para exibição compacta."""
    if not generos or generos == 'desconhecido':
        return 'N/D'
    partes = [g.strip() for g in generos.split(',')][:max_generos]
    resultado = ', '.join(partes)
    if len(resultado) > limite:
        resultado = resultado[:limite - 1] + '…'
    return resultado


def _formatar_numero(valor: float) -> str:
    """Formata um número grande de forma legível, ex: 4200000 → '4.2M'."""
    valor = float(valor)
    if valor >= 1_000_000:
        return f'{valor / 1_000_000:.1f}M'
    if valor >= 1_000:
        return f'{valor / 1_000:.1f}K'
    return f'{valor:.0f}'


def exibir_boas_vindas():
    """Exibe a tela inicial com título e instruções, aguardando ENTER para começar."""
    console.clear()

    titulo = Text()
    titulo.append('🎮  SteamMatch\n', style='bold cyan')
    titulo.append('Sistema de Recomendação de Jogos', style='dim')

    painel_titulo = Panel(
        Align.center(titulo),
        box=box.DOUBLE,
        width=LARGURA_PAINEL,
        style='cyan',
    )
    console.print()
    console.print(Align.center(painel_titulo))
    console.print()

    instrucoes = Text()
    instrucoes.append('  Bem-vindo! Vamos descobrir seus jogos favoritos.\n', style='white')
    instrucoes.append('  Dê like nos jogos que te interessam e dislike\n', style='white')
    instrucoes.append('  nos que não curtir. O sistema aprende com você!\n\n', style='white')
    instrucoes.append('  [ ENTER para começar ]', style='bold yellow')

    console.print(Align.center(instrucoes))
    console.print()
    input()


def exibir_card_jogo(jogo: dict, sessao) -> str:
    """Exibe o card do jogo no estilo Tinder e retorna 'l', 'd' ou 'q' conforme o input."""
    console.clear()

    nome      = jogo.get('nome', 'Desconhecido')
    generos   = jogo.get('generos', 'desconhecido')
    tags_raw  = jogo.get('tags', 'desconhecido')
    descricao = _truncar(jogo.get('descricao', ''), 120)
    positivas = jogo.get('positivas', 0)
    total_rev = jogo.get('total_reviews', 0)
    motivo    = jogo.get('motivo', '')

    # Filtra apenas as primeiras 3 tags
    if tags_raw and tags_raw != 'desconhecido':
        lista_tags = [t.strip() for t in tags_raw.split(',')][:3]
        tags_fmt = ', '.join(lista_tags)
    else:
        tags_fmt = 'Não disponível'

    if generos == 'desconhecido':
        generos_fmt = 'Não disponível'
    else:
        generos_fmt = generos

    max_reviews_referencia = 500_000
    barra_pop  = _barra_progresso_visual(positivas, max_reviews_referencia)
    positivas_fmt = _formatar_numero(positivas)
    total_fmt     = _formatar_numero(total_rev)

    conteudo = Text()
    conteudo.append(f'🎮  {nome}\n', style='bold white')
    conteudo.append('  ' + '─' * (LARGURA_PAINEL - 6) + '\n', style='dim')
    conteudo.append('  🏷️  Gêneros : ', style='yellow')
    conteudo.append(f'{generos_fmt}\n', style='white')
    conteudo.append('  🔖  Tags    : ', style='yellow')
    conteudo.append(f'{tags_fmt}\n\n', style='white')
    conteudo.append(f'  📝  "{descricao}"\n\n', style='italic dim')
    conteudo.append(f'  📊  Popularidade  {barra_pop}  {positivas_fmt} positivas\n', style='cyan')
    conteudo.append(f'  👥  Avaliações    {total_fmt} reviews totais\n\n', style='cyan')
    conteudo.append('  🤖  Recomendado por: ', style='dim')
    conteudo.append(f'{motivo}\n', style='dim italic')

    rodape = Text(justify='center')
    rodape.append('  [L] Like 💚', style='bold green')
    rodape.append('    ')
    rodape.append('[D] Dislike ❌', style='bold red')
    rodape.append('    ')
    rodape.append('[Q] Sair', style='bold yellow')

    card = Panel(
        conteudo,
        title=f'[bold cyan]Jogo {len(sessao.vistos) + 1}[/bold cyan]',
        subtitle=str(rodape),
        box=box.ROUNDED,
        width=LARGURA_PAINEL + 4,
        style='white',
    )

    console.print()
    console.print(Align.center(card))

    contadores = Text(justify='center')
    contadores.append(f'  💚 Curtidos: {len(sessao.curtidos)}', style='green')
    contadores.append(f'   ❌ Rejeitados: {len(sessao.rejeitados)}', style='red')
    contadores.append(f'   👁 Vistos: {len(sessao.vistos)}', style='dim')
    console.print()
    console.print(Align.center(contadores))
    console.print()

    while True:
        tecla = input('  > ').strip().lower()
        if tecla in ('l', 'd', 'q'):
            return tecla
        console.print('  [yellow]Use L (like), D (dislike) ou Q (sair)[/yellow]')


def exibir_feedback_curtida():
    """Exibe mensagem de like em verde e aguarda 1 segundo."""
    console.print(
        Align.center(
            Text('💚 Curtido! Aprendendo seu gosto...', style='bold green')
        )
    )
    time.sleep(1)


def exibir_feedback_rejeicao():
    """Exibe mensagem de dislike em vermelho e aguarda 1 segundo."""
    console.print(
        Align.center(
            Text('❌ Anotado! Buscando algo diferente...', style='bold red')
        )
    )
    time.sleep(1)


def exibir_tela_match(sessao, modelos: dict):
    """Exibe a tela de match a cada 5 likes com gêneros favoritos e top 3 recomendações."""
    console.clear()

    df = modelos['df_jogos']
    generos_favoritos = sessao.obter_generos_favoritos_de(df)[:2]

    from modelos.baseline import obter_jogos_populares
    from modelos.conteudo import recomendar_por_conteudo

    estrategia = sessao.decidir_estrategia()
    excluir = sessao.vistos.copy()

    if estrategia == 'popular':
        lista = obter_jogos_populares(df, n=3, excluir_nomes=excluir)
    else:
        lista = recomendar_por_conteudo(
            sessao.curtidos, df,
            modelos['matriz_sim'], modelos['indice_jogos'],
            excluir_nomes=excluir, n=3
        )

    medalhas = ['🥇', '🥈', '🥉']

    conteudo = Text()
    conteudo.append('  Com base nos seus likes, você curte:\n\n', style='white')

    for genero, _ in generos_favoritos:
        conteudo.append(f'   ▸ {genero}\n', style='bold cyan')

    conteudo.append('\n  Top 3 recomendações agora:\n\n', style='white')

    for i, jogo in enumerate(lista[:3]):
        medalha = medalhas[i] if i < len(medalhas) else '  '
        nome   = jogo['nome'][:20]
        genero = _genero_curto(jogo.get('generos', ''), max_generos=2, limite=16)
        conteudo.append(f'   {medalha} {nome:<22} {genero}\n', style='bold white')

    conteudo.append('\n')

    painel = Panel(
        Align.center(conteudo),
        title='[bold yellow]🎯  MATCH ENCONTRADO![/bold yellow]',
        box=box.DOUBLE,
        width=LARGURA_PAINEL,
        style='yellow',
    )

    console.print()
    console.print(Align.center(painel))
    console.print()
    console.print(Align.center(Text('[ ENTER para continuar descobrindo ]', style='bold yellow')))
    input()


def exibir_resumo_final(sessao, modelos: dict):
    """Exibe estatísticas da sessão, gêneros favoritos e top 5 recomendações finais."""
    console.clear()

    df = modelos['df_jogos']
    generos_favoritos = sessao.obter_generos_favoritos_de(df)
    estrategia_final = sessao.decidir_estrategia()

    mapa_estrategia = {
        'popular':  'Popularidade (baseline)',
        'conteudo': 'Conteúdo (TF-IDF)',
    }
    nome_estrategia = mapa_estrategia.get(estrategia_final, estrategia_final)

    from modelos.baseline import obter_jogos_populares
    from modelos.conteudo import recomendar_por_conteudo

    excluir = sessao.vistos.copy()

    if estrategia_final == 'popular':
        lista_final = obter_jogos_populares(df, n=5, excluir_nomes=excluir)
    else:
        lista_final = recomendar_por_conteudo(
            sessao.curtidos, df,
            modelos['matriz_sim'], modelos['indice_jogos'],
            excluir_nomes=excluir, n=5
        )

    conteudo = Text()

    conteudo.append(f'  Jogos vistos    : {len(sessao.vistos)}\n', style='white')
    conteudo.append(f'  💚 Curtidos     : {len(sessao.curtidos)}\n', style='green')
    conteudo.append(f'  ❌ Rejeitados   : {len(sessao.rejeitados)}\n\n', style='red')

    if generos_favoritos:
        conteudo.append('  Seus gêneros favoritos:\n', style='white')
        for genero, qtd in generos_favoritos[:3]:
            conteudo.append(f'   ▸ {genero}  ({qtd} jogo{"s" if qtd > 1 else ""} curtido{"s" if qtd > 1 else ""})\n', style='cyan')
        conteudo.append('\n')

    conteudo.append(f'  🤖 Estratégia final: ', style='dim')
    conteudo.append(f'{nome_estrategia}\n\n', style='bold dim')

    if lista_final:
        conteudo.append('  Top 5 recomendações para você:\n\n', style='white')
        for i, jogo in enumerate(lista_final[:5], start=1):
            nome   = jogo['nome'][:20]
            genero = _genero_curto(jogo.get('generos', ''), max_generos=2, limite=16)
            conteudo.append(
                f'   {i}. {nome:<22} {genero}\n',
                style='bold white'
            )
    else:
        conteudo.append('  Interaja mais para receber recomendações personalizadas!\n', style='dim')

    conteudo.append('\n')

    painel = Panel(
        conteudo,
        title='[bold cyan]📊  SUA SESSÃO[/bold cyan]',
        box=box.DOUBLE,
        width=LARGURA_PAINEL,
        style='cyan',
    )

    console.print()
    console.print(Align.center(painel))
    console.print()
    console.print(Align.center(Text('Obrigado por usar o SteamMatch! 🎮', style='bold cyan')))
    console.print()
