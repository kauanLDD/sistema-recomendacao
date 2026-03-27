"""Gera frontend/js/dados.js a partir do games.csv real."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modelos.carregador import carregar_dados

N_JOGOS = 300


def _fonte_steam(ratio: float) -> str:
    if ratio >= 0.95: return 'Extremamente Positivo'
    if ratio >= 0.80: return 'Muito Positivo'
    if ratio >= 0.70: return 'Majoritariamente Positivo'
    if ratio >= 0.40: return 'Misto'
    return 'Predominantemente Negativo'


def exportar():
    _dir = os.path.dirname(os.path.abspath(__file__))
    df = carregar_dados(os.path.join(_dir, 'dados'))

    # Top N por pontuacao ponderada (popularidade + qualidade)
    df_top = df.nlargest(N_JOGOS, 'pontuacao_ponderada').reset_index(drop=True)

    jogos = []
    for i, row in df_top.iterrows():
        total = int(row['total_reviews'])
        ratio = float(row['ratio_positivo'])
        avaliacao = int(ratio * 100)

        generos_raw = str(row.get('generos', ''))
        generos = [g.strip() for g in generos_raw.split(',') if g.strip()]

        descricao = str(row.get('descricao', '')).strip()
        if len(descricao) > 300:
            descricao = descricao[:297] + '...'

        jogos.append({
            'id':              i + 1,
            'nome':            str(row['Nome_Jogo']),
            'generos':         generos[:4],
            'descricao':       descricao or 'Sem descrição disponível.',
            'avaliacao':       avaliacao,
            'total_avaliacoes': total,
            'fonte':           _fonte_steam(ratio),
        })

    saida = os.path.join(_dir, 'frontend', 'js', 'dados.js')
    jogos_json = json.dumps(jogos, ensure_ascii=False, indent=2)

    with open(saida, 'w', encoding='utf-8') as f:
        f.write(f'/** dados.js — {len(jogos)} jogos exportados do games.csv */\n\n')
        f.write(f'const JOGOS = {jogos_json};\n')

    print(f'\nExportado: {len(jogos)} jogos → {saida}')


if __name__ == '__main__':
    exportar()
