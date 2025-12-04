/* ===================================================
   APP.JS - JORNAL DO COMMERCIO
   Inicialização e Controle Principal
   =================================================== */

// Estado Global da Aplicação
const AppState = {
    menuAberto: false,
    buscaAberta: false,
    filtrosAbertos: false,
    paginaAtual: 1,
    categoriaSelecionada: 'todas',
    noticiasSalvas: [],
    usuarioLogado: null
};

// ===================================================
// INICIALIZAÇÃO
// ===================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Jornal do Commercio - Iniciando...');

    // Inicializar módulos
    initApp();

    // Carregar dados salvos
    carregarDadosLocais();

    // Registrar service worker (PWA futuro)
    registrarServiceWorker();

    console.log('✅ Aplicação iniciada com sucesso!');
});

// ===================================================
// FUNÇÕES PRINCIPAIS
// ===================================================

function initApp() {
    // Detectar dispositivo
    detectarDispositivo();

    // Configurar tema
    configurarTema();

    // Prevenir zoom no iOS
    prevenirZoomIOS();

    // Inicializar observadores
    inicializarObservadores();

    // Configurar listeners globais
    configurarListenersGlobais();
}

// ===================================================
// DETECÇÃO E CONFIGURAÇÃO
// ===================================================

function detectarDispositivo() {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isTablet = /(ipad|tablet|(android(?!.*mobile))|(windows(?!.*phone)(.*touch))|kindle|playbook|silk|(puffin(?!.*(IP|AP|WP))))/i.test(navigator.userAgent);

    document.body.classList.add(isMobile ? 'dispositivo-mobile' : 'dispositivo-desktop');
    if (isTablet) document.body.classList.add('dispositivo-tablet');

    // Adicionar classe para iOS (para ajustes específicos)
    if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
        document.body.classList.add('ios');
    }
}

function configurarTema() {
    // Forçar tema claro sempre
    document.documentElement.setAttribute('data-theme', 'light');

    // Prevenir dark mode
    const meta = document.createElement('meta');
    meta.name = 'color-scheme';
    meta.content = 'light only';
    document.head.appendChild(meta);
}

function prevenirZoomIOS() {
    // Prevenir zoom duplo toque no iOS
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (event) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, { passive: false });
}

// ===================================================
// OBSERVADORES
// ===================================================

function inicializarObservadores() {
    // Intersection Observer para lazy loading
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('carregada');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        // Observar todas as imagens com data-src
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Animação do header foi movida para header-animation.js
}

// ===================================================
// LISTENERS GLOBAIS
// ===================================================

function configurarListenersGlobais() {
    // Fechar menu/busca ao clicar fora
    document.addEventListener('click', (e) => {
        const menuLateral = document.getElementById('menuLateral');
        const menuOverlay = document.getElementById('menuOverlay');
        const barraBusca = document.getElementById('barraBusca');
        const menuHamburguer = document.getElementById('menuHamburguer');

        // Fechar menu APENAS se clicar no overlay (fora do menu)
        if (e.target === menuOverlay) {
            fecharMenu();
        }

        // NÃO fechar se clicar dentro do menu ou no hambúrguer
        if (AppState.menuAberto &&
            !menuLateral.contains(e.target) &&
            !menuHamburguer.contains(e.target) &&
            e.target !== menuOverlay) {
            // Só fecha se clicar em outro lugar que não seja menu, hambúrguer ou overlay
            // Por enquanto, NÃO vamos fechar automaticamente
        }

        // Fechar busca se clicar fora
        if (!barraBusca.contains(e.target) &&
            !e.target.closest('.botao-busca') &&
            AppState.buscaAberta) {
            fecharBusca();
        }
    });

    // Teclas de atalho
    document.addEventListener('keydown', (e) => {
        // ESC para fechar menu/busca
        if (e.key === 'Escape') {
            if (AppState.menuAberto) fecharMenu();
            if (AppState.buscaAberta) fecharBusca();
        }

        // Ctrl+K ou Cmd+K para busca
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleBusca();
        }
    });

    // Orientação da tela
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            ajustarLayoutOrientacao();
        }, 100);
    });

    // Resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            ajustarLayoutResize();
        }, 250);
    });
}

// ===================================================
// DADOS LOCAIS
// ===================================================

function carregarDadosLocais() {
    // Carregar notícias salvas
    const salvas = localStorage.getItem('noticiasSalvas');
    if (salvas) {
        AppState.noticiasSalvas = JSON.parse(salvas);
    }

    // Carregar preferências do usuário
    const preferencias = localStorage.getItem('preferenciasUsuario');
    if (preferencias) {
        aplicarPreferencias(JSON.parse(preferencias));
    }
}

function salvarDadosLocais(tipo, dados) {
    try {
        localStorage.setItem(tipo, JSON.stringify(dados));
        return true;
    } catch (e) {
        console.error('Erro ao salvar dados locais:', e);
        return false;
    }
}

function aplicarPreferencias(prefs) {
    // Aplicar tamanho de fonte preferido
    if (prefs.tamanhoFonte) {
        document.documentElement.style.fontSize = prefs.tamanhoFonte + 'px';
    }
}

// ===================================================
// UTILITÁRIOS
// ===================================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function formatarData(data) {
    const agora = new Date();
    const dataNoticia = new Date(data);
    const diferenca = agora - dataNoticia;

    const minutos = Math.floor(diferenca / 60000);
    const horas = Math.floor(diferenca / 3600000);
    const dias = Math.floor(diferenca / 86400000);

    if (minutos < 60) return `Há ${minutos} minutos`;
    if (horas < 24) return `Há ${horas} horas`;
    if (dias < 7) return `Há ${dias} dias`;

    return dataNoticia.toLocaleDateString('pt-BR');
}

// ===================================================
// AJUSTES DE LAYOUT
// ===================================================

function ajustarLayoutOrientacao() {
    const isLandscape = window.orientation === 90 || window.orientation === -90;
    document.body.classList.toggle('landscape', isLandscape);
}

function ajustarLayoutResize() {
    const width = window.innerWidth;

    // Fechar menu em desktop
    if (width >= 1024 && AppState.menuAberto) {
        fecharMenu();
    }

    // Ajustar grid de notícias
    const feedNoticias = document.getElementById('feedNoticias');
    if (feedNoticias) {
        if (width >= 768) {
            feedNoticias.classList.add('grid-tablet');
        } else {
            feedNoticias.classList.remove('grid-tablet');
        }
    }
}

// ===================================================
// SERVICE WORKER (PWA)
// ===================================================

function registrarServiceWorker() {
    if ('serviceWorker' in navigator) {
        // Será implementado na fase de PWA
        console.log('Service Worker será implementado na fase PWA');
    }
}

// ===================================================
// FUNÇÕES AUXILIARES GLOBAIS
// ===================================================

function fecharMenu() {
    const menuLateral = document.getElementById('menuLateral');
    const menuOverlay = document.getElementById('menuOverlay');
    const menuHamburguer = document.getElementById('menuHamburguer');

    menuLateral.classList.remove('ativo');
    menuOverlay.classList.remove('ativo');
    menuHamburguer.classList.remove('ativo');
    document.body.style.overflow = '';

    AppState.menuAberto = false;
}

function fecharBusca() {
    const barraBusca = document.getElementById('barraBusca');
    barraBusca.classList.remove('ativa');
    AppState.buscaAberta = false;
}

function toggleBusca() {
    const barraBusca = document.getElementById('barraBusca');
    barraBusca.classList.toggle('ativa');
    AppState.buscaAberta = !AppState.buscaAberta;

    if (AppState.buscaAberta) {
        const campoBusca = document.querySelector('.campo-busca');
        campoBusca.focus();
    }
}

// ===================================================
// EXPORTAR PARA OUTROS MÓDULOS
// ===================================================

window.JC = {
    state: AppState,
    utils: {
        debounce,
        throttle,
        formatarData,
        salvarDadosLocais
    }
};