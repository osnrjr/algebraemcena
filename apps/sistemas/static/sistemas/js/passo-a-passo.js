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

  /* Traz `alvo` para a vista rolando SÓ o 3º quadrante (RN-028). Se a conta não tem rolagem
     própria (quadrantes empilhados), não mexe em nada: a página nunca sai da matriz sozinha. */
  function rolarNaConta(alvo) {
    const caixa = alvo && alvo.closest('.conta');
    if (!caixa || caixa.scrollHeight <= caixa.clientHeight + 1) return;
    const r = alvo.getBoundingClientRect();
    const c = caixa.getBoundingClientRect();
    const folga = 8;
    let delta = 0;
    if (r.top < c.top + folga) delta = r.top - c.top - folga;
    else if (r.bottom > c.bottom - folga) delta = Math.min(r.bottom - c.bottom + folga, r.top - c.top - folga);
    if (delta) caixa.scrollBy({ top: delta, behavior: reduzMovimento ? 'auto' : 'smooth' });
  }

  function destacarLinhaMetodo(indiceLinha) {
    const bloco = document.querySelector('.metodo-passo.atual');
    if (!bloco) return;
    const lis = bloco.querySelectorAll('.metodo-linhas li');
    lis.forEach((li, idx) => {
      const eAtiva = idx === indiceLinha;
      li.classList.toggle('linha-em-execucao', eAtiva);
      if (eAtiva && !document.body.classList.contains('modo-dividido')) rolarNaConta(li);
    });
  }

  /* ---------- desenho por tipo de passo ---------- */
  const desenhar = {
    async forma_matricial(p, animar) {
      desenharMatriz(p, p.matriz, p.papeis);
      for (let i = 0; i < p.equacoes.length; i++) {
        destacarLinhaMetodo(i);
        item('L' + (i + 1) + ':  ' + p.equacoes[i]);
        if (animar && !(await depois(350))) return;
      }
    },

    async determinante(p, animar) {
      const celulas = desenharMatriz(p, p.matriz, p.papeis);
      const resultados = desenharProdutos(p);
      const valor = el.destaque.appendChild(criar('span', 'valor-grande', p.rotulo + ' = ?'));
      for (let k = 0; k < p.diagonais.length; k++) {
        const d = p.diagonais[k];
        destacarLinhaMetodo(k);
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
      const idxMais = p.diagonais.length;
      destacarLinhaMetodo(idxMais);
      if (animar && !(await depois(400))) return;
      const mais = p.diagonais.filter((d) => d.sinal === '+').map((d) => comSinal(d.contribuicao));
      const menos = p.diagonais.filter((d) => d.sinal === '-').map((d) => comSinal(d.contribuicao));
      item('Soma (+): ' + mais.join(' ') + ' = ' + fmt(p.soma_mais), 'mais');

      const idxMenos = idxMais + 1;
      destacarLinhaMetodo(idxMenos);
      if (animar && !(await depois(400))) return;
      item('Soma (−): ' + menos.join(' ') + ' = ' + fmt(p.soma_menos), 'menos');

      const idxTotal = idxMenos + 1;
      destacarLinhaMetodo(idxTotal);
      const sinal = String(p.soma_menos).startsWith('-') ? ' − ' : ' + ';
      item(p.rotulo + ' = ' + fmt(p.soma_mais) + sinal + semSinal(p.soma_menos) + ' = ' + fmt(p.valor), 'total');
      valor.textContent = p.rotulo + ' = ' + fmt(p.valor);
    },

    async substituir_coluna(p, animar) {
      destacarLinhaMetodo(0);
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

    async quocientes(p, animar) {
      desenharMatriz(p, null);
      const lista = painel(criar('ul', 'painel-lista'));
      for (let i = 0; i < p.itens.length; i++) {
        const it = p.itens[i];
        destacarLinhaMetodo(i);
        lista.appendChild(criar('li', 'conjunto', rotulos[it.variavel] + ' = ' + fmt(it.valor)));
        item(it.texto, 'total');
        if (animar && !(await depois(450))) return;
      }
    },

    aviso(p) {
      destacarLinhaMetodo(0);
      desenharMatriz(p, null);
      painel(criar('div', 'aviso-cena', p.titulo));
    },

    async operacao_elementar(p, animar) {
      destacarLinhaMetodo(0);
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
      destacarLinhaMetodo(0);
      desenharMatriz(p, p.matriz, p.papeis, { linhas: p.linhas, pivos: p.pivos });
    },

    forma_reduzida(p) {
      destacarLinhaMetodo(0);
      desenharMatriz(p, p.matriz, p.papeis, { linhas: p.linhas, pivos: p.pivos });
    },

    classificacao(p) {
      destacarLinhaMetodo(0);
      desenharMatriz(p, null);
      painel(criar('span', 'selo selo-grande selo-' + p.valor, p.valor));
      item('posto(A) = ' + p.posto_A + '   posto([A|K]) = ' + p.posto_AK);
    },

    solucao(p) {
      destacarLinhaMetodo(0);
      desenharMatriz(p, null);
      const formal = p.formal;                         // RN-029: termos formais do conjunto solução
      if (formal) painel(criar('span', 'quantidade-solucao', formal.quantidade));
      painel(criar('span', 'conjunto', p.conjunto));
      if (formal) formal.formas.slice(1).forEach((f) => painel(criar('span', 'conjunto conjunto-alt', 'ou ' + f)));
      p.itens.forEach((it) => item(it.texto));
      if (formal) item(formal.nota, 'nota');
    },

    async verificacao(p, animar) {
      desenharMatriz(p, null);
      painel(criar('span', 'conjunto ' + (p.ok ? 'texto-ok' : 'texto-falha'),
        p.ok ? '✓ Todas as equações conferem' : '✗ Alguma equação não confere'));
      for (let i = 0; i < p.itens.length; i++) {
        destacarLinhaMetodo(i);
        if (animar && !(await depois(500))) return;
        item(p.itens[i].texto, p.itens[i].ok ? 'ok' : 'falha');
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

    // Colapsa os métodos que não estão em destaque e expande apenas o método atual
    document.querySelectorAll('.resolucao-metodos details.metodo').forEach((det) => {
      det.open = (det.dataset.secao === p.secao);
    });

    // Destaca em azul apenas o passo em resolução e colapsa os demais
    let blocoAtivo = null;
    document.querySelectorAll('.metodo-passo').forEach((bloco) => {
      const eAtual = Number(bloco.dataset.passo) === p.id;
      bloco.classList.toggle('atual', eAtual);
      if (eAtual) blocoAtivo = bloco;
    });

    if (document.body.classList.contains('modo-dividido')) {
      // Tela dividida: a metade de baixo abre na explicação do passo; o histórico fica abaixo.
      const caixa = document.querySelector('#q-conta .conta');
      if (caixa) caixa.scrollTo({ top: 0, behavior: reduzMovimento ? 'auto' : 'smooth' });
    } else if (blocoAtivo) {
      rolarNaConta(blocoAtivo);
    }

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
    destacarLinhaMetodo(-1);
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

  function atualizarBotaoResolver(estaTocando) {
    const btn = document.getElementById('btn-resolver');
    if (!btn) return;
    const icone = btn.querySelector('i');
    const rotulo = btn.querySelector('.rotulo-resolver') || btn;
    const btnParar = document.getElementById('btn-parar');
    if (estaTocando) {
      btn.classList.add('tocando');
      if (icone) icone.className = 'bi bi-pause-fill';
      btn.setAttribute('aria-label', 'Pausar passo a passo');
      if (rotulo && rotulo !== btn) rotulo.textContent = 'Pausar';
      if (btnParar) btnParar.classList.remove('d-none');
    } else {
      btn.classList.remove('tocando');
      if (icone) icone.className = 'bi bi-play-fill';
      btn.setAttribute('aria-label', 'Reproduzir passo a passo');
      if (rotulo && rotulo !== btn) {
        rotulo.textContent = (atual > 0 && atual < passos.length - 1) ? 'Continuar' : 'Resolver';
      }
      if (btnParar && (atual > 0 || (cena && !cena.hidden))) {
        btnParar.classList.remove('d-none');
      }
    }
  }

  function tocar() {
    tocando = true;
    el.tocar.setAttribute('aria-label', 'Pausar');
    el.tocar.querySelector('i').className = 'bi bi-pause-fill';
    if (typeof window.__travarPrimeiroQuadrante === 'function') window.__travarPrimeiroQuadrante(true);
    const btnParar = document.getElementById('btn-parar');
    if (btnParar) btnParar.classList.remove('d-none');
    atualizarBotaoResolver(true);
    if (atual >= passos.length - 1) ir(0); else ir(atual + 1);
  }

  function parar() {
    tocando = false;
    window.clearTimeout(timerTocar);
    el.tocar.setAttribute('aria-label', 'Reproduzir automaticamente');
    el.tocar.querySelector('i').className = 'bi bi-play-fill';
    atualizarBotaoResolver(false);
  }

  el.inicio.addEventListener('click', () => { parar(); ir(0); });
  el.anterior.addEventListener('click', () => { parar(); ir(atual - 1); });
  el.proximo.addEventListener('click', () => { parar(); ir(atual + 1); });
  el.fim.addEventListener('click', () => { parar(); ir(passos.length - 1); });
  el.tocar.addEventListener('click', () => (tocando ? parar() : tocar()));

  document.querySelectorAll('.metodo-passo').forEach((bloco) => {
    bloco.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const num = Number(bloco.dataset.passo);
      const idx = passos.findIndex((s) => s.id === num);
      if (idx !== -1) {
        parar();
        ir(idx);
      }
    });
    bloco.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        bloco.click();
      }
    });
  });

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
  atualizarBotaoResolver(false);

  window.__passoAPasso = { parar, tocar, ir };
  // No carregamento inicial (ex.: F5), mantém os campos destravados para permitir alteração
  if (typeof window.__travarPrimeiroQuadrante === 'function') {
    window.__travarPrimeiroQuadrante(false);
  }

  /* Autoplay automático se solicitado pelo formulário/URL */
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('autoplay') === '1') {
    window.setTimeout(() => {
      if (!tocando) tocar();
    }, 600);
    const url = new URL(window.location.href);
    url.searchParams.delete('autoplay');
    const restante = url.searchParams.toString();
    window.history.replaceState({}, '', url.pathname + (restante ? '?' + restante : ''));
  }

  /* ---------- Celular e tablet em pé: tela dividida (RN-028) ----------
     Matriz fixa na metade de cima, conta rolando na de baixo. Em pé com altura suficiente;
     deitado ou baixo demais, os quadrantes continuam empilhados (e a página não salta). */
  const telaDividida = window.matchMedia('(max-width: 1199.98px) and (min-height: 540px)');
  const telaEmpilhada = window.matchMedia('(max-width: 1199.98px)');
  const corpo = document.body;
  // Lápis no cabeçalho da cena: editar o sistema; botão no formulário: voltar ao passo a passo.
  const atalhos = document.querySelectorAll('[data-vista]');

  function mostrarVista(vista) {
    corpo.classList.toggle('vista-sistema', vista === 'sistema');
    window.scrollTo(0, 0);
  }

  function aplicarDivisao() {
    const dividir = telaDividida.matches;
    corpo.classList.toggle('modo-dividido', dividir);
    if (dividir) mostrarVista(corpo.classList.contains('vista-sistema') ? 'sistema' : 'passos');
    else corpo.classList.remove('vista-sistema');
  }

  atalhos.forEach((a) => a.addEventListener('click', (ev) => {
    if (!corpo.classList.contains('modo-dividido')) return;
    ev.preventDefault();
    mostrarVista(a.dataset.vista);
  }));
  // Parar a resolução leva ao formulário; resolver de novo volta ao passo a passo.
  ['btn-parar', 'btn-cena-parar'].forEach((id) => {
    const b = document.getElementById(id);
    if (b) b.addEventListener('click', () => { if (corpo.classList.contains('modo-dividido')) mostrarVista('sistema'); });
  });
  window.__mostrarPassoAPasso = () => { if (corpo.classList.contains('modo-dividido')) mostrarVista('passos'); };

  /* A metade de cima só cresce durante a resolução: passos menores (resultado, classificação)
     não puxam a divisória para cima; ela fica na altura do maior passo já visto. */
  const cenaCard = document.getElementById('cena');
  let alturaCena = 0;
  function fixarAlturaCena() {
    if (!corpo.classList.contains('modo-dividido')) {
      alturaCena = 0;
      cenaCard.style.minHeight = '';
      return;
    }
    const altura = cenaCard.scrollHeight;
    if (altura > alturaCena + 1) {
      alturaCena = altura;
      cenaCard.style.minHeight = altura + 'px';
    }
  }
  if (cenaCard && 'ResizeObserver' in window) new ResizeObserver(fixarAlturaCena).observe(cenaCard);

  telaDividida.addEventListener('change', () => { alturaCena = 0; cenaCard.style.minHeight = ''; aplicarDivisao(); });
  aplicarDivisao();

  /* Empilhado (sem divisão): depois de resolver, mostrar direto a matriz. */
  if (!telaDividida.matches && window.location.search && telaEmpilhada.matches) {
    document.getElementById('q-cena').scrollIntoView({ block: 'start' });
  }
})();
