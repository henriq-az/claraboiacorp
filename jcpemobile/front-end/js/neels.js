(function() {
    const wrapper = document.getElementById('reelsWrapper');
    const container = document.getElementById('reelsContainer');
    const slides = document.querySelectorAll('.reel-slide');

    let currentIndex = 0;
    let startY = 0;
    let currentY = 0;
    let isDragging = false;
    let isScrolling = false;
    let isClickingButton = false;
    const threshold = 50;
    const scrollCooldown = 500; // tempo em ms entre scrolls

    // Função para obter CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    function goToSlide(index) {
        if (index < 0 || index >= slides.length) return;

        // Colapsa qualquer texto expandido antes de trocar de slide
        document.querySelectorAll('.reel-description.expanded').forEach(desc => {
            desc.classList.remove('expanded');
            const content = desc.closest('.reel-content');
            if (content) {
                content.classList.remove('expanded');
            }
            // Esconde "Ver menos"
            const verMenos = desc.querySelector('.ver-menos');
            if (verMenos) {
                verMenos.style.display = 'none';
            }
        });

        currentIndex = index;
        const offset = -currentIndex * 100;
        wrapper.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        wrapper.style.transform = `translateY(${offset}vh)`;
    }

    function nextSlide() {
        if (currentIndex < slides.length - 1) {
            goToSlide(currentIndex + 1);
        }
    }

    function prevSlide() {
        if (currentIndex > 0) {
            goToSlide(currentIndex - 1);
        }
    }

    // Touch events
    container.addEventListener('touchstart', (e) => {
        // Ignora se clicar em texto expandido (permite scroll no texto)
        const expandedText = e.target.closest('.reel-description.expanded');
        if (expandedText) {
            return; // Permite scroll no texto expandido
        }

        // Ignora se clicar no conteúdo de texto
        if (e.target.closest('.reel-description')) {
            return; // Permite clique para expandir
        }

        // Marca se está clicando em um botão
        if (e.target.closest('.reel-action') || e.target.closest('.reel-actions')) {
            isClickingButton = true;
            return; // Permite clique nos botões
        }

        isClickingButton = false;
        startY = e.touches[0].clientY;
        isDragging = true;
        wrapper.style.transition = 'none';
    }, { passive: true });

    container.addEventListener('touchmove', (e) => {
        if (!isDragging || isClickingButton) return;

        currentY = e.touches[0].clientY;
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
        // Se estava clicando em um botão, apenas reseta a flag
        if (isClickingButton) {
            isClickingButton = false;
            return;
        }

        if (!isDragging) return;

        isDragging = false;
        const diff = startY - currentY;

        if (diff > threshold) {
            nextSlide();
        } else if (diff < -threshold) {
            prevSlide();
        } else {
            goToSlide(currentIndex);
        }
    });

    // Mouse wheel - uma notícia por scroll
    container.addEventListener('wheel', (e) => {
        // Se estiver scrollando em um texto expandido, não muda de slide
        const expandedText = e.target.closest('.reel-description.expanded');
        if (expandedText) {
            return; // Permite scroll normal no texto
        }

        e.preventDefault();

        // Ignora se já está scrollando (debounce)
        if (isScrolling) return;

        isScrolling = true;

        if (e.deltaY > 0) {
            nextSlide();
        } else {
            prevSlide();
        }

        // Libera após o cooldown
        setTimeout(() => {
            isScrolling = false;
        }, scrollCooldown);
    }, { passive: false });

    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === ' ') {
            e.preventDefault();
            nextSlide();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            prevSlide();
        }
    });

    // Expansão/Colapso do texto ao clicar na descrição
    document.querySelectorAll('.reel-description').forEach(description => {
        // Adiciona span "Ver menos" no final do texto (inicialmente oculto)
        const verMenos = document.createElement('span');
        verMenos.className = 'ver-menos';
        verMenos.textContent = ' Ver menos';
        verMenos.style.cssText = 'display: none; color: #FFFFFF; font-weight: bold; font-size: 14px; cursor: pointer; margin-left: 5px;';
        description.appendChild(verMenos);

        description.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanding = !description.classList.contains('expanded');

            // Toggle da descrição
            description.classList.toggle('expanded');

            // Mostra/esconde "Ver menos"
            verMenos.style.display = isExpanding ? 'inline' : 'none';

            // Toggle do container pai para ajustar espaçamento
            const content = description.closest('.reel-content');
            if (content) {
                content.classList.toggle('expanded', isExpanding);
            }
        });
    });

    // Função para salvar/remover notícia
    async function toggleSaveNoticia(noticiaId, btn) {
        console.log('[NEELS] toggleSaveNoticia chamado com ID:', noticiaId);

        if (!noticiaId) {
            console.error('[NEELS] ID da notícia não encontrado!');
            showToast('Erro: ID da notícia não encontrado');
            return;
        }

        const isSaved = btn.classList.contains('saved');

        try {
            const url = isSaved
                ? `/remover-noticia-salva/${noticiaId}/`
                : `/salvar-noticia/${noticiaId}/`;

            console.log('[NEELS] Fazendo requisição para:', url);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                }
            });

            console.log('[NEELS] Status da resposta:', response.status);

            const data = await response.json();
            console.log('[NEELS] Dados da resposta:', data);

            if (data.success) {
                btn.classList.toggle('saved');
                showToast(data.message);
            } else {
                // Se não estiver autenticado, redireciona para login
                if (response.status === 403 || response.status === 401) {
                    showToast('Faça login para salvar notícias');
                    setTimeout(() => {
                        window.location.href = '/login/';
                    }, 1500);
                } else {
                    showToast(data.message || 'Erro ao salvar notícia');
                }
            }
        } catch (error) {
            console.error('[NEELS] Erro:', error);
            showToast('Erro ao processar requisição');
        }
    }

    // Verifica estado inicial das notícias salvas
    async function verificarNoticiasSalvas() {
        const saveButtons = document.querySelectorAll('.reel-action[data-action="save"]');
        console.log('[NEELS] Verificando notícias salvas. Total de botões:', saveButtons.length);

        for (const btn of saveButtons) {
            const noticiaId = btn.dataset.noticiaId;
            console.log('[NEELS] Verificando notícia ID:', noticiaId);

            if (!noticiaId) {
                console.warn('[NEELS] Botão sem ID encontrado:', btn);
                continue;
            }

            try {
                const response = await fetch(`/verificar-noticia-salva/${noticiaId}/`);
                console.log('[NEELS] Verificação - Status:', response.status, 'para ID:', noticiaId);

                if (response.ok) {
                    const data = await response.json();
                    console.log('[NEELS] Verificação - Dados:', data);
                    if (data.salva) {
                        btn.classList.add('saved');
                    }
                }
            } catch (error) {
                console.error('[NEELS] Erro ao verificar notícia:', error);
            }
        }
    }

    // Verifica estado inicial ao carregar
    verificarNoticiasSalvas();

    // Ações (like, save, share)
    document.querySelectorAll('.reel-action').forEach(btn => {
        let lastActionTime = 0;

        function executeAction() {
            // Previne execução dupla (debounce de 300ms)
            const now = Date.now();
            if (now - lastActionTime < 300) {
                return;
            }
            lastActionTime = now;

            const action = btn.dataset.action;
            const noticiaId = btn.dataset.noticiaId;

            console.log('[NEELS] Botão clicado - Action:', action, 'ID:', noticiaId);

            if (action === 'like') {
                btn.classList.toggle('liked');
            } else if (action === 'save') {
                toggleSaveNoticia(noticiaId, btn);
            } else if (action === 'share') {
                shareContent();
            }
        }

        // Click events (desktop e fallback)
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            executeAction();
        });

        // Touch events para mobile
        btn.addEventListener('touchstart', (e) => {
            e.stopPropagation();
            isClickingButton = true;
        }, { passive: true });

        btn.addEventListener('touchend', (e) => {
            e.stopPropagation();
            e.preventDefault();

            executeAction();

            setTimeout(() => {
                isClickingButton = false;
            }, 100);
        });
    });

    function showToast(message) {
        let toast = document.querySelector('.share-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'share-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 2000);
    }

    function shareContent() {
        const currentSlide = slides[currentIndex];
        const title = currentSlide.querySelector('.reel-title').textContent;
        const description = currentSlide.querySelector('.reel-description').textContent;

        if (navigator.share) {
            navigator.share({
                title: title,
                text: description,
                url: window.location.href
            }).catch(() => {
                fallbackShare();
            });
        } else {
            fallbackShare();
        }
    }

    function fallbackShare() {
        navigator.clipboard.writeText(window.location.href);
        showToast('Link copiado!');
    }
})();
