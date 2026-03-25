/**
 * logica.js — Lógica de recomendação simulada do SteamMatch
 *
 * Progressão da estratégia:
 *   0 interações        → 100% aleatório
 *   1-2 interações      → 80% popular + 20% aleatório
 *   3-7 curtidas        → filtrar por gênero mais curtido (conteúdo)
 *   8+ interações       → ordenar por avaliação dentro do gênero (conteúdo avançado)
 */

const sessao = {
  curtidos:   [],   // ids dos jogos curtidos
  rejeitados: [],   // ids dos jogos rejeitados
  vistos:     [],   // ids de todos os jogos exibidos

  /* ── Getter calculado ──────────────────────────────── */
  get totalInteracoes() {
    return this.curtidos.length + this.rejeitados.length;
  },

  /* ── Decidir qual estratégia usar ──────────────────── */
  decidirEstrategia() {
    const nInteracoes = this.totalInteracoes;
    const nCurtidos   = this.curtidos.length;

    if (nInteracoes === 0)                       return 'aleatorio';
    if (nInteracoes <= 2)                        return 'popular';
    if (nCurtidos < 3)                           return 'popular';
    if (nInteracoes >= 8 && nCurtidos >= 3)      return 'conteudo_avancado';
    return 'conteudo';
  },

  /* ── Jogos ainda não exibidos ──────────────────────── */
  _disponiveis() {
    return JOGOS.filter(j => !this.vistos.includes(j.id));
  },

  /* ── Retornar o próximo jogo com motivo ────────────── */
  obterProximoJogo() {
    const disponiveis = this._disponiveis();
    if (disponiveis.length === 0) return null;

    const estrategia = this.decidirEstrategia();
    let jogo  = null;
    let motivo = '';

    switch (estrategia) {

      case 'aleatorio': {
        jogo   = _sortear(disponiveis);
        motivo = '🎲 Exploração aleatória';
        break;
      }

      case 'popular': {
        if (Math.random() < 0.2) {
          jogo   = _sortear(disponiveis);
          motivo = '🎲 Exploração aleatória';
        } else {
          jogo   = _maiorAvaliacao(disponiveis, 'total_avaliacoes');
          motivo = '📈 Baseado em popularidade';
        }
        break;
      }

      case 'conteudo': {
        const genFav = this.obterGenerosFavoritos();
        const porGen = disponiveis.filter(j =>
          j.generos.some(g => genFav.includes(g))
        );

        const sorteio = Math.random();
        if (porGen.length > 0 && sorteio < 0.60) {
          jogo   = _sortear(porGen);
          motivo = '🧠 Baseado no seu gosto';
        } else if (sorteio < 0.80) {
          jogo   = _maiorAvaliacao(disponiveis, 'total_avaliacoes');
          motivo = '📈 Baseado em popularidade';
        } else {
          jogo   = _sortear(disponiveis);
          motivo = '🎲 Exploração aleatória';
        }
        break;
      }

      case 'conteudo_avancado': {
        const genFav = this.obterGenerosFavoritos();
        const porGen = disponiveis.filter(j =>
          j.generos.some(g => genFav.includes(g))
        );

        const pool = porGen.length > 0 ? porGen : disponiveis;
        jogo   = _maiorAvaliacao(pool, 'avaliacao');
        motivo = '🧠 Baseado no seu gosto';
        break;
      }
    }

    if (!jogo) return null;

    this.vistos.push(jogo.id);
    return { ...jogo, motivo };
  },

  /* ── Registrar interações ──────────────────────────── */
  registrarCurtida(id) {
    if (!this.curtidos.includes(id)) this.curtidos.push(id);
  },

  registrarRejeicao(id) {
    if (!this.rejeitados.includes(id)) this.rejeitados.push(id);
  },

  /* ── Gêneros favoritos ordenados por frequência ────── */
  obterGenerosFavoritos() {
    const contagem = {};
    this.curtidos.forEach(id => {
      const jogo = JOGOS.find(j => j.id === id);
      if (!jogo) return;
      jogo.generos.forEach(g => {
        contagem[g] = (contagem[g] || 0) + 1;
      });
    });
    return Object.entries(contagem)
      .sort((a, b) => b[1] - a[1])
      .map(([genero]) => genero);
  },

  /* ── Top N recomendações pontuadas ─────────────────── */
  obterRecomendacoes(n = 5) {
    const naoVistos = JOGOS.filter(j => !this.vistos.includes(j.id));
    const genFav    = this.obterGenerosFavoritos();

    if (genFav.length === 0) {
      return [...naoVistos]
        .sort((a, b) => b.avaliacao - a.avaliacao)
        .slice(0, n);
    }

    const pontuados = naoVistos.map(jogo => {
      let score = jogo.avaliacao;
      jogo.generos.forEach(g => {
        const idx = genFav.indexOf(g);
        if (idx !== -1) score += (genFav.length - idx) * 15;
      });
      return { ...jogo, _score: score };
    });

    return pontuados
      .sort((a, b) => b._score - a._score)
      .slice(0, n);
  },

  /* ── Reiniciar sessão ──────────────────────────────── */
  reiniciar() {
    this.curtidos   = [];
    this.rejeitados = [];
    this.vistos     = [];
  },
};

/* ── Funções auxiliares privadas ───────────────────────── */
function _sortear(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function _maiorAvaliacao(arr, campo) {
  return arr.reduce((melhor, atual) =>
    atual[campo] > melhor[campo] ? atual : melhor
  );
}
