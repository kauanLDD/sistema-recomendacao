/** logica.js — Sessao do SteamMatch via API Python */

const API = 'http://localhost:5000/api';

const sessao = {
  curtidos:   [],
  rejeitados: [],
  vistos:     [],
  _generos:   {},   // { genero: contagem } acumulado dos curtidos

  get totalInteracoes() {
    return this.curtidos.length + this.rejeitados.length;
  },

  /* Estrategia local — so decide qual parametro mandar para a API */
  decidirEstrategia() {
    const n = this.totalInteracoes;
    const c = this.curtidos.length;
    if (n === 0)          return 'aleatorio';
    if (n <= 2 || c < 3)  return 'popular';
    return 'conteudo';
  },

  /* Proximo jogo via /api/proximo (replica logica exata do terminal) */
  async obterProximoJogo() {
    const resp = await fetch(`${API}/proximo`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        curtidos:   this.curtidos,
        rejeitados: this.rejeitados,
        vistos:     this.vistos,
      }),
    });
    if (!resp.ok) throw new Error(`Erro ${resp.status}`);
    const jogo = await resp.json();
    if (jogo) this.vistos.push(jogo.nome);
    return jogo;
  },

  registrarCurtida(nome, generos = []) {
    if (!this.curtidos.includes(nome)) {
      this.curtidos.push(nome);
      generos.forEach(g => { this._generos[g] = (this._generos[g] || 0) + 1; });
    }
  },

  registrarRejeicao(nome) {
    if (!this.rejeitados.includes(nome)) this.rejeitados.push(nome);
  },

  /* Generos favoritos ordenados por frequencia (calculado localmente) */
  obterGenerosFavoritos() {
    return Object.entries(this._generos)
      .sort((a, b) => b[1] - a[1])
      .map(([g]) => g);
  },

  /* N recomendacoes via /api/recomendar */
  async obterRecomendacoes(n = 5) {
    const estrategia = this.curtidos.length >= 3 ? 'conteudo' : 'popular';
    const resp = await fetch(`${API}/recomendar`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        estrategia,
        jogos:   this.curtidos,
        excluir: this.vistos,
        n,
      }),
    });
    if (!resp.ok) throw new Error(`Erro ${resp.status}`);
    return await resp.json();
  },

  reiniciar() {
    this.curtidos   = [];
    this.rejeitados = [];
    this.vistos     = [];
    this._generos   = {};
  },
};
