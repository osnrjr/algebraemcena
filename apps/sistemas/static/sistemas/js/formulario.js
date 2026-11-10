/* Formulário do resolver: alterna 2×2/3×3, mostra o sistema informado a partir da matriz,
 * preenche as equações ao trocar de modo e copia o link. A leitura oficial é feita no servidor. */
(function () {
  'use strict';

  const VARS = ['x', 'y', 'z'];
  const form = document.getElementById('form-sistema');
  const ordem = document.getElementById('id_n');
  const grade = document.getElementById('grade');
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

  if (ordem && grade) {
    ordem.addEventListener('change', () => {
      grade.classList.remove('ordem-2', 'ordem-3');
      grade.classList.add('ordem-' + ordem.value);
      atualizarSistema();
      textoEditado = false;
    });
  }

  document.querySelectorAll('.coef').forEach((campo) => {
    campo.addEventListener('input', () => {
      campo.removeAttribute('aria-invalid');
      atualizarSistema();
      textoEditado = false;
    });
  });

  if (texto) texto.addEventListener('input', () => { textoEditado = true; });

  if (modoEquacoes && texto) {
    modoEquacoes.addEventListener('change', () => {
      if (modoEquacoes.checked && !textoEditado) texto.value = equacoes().join('\n');
    });
  }

  /* Altura real da barra superior: os quadrantes ocupam o restante da tela (primeira dobra). */
  const barra = document.querySelector('.app-navbar');
  function medirBarra() {
    if (barra) document.documentElement.style.setProperty('--altura-topo', barra.offsetHeight + 'px');
  }
  medirBarra();
  window.addEventListener('resize', medirBarra);

  /* O método fica na barra superior (atributo form="form-sistema"): trocar já resolve de novo. */
  const metodo = document.getElementById('id_metodo');
  if (metodo && form) metodo.addEventListener('change', () => form.requestSubmit());

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
