/* Passo a passo animado do Álgebra em Cena.
 * Lê o trace (RN-013) do <script type="application/json" id="trace-data"> e desenha cada passo
 * em dois quadrantes: a matriz (cena) e a conta. Não recalcula nada: o trace é o contrato único
 * (ADR-001). Sem estilo inline (CSP): cores por classe; geometria só via CSSOM. */
(function () {
  'use strict';

  const dados = document.getElementById('trace-data');
  const cena = document.getElementById('cena');
  const conta = document.getElementById('conta');
  if (!dados || !cena || !conta) return;

  const trace = JSON.parse(dados.textContent);
  const passos = trace.passos;
  const reduzMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const T = reduzMovimento ? 0 : 1;            // multiplicador de tempo
  const SVG = 'http://www.w3.org/2000/svg';
  const AUMENTADA = new Set(['forma_matricial', 'operacao_elementar', 'forma_escalonada', 'forma_reduzida']);
  const SECOES = { inicio: 'Sistema', cramer: 'Cramer', escalonamento: 'Escalonamento', resultado: 'Resultado' };
  const rotulos = trace.entrada.rotulos;

  const el = {
    titulo: document.getElementById('cena-titulo'),
    matriz: document.getElementById('cena-matriz'),
    produtos: document.getElementById('cena-produtos'),
    envoltorio: document.getElementById('cena-envoltorio'),
    svg: document.getElementById('cena-diagonais'),
    painel: document.getElementById('cena-painel'),
    destaque: document.getElementById('cena-destaque'),
    texto: document.getElementById('cena-texto'),
    itens: document.getElementById('cena-itens'),
    contador: document.getElementById('cena-contador'),
    barra: document.getElementById('cena-barra'),
    secoes: document.getElementById('cena-secoes'),
    inicio: document.getElementById('btn-inicio'),
    anterior: document.getElementById('btn-anterior'),
    tocar: document.getElementById('btn-tocar'),
    proximo: document.getElementById('btn-proximo'),
    fim: document.getElementById('btn-fim'),
  };

  let atual = 0;
  let geracao = 0;          // invalida timers de passos anteriores
  let tocando = false;
  let timerTocar = null;

  /* ---------- utilidades ---------- */
  const fmt = (v) => String(v).replace(/-/g, '−');
  const comSinal = (v) => (String(v).startsWith('-') ? fmt(v) : '+' + v);
  const semSinal = (v) => String(v).replace(/^-/, '');
  function criar(tag, classes, texto) {
    const n = document.createElement(tag);
    if (classes) n.className = classes;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }
  function depois(ms, fn) {
    const g = geracao;
    return new Promise((resolve) => {
      window.setTimeout(() => { if (g === geracao) { if (fn) fn(); resolve(true); } else { resolve(false); } }, ms * T);
    });
  }
  function limpar(no) { while (no.firstChild) no.removeChild(no.firstChild); }

  /* ---------- matriz ---------- */
  function desenharMatriz(passo, matriz, papeis, opcoes) {
    opcoes = opcoes || {};
    limpar(el.matriz);
    limpar(el.svg);
    limpar(el.painel);
    limpar(el.produtos);
    el.produtos.hidden = true;
    el.cabecalho = [];
    if (!matriz) {
      el.envoltorio.hidden = true;
      el.painel.hidden = false;
      return null;
    }
    el.envoltorio.hidden = false;
    el.painel.hidden = true;
    const colunas = matriz[0].length;
    const aumentada = AUMENTADA.has(passo.tipo);
    const copias = new Set(passo.copias || []);
    el.matriz.style.gridTemplateColumns = 'auto repeat(' + colunas + ', auto)';

    el.cabecalho.push(el.matriz.appendChild(criar('span', 'rl')));
    for (let j = 0; j < colunas; j++) {
      const papel = papeis[j];
      let rotulo = papel === 'k' ? 'K' : (rotulos[['x', 'y', 'z'].indexOf(papel)] || papel);
      if (opcoes.colunaSubstituida === j) rotulo = 'K → C' + (j + 1);
      const hd = criar('span', 'hd col-' + papel + '-texto' + (copias.has(j) ? ' copia' : ''), rotulo);
      if (aumentada && j === colunas - 1) hd.classList.add('separador');
      el.cabecalho.push(el.matriz.appendChild(hd));
    }

    const papelLinha = {};
    (opcoes.linhas || []).forEach((l) => { papelLinha[l.indice] = l.papel; });
    const pivos = new Set((opcoes.pivos || []).map((p) => p[0] + ':' + p[1]));
    const celulas = [];
    matriz.forEach((linha, i) => {
      const papel = papelLinha[i];
      let rotuloLinha = 'L' + (i + 1);
      if (papel === 'pivo') rotuloLinha += ' (pivô)';
      if (papel === 'alvo') rotuloLinha += ' ←';
      if (papel === 'contradicao') rotuloLinha += ' (0 = c)';
      el.matriz.appendChild(criar('span', 'rl' + (papel === 'pivo' || papel === 'alvo' ? ' ativo' : ''), rotuloLinha));
      const linhaCelulas = [];
      linha.forEach((valor, j) => {
        const c = criar('span', 'celula col-' + papeis[j], fmt(valor));
        if (copias.has(j)) c.classList.add('copia');
        if (aumentada && j === colunas - 1) c.classList.add('separador');
        if (papel) c.classList.add('linha-' + papel);
        if (pivos.has(i + ':' + j)) c.classList.add('celula-pivo');
        if (opcoes.colunaSubstituida === j) c.classList.add('substituida');
        c.setAttribute('aria-label', 'Linha ' + (i + 1) + ', coluna ' + (j + 1) + ': ' + fmt(valor));
        el.matriz.appendChild(c);
        linhaCelulas.push(c);
      });
      celulas.push(linhaCelulas);
    });
    return celulas;
  }

  /* Linhas de resultado abaixo das diagonais, fora dos colchetes (como no caderno): cada produto fica
   * sob a coluna onde a diagonal termina. 3×3: uma linha para as descendentes (+) e outra para as
   * ascendentes (−); 2×2: uma linha só. A grade copia as larguras das colunas da matriz. */
  function desenharProdutos(passo) {
    const colunas = passo.matriz[0].length;
    const grupos = passo.matriz.length === 3 ? ['+', '-'] : ['*'];
    const resultados = new Array(passo.diagonais.length);
    el.produtos.hidden = false;
    el.produtos.style.gridTemplateColumns = el.cabecalho
      .map((c) => Math.ceil(c.getBoundingClientRect().width) + 'px').join(' ');
    grupos.forEach((grupo) => {
      const rotulo = grupo === '+' ? '+' : (grupo === '-' ? '\u2212' : '');
      const classe = grupo === '+' ? ' mais' : (grupo === '-' ? ' menos' : '');
      el.produtos.appendChild(criar('span', 'rl rl-produto' + classe, rotulo));
      const linha = [];
      for (let j = 0; j < colunas; j++) linha.push(el.produtos.appendChild(criar('span', 'produto produto-vazio')));
      passo.diagonais.forEach((d, indice) => {
        if (grupo !== '*' && d.sinal !== grupo) return;
        const celula = linha[d.celulas[d.celulas.length - 1][1]];
        celula.className = 'produto ' + (d.sinal === '+' ? 'mais' : 'menos') + ' oculto';
        celula.textContent = comSinal(d.contribuicao);
        celula.setAttribute('aria-label', 'Resultado da diagonal: ' + comSinal(d.contribuicao));
        resultados[indice] = celula;
      });
    });
    return resultados;
  }

  function centro(no) {
    const base = el.envoltorio.getBoundingClientRect();
    const r = no.getBoundingClientRect();
    return { x: r.left - base.left + r.width / 2 + el.envoltorio.scrollLeft, y: r.top - base.top + r.height / 2 };
  }

  function tracarDiagonal(celulas, diagonal, animar) {
    const pontos = diagonal.celulas.map(([i, j]) => centro(celulas[i][j]));
    const ini = pontos[0];
    const fim = pontos[pontos.length - 1];
    const linha = document.createElementNS(SVG, 'line');
    linha.setAttribute('x1', ini.x); linha.setAttribute('y1', ini.y);
    linha.setAttribute('x2', fim.x); linha.setAttribute('y2', fim.y);
    linha.setAttribute('pathLength', '1');
    linha.setAttribute('class', (diagonal.sinal === '+' ? 'mais' : 'menos') + (animar ? ' desenhando' : ''));
    el.svg.appendChild(linha);
  }

  function item(texto, classes) {
    const li = criar('li', classes || '', texto);
    if (T) li.classList.add('novo');
    el.itens.appendChild(li);
    return li;
  }

  function painel(no) { el.painel.appendChild(no); return no; }

  /* ---------- desenho por tipo de passo ---------- */
  const desenhar = {
    forma_matricial(p) {
      desenharMatriz(p, p.matriz, p.papeis);
      p.equacoes.forEach((eq, i) => item('L' + (i + 1) + ':  ' + eq));
    },

    async determinante(p, animar) {
      const celulas = desenharMatriz(p, p.matriz, p.papeis);
      const resultados = desenharProdutos(p);
      const valor = el.destaque.appendChild(criar('span', 'valor-grande', p.rotulo + ' = ?'));
      for (let k = 0; k < p.diagonais.length; k++) {
        const d = p.diagonais[k];
        if (animar && !(await depois(650))) return;
        const classe = d.sinal === '+' ? 'em-produto-mais' : 'em-produto-menos';
        d.celulas.forEach(([i, j]) => celulas[i][j].classList.add(classe));
        tracarDiagonal(celulas, d, animar);
        resultados[k].classList.remove('oculto');
        if (animar) resultados[k].classList.add('novo');
        item((d.sinal === '+' ? '+  ' : '−  ') + d.texto, d.sinal === '+' ? 'mais' : 'menos');
        if (animar && !(await depois(450))) return;
        d.celulas.forEach(([i, j]) => celulas[i][j].classList.remove(classe));
      }
      if (animar && !(await depois(400))) return;
      const mais = p.diagonais.filter((d) => d.sinal === '+').map((d) => comSinal(d.contribuicao));
      const menos = p.diagonais.filter((d) => d.sinal === '-').map((d) => comSinal(d.contribuicao));
      item('Soma (+): ' + mais.join(' ') + ' = ' + fmt(p.soma_mais), 'mais');
      item('Soma (−): ' + menos.join(' ') + ' = ' + fmt(p.soma_menos), 'menos');
      const sinal = String(p.soma_menos).startsWith('-') ? ' − ' : ' + ';
      item(p.rotulo + ' = ' + fmt(p.soma_mais) + sinal + semSinal(p.soma_menos) + ' = ' + fmt(p.valor), 'total');
      valor.textContent = p.rotulo + ' = ' + fmt(p.valor);
    },

    async substituir_coluna(p, animar) {
      const j = p.coluna;
      el.destaque.appendChild(criar('span', 'notacao', 'C' + (j + 1) + ' → K'));
      if (!animar) {
        desenharMatriz(p, p.matriz, p.papeis, { colunaSubstituida: j });
        return;
      }
      const papeisAntes = p.papeis.slice();
      papeisAntes[j] = p.papel_original;
      const celulas = desenharMatriz(p, p.matriz_antes, papeisAntes);
      if (!(await depois(700))) return;
      celulas.forEach((linha) => linha[j].classList.add('saindo'));
      if (!(await depois(500))) return;
      const novas = desenharMatriz(p, p.matriz, p.papeis, { colunaSubstituida: j });
      novas.forEach((linha) => linha[j].classList.add('entrando'));
    },

    quocientes(p) {
      desenharMatriz(p, null);
      const lista = painel(criar('ul', 'painel-lista'));
      p.itens.forEach((it) => {
        lista.appendChild(criar('li', 'conjunto', rotulos[it.variavel] + ' = ' + fmt(it.valor)));
        item(it.texto, 'total');
      });
    },

    aviso(p) {
      desenharMatriz(p, null);
      painel(criar('div', 'aviso-cena', p.titulo));
    },

    async operacao_elementar(p, animar) {
      const op = p.operacao;
      const linhas = p.linhas;
      el.destaque.appendChild(criar('span', 'notacao', p.notacao));
      if (!animar) {
        desenharMatriz(p, p.matriz, p.papeis, { linhas });
        return;
      }
      desenharMatriz(p, p.matriz_antes, p.papeis, { linhas });
      if (!(await depois(900))) return;
      const celulas = desenharMatriz(p, p.matriz, p.papeis, { linhas });
      const mudaram = op.codigo === 'E1' ? [op.alvo, op.pivo] : [op.alvo];
      mudaram.forEach((i) => celulas[i].forEach((c) => c.classList.add('mudando')));
    },

    forma_escalonada(p) {
      desenharMatriz(p, p.matriz, p.papeis, { linhas: p.linhas, pivos: p.pivos });
    },

    forma_reduzida(p) {
      desenharMatriz(p, p.matriz, p.papeis, { linhas: p.linhas, pivos: p.pivos });
    },

    classificacao(p) {
      desenharMatriz(p, null);
      painel(criar('span', 'selo selo-grande selo-' + p.valor, p.valor));
      item('posto(A) = ' + p.posto_A + '   posto([A|K]) = ' + p.posto_AK);
    },

    solucao(p) {
      desenharMatriz(p, null);
      painel(criar('span', 'conjunto', p.conjunto));
      p.itens.forEach((it) => item(it.texto));
    },

    async verificacao(p, animar) {
      desenharMatriz(p, null);
      painel(criar('span', 'conjunto ' + (p.ok ? 'texto-ok' : 'texto-falha'),
        p.ok ? '✓ Todas as equações conferem' : '✗ Alguma equação não confere'));
      for (const it of p.itens) {
        if (animar && !(await depois(500))) return;
        item(it.texto, it.ok ? 'ok' : 'falha');
      }
    },
  };

  /* ---------- navegação ---------- */
  function montarSecoes() {
    const vistas = new Set();
    passos.forEach((p, indice) => {
      if (vistas.has(p.secao)) return;
      vistas.add(p.secao);
      const b = criar('button', 'btn btn-outline-secondary', SECOES[p.secao] || p.secao);
      b.type = 'button';
      b.dataset.secao = p.secao;
      b.addEventListener('click', () => { parar(); ir(indice); });
      el.secoes.appendChild(b);
    });
  }

  function atualizarControles() {
    const p = passos[atual];
    el.contador.textContent = 'Passo ' + (atual + 1) + ' de ' + passos.length;
    el.barra.style.width = ((atual + 1) / passos.length * 100) + '%';
    el.anterior.disabled = atual === 0;
    el.inicio.disabled = atual === 0;
    el.proximo.disabled = atual === passos.length - 1;
    el.fim.disabled = atual === passos.length - 1;
    document.querySelectorAll('.metodo-passo').forEach((bloco) => {
      bloco.classList.toggle('atual', Number(bloco.dataset.passo) === p.id);
    });
    el.secoes.querySelectorAll('button').forEach((b) => {
      if (b.dataset.secao === p.secao) b.setAttribute('aria-current', 'step');
      else b.removeAttribute('aria-current');
    });
  }

  async function ir(indice, animar) {
    if (animar === undefined) animar = true;
    geracao += 1;
    atual = Math.max(0, Math.min(passos.length - 1, indice));
    const p = passos[atual];
    limpar(el.destaque);
    limpar(el.itens);
    el.titulo.textContent = p.titulo;
    /* No determinante, a lista de contas já detalha cada diagonal: o texto fica só com a regra. */
    el.texto.textContent = p.tipo === 'determinante'
      ? (p.matriz.length === 3
        ? 'Sarrus: some as diagonais descendentes (+) e subtraia as ascendentes (\u2212).'
        : 'Diagonal principal (+) menos diagonal secundária (\u2212).')
      : p.texto;
    atualizarControles();
    const fn = desenhar[p.tipo];
    const g = geracao;
    if (fn) await fn(p, animar && T > 0);
    if (tocando && g === geracao) agendarProximo();
  }

  function agendarProximo() {
    window.clearTimeout(timerTocar);
    if (atual >= passos.length - 1) { parar(); return; }
    timerTocar = window.setTimeout(() => ir(atual + 1), 2600);
  }

  function tocar() {
    tocando = true;
    el.tocar.setAttribute('aria-label', 'Pausar');
    el.tocar.querySelector('i').className = 'bi bi-pause-fill';
    if (atual >= passos.length - 1) ir(0); else ir(atual + 1);
  }

  function parar() {
    tocando = false;
    window.clearTimeout(timerTocar);
    el.tocar.setAttribute('aria-label', 'Reproduzir automaticamente');
    el.tocar.querySelector('i').className = 'bi bi-play-fill';
  }

  el.inicio.addEventListener('click', () => { parar(); ir(0); });
  el.anterior.addEventListener('click', () => { parar(); ir(atual - 1); });
  el.proximo.addEventListener('click', () => { parar(); ir(atual + 1); });
  el.fim.addEventListener('click', () => { parar(); ir(passos.length - 1); });
  el.tocar.addEventListener('click', () => (tocando ? parar() : tocar()));

  document.addEventListener('keydown', (ev) => {
    const alvo = ev.target;
    if (alvo.closest && alvo.closest('input, select, textarea, [contenteditable]')) return;
    if (ev.key === 'ArrowRight') { ev.preventDefault(); parar(); ir(atual + 1); }
    else if (ev.key === 'ArrowLeft') { ev.preventDefault(); parar(); ir(atual - 1); }
    else if (ev.key === ' ' && !(alvo.closest && alvo.closest('button, a, summary'))) {
      ev.preventDefault(); if (tocando) parar(); else tocar();
    }
  });

  let timerRedimensionar = null;
  window.addEventListener('resize', () => {
    window.clearTimeout(timerRedimensionar);
    timerRedimensionar = window.setTimeout(() => ir(atual, false), 150);
  });

  cena.hidden = false;
  conta.hidden = false;
  montarSecoes();
  ir(0);

  /* No celular/tablet os quadrantes se empilham: depois de resolver, mostrar direto a matriz. */
  if (window.location.search && window.matchMedia('(max-width: 1199.98px)').matches) {
    document.getElementById('q-cena').scrollIntoView({ block: 'start' });
  }
})();
