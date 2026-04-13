"""SteamMatch — sobe o servidor e abre o frontend no navegador."""

import os
import sys
import time
import webbrowser
import subprocess
import urllib.request
import urllib.error

_DIR = os.path.dirname(os.path.abspath(__file__))
URL  = 'http://localhost:5000'


def _aguardar_api(tentativas: int = 60, intervalo: float = 0.5) -> bool:
    for _ in range(tentativas):
        try:
            urllib.request.urlopen(f'{URL}/api/health', timeout=1)
            return True
        except Exception:
            time.sleep(intervalo)
    return False


def main():
    proc = subprocess.Popen([sys.executable, os.path.join(_DIR, 'api.py')])

    print('Aguardando servidor...')
    if not _aguardar_api():
        print('Servidor nao respondeu. Verifique se o games.csv esta em steamatch/dados/')
        proc.terminate()
        sys.exit(1)

    print(f'Abrindo {URL} no navegador...')
    webbrowser.open(URL)

    try:
        proc.wait()
    except KeyboardInterrupt:
        print('\nEncerrando SteamMatch.')
        proc.terminate()
        proc.wait()


if __name__ == '__main__':
    main()
