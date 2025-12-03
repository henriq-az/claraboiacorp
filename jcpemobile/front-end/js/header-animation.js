/* ===================================================
   HEADER-ANIMATION.JS - JORNAL DO COMMERCIO
   Animação de scroll para cabeçalho e barra UOL
   =================================================== */

(function() {
    'use strict';

    // Função para inicializar a animação do cabeçalho
    function initHeaderAnimation() {
        const header = document.getElementById('cabecalho');
        const barraUol = document.querySelector('.barra-uol');
        const topBar = document.querySelector('.top-bar');

        // Se não encontrar o cabeçalho, não fazer nada
        if (!header) return;

        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;

            // No topo da página - sempre mostrar
            if (currentScroll <= 0) {
                header.classList.remove('cabecalho-oculto');
                header.classList.add('cabecalho-visivel');
                if (barraUol) barraUol.classList.remove('barra-oculta');
                if (topBar) topBar.classList.remove('barra-oculta');
                return;
            }

            // Scrolling down - esconder cabeçalho e barras
            if (currentScroll > lastScroll && currentScroll > 100) {
                header.classList.add('cabecalho-oculto');
                header.classList.remove('cabecalho-visivel');
                if (barraUol) barraUol.classList.add('barra-oculta');
                if (topBar) topBar.classList.add('barra-oculta');
            }
            // Scrolling up - mostrar cabeçalho e barras
            else {
                header.classList.remove('cabecalho-oculto');
                header.classList.add('cabecalho-visivel');
                if (barraUol) barraUol.classList.remove('barra-oculta');
                if (topBar) topBar.classList.remove('barra-oculta');
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHeaderAnimation);
    } else {
        // DOM já está pronto
        initHeaderAnimation();
    }
})();
