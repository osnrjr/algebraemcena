/* Player do vídeo de apresentação (apps/site/templates/site/_player_video.html).
 *
 * - Capa própria (imagem + botão play). O iframe do YouTube (youtube-nocookie) só é criado no
 *   primeiro clique: nada de terceiros é carregado antes disso.
 * - Controles do YouTube desligados (controls=0); os nossos: reproduzir/pausar, volume, tela cheia.
 *   O progresso é só indicativo (não há busca).
 * - Uma camada transparente cobre o iframe: cliques não levam ao YouTube; título e prateleira de
 *   vídeos ficam fora da área visível (o iframe é mais alto que o quadro e é recortado).
 * - Ao terminar, o vídeo para e a capa volta, com o botão play no centro.
 *
 * Teclado (com o foco no player): espaço/K reproduz ou pausa, M silencia, F tela cheia.
 *
 * Medição (RF-016): o player conta o tempo em reprodução (segundosAssistidos), a maior posição
 * alcançada e a duração, e emite eventos no contêiner — pa:iniciar (clique no play da capa),
 * pa:pausa e pa:fim. Quem envia ao servidor é static/js/experimento.js.
 */
(() => {
  'use strict';

  const API_URL = 'https://www.youtube.com/iframe_api';
  const HOST_PLAYER = 'https://www.youtube-nocookie.com';
  const OCULTAR_CONTROLES_MS = 2600;
  let apiPromessa = null;

  function carregarApi() {
    if (window.YT && window.YT.Player) return Promise.resolve(window.YT);
    if (apiPromessa) return apiPromessa;
    apiPromessa = new Promise((resolve, reject) => {
      const anterior = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        if (typeof anterior === 'function') anterior();
        resolve(window.YT);
      };
      const s = document.createElement('script');
      s.src = API_URL;
      s.async = true;
      s.onerror = () => { apiPromessa = null; reject(new Error('IFrame API indisponível')); };
      document.head.appendChild(s);
    });
    return apiPromessa;
  }

  const formatar = (seg) => {
    const s = Math.max(0, Math.floor(seg || 0));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  };

  class PlayerApresentacao {
    constructor(raiz) {
      this.raiz = raiz;
      this.videoId = raiz.dataset.videoId;
      this.alvo = raiz.querySelector('[data-palco]');
      this.btnAlternar = raiz.querySelector('[data-acao="alternar"]');
      this.btnSom = raiz.querySelector('[data-acao="som"]');
      this.btnTela = raiz.querySelector('[data-acao="tela"]');
      this.volume = raiz.querySelector('[data-volume]');
      this.tempo = raiz.querySelector('[data-tempo]');
      this.progresso = raiz.querySelector('[data-progresso]');
      this.aviso = raiz.querySelector('[data-aviso]');
      this.player = null;
      this.relogio = null;
      this.temporizador = null;
      this.segundosAssistidos = 0;   // só tempo em reprodução, somando replays
      this.posicaoMaxima = 0;
      this.duracao = 0;
      this.marco = null;             // performance.now() do último tique em reprodução

      raiz.querySelector('[data-acao="iniciar"]').addEventListener('click', () => this.iniciar());
      raiz.querySelector('[data-camada]').addEventListener('click', () => this.alternar());
      raiz.querySelector('[data-camada]').addEventListener('dblclick', () => this.telaCheia());
      this.btnAlternar.addEventListener('click', () => this.alternar());
      this.btnSom.addEventListener('click', () => this.alternarSom());
      this.volume.addEventListener('input', () => this.aplicarVolume());
      if (document.fullscreenEnabled) {
        this.btnTela.addEventListener('click', () => this.telaCheia());
        document.addEventListener('fullscreenchange', () => this.atualizarTela());
      } else {
        this.btnTela.hidden = true;            // iOS: sem tela cheia de elemento
      }
      raiz.addEventListener('pointermove', () => this.mostrarControles());
      raiz.addEventListener('pointerleave', () => this.agendarOcultar(300));
      raiz.addEventListener('focusin', () => this.mostrarControles());
      raiz.addEventListener('keydown', (e) => this.tecla(e));
      raiz.playerApresentacao = this;
    }

    get estado() { return this.raiz.dataset.estado; }

    set estado(valor) {
      // A capa some ao tocar: o foco que estava nela passa ao player (Esc do modal e atalhos seguem valendo).
      const capa = this.raiz.querySelector('[data-acao="iniciar"]');
      const ativo = document.activeElement;
      if (valor === 'tocando' && (ativo === capa || ativo === document.body || !ativo)) this.raiz.focus({ preventScroll: true });
      this.raiz.dataset.estado = valor;
      const tocando = valor === 'tocando';
      this.btnAlternar.setAttribute('aria-label', tocando ? 'Pausar' : 'Reproduzir');
      this.btnAlternar.querySelector('i').className = tocando ? 'bi bi-pause-fill' : 'bi bi-play-fill';
      if (tocando) this.agendarOcultar(); else this.mostrarControles(false);
      this.contarTempo(tocando);
    }

    /** Acumula o tempo em reprodução; chamado nas mudanças de estado e a cada tique do relógio. */
    contarTempo(tocando = this.estado === 'tocando') {
      const agora = performance.now();
      // Teto por tique: aba em segundo plano tem relógio lento; suspensão do sistema não vira "assistido".
      if (this.marco !== null) this.segundosAssistidos += Math.min(agora - this.marco, 70000) / 1000;
      this.marco = tocando ? agora : null;
    }

    emitir(nome) {
      this.raiz.dispatchEvent(new CustomEvent(nome, { detail: this }));
    }

    async iniciar() {
      this.aviso.hidden = true;
      this.emitir('pa:iniciar');
      if (this.player) {
        this.estado = 'carregando';
        this.player.seekTo(0, true);
        this.player.playVideo();
        return;
      }
      this.estado = 'carregando';
      try {
        const YT = await carregarApi();
        this.player = new YT.Player(this.alvo, {
          host: HOST_PLAYER,
          videoId: this.videoId,
          width: '100%',
          height: '100%',
          playerVars: {
            autoplay: 1, controls: 0, disablekb: 1, fs: 0, rel: 0, iv_load_policy: 3,
            playsinline: 1, cc_load_policy: 0, modestbranding: 1, origin: window.location.origin,
          },
          events: {
            onReady: (e) => this.pronto(e),
            onStateChange: (e) => this.mudou(e),
            onError: () => this.falhou(),
          },
        });
      } catch (erro) {
        this.falhou();
      }
    }

    pronto(e) {
      const iframe = e.target.getIframe();
      iframe.setAttribute('tabindex', '-1');
      iframe.setAttribute('title', 'Vídeo de apresentação do Álgebra em Cena');
      this.aplicarVolume();
      e.target.playVideo();
      clearInterval(this.relogio);
      this.relogio = setInterval(() => this.atualizarTempo(), 250);
    }

    mudou(e) {
      const S = window.YT.PlayerState;
      if (e.data === S.PLAYING) {
        this.estado = 'tocando';
      } else if (e.data === S.PAUSED) {
        this.estado = 'pausado';
        this.emitir('pa:pausa');
      } else if (e.data === S.ENDED) {
        this.posicaoMaxima = Math.max(this.posicaoMaxima, this.duracao);
        this.contarTempo(false);
        this.emitir('pa:fim');
        this.voltarCapa();
      }
    }

    falhou() {
      this.estado = 'capa';
      this.aviso.hidden = false;
    }

    voltarCapa() {
      if (this.player) this.player.stopVideo();
      if (document.fullscreenElement === this.raiz) document.exitFullscreen();
      this.estado = 'capa';
      this.progresso.style.width = '0%';
      this.raiz.querySelector('[data-acao="iniciar"]').focus({ preventScroll: true });
    }

    alternar() {
      if (!this.player) return;
      if (this.estado === 'tocando') this.player.pauseVideo();
      else this.player.playVideo();
    }

    /** Usado por quem embute o player (ex.: modal): pausa sem mexer na capa. */
    pausar() {
      if (this.player && this.estado === 'tocando') this.player.pauseVideo();
    }

    aplicarVolume() {
      const v = Number(this.volume.value);
      if (this.player && this.player.setVolume) {
        this.player.setVolume(v);
        if (v > 0) this.player.unMute(); else this.player.mute();
      }
      this.volume.style.setProperty('--pa-nivel', `${v}%`);
      this.desenharSom(v === 0);
    }

    alternarSom() {
      if (Number(this.volume.value) === 0) {
        this.volume.value = this.volume.dataset.anterior || 80;
      } else {
        this.volume.dataset.anterior = this.volume.value;
        this.volume.value = 0;
      }
      this.aplicarVolume();
    }

    desenharSom(mudo) {
      const v = Number(this.volume.value);
      const icone = mudo ? 'bi-volume-mute-fill' : (v < 50 ? 'bi-volume-down-fill' : 'bi-volume-up-fill');
      this.btnSom.querySelector('i').className = `bi ${icone}`;
      this.btnSom.setAttribute('aria-label', mudo ? 'Ativar som' : 'Silenciar');
    }

    telaCheia() {
      if (!document.fullscreenEnabled) return;
      if (document.fullscreenElement) document.exitFullscreen();
      else this.raiz.requestFullscreen().catch(() => {});
    }

    atualizarTela() {
      const cheia = document.fullscreenElement === this.raiz;
      this.btnTela.querySelector('i').className = cheia ? 'bi bi-fullscreen-exit' : 'bi bi-fullscreen';
      this.btnTela.setAttribute('aria-label', cheia ? 'Sair da tela cheia' : 'Tela cheia');
    }

    atualizarTempo() {
      if (!this.player || !this.player.getDuration) return;
      const total = this.player.getDuration() || 0;
      const atual = this.player.getCurrentTime() || 0;
      if (this.estado === 'tocando') {
        this.contarTempo(true);
        this.posicaoMaxima = Math.max(this.posicaoMaxima, atual);
      }
      if (total > 0) {
        this.duracao = total;
        this.progresso.style.width = `${Math.min(100, (atual / total) * 100)}%`;
        this.tempo.textContent = `${formatar(atual)} / ${formatar(total)}`;
      }
    }

    mostrarControles(agendar = true) {
      this.raiz.classList.add('pa-ativo');
      if (agendar && this.estado === 'tocando') this.agendarOcultar();
    }

    agendarOcultar(ms = OCULTAR_CONTROLES_MS) {
      clearTimeout(this.temporizador);
      this.temporizador = setTimeout(() => {
        // Mantém visível só se o foco veio do teclado (clique em botão não segura os controles).
        if (this.estado === 'tocando' && !this.raiz.querySelector(':focus-visible')) this.raiz.classList.remove('pa-ativo');
      }, ms);
    }

    tecla(e) {
      if (e.target.matches('input[type="range"]') && e.key.startsWith('Arrow')) return;
      const k = e.key.toLowerCase();
      if ((k === ' ' || k === 'k') && !e.target.matches('button')) {
        e.preventDefault();
        if (this.estado === 'capa') this.iniciar(); else this.alternar();
      } else if (k === 'm') {
        this.alternarSom();
      } else if (k === 'f') {
        this.telaCheia();
      }
    }
  }

  document.querySelectorAll('[data-player-apresentacao]').forEach((raiz) => new PlayerApresentacao(raiz));

  // Player dentro de modal (Bootstrap): pausa ao fechar.
  document.querySelectorAll('.modal').forEach((modal) => {
    modal.addEventListener('hidden.bs.modal', () => {
      modal.querySelectorAll('[data-player-apresentacao]').forEach((r) => r.playerApresentacao?.pausar());
    });
  });
})();
