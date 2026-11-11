/* Formulário do resolver: alterna 2×2/3×3, mostra o sistema informado a partir da matriz,
 * preenche as equações ao trocar de modo e copia o link. A leitura oficial é feita no servidor. */
(function () {
  'use strict';

  document.body.classList.add('pagina-resolver');

  const form = document.getElementById('form-sistema');
  const ordem = document.getElementById('id_n');
  const grade = document.getElementById('grade');
  // Letras das incógnitas (RN-022): x, y, z ou as que vieram das equações (a, b, c…).
  const VARS = ((grade && grade.dataset.incognitas) || 'x,y,z').split(',');
  const lista = document.getElementById('sistema-informado');
  const texto = document.getElementById('id_equacoes');
  const modoEquacoes = document.getElementById('entrada-equacoes');
  let textoEditado = Boolean(modoEquacoes && modoEquacoes.checked);

  const menos = (s) => s.replace(/-/g, '−');

  function termo(valor, variavel, primeiro) {
    let v = (valor || '').trim().replace('−', '-');
    if (v === '' || /^[+-]?0+([.,]0*)?$/.test(v)) v = '0';
    const negativo = v.startsWith('-');
    let abs = v.replace(/^[+-]/, '');
    if (abs === '1') abs = '';
    else if (abs.includes('/')) abs = '(' + abs + ')';
    const corpo = abs + variavel;
    if (primeiro) return (negativo ? '−' : '') + corpo;
    return (negativo ? '− ' : '+ ') + corpo;
  }

  function equacoes() {
    const n = parseInt(ordem ? ordem.value : '2', 10);
    const linhas = [];
    for (let i = 1; i <= n; i++) {
      const partes = [];
      for (let j = 1; j <= n; j++) {
        const campo = form.elements['a' + i + j];
        partes.push(termo(campo ? campo.value : '', VARS[j - 1], j === 1));
      }
      const k = form.elements['k' + i];
      const kv = (k && k.value.trim()) || '0';
      linhas.push(partes.join(' ') + ' = ' + menos(kv));
    }
    return linhas;
  }

  function atualizarSistema() {
    if (!lista) return;
    while (lista.firstChild) lista.removeChild(lista.firstChild);
    equacoes().forEach((eq, i) => {
      const li = document.createElement('li');
      const rot = document.createElement('span');
      rot.className = 'texto-suave';
      rot.textContent = 'L' + (i + 1) + ': ';
      li.appendChild(rot);
      li.appendChild(document.createTextNode(eq));
      lista.appendChild(li);
    });
  }

  const PADRAO_L3 = { a31: '1', a32: '-4', a33: '1', k3: '-4' };

  function preencherExemploL3SeVazio() {
    if (!form) return;
    const camposL3 = ['a31', 'a32', 'a33', 'k3'].map((id) => form.elements[id]);
    const temValorL3 = camposL3.some((campo) => campo && campo.value.trim() !== '');
    if (temValorL3) return;

    let dados = PADRAO_L3;
    if (grade && grade.dataset.exemploL3) {
      try {
        dados = JSON.parse(grade.dataset.exemploL3);
      } catch (e) {
        dados = PADRAO_L3;
      }
    }
    Object.keys(dados).forEach((id) => {
      const campo = form.elements[id];
      if (campo) {
        campo.value = dados[id];
        campo.removeAttribute('aria-invalid');
      }
    });
  }

  let formModificado = false;
  const btnResolver = document.getElementById('btn-resolver');
  const btnParar = document.getElementById('btn-parar');
  const btnCenaParar = document.getElementById('btn-cena-parar');
  const badgeTravado = document.getElementById('status-travado');
  const btnTocar = document.getElementById('btn-tocar');
  const cena = document.getElementById('cena');
  const cenaPlaceholder = document.getElementById('cena-placeholder');
  const conta = document.getElementById('conta');
  const contaPlaceholder = document.getElementById('conta-placeholder');
  const metodos = document.querySelector('.resolucao-metodos');
  const btnSalvarTxt = document.getElementById('btn-salvar-txt');
  const metodo = document.getElementById('id_metodo');

  function travarPrimeiroQuadrante(travado) {
    document.querySelectorAll('.coef').forEach((el) => { el.disabled = travado; });
    if (ordem) ordem.disabled = travado;
    if (texto) texto.disabled = travado;
    document.querySelectorAll('input[name="entrada"]').forEach((r) => { r.disabled = travado; });
    if (metodo) metodo.disabled = travado;
    if (form) form.classList.toggle('quadrante-travado', travado);
    if (badgeTravado) badgeTravado.classList.toggle('d-none', !travado);
  }
  window.__travarPrimeiroQuadrante = travarPrimeiroQuadrante;

  function pararProcessamento() {
    if (window.__passoAPasso && typeof window.__passoAPasso.parar === 'function') {
      window.__passoAPasso.parar();
    } else if (btnTocar && btnTocar.querySelector('.bi-pause-fill')) {
      btnTocar.click();
    }
    travarPrimeiroQuadrante(false);

    if (btnResolver) {
      btnResolver.classList.remove('tocando');
      const icone = btnResolver.querySelector('i');
      if (icone) icone.className = 'bi bi-play-fill';
      const rotulo = btnResolver.querySelector('.rotulo-resolver');
      if (rotulo && cena && !cena.hidden) {
        rotulo.textContent = 'Continuar';
      }
    }
    if (btnParar && cena && !cena.hidden) {
      btnParar.classList.remove('d-none');
    }
  }
  window.__pararProcessamento = pararProcessamento;

  if (btnParar) {
    btnParar.addEventListener('click', pararProcessamento);
  }
  if (btnCenaParar) {
    btnCenaParar.addEventListener('click', pararProcessamento);
  }

  function limparResolucao() {
    if (window.__passoAPasso && typeof window.__passoAPasso.parar === 'function') {
      window.__passoAPasso.parar();
    } else if (btnTocar && btnTocar.querySelector('.bi-pause-fill')) {
      btnTocar.click();
    }

    if (cena) cena.hidden = true;
    if (cenaPlaceholder) cenaPlaceholder.classList.remove('d-none');

    if (conta) conta.hidden = true;
    if (metodos) metodos.classList.add('d-none');
    if (btnSalvarTxt) btnSalvarTxt.classList.add('d-none');
    if (contaPlaceholder) contaPlaceholder.classList.remove('d-none');

    travarPrimeiroQuadrante(false);
    formModificado = true;

    if (btnResolver) {
      btnResolver.classList.remove('tocando');
      const icone = btnResolver.querySelector('i');
      if (icone) icone.className = 'bi bi-play-fill';
      const rotulo = btnResolver.querySelector('.rotulo-resolver');
      if (rotulo) rotulo.textContent = 'Resolver';
    }
    if (btnParar) btnParar.classList.add('d-none');
  }
  window.__limparResolucao = limparResolucao;

  if (ordem && grade) {
    ordem.addEventListener('change', () => {
      formModificado = true;
      limparResolucao();

      if (ordem.value === '3') {
        preencherExemploL3SeVazio();
      } else if (ordem.value === '2') {
        ['a13', 'a23', 'a31', 'a32', 'a33', 'k3'].forEach((id) => {
          const c = form.elements[id];
          if (c) {
            c.value = '';
            c.removeAttribute('aria-invalid');
          }
        });
      }

      grade.classList.remove('ordem-2', 'ordem-3');
      grade.classList.add('ordem-' + ordem.value);
      atualizarSistema();
      textoEditado = false;
    });
  }

  document.querySelectorAll('.coef').forEach((campo) => {
    campo.addEventListener('input', () => {
      formModificado = true;
      limparResolucao();
      campo.removeAttribute('aria-invalid');
      atualizarSistema();
      textoEditado = false;
    });
  });

  if (texto) {
    texto.addEventListener('input', () => {
      formModificado = true;
      limparResolucao();
      textoEditado = true;
    });
  }

  if (modoEquacoes && texto) {
    modoEquacoes.addEventListener('change', () => {
      formModificado = true;
      limparResolucao();
      if (modoEquacoes.checked && !textoEditado) texto.value = equacoes().join('\n');
    });
  }

  const modoMatriz = document.getElementById('entrada-matriz');
  if (modoMatriz) {
    modoMatriz.addEventListener('change', () => {
      formModificado = true;
      limparResolucao();
    });
  }

  function ativarAutoplay() {
    if (!form) return;
    let inputAutoplay = form.querySelector('input[name="autoplay"]');
    if (!inputAutoplay) {
      inputAutoplay = document.createElement('input');
      inputAutoplay.type = 'hidden';
      inputAutoplay.name = 'autoplay';
      form.appendChild(inputAutoplay);
    }
    inputAutoplay.value = '1';
  }

  if (btnResolver) {
    btnResolver.addEventListener('click', (ev) => {
      const cenaAtiva = Boolean(cena && !cena.hidden);
      if (!formModificado && btnTocar && cenaAtiva) {
        ev.preventDefault();
        travarPrimeiroQuadrante(true);
        if (btnParar) btnParar.classList.remove('d-none');
        btnTocar.click();
        if (typeof window.__mostrarPassoAPasso === 'function') window.__mostrarPassoAPasso();
        if (window.matchMedia('(max-width: 1199.98px)').matches && !document.body.classList.contains('modo-dividido')) {
          const qCena = document.getElementById('q-cena');
          if (qCena) qCena.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        return;
      }
      ativarAutoplay();
    });
  }

  if (form) {
    form.addEventListener('submit', () => {
      ativarAutoplay();
    });
  }

  if (metodo && form) {
    metodo.addEventListener('change', () => {
      formModificado = true;
      limparResolucao();
      form.requestSubmit();
    });
  }

  /* Altura real da barra superior: os quadrantes ocupam o restante da tela (primeira dobra). */
  const barra = document.querySelector('.app-navbar');
  function medirBarra() {
    if (barra) {
      const h = barra.offsetHeight + 'px';
      document.documentElement.style.setProperty('--altura-topo', h);
      document.body.style.setProperty('--altura-topo', h);
    }
  }
  medirBarra();
  window.addEventListener('resize', medirBarra);

  const copiar = document.getElementById('copiar-link');
  if (copiar && navigator.clipboard) {
    copiar.addEventListener('click', () => {
      navigator.clipboard.writeText(window.location.href).then(() => {
        const original = copiar.innerHTML;
        copiar.textContent = copiar.dataset.copiado;
        window.setTimeout(() => { copiar.innerHTML = original; }, 1800);
      });
    });
  }
})();
