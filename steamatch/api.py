"""API Flask do SteamMatch — expoe o modelo TF-IDF como servico HTTP."""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modelos.carregador import carregar_dados
from modelos.baseline import obter_jogos_populares, obter_jogo_aleatorio
from modelos.conteudo import construir_modelo_conteudo, recomendar_por_conteudo
from interface.sessao import SessaoUsuario

_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# Carrega modelos uma vez na inicializacao
print('Carregando modelos...')
_df              = carregar_dados(os.path.join(_DIR, 'dados'))
_matriz, _indice = construir_modelo_conteudo(_df)
MODELOS = {'df_jogos': _df, 'matriz_sim': _matriz, 'indice_jogos': _indice}
print(f'{len(_df)} jogos prontos.\n')


def _fonte_steam(ratio: float) -> str:
    if ratio >= 0.95: return 'Extremamente Positivo'
    if ratio >= 0.80: return 'Muito Positivo'
    if ratio >= 0.70: return 'Majoritariamente Positivo'
    if ratio >= 0.40: return 'Misto'
    return 'Predominantemente Negativo'


def _serializar(jogo: dict) -> dict:
    """Converte dict do backend para o formato JSON esperado pelo frontend."""
    positivas = int(jogo.get('positivas', 0))
    total     = int(jogo.get('total_reviews', 0))
    ratio     = positivas / total if total > 0 else 0.0
    generos   = [g.strip() for g in str(jogo.get('generos', '')).split(',') if g.strip()]
    return {
        'nome':             jogo['nome'],
        'generos':          generos[:4],
        'descricao':        str(jogo.get('descricao', '')),
        'avaliacao':        int(ratio * 100),
        'total_avaliacoes': total,
        'fonte':            _fonte_steam(ratio),
        'motivo':           jogo.get('motivo', ''),
    }


def _sessao_from_body(body: dict) -> SessaoUsuario:
    s = SessaoUsuario()
    s.curtidos         = body.get('curtidos', [])
    s.rejeitados       = body.get('rejeitados', [])
    s.vistos           = body.get('vistos', [])
    s.total_interacoes = len(s.curtidos) + len(s.rejeitados)
    return s


@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'jogos': len(_df)})


@app.get('/api/jogos')
def listar_jogos():
    """Lista jogos com busca opcional por nome (para autocomplete)."""
    q     = request.args.get('q', '').lower()
    limit = min(int(request.args.get('limit', 20)), 200)

    df = _df if not q else _df[_df['Nome_Jogo'].str.lower().str.contains(q, na=False)]
    resultado = [
        {'nome': row['Nome_Jogo'], 'generos': str(row['generos'])}
        for _, row in df.head(limit).iterrows()
    ]
    return jsonify(resultado)


@app.post('/api/proximo')
def proximo_jogo():
    """Proximo jogo para o fluxo de swipe — replica a logica exata do terminal."""
    sessao = _sessao_from_body(request.json or {})
    jogo   = sessao.obter_proximo_jogo(MODELOS)
    if jogo is None:
        return jsonify(None)
    return jsonify(_serializar(jogo))


@app.post('/api/recomendar')
def recomendar():
    """Retorna N recomendacoes por estrategia: aleatorio | popular | conteudo."""
    body       = request.json or {}
    estrategia = body.get('estrategia', 'popular')
    jogos      = body.get('jogos', [])
    excluir    = body.get('excluir', [])
    n          = min(int(body.get('n', 10)), 50)

    if estrategia == 'aleatorio':
        jogo      = obter_jogo_aleatorio(_df, excluir_nomes=excluir)
        resultado = [_serializar(jogo)] if jogo else []

    elif estrategia == 'popular':
        lista     = obter_jogos_populares(_df, n=n, excluir_nomes=excluir)
        resultado = [_serializar(j) for j in lista]

    elif estrategia == 'conteudo':
        if not jogos:
            lista = obter_jogos_populares(_df, n=n, excluir_nomes=excluir)
        else:
            lista = recomendar_por_conteudo(
                jogos, _df, _matriz, _indice, excluir_nomes=excluir, n=n,
            )
            if not lista:
                lista = obter_jogos_populares(_df, n=n, excluir_nomes=excluir)
        resultado = [_serializar(j) for j in lista]

    else:
        return jsonify({'erro': f'Estrategia desconhecida: {estrategia}'}), 400

    return jsonify(resultado)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
