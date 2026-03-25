/** interface.js — DOM, eventos e animações do SteamMatch */

/* ════════════════════════════════════════════════════════
   REFERÊNCIAS DO DOM
════════════════════════════════════════════════════════ */
const $telas = {
  inicio : document.getElementById('tela-inicio'),
  jogo   : document.getElementById('tela-jogo'),
  resumo : document.getElementById('tela-resumo'),
};

const $modal           = document.getElementById('modal-match');
const $cardContainer   = document.getElementById('area-card-container');
const $overlayLike     = document.getElementById('overlay-like');
const $overlayDislike  = document.getElementById('overlay-dislike');

const $estrategiaTexto = document.getElementById('estrategia-texto');
const $valorLikes      = document.getElementById('valor-likes');
const $valorDislikes   = document.getElementById('valor-dislikes');
const $valorVistos     = document.getElementById('valor-vistos');

const $btnIniciar      = document.getElementById('btn-iniciar');
const $btnLike         = document.getElementById('btn-like');
const $btnDislike      = document.getElementById('btn-dislike');
const $btnEncerrar     = document.getElementById('btn-encerrar');
const $btnFecharModal  = document.getElementById('btn-fechar-modal');
const $btnReiniciar    = document.getElementById('btn-reiniciar');

/* Estado local */
let jogoAtual  = null;
let bloqueado  = false;   // impede duplo-clique durante animação


/* ════════════════════════════════════════════════════════
   UTILITÁRIOS
════════════════════════════════════════════════════════ */
function formatarNumero(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000)     return Math.round(n / 1_000) + 'K';
  return String(n);
}

function mostrarTela(nome) {
  Object.entries($telas).forEach(([key, el]) => {
    const ativa = key === nome;
    el.classList.toggle('ativa',  ativa);
    el.classList.toggle('oculta', !ativa);
  });
}

function animarContador(elemento, valor) {
  elemento.textContent = valor;
  elemento.classList.remove('bounce');
  /* reflow para reiniciar a animação CSS */
  void elemento.offsetWidth;
  elemento.classList.add('bounce');
  elemento.addEventListener('animationend', () =>
    elemento.classList.remove('bounce'), { once: true }
  );
}

function criarTag(texto, classe = 'tag-genero') {
  const span = document.createElement('span');
  span.className = classe;
  span.textContent = texto;
  return span;
}


/* ════════════════════════════════════════════════════════
   RENDERIZAR CARD
════════════════════════════════════════════════════════ */
function renderizarCard(jogo) {
  /* Nome */
  document.getElementById('card-nome').textContent = jogo.nome;

  /* Gêneros */
  const $generos = document.getElementById('card-generos');
  $generos.innerHTML = '';
  jogo.generos.forEach(g => $generos.appendChild(criarTag(g)));

  /* Descrição */
  document.getElementById('card-descricao').textContent = jogo.descricao;

  /* Barra de avaliação — anima após pequeno delay */
  const $barra = document.getElementById('card-barra-avaliacao');
  $barra.style.width = '0%';

  if (jogo.avaliacao >= 80) {
    $barra.style.background = 'linear-gradient(90deg, #4caf50, #81c784)';
  } else if (jogo.avaliacao >= 60) {
    $barra.style.background = 'linear-gradient(90deg, #ff9800, #ffb74d)';
  } else {
    $barra.style.background = 'linear-gradient(90deg, #f44336, #e57373)';
  }

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      $barra.style.width = jogo.avaliacao + '%';
    });
  });

  document.getElementById('card-avaliacao-valor').textContent = jogo.avaliacao + '%';
  document.getElementById('card-total-avaliacoes').textContent =
    formatarNumero(jogo.total_avaliacoes) + ' avaliações';
  document.getElementById('card-fonte').textContent   = jogo.fonte;
  document.getElementById('card-motivo').textContent  = jogo.motivo || '';

  /* Resetar overlays */
  $overlayLike.style.opacity    = '0';
  $overlayDislike.style.opacity = '0';

  /* Resetar animação de entrada do card */
  const $card = document.getElementById('card-jogo');
  $card.style.animation = 'none';
  void $card.offsetWidth;
  $card.style.animation = '';
}


/* ════════════════════════════════════════════════════════
   ATUALIZAR BADGE DE ESTRATÉGIA
════════════════════════════════════════════════════════ */
const NOMES_ESTRATEGIA = {
  aleatorio          : '🎲 Explorando',
  popular            : '📈 Por popularidade',
  conteudo           : '🧠 Pelo seu gosto',
  conteudo_avancado  : '🧠 Modo avançado',
};

function atualizarEstrategia() {
  const e = sessao.decidirEstrategia();
  $estrategiaTexto.textContent = NOMES_ESTRATEGIA[e] || e;
}


/* ════════════════════════════════════════════════════════
   CARREGAR PRÓXIMO JOGO
════════════════════════════════════════════════════════ */
function carregarProximoJogo() {
  jogoAtual = sessao.obterProximoJogo();

  if (!jogoAtual) {
    encerrarSessao();
    return;
  }

  renderizarCard(jogoAtual);
  atualizarEstrategia();
  bloqueado = false;
}


/* ════════════════════════════════════════════════════════
   AÇÕES: LIKE E DISLIKE
════════════════════════════════════════════════════════ */
function executarLike() {
  if (bloqueado || !jogoAtual) return;
  bloqueado = true;

  $overlayLike.style.opacity = '1';
  $cardContainer.classList.add('animando-like');

  sessao.registrarCurtida(jogoAtual.id);
  animarContador($valorLikes,  sessao.curtidos.length);
  animarContador($valorVistos, sessao.vistos.length);

  setTimeout(() => {
    $cardContainer.classList.remove('animando-like');

    if (sessao.curtidos.length > 0 && sessao.curtidos.length % 5 === 0) {
      exibirModalMatch();
    } else {
      carregarProximoJogo();
    }
  }, 480);
}

function executarDislike() {
  if (bloqueado || !jogoAtual) return;
  bloqueado = true;

  $overlayDislike.style.opacity = '1';
  $cardContainer.classList.add('animando-dislike');

  sessao.registrarRejeicao(jogoAtual.id);
  animarContador($valorDislikes, sessao.rejeitados.length);
  animarContador($valorVistos,   sessao.vistos.length);

  setTimeout(() => {
    $cardContainer.classList.remove('animando-dislike');
    carregarProximoJogo();
  }, 480);
}


/* ════════════════════════════════════════════════════════
   MODAL DE MATCH
════════════════════════════════════════════════════════ */
const MEDALHAS = ['🥇', '🥈', '🥉'];

function exibirModalMatch() {
  const generos        = sessao.obterGenerosFavoritos().slice(0, 3);
  const recomendacoes  = sessao.obterRecomendacoes(3);

  /* Gêneros favoritos */
  const $listaGeneros = document.getElementById('modal-lista-generos');
  $listaGeneros.innerHTML = '';
  generos.forEach(g => $listaGeneros.appendChild(criarTag(g, 'modal-genero-tag')));

  /* Recomendações */
  const $listaRec = document.getElementById('modal-lista-recomendacoes');
  $listaRec.innerHTML = '';
  recomendacoes.forEach((j, i) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="medalha">${MEDALHAS[i] || '▸'}</span>
      <span>${j.nome}</span>
      <span class="rec-genero">${j.generos[0]}</span>
    `;
    $listaRec.appendChild(li);
  });

  $modal.classList.remove('oculto');
  $modal.classList.add('visivel');
  document.getElementById('btn-fechar-modal').focus();
}

function fecharModalMatch() {
  $modal.classList.remove('visivel');
  $modal.classList.add('oculto');
  carregarProximoJogo();
}


/* ════════════════════════════════════════════════════════
   TELA DE RESUMO FINAL
════════════════════════════════════════════════════════ */
function encerrarSessao() {
  const generos       = sessao.obterGenerosFavoritos();
  const recomendacoes = sessao.obterRecomendacoes(5);
  const NUMS          = ['🥇', '🥈', '🥉', '4.', '5.'];

  /* Stats */
  document.getElementById('resumo-vistos').textContent    = sessao.vistos.length;
  document.getElementById('resumo-likes').textContent     = sessao.curtidos.length;
  document.getElementById('resumo-dislikes').textContent  = sessao.rejeitados.length;

  /* Gêneros favoritos */
  const $secaoGen = document.getElementById('resumo-secao-generos');
  if (generos.length > 0) {
    const $listaGen = document.getElementById('resumo-lista-generos');
    $listaGen.innerHTML = '';
    generos.slice(0, 5).forEach(g =>
      $listaGen.appendChild(criarTag(g, 'modal-genero-tag'))
    );
    $secaoGen.style.display = '';
  } else {
    $secaoGen.style.display = 'none';
  }

  /* Recomendações */
  const $listaRec = document.getElementById('resumo-lista-recomendacoes');
  $listaRec.innerHTML = '';

  if (recomendacoes.length > 0) {
    recomendacoes.forEach((j, i) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="medalha">${NUMS[i]}</span>
        <span class="recomendacao-nome">${j.nome}</span>
        <span class="recomendacao-genero">${j.generos[0]}</span>
      `;
      $listaRec.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'Interaja mais para receber recomendações personalizadas!';
    li.style.color = 'var(--texto-secundario)';
    li.style.fontStyle = 'italic';
    $listaRec.appendChild(li);
  }

  mostrarTela('resumo');
}


/* ════════════════════════════════════════════════════════
   INICIAR SESSÃO
════════════════════════════════════════════════════════ */
function iniciarSessao() {
  sessao.reiniciar();
  $valorLikes.textContent    = '0';
  $valorDislikes.textContent = '0';
  $valorVistos.textContent   = '0';
  mostrarTela('jogo');
  carregarProximoJogo();
}


/* ════════════════════════════════════════════════════════
   EVENTOS DE CLIQUE
════════════════════════════════════════════════════════ */
$btnIniciar    .addEventListener('click', iniciarSessao);
$btnLike       .addEventListener('click', executarLike);
$btnDislike    .addEventListener('click', executarDislike);
$btnEncerrar   .addEventListener('click', encerrarSessao);
$btnFecharModal.addEventListener('click', fecharModalMatch);
$btnReiniciar  .addEventListener('click', iniciarSessao);

/* Fechar modal clicando no overlay escuro */
document.querySelector('.modal-overlay').addEventListener('click', fecharModalMatch);


/* ════════════════════════════════════════════════════════
   EVENTOS DE TECLADO
════════════════════════════════════════════════════════ */
document.addEventListener('keydown', e => {
  const jogoAtivo = $telas.jogo.classList.contains('ativa');
  const modalAberto = $modal.classList.contains('visivel');

  if (jogoAtivo && !modalAberto) {
    if (e.key === 'ArrowRight' || e.key === 'l' || e.key === 'L') executarLike();
    if (e.key === 'ArrowLeft'  || e.key === 'd' || e.key === 'D') executarDislike();
    if (e.key === 'q'          || e.key === 'Q' || e.key === 'Escape') encerrarSessao();
  }

  if (modalAberto && (e.key === 'Enter' || e.key === 'Escape')) {
    fecharModalMatch();
  }
});
