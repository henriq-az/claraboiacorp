/* ===================================================
   RADIO-PLAYER.JS - JORNAL DO COMMERCIO
   Player de Rádio Ao Vivo com Drop-up
   =================================================== */

// ===================================================
// INITIALIZATION
// ===================================================

document.addEventListener('DOMContentLoaded', () => {
    inicializarRadioPlayer();
});

function inicializarRadioPlayer() {
    console.log('Inicializando Radio Player...');

    // Setup player state
    if (!window.JC) {
        window.JC = {};
    }

    window.JC.radioPlayer = {
        isPlaying: false,
        isOpen: false,
        currentTime: 0,
        volume: 85,
        timerInterval: null
    };

    // Configure components
    configurarTogglePlayer();
    configurarPlayPause();
    configurarVolumeSlider();
    configurarOverlay();

    console.log('Radio Player inicializado com sucesso');
}

// ===================================================
// TOGGLE PLAYER OPEN/CLOSE
// ===================================================

function configurarTogglePlayer() {
    const botaoRadio = document.querySelector('.nav-item[href="#radio"]');
    const radioPlayer = document.getElementById('radioPlayer');

    if (!botaoRadio || !radioPlayer) {
        console.error('Botão Rádio ou Player não encontrado');
        return;
    }

    botaoRadio.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // Previne que o navegacao.js marque o item como ativo

        // Preservar o item de navegação atualmente ativo
        const navItemAtivo = document.querySelector('.navegacao-inferior .nav-item-ativo');

        toggleRadioPlayer();

        // Restaurar o item ativo anterior após um pequeno delay
        // (para que navegacao.js não interfira)
        setTimeout(() => {
            // Remove ativo do botão de rádio
            botaoRadio.classList.remove('nav-item-ativo');

            // Restaura o item que estava ativo antes
            if (navItemAtivo && navItemAtivo !== botaoRadio) {
                navItemAtivo.classList.add('nav-item-ativo');
            }
        }, 10);

        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(10);
        }
    });
}

function toggleRadioPlayer() {
    const isOpen = window.JC.radioPlayer.isOpen;

    if (isOpen) {
        fecharRadioPlayer();
    } else {
        abrirRadioPlayer();
    }
}

function abrirRadioPlayer() {
    const radioPlayer = document.getElementById('radioPlayer');
    const overlay = document.getElementById('radioPlayerOverlay');

    radioPlayer.classList.add('ativo');
    overlay.classList.add('ativo');

    window.JC.radioPlayer.isOpen = true;

    console.log('Radio Player aberto');
}

function fecharRadioPlayer() {
    const radioPlayer = document.getElementById('radioPlayer');
    const overlay = document.getElementById('radioPlayerOverlay');

    radioPlayer.classList.remove('ativo');
    overlay.classList.remove('ativo');

    window.JC.radioPlayer.isOpen = false;

    console.log('Radio Player fechado');
}

// ===================================================
// OVERLAY - CLICK TO CLOSE (DESABILITADO)
// ===================================================

function configurarOverlay() {
    // Overlay desabilitado para permitir navegação
    // O player só fecha ao clicar no botão "Ao vivo" novamente
}

// ===================================================
// PLAY/PAUSE FUNCTIONALITY
// ===================================================

function configurarPlayPause() {
    const playButton = document.getElementById('radioPlayButton');
    const radioPlayer = document.getElementById('radioPlayer');

    if (!playButton || !radioPlayer) return;

    playButton.addEventListener('click', () => {
        togglePlayPause();
    });
}

function togglePlayPause() {
    const isPlaying = window.JC.radioPlayer.isPlaying;

    if (isPlaying) {
        pausarRadio();
    } else {
        tocarRadio();
    }
}

function tocarRadio() {
    const radioPlayer = document.getElementById('radioPlayer');

    // Adiciona classe playing para mostrar ícone de pause
    radioPlayer.classList.add('playing');
    window.JC.radioPlayer.isPlaying = true;

    // Inicia o timer
    iniciarTimer();

    // TODO: Integrar áudio real aqui
    console.log('Rádio tocando...');
}

function pausarRadio() {
    const radioPlayer = document.getElementById('radioPlayer');

    // Remove classe playing para mostrar ícone de play
    radioPlayer.classList.remove('playing');
    window.JC.radioPlayer.isPlaying = false;

    // Para o timer
    pararTimer();

    console.log('Rádio pausado');
}

// ===================================================
// TIMER FUNCTIONALITY
// ===================================================

function iniciarTimer() {
    // Limpa qualquer interval existente
    if (window.JC.radioPlayer.timerInterval) {
        clearInterval(window.JC.radioPlayer.timerInterval);
    }

    // Inicia novo interval
    window.JC.radioPlayer.timerInterval = setInterval(() => {
        window.JC.radioPlayer.currentTime++;
        atualizarDisplayTimer();
    }, 1000);
}

function pararTimer() {
    if (window.JC.radioPlayer.timerInterval) {
        clearInterval(window.JC.radioPlayer.timerInterval);
        window.JC.radioPlayer.timerInterval = null;
    }
}

function atualizarDisplayTimer() {
    const timerElement = document.getElementById('radioTimer');
    const seconds = window.JC.radioPlayer.currentTime;

    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;

    const formatted = `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    timerElement.textContent = formatted;
}

function resetarTimer() {
    window.JC.radioPlayer.currentTime = 0;
    pararTimer();
    const timerElement = document.getElementById('radioTimer');
    if (timerElement) {
        timerElement.textContent = '00:00';
    }
}

// ===================================================
// VOLUME SLIDER
// ===================================================

function configurarVolumeSlider() {
    const volumeSlider = document.getElementById('radioVolumeSlider');

    if (!volumeSlider) return;

    // Define volume inicial
    volumeSlider.value = window.JC.radioPlayer.volume;
    atualizarVolumeVisual(window.JC.radioPlayer.volume);

    // Handle volume change
    volumeSlider.addEventListener('input', (e) => {
        const volume = parseInt(e.target.value);
        window.JC.radioPlayer.volume = volume;
        atualizarVolumeVisual(volume);

        // TODO: Aplicar volume ao elemento de áudio real
    });
}

function atualizarVolumeVisual(volume) {
    const volumeFill = document.getElementById('volumeFill');

    if (!volumeFill) return;

    // Atualiza a largura da barra de preenchimento
    volumeFill.style.width = `${volume}%`;
}

// ===================================================
// KEYBOARD SHORTCUTS
// ===================================================

document.addEventListener('keydown', (e) => {
    // Apenas se o player estiver aberto
    if (!window.JC.radioPlayer.isOpen) return;

    switch(e.key) {
        case ' ':
        case 'k':
            // Espaço ou K para play/pause
            e.preventDefault();
            togglePlayPause();
            break;
        case 'Escape':
            // Escape para fechar player
            fecharRadioPlayer();
            break;
        case 'ArrowUp':
            // Seta para cima aumenta volume
            e.preventDefault();
            ajustarVolume(5);
            break;
        case 'ArrowDown':
            // Seta para baixo diminui volume
            e.preventDefault();
            ajustarVolume(-5);
            break;
    }
});

function ajustarVolume(delta) {
    const volumeSlider = document.getElementById('radioVolumeSlider');
    const novoVolume = Math.max(0, Math.min(100, window.JC.radioPlayer.volume + delta));

    volumeSlider.value = novoVolume;
    window.JC.radioPlayer.volume = novoVolume;
    atualizarVolumeVisual(novoVolume);

    console.log('Volume ajustado para:', novoVolume);
}

// ===================================================
// CLEANUP ON PAGE UNLOAD
// ===================================================

window.addEventListener('beforeunload', () => {
    if (window.JC.radioPlayer && window.JC.radioPlayer.timerInterval) {
        clearInterval(window.JC.radioPlayer.timerInterval);
    }
});
