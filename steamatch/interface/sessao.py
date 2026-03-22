"""Gerencia o estado da sessão e decide qual modelo de recomendação usar."""

import random
from collections import Counter

from modelos.baseline import obter_jogos_populares, obter_jogo_aleatorio
from modelos.conteudo import recomendar_por_conteudo
from modelos.colaborativo import recomendar_colaborativo


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
        """Decide qual modelo usar com base no histórico da sessão. Retorna 'popular', 'conteudo' ou 'hibrido'."""
        n_curtidos = len(self.curtidos)

        if self.total_interacoes >= 8 and n_curtidos >= 3:
            return 'hibrido'
        elif n_curtidos >= 3:
            return 'conteudo'
        else:
            return 'popular'

    def obter_proximo_jogo(self, modelos: dict) -> dict | None:
        """Obtém o próximo jogo a exibir usando a estratégia atual, com fallback para baseline."""
        estrategia = self.decidir_estrategia()
        df         = modelos['df_enriquecido']
        excluir    = self.vistos.copy()

        # 30% de chance de exibir um jogo aleatório para diversidade
        if random.random() < 0.3:
            proximo = obter_jogo_aleatorio(df, excluir_nomes=excluir)
            if proximo is not None:
                self.vistos.append(proximo['nome'])
                return proximo

        candidatos: list[dict] = []

        if estrategia == 'popular':
            candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)

        elif estrategia == 'conteudo':
            candidatos = recomendar_por_conteudo(
                self.curtidos,
                df,
                modelos['matriz_sim'],
                modelos['indice_jogos'],
                excluir_nomes=excluir,
                n=20,
            )

        elif estrategia == 'hibrido':
            candidatos = self._combinar_hibrido(modelos, excluir)

        if not candidatos:
            candidatos = obter_jogos_populares(df, n=50, excluir_nomes=excluir)

        if not candidatos:
            return None

        proximo = candidatos[0]
        if proximo['nome'] not in self.vistos:
            self.vistos.append(proximo['nome'])

        return proximo

    def _combinar_hibrido(self, modelos: dict, excluir: list[str]) -> list[dict]:
        """Combina conteúdo e colaborativo 50/50 e retorna candidatos ordenados por pontuacao_hibrida."""
        df = modelos['df_enriquecido']

        lista_conteudo = recomendar_por_conteudo(
            self.curtidos,
            df,
            modelos['matriz_sim'],
            modelos['indice_jogos'],
            excluir_nomes=excluir,
            n=30,
        )
        lista_colab = recomendar_colaborativo(
            self.curtidos,
            modelos['matriz_ii'],
            modelos['indice_itens'],
            df,
            excluir_nomes=excluir,
            n=30,
        )

        pontos_conteudo = {
            j['nome']: j.get('pontuacao_conteudo', 0.0)
            for j in lista_conteudo
        }
        pontos_colab = {
            j['nome']: j.get('pontuacao_colaborativa', 0.0)
            for j in lista_colab
        }

        todos_nomes = set(pontos_conteudo) | set(pontos_colab)

        mapa_df = df.set_index('Nome_Jogo')

        pontos_pop = {
            nome: float(mapa_df.loc[nome].get('pontuacao_ponderada', 0))
            if nome in mapa_df.index else 0.0
            for nome in todos_nomes
        }

        def normalizar(dicionario: dict) -> dict:
            if not dicionario:
                return {}
            max_val = max(dicionario.values()) or 1.0
            return {nome: val / max_val for nome, val in dicionario.items()}

        pontos_conteudo_norm = normalizar(pontos_conteudo)
        pontos_colab_norm    = normalizar(pontos_colab)
        pontos_pop_norm      = normalizar(pontos_pop)

        candidatos_hibridos = []
        for nome in todos_nomes:
            pc  = pontos_conteudo_norm.get(nome, 0.0)
            pco = pontos_colab_norm.get(nome, 0.0)
            pop = pontos_pop_norm.get(nome, 0.0)
            pontuacao_final = 0.5 * pc + 0.5 * pco + 0.2 * pop

            if nome in mapa_df.index:
                linha = mapa_df.loc[nome]
                candidatos_hibridos.append({
                    'nome':                   nome,
                    'generos':                linha['generos'],
                    'tags':                   linha['tags'],
                    'descricao':              linha['descricao'],
                    'total_horas':            linha.get('total_horas', 0),
                    'total_usuarios_jogaram': linha.get('total_usuarios_jogaram', 0),
                    'pontuacao_ponderada':    linha.get('pontuacao_ponderada', 0),
                    'pontuacao_hibrida':      pontuacao_final,
                    'motivo':                 'Híbrido: conteúdo + colaborativo + popularidade',
                })

        if candidatos_hibridos:
            max_h = max(j['pontuacao_hibrida'] for j in candidatos_hibridos) or 1.0
            for j in candidatos_hibridos:
                j['pontuacao_hibrida'] /= max_h

        candidatos_hibridos.sort(key=lambda x: x['pontuacao_hibrida'], reverse=True)
        return candidatos_hibridos

    def obter_generos_favoritos(self) -> list[tuple]:
        """Conta gêneros dos jogos curtidos. Retorna lista de tuplas (genero, contagem)."""
        contagem = Counter()
        for nome in self.curtidos:
            pass
        return contagem.most_common()

    def obter_generos_favoritos_de(self, df_enriquecido) -> list[tuple]:
        """Conta gêneros dos curtidos usando o DataFrame de metadados. Retorna lista de tuplas (genero, contagem)."""
        mapa = df_enriquecido.set_index('Nome_Jogo')['generos'].to_dict()
        contagem = Counter()

        for nome in self.curtidos:
            generos_raw = mapa.get(nome, 'desconhecido')
            if generos_raw and generos_raw != 'desconhecido':
                for genero in generos_raw.split(','):
                    genero = genero.strip()
                    if genero:
                        contagem[genero] += 1

        return contagem.most_common()
