"""
Script de coleta de metadados via Steam API.
Combina steam-200k.csv com dados de gênero, categoria e descrição da API oficial.
Não requer API key. Salva progresso a cada 100 jogos para permitir retomada.

Uso:
    cd steamatch/dados
    python coletar_metadados.py

Tempo estimado: ~2.5h para ~5.155 jogos (sleep 1.5s entre requisições).
"""

import time
import csv
import os
import re
import requests
import pandas as pd

# ─── Configurações ────────────────────────────────────────────────────────────
DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_200K       = os.path.join(DIR, 'steam-200k.csv')
ARQUIVO_PARCIAL    = os.path.join(DIR, 'steam_dataset_parcial.csv')
ARQUIVO_FINAL      = os.path.join(DIR, 'steam_dataset_completo.csv')
SLEEP_ENTRE_REQS   = 1.5
CHECKPOINT_INTERVALO = 100

URL_APPLIST_STEAM    = 'https://api.steampowered.com/ISteamApps/GetAppList/v0002/'
URL_APPLIST_STEAMSPY = 'https://steamspy.com/api.php?request=all&page={page}'
URL_APPDETAILS       = 'https://store.steampowered.com/api/appdetails'
STEAMSPY_MAX_PAGES   = 20


def normalizar(nome: str) -> str:
    return re.sub(r'\s+', ' ', nome.lower().strip())


# ─── Etapa 1: carregar jogos únicos do steam-200k.csv ─────────────────────────
print('📂 Carregando steam-200k.csv...')
df_principal = pd.read_csv(
    ARQUIVO_200K,
    header=None,
    names=['usuario_id', 'nome_jogo', 'comportamento', 'valor', '_extra'],
)
jogos_unicos = df_principal['nome_jogo'].unique().tolist()
print(f'   {len(jogos_unicos)} jogos únicos encontrados.')


# ─── Etapa 2: baixar lista completa de AppIDs ─────────────────────────────────
print('\n🌐 Baixando lista de AppIDs...')

appid_por_nome = {}
fonte_usada = None

# Etapa 2a: Steam API oficial (retorna 100k+ apps em uma requisição)
try:
    resp = requests.get(
        URL_APPLIST_STEAM,
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=30,
    )
    resp.raise_for_status()
    apps = resp.json()['applist']['apps']
    appid_por_nome = {normalizar(a['name']): a['appid'] for a in apps if a.get('name')}
    fonte_usada = 'Steam API v0002'
    print(f'   ✅ Steam API: {len(appid_por_nome)} apps indexados.')
except Exception as e:
    print(f'   ⚠️  Steam API falhou ({e}), usando SteamSpy com paginação...')

# Etapa 2b: SteamSpy com paginação (fallback — ~1000 apps por página)
if not appid_por_nome:
    for page in range(STEAMSPY_MAX_PAGES):
        try:
            resp = requests.get(URL_APPLIST_STEAMSPY.format(page=page), timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            if not dados:
                print(f'   Página {page}: vazia, encerrando paginação.')
                break
            novos = {normalizar(v['name']): v['appid'] for v in dados.values() if v.get('name')}
            appid_por_nome.update(novos)
            print(f'   Página {page}: +{len(novos)} apps (total: {len(appid_por_nome)})')
            time.sleep(2)
        except Exception as e:
            print(f'   ⚠️  Página {page} falhou ({e}), continuando...')
            time.sleep(2)
    fonte_usada = 'SteamSpy (paginado)'

if not appid_por_nome:
    print('   ❌ Nenhuma fonte retornou AppIDs. Encerrando.')
    raise SystemExit(1)

print(f'\n   Total indexado via {fonte_usada}: {len(appid_por_nome)} apps.')


# ─── Etapa 3: mapear nome → AppID ─────────────────────────────────────────────
mapeamento = {}
sem_appid = []
for nome in jogos_unicos:
    appid = appid_por_nome.get(normalizar(nome))
    if appid:
        mapeamento[nome] = appid
    else:
        sem_appid.append(nome)
print(f'\n🔗 AppIDs encontrados: {len(mapeamento)} / {len(jogos_unicos)}')
print(f'   Sem AppID: {len(sem_appid)}')


# ─── Etapa 4: buscar metadados por AppID ──────────────────────────────────────

# Carregar checkpoint se existir (pular jogos já processados)
ja_processados = {}
if os.path.exists(ARQUIVO_PARCIAL):
    df_parcial = pd.read_csv(ARQUIVO_PARCIAL)
    for _, row in df_parcial.iterrows():
        ja_processados[row['nome_jogo']] = {
            'generos':    row.get('generos', ''),
            'categorias': row.get('categorias', ''),
            'descricao':  row.get('descricao', ''),
        }
    print(f'\n♻️  Retomando: {len(ja_processados)} jogos já processados.')

metadados = dict(ja_processados)
erros_api = []
contador = 0

jogos_para_buscar = [n for n in mapeamento if n not in ja_processados]
total = len(jogos_para_buscar)
print(f'\n🔍 Buscando metadados para {total} jogos...\n')

for i, nome in enumerate(jogos_para_buscar, start=1):
    appid = mapeamento[nome]

    try:
        r = requests.get(
            URL_APPDETAILS,
            params={'appids': appid, 'l': 'english'},
            timeout=10,
        )
        r.raise_for_status()
        dados = r.json().get(str(appid), {})

        if not dados.get('success'):
            metadados[nome] = {'generos': '', 'categorias': '', 'descricao': ''}
        else:
            info = dados['data']
            generos = ', '.join(g['description'] for g in info.get('genres', []))
            categorias = ', '.join(c['description'] for c in info.get('categories', []))
            descricao = info.get('short_description', '')
            metadados[nome] = {
                'generos':    generos,
                'categorias': categorias,
                'descricao':  descricao,
            }

    except Exception as e:
        erros_api.append(nome)
        metadados[nome] = {'generos': '', 'categorias': '', 'descricao': ''}

    contador += 1

    if contador % 10 == 0 or i == total:
        print(f'   [{i}/{total}] {nome[:50]}')

    # Checkpoint a cada 100 jogos
    if contador % CHECKPOINT_INTERVALO == 0:
        _rows = [{'nome_jogo': n, **v} for n, v in metadados.items()]
        pd.DataFrame(_rows).to_csv(ARQUIVO_PARCIAL, index=False)
        print(f'   💾 Checkpoint salvo ({len(metadados)} jogos)')

    time.sleep(SLEEP_ENTRE_REQS)

# Checkpoint final
_rows = [{'nome_jogo': n, **v} for n, v in metadados.items()]
pd.DataFrame(_rows).to_csv(ARQUIVO_PARCIAL, index=False)


# ─── Etapa 5: montar dataset final ────────────────────────────────────────────
print('\n📊 Montando dataset final...')
df_meta = pd.DataFrame([
    {'nome_jogo': n, **v} for n, v in metadados.items()
])

df_final = df_principal[['usuario_id', 'nome_jogo', 'comportamento', 'valor']].merge(
    df_meta,
    on='nome_jogo',
    how='left',
)
df_final.to_csv(ARQUIVO_FINAL, index=False)


# ─── Etapa 6: relatório final ─────────────────────────────────────────────────
com_meta = df_meta[df_meta['generos'].str.strip().astype(bool)].shape[0]
pct = com_meta / len(jogos_unicos) * 100

print(f'\n✅ Jogos processados     : {len(jogos_unicos)}')
print(f'✅ Com metadados         : {com_meta} ({pct:.1f}%)')
print(f'❌ Sem AppID encontrado  : {len(sem_appid)}')
print(f'❌ Erro na API           : {len(erros_api)}')
print(f'📁 Arquivo salvo em      : {ARQUIVO_FINAL}')
