"""Gerencia o estado da sessão e decide qual modelo de recomendação usar."""

import random
from collections import Counter

from modelos.baseline import obter_jogos_populares, obter_jogo_aleatorio
from modelos.conteudo import recomendar_por_conteudo


class SessaoUsuario:
    """Mantém histórico de likes/dislikes e controla a estratégia de recomendação."""

    def __init__(self):
        self.curtidos:         list[str] = []
        self.rejeitados:       list[str] = []
        self.vistos:           list[str] = []
        self.total_interacoes: int       = 0

    def registrar_curtida(self, nome_jogo: str):
        """Registra um like e incrementa o contador de interações."""
        if nome_jogo not in self.curtidos:
            self.curtidos.append(nome_jogo)
        if nome_jogo not in self.vistos:
            self.vistos.append(nome_jogo)
        self.total_interacoes += 1

    def registrar_rejeicao(self, nome_jogo: str):
        """Registra um dislike e incrementa o contador de interações."""
        if nome_jogo not in self.rejeitados:
            self.rejeitados.append(nome_jogo)
        if nome_jogo not in self.vistos:
            self.vistos.append(nome_jogo)
        self.total_interacoes += 1

    def decidir_estrategia(self) -> str:
        """Decide qual modelo usar: 'popular' (< 3 curtidas) ou 'conteudo' (>= 3)."""
        if len(self.curtidos) >= 3:
            return 'conteudo'
        return 'popular'

    def obter_proximo_jogo(self, modelos: dict) -> dict | None:
        """Obtém o próximo jogo com progressão gradual: aleatório → popular → conteúdo."""
        df      = modelos['df_jogos']
        excluir = self.vistos.copy()
        total_vistos = len(self.vistos)

        # Primeiro jogo sempre aleatório
        if total_vistos == 0:
            proximo = obter_jogo_aleatorio(df, excluir_nomes=excluir)
            if proximo:
                self.vistos.append(proximo['nome'])
            return proximo

        # Jogos 2-3: majoritariamente aleatório, cresce gradualmente para popular
        if total_vistos <= 2:
            peso_popular = total_vistos * 0.1
            if random.random() > peso_popular:
                proximo = obter_jogo_aleatorio(df, excluir_nomes=excluir)
            else:
                candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)
                proximo = candidatos[0] if candidatos else obter_jogo_aleatorio(df, excluir_nomes=excluir)
            if proximo and proximo['nome'] not in self.vistos:
                self.vistos.append(proximo['nome'])
            return proximo

        estrategia = self.decidir_estrategia()
        proximo = None

        if estrategia == 'popular':
            if random.random() < 0.3:
                proximo = obter_jogo_aleatorio(df, excluir_nomes=excluir)
            else:
                candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)
                proximo = candidatos[0] if candidatos else None

        elif estrategia == 'conteudo':
            sorteio = random.random()
            if sorteio < 0.60:
                candidatos = recomendar_por_conteudo(
                    self.curtidos, df,
                    modelos['matriz_sim'], modelos['indice_jogos'],
                    excluir_nomes=excluir, n=20,
                )
                proximo = candidatos[0] if candidatos else None
            elif sorteio < 0.80:
                candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)
                proximo = candidatos[0] if candidatos else None
            else:
                proximo = obter_jogo_aleatorio(df, excluir_nomes=excluir)

        # Fallback para popular se nenhuma fonte retornou
        if proximo is None:
            candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)
            proximo = candidatos[0] if candidatos else None

        if proximo is None:
            return None

        if proximo['nome'] not in self.vistos:
            self.vistos.append(proximo['nome'])
        return proximo

    def obter_generos_favoritos_de(self, df_jogos) -> list[tuple]:
        """Conta gêneros dos curtidos usando o DataFrame de metadados. Retorna lista de tuplas (genero, contagem)."""
        mapa = df_jogos.set_index('Nome_Jogo')['generos'].to_dict()
        contagem = Counter()

        for nome in self.curtidos:
            generos_raw = mapa.get(nome, 'desconhecido')
            if generos_raw and generos_raw != 'desconhecido':
                for genero in generos_raw.split(','):
                    genero = genero.strip()
                    if genero:
                        contagem[genero] += 1

        return contagem.most_common()
