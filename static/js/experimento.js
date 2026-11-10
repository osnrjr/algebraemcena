/* Medição do vídeo de apresentação na landing em rodízio (RF-016, RN-026).
 *
 * Só é carregado quando a página tem uma exibição (data-exibicao no player). Envia ao servidor,
 * por sendBeacon (sobrevive ao fechamento da aba):
 *   clique    — clique no play da capa (cada replay conta de novo)
 *   progresso — a cada 15 s em reprodução, ao pausar e ao sair da página
 *   fim       — o vídeo chegou ao fim
 * com o tempo em reprodução acumulado, a maior posição alcançada e a duração do vídeo.
 */
(() => {
  'use strict';

  const raiz = document.querySelector('[data-player-apresentacao][data-exibicao]');
  if (!raiz || !raiz.playerApresentacao) return;
  const player = raiz.playerApresentacao;
  const url = raiz.dataset.eventoUrl;
  const token = raiz.dataset.exibicao;
  const INTERVALO_MS = 15000;
  let ultimoEnviado = -1;

  function enviar(evento) {
    player.contarTempo();
    const segundos = player.segundosAssistidos;
    if (evento === 'progresso' && Math.abs(segundos - ultimoEnviado) < 0.5) return;   // nada novo
    ultimoEnviado = segundos;
    const dados = new URLSearchParams({
      token, evento,
      segundos: segundos.toFixed(1),
      posicao: player.posicaoMaxima.toFixed(1),
      duracao: player.duracao.toFixed(1),
    });
    if (navigator.sendBeacon && navigator.sendBeacon(url, dados)) return;
    fetch(url, { method: 'POST', body: dados, keepalive: true, credentials: 'same-origin' }).catch(() => {});
  }

  raiz.addEventListener('pa:iniciar', () => enviar('clique'));
  raiz.addEventListener('pa:pausa', () => enviar('progresso'));
  raiz.addEventListener('pa:fim', () => enviar('fim'));
  setInterval(() => { if (raiz.dataset.estado === 'tocando') enviar('progresso'); }, INTERVALO_MS);

  const sair = () => { if (player.segundosAssistidos > 0) enviar('progresso'); };
  window.addEventListener('pagehide', sair);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') sair(); });
})();
