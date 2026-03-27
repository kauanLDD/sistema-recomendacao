/** interface.js — DOM, eventos e animações do SteamMatch */

/* DOM */
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

let jogoAtual = null;
let bloqueado = false;


/* Utilitários */
function formatarNumero(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000)     return Math.round(n / 1_000) + 'K';
  return String(n);
}

function mostrarTela(nome) {
  Object.entries($telas).forEach(([key, el]) => {
    el.classList.toggle('ativa',  key === nome);
    el.classList.toggle('oculta', key !== nome);
  });
}

function animarContador(elemento, valor) {
  elemento.textContent = valor;
  elemento.classList.remove('bounce');
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

function mostrarErroCard(msg) {
  const $card = document.getElementById('card-jogo');
  $card.innerHTML = `
    <div style="text-align:center;padding:3rem 2rem;color:var(--vermelho-dislike)">
      <p style="font-size:2rem;margin-bottom:1rem">⚠️</p>
      <p style="font-weight:600;margin-bottom:.5rem">Erro de conexão</p>
      <p style="color:var(--texto-secundario);font-size:.9rem">${msg}</p>
    </div>`;
  bloqueado = false;
}


/* Renderizar card */
function renderizarCard(jogo) {
  document.getElementById('card-nome').textContent = jogo.nome;

  const $generos = document.getElementById('card-generos');
  $generos.innerHTML = '';
  jogo.generos.forEach(g => $generos.appendChild(criarTag(g)));

  document.getElementById('card-descricao').textContent = jogo.descricao;

  const $barra = document.getElementById('card-barra-avaliacao');
  $barra.style.width = '0%';
  if (jogo.avaliacao >= 80) {
    $barra.style.background = 'linear-gradient(90deg, #4caf50, #81c784)';
  } else if (jogo.avaliacao >= 60) {
    $barra.style.background = 'linear-gradient(90deg, #ff9800, #ffb74d)';
  } else {
    $barra.style.background = 'linear-gradient(90deg, #f44336, #e57373)';
  }
  requestAnimationFrame(() => requestAnimationFrame(() => {
    $barra.style.width = jogo.avaliacao + '%';
  }));

  document.getElementById('card-avaliacao-valor').textContent = jogo.avaliacao + '%';
  document.getElementById('card-total-avaliacoes').textContent =
    formatarNumero(jogo.total_avaliacoes) + ' avaliações';
  document.getElementById('card-fonte').textContent  = jogo.fonte;
  document.getElementById('card-motivo').textContent = jogo.motivo || '';

  $overlayLike.style.opacity    = '0';
  $overlayDislike.style.opacity = '0';

  /* Reinicia animação de entrada */
  const $card = document.getElementById('card-jogo');
  $card.style.animation = 'none';
  void $card.offsetWidth;
  $card.style.animation = '';
}


/* Badge de estratégia */
const NOMES_ESTRATEGIA = {
  aleatorio : '🎲 Explorando',
  popular   : '📈 Por popularidade',
  conteudo  : '🧠 Pelo seu gosto',
};

function atualizarEstrategia() {
  const e = sessao.decidirEstrategia();
  $estrategiaTexto.textContent = NOMES_ESTRATEGIA[e] || e;
}


/* Carregar próximo jogo */
async function carregarProximoJogo() {
  bloqueado = true;
  try {
    jogoAtual = await sessao.obterProximoJogo();
  } catch {
    mostrarErroCard('Verifique se o servidor está rodando: python api.py');
    return;
  }

  if (!jogoAtual) {
    await encerrarSessao();
    return;
  }

  renderizarCard(jogoAtual);
  atualizarEstrategia();
  bloqueado = false;
}


/* Like */
function executarLike() {
  if (bloqueado || !jogoAtual) return;
  bloqueado = true;

  $overlayLike.style.opacity = '1';
  $cardContainer.classList.add('animando-like');

  sessao.registrarCurtida(jogoAtual.nome, jogoAtual.generos);
  animarContador($valorLikes,  sessao.curtidos.length);
  animarContador($valorVistos, sessao.vistos.length);

  setTimeout(async () => {
    $cardContainer.classList.remove('animando-like');
    if (sessao.curtidos.length > 0 && sessao.curtidos.length % 5 === 0) {
      await exibirModalMatch();
    } else {
      await carregarProximoJogo();
    }
  }, 480);
}


/* Dislike */
function executarDislike() {
  if (bloqueado || !jogoAtual) return;
  bloqueado = true;

  $overlayDislike.style.opacity = '1';
  $cardContainer.classList.add('animando-dislike');

  sessao.registrarRejeicao(jogoAtual.nome);
  animarContador($valorDislikes, sessao.rejeitados.length);
  animarContador($valorVistos,   sessao.vistos.length);

  setTimeout(async () => {
    $cardContainer.classList.remove('animando-dislike');
    await carregarProximoJogo();
  }, 480);
}


/* Modal de match */
const MEDALHAS = ['🥇', '🥈', '🥉'];

async function exibirModalMatch() {
  const generos = sessao.obterGenerosFavoritos().slice(0, 3);

  const $listaGeneros = document.getElementById('modal-lista-generos');
  $listaGeneros.innerHTML = '';
  generos.forEach(g => $listaGeneros.appendChild(criarTag(g, 'modal-genero-tag')));

  const $listaRec = document.getElementById('modal-lista-recomendacoes');
  $listaRec.innerHTML = '<li style="color:var(--texto-secundario)">Carregando...</li>';

  $modal.classList.remove('oculto');
  $modal.classList.add('visivel');
  document.getElementById('btn-fechar-modal').focus();

  try {
    const recomendacoes = await sessao.obterRecomendacoes(3);
    $listaRec.innerHTML = '';
    recomendacoes.forEach((j, i) => {
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="medalha">${MEDALHAS[i] || '▸'}</span>
        <span>${j.nome}</span>
        <span class="rec-genero">${j.generos[0] || ''}</span>
      `;
      $listaRec.appendChild(li);
    });
  } catch {
    $listaRec.innerHTML = '<li style="color:var(--texto-secundario)">Não foi possível carregar.</li>';
  }
}

async function fecharModalMatch() {
  $modal.classList.remove('visivel');
  $modal.classList.add('oculto');
  await carregarProximoJogo();
}


/* Tela de resumo final */
async function encerrarSessao() {
  const NUMS = ['🥇', '🥈', '🥉', '4.', '5.'];

  document.getElementById('resumo-vistos').textContent   = sessao.vistos.length;
  document.getElementById('resumo-likes').textContent    = sessao.curtidos.length;
  document.getElementById('resumo-dislikes').textContent = sessao.rejeitados.length;

  /* Gêneros favoritos (calculados localmente) */
  const generos = sessao.obterGenerosFavoritos();
  const $secaoGen = document.getElementById('resumo-secao-generos');
  if (generos.length > 0) {
    const $lista = document.getElementById('resumo-lista-generos');
    $lista.innerHTML = '';
    generos.slice(0, 5).forEach(g => $lista.appendChild(criarTag(g, 'modal-genero-tag')));
    $secaoGen.style.display = '';
  } else {
    $secaoGen.style.display = 'none';
  }

  /* Mostra a tela com loading e preenche as recomendações quando chegarem */
  const $listaRec = document.getElementById('resumo-lista-recomendacoes');
  $listaRec.innerHTML = '<li style="color:var(--texto-secundario)">Carregando recomendações...</li>';
  mostrarTela('resumo');

  try {
    const recomendacoes = await sessao.obterRecomendacoes(5);
    $listaRec.innerHTML = '';
    if (recomendacoes.length > 0) {
      recomendacoes.forEach((j, i) => {
        const li = document.createElement('li');
        li.innerHTML = `
          <span class="medalha">${NUMS[i]}</span>
          <span class="recomendacao-nome">${j.nome}</span>
          <span class="recomendacao-genero">${j.generos[0] || ''}</span>
        `;
        $listaRec.appendChild(li);
      });
    } else {
      $listaRec.innerHTML =
        '<li style="color:var(--texto-secundario);font-style:italic">Interaja mais para receber recomendações personalizadas!</li>';
    }
  } catch {
    $listaRec.innerHTML =
      '<li style="color:var(--vermelho-dislike)">Não foi possível carregar recomendações.</li>';
  }
}


/* Iniciar sessão */
async function iniciarSessao() {
  sessao.reiniciar();
  $valorLikes.textContent    = '0';
  $valorDislikes.textContent = '0';
  $valorVistos.textContent   = '0';
  mostrarTela('jogo');
  await carregarProximoJogo();
}


/* Eventos de clique */
$btnIniciar    .addEventListener('click', iniciarSessao);
$btnLike       .addEventListener('click', executarLike);
$btnDislike    .addEventListener('click', executarDislike);
$btnEncerrar   .addEventListener('click', encerrarSessao);
$btnFecharModal.addEventListener('click', fecharModalMatch);
$btnReiniciar  .addEventListener('click', iniciarSessao);

document.querySelector('.modal-overlay').addEventListener('click', fecharModalMatch);


/* Teclado */
document.addEventListener('keydown', e => {
  const jogoAtivo   = $telas.jogo.classList.contains('ativa');
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
