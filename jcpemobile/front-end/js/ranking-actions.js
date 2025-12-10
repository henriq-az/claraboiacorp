/**
 * Funcionalidades de Salvar e Compartilhar para a seção Mais Lidas (Ranking)
 */

document.addEventListener('DOMContentLoaded', function() {

    // ===============================
    // FUNCIONALIDADE DE SALVAR/FAVORITAR
    // ===============================

    /**
     * Inicializa os botões de favoritar
     */
    function initFavoriteButtons() {
        const favButtons = document.querySelectorAll('.ranking-fav');

        // Carregar notícias salvas do localStorage
        const savedNews = getSavedNews();

        favButtons.forEach(button => {
            const newsItem = button.closest('.ranking-item');
            const newsUrl = newsItem ? newsItem.getAttribute('href') : null;
            const newsTitle = newsItem ? newsItem.querySelector('.ranking-title')?.textContent.trim() : '';

            // Verificar se a notícia já está salva
            if (newsUrl && savedNews.some(item => item.url === newsUrl)) {
                button.classList.add('favorited');
                updateFavIcon(button, true);
            }

            // Adicionar event listener
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                toggleFavorite(button, newsUrl, newsTitle);
            });

            // Adicionar suporte para teclado (Enter e Space)
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleFavorite(button, newsUrl, newsTitle);
                }
            });
        });
    }

    /**
     * Toggle de favoritar/desfavoritar notícia
     */
    function toggleFavorite(button, newsUrl, newsTitle) {
        const isFavorited = button.classList.contains('favorited');

        if (isFavorited) {
            // Desfavoritar
            button.classList.remove('favorited');

            // Forçar reset completo do SVG
            const svg = button.querySelector('svg path');
            if (svg) {
                // Remover todos os atributos de estilo
                svg.removeAttribute('style');
                svg.removeAttribute('fill');
                svg.removeAttribute('stroke');

                // Forçar re-renderização
                setTimeout(() => {
                    svg.setAttribute('fill', 'none');
                    svg.setAttribute('stroke', '#000');
                    // Forçar o navegador a recalcular o estilo
                    void svg.offsetWidth;
                }, 0);
            }

            updateFavIcon(button, false);
            removeFromSaved(newsUrl);
            showToast('Notícia removida dos salvos', 'info');
        } else {
            // Favoritar
            button.classList.add('favorited');

            // Animação de pulsar
            button.style.animation = 'pulse 0.3s ease';
            setTimeout(() => button.style.animation = '', 300);

            updateFavIcon(button, true);

            // Salvar no localStorage
            const newsItem = button.closest('.ranking-item');
            const newsImage = newsItem?.querySelector('.ranking-image')?.getAttribute('src') || '';
            const newsCategory = newsItem?.querySelector('.tag')?.textContent.trim() || '';

            saveNews({
                url: newsUrl,
                title: newsTitle,
                image: newsImage,
                category: newsCategory,
                savedAt: new Date().toISOString()
            });

            showToast('Notícia salva com sucesso!', 'success');
        }
    }

    /**
     * Atualiza o ícone do botão de favoritar
     */
    function updateFavIcon(button, isFavorited) {
        const svg = button.querySelector('svg path');
        if (svg) {
            if (isFavorited) {
                svg.setAttribute('fill', '#000');
                svg.setAttribute('stroke', '#000');
            } else {
                svg.setAttribute('fill', 'none');
                svg.setAttribute('stroke', '#000');
            }
        }
    }

    /**
     * Salva notícia no localStorage
     */
    function saveNews(newsData) {
        let savedNews = getSavedNews();

        // Verificar se já não está salva
        const exists = savedNews.some(item => item.url === newsData.url);
        if (!exists) {
            savedNews.unshift(newsData); // Adiciona no início

            // Limitar a 50 notícias salvas
            if (savedNews.length > 50) {
                savedNews = savedNews.slice(0, 50);
            }

            localStorage.setItem('jc_saved_news', JSON.stringify(savedNews));
        }
    }

    /**
     * Remove notícia dos salvos
     */
    function removeFromSaved(newsUrl) {
        let savedNews = getSavedNews();
        savedNews = savedNews.filter(item => item.url !== newsUrl);
        localStorage.setItem('jc_saved_news', JSON.stringify(savedNews));
    }

    /**
     * Obtém notícias salvas do localStorage
     */
    function getSavedNews() {
        const saved = localStorage.getItem('jc_saved_news');
        return saved ? JSON.parse(saved) : [];
    }

    // ===============================
    // FUNCIONALIDADE DE COMPARTILHAR
    // ===============================

    /**
     * Inicializa os botões de compartilhar
     */
    function initShareButtons() {
        const shareButtons = document.querySelectorAll('.ranking-action');

        shareButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const newsItem = button.closest('.ranking-item');
                const newsUrl = newsItem ? newsItem.getAttribute('href') : null;
                const newsTitle = newsItem ? newsItem.querySelector('.ranking-title')?.textContent.trim() : '';

                if (newsUrl) {
                    shareNews(newsUrl, newsTitle);
                }
            });

            // Adicionar suporte para teclado (Enter e Space)
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.stopPropagation();

                    const newsItem = button.closest('.ranking-item');
                    const newsUrl = newsItem ? newsItem.getAttribute('href') : null;
                    const newsTitle = newsItem ? newsItem.querySelector('.ranking-title')?.textContent.trim() : '';

                    if (newsUrl) {
                        shareNews(newsUrl, newsTitle);
                    }
                }
            });
        });
    }

    /**
     * Compartilha notícia
     */
    async function shareNews(newsUrl, newsTitle) {
        // Construir URL completa se for relativa
        const fullUrl = newsUrl.startsWith('http') ? newsUrl : window.location.origin + newsUrl;

        const shareData = {
            title: newsTitle || 'Jornal do Commercio - JC PE',
            text: `Confira esta notícia: ${newsTitle}`,
            url: fullUrl
        };

        try {
            // Tentar usar Web Share API (funciona em mobile)
            if (navigator.share) {
                await navigator.share(shareData);
                showToast('Compartilhado com sucesso!', 'success');
            } else {
                // Fallback: mostrar modal com opções de compartilhamento
                showShareModal(fullUrl, newsTitle);
            }
        } catch (err) {
            // Usuário cancelou ou erro
            if (err.name !== 'AbortError') {
                console.error('Erro ao compartilhar:', err);
                showShareModal(fullUrl, newsTitle);
            }
        }
    }

    /**
     * Mostra modal com opções de compartilhamento
     */
    function showShareModal(url, title) {
        // Criar modal se não existir
        let modal = document.getElementById('shareModal');

        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'shareModal';
            modal.className = 'share-modal';
            modal.innerHTML = `
                <div class="share-modal-overlay"></div>
                <div class="share-modal-content">
                    <button class="share-modal-close" aria-label="Fechar">
                        <i class="fas fa-times"></i>
                    </button>
                    <h3 class="share-modal-title">Compartilhar notícia</h3>
                    <div class="share-options">
                        <button class="share-option" data-platform="whatsapp">
                            <i class="fab fa-whatsapp"></i>
                            <span>WhatsApp</span>
                        </button>
                        <button class="share-option" data-platform="facebook">
                            <i class="fab fa-facebook-f"></i>
                            <span>Facebook</span>
                        </button>
                        <button class="share-option" data-platform="twitter">
                            <i class="fab fa-twitter"></i>
                            <span>Twitter</span>
                        </button>
                        <button class="share-option" data-platform="telegram">
                            <i class="fab fa-telegram-plane"></i>
                            <span>Telegram</span>
                        </button>
                        <button class="share-option" data-platform="email">
                            <i class="fas fa-envelope"></i>
                            <span>E-mail</span>
                        </button>
                        <button class="share-option" data-platform="copy">
                            <i class="fas fa-link"></i>
                            <span>Copiar link</span>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Adicionar estilos
            addShareModalStyles();
        }

        // Atualizar URL e título
        modal.dataset.url = url;
        modal.dataset.title = title;

        // Mostrar modal
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('active'), 10);
        document.body.style.overflow = 'hidden';

        // Event listeners
        const closeBtn = modal.querySelector('.share-modal-close');
        const overlay = modal.querySelector('.share-modal-overlay');
        const shareOptions = modal.querySelectorAll('.share-option');

        closeBtn.onclick = () => closeShareModal();
        overlay.onclick = () => closeShareModal();

        shareOptions.forEach(option => {
            option.onclick = function() {
                const platform = this.dataset.platform;
                handleSharePlatform(platform, url, title);
            };
        });

        // Fechar com ESC
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                closeShareModal();
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    /**
     * Fecha modal de compartilhamento
     */
    function closeShareModal() {
        const modal = document.getElementById('shareModal');
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }, 300);
        }
    }

    /**
     * Gerencia compartilhamento por plataforma
     */
    function handleSharePlatform(platform, url, title) {
        const encodedUrl = encodeURIComponent(url);
        const encodedTitle = encodeURIComponent(title);
        let shareUrl = '';

        switch (platform) {
            case 'whatsapp':
                shareUrl = `https://wa.me/?text=${encodedTitle}%20${encodedUrl}`;
                break;
            case 'facebook':
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
                break;
            case 'twitter':
                shareUrl = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`;
                break;
            case 'telegram':
                shareUrl = `https://t.me/share/url?url=${encodedUrl}&text=${encodedTitle}`;
                break;
            case 'email':
                shareUrl = `mailto:?subject=${encodedTitle}&body=${encodedTitle}%0A%0A${encodedUrl}`;
                break;
            case 'copy':
                copyToClipboard(url);
                closeShareModal();
                return;
        }

        if (shareUrl) {
            window.open(shareUrl, '_blank', 'width=600,height=400');
            closeShareModal();
        }
    }

    /**
     * Copia texto para área de transferência
     */
    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            showToast('Link copiado para a área de transferência!', 'success');
        } catch (err) {
            console.error('Erro ao copiar:', err);

            // Fallback para navegadores mais antigos
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            document.body.appendChild(textArea);
            textArea.select();

            try {
                document.execCommand('copy');
                showToast('Link copiado!', 'success');
            } catch (err2) {
                showToast('Não foi possível copiar o link', 'error');
            }

            document.body.removeChild(textArea);
        }
    }

    // ===============================
    // SISTEMA DE TOAST/NOTIFICAÇÕES
    // ===============================

    /**
     * Mostra toast de notificação
     */
    function showToast(message, type = 'info') {
        // Criar container de toasts se não existir
        let toastContainer = document.getElementById('toastContainer');

        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        // Criar toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icon = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        }[type] || 'fa-info-circle';

        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;

        toastContainer.appendChild(toast);

        // Animação de entrada
        setTimeout(() => toast.classList.add('show'), 10);

        // Remover após 3 segundos
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();

                // Remover container se vazio
                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        }, 3000);
    }

    /**
     * Adiciona estilos do modal de compartilhamento
     */
    function addShareModalStyles() {
        if (document.getElementById('shareModalStyles')) return;

        const styles = document.createElement('style');
        styles.id = 'shareModalStyles';
        styles.textContent = `
            .share-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 10000;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .share-modal.active {
                opacity: 1;
            }

            .share-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
            }

            .share-modal-content {
                position: relative;
                background: white;
                border-radius: 20px;
                padding: 30px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                transform: translateY(-20px);
                transition: transform 0.3s ease;
            }

            .share-modal.active .share-modal-content {
                transform: translateY(0);
            }

            .share-modal-close {
                position: absolute;
                top: 15px;
                right: 15px;
                width: 32px;
                height: 32px;
                border: none;
                background: transparent;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                font-size: 18px;
                color: #333;
            }

            .share-modal-close:hover {
                background: #f5f5f5;
                transform: scale(1.1);
            }

            .share-modal-title {
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 20px;
                font-weight: 700;
                color: #000;
                margin: 0 0 20px 0;
                text-align: center;
            }

            .share-options {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
            }

            .share-option {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 15px 10px;
                border: 1px solid #ddd;
                border-radius: 12px;
                background: white;
                cursor: pointer;
                transition: all 0.3s ease;
                font-family: system-ui, -apple-system, sans-serif;
            }

            .share-option:hover {
                background: #f5f5f5;
                border-color: #c9302c;
                transform: translateY(-2px);
            }

            .share-option i {
                font-size: 24px;
                color: #333;
            }

            .share-option span {
                font-size: 12px;
                color: #666;
                font-weight: 500;
            }

            .share-option[data-platform="whatsapp"]:hover i {
                color: #25D366;
            }

            .share-option[data-platform="facebook"]:hover i {
                color: #1877F2;
            }

            .share-option[data-platform="twitter"]:hover i {
                color: #1DA1F2;
            }

            .share-option[data-platform="telegram"]:hover i {
                color: #0088cc;
            }

            .share-option[data-platform="email"]:hover i {
                color: #EA4335;
            }

            .share-option[data-platform="copy"]:hover i {
                color: #c9302c;
            }

            .toast-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10001;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            .toast {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 12px 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 14px;
                min-width: 250px;
                opacity: 0;
                transform: translateX(100px);
                transition: all 0.3s ease;
            }

            .toast.show {
                opacity: 1;
                transform: translateX(0);
            }

            .toast i {
                font-size: 18px;
            }

            .toast-success {
                border-left: 4px solid #28a745;
            }

            .toast-success i {
                color: #28a745;
            }

            .toast-error {
                border-left: 4px solid #dc3545;
            }

            .toast-error i {
                color: #dc3545;
            }

            .toast-info {
                border-left: 4px solid #17a2b8;
            }

            .toast-info i {
                color: #17a2b8;
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.15); }
                100% { transform: scale(1); }
            }

            /* Estado padrão do botão de salvar - máxima especificidade */
            .ranking-item .ranking-actions .ranking-fav:not(.favorited) svg path,
            .ranking-actions .ranking-fav:not(.favorited) svg path,
            .ranking-actions .ranking-fav svg path {
                stroke: #000 !important;
                fill: none !important;
            }

            /* Hover quando NÃO está salvo - mantém preto */
            .ranking-item .ranking-actions .ranking-fav:not(.favorited):hover svg path,
            .ranking-actions .ranking-fav:not(.favorited):hover svg path {
                stroke: #000 !important;
                fill: none !important;
            }

            /* Estado salvo - preto preenchido */
            .ranking-item .ranking-fav.favorited svg path,
            .ranking-fav.favorited svg path {
                fill: #000 !important;
                stroke: #000 !important;
            }

            /* Hover quando está salvo - mantém preto */
            .ranking-item .ranking-fav.favorited:hover svg path,
            .ranking-fav.favorited:hover svg path {
                fill: #000 !important;
                stroke: #000 !important;
            }

            /* Botão de compartilhar hover */
            .ranking-actions .ranking-action:hover svg path {
                fill: #c9302c !important;
            }

            @media (max-width: 600px) {
                .share-modal-content {
                    padding: 20px;
                }

                .share-options {
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }

                .toast-container {
                    bottom: 10px;
                    right: 10px;
                    left: 10px;
                }

                .toast {
                    min-width: auto;
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    // ===============================
    // INICIALIZAÇÃO
    // ===============================

    // Inicializar funcionalidades
    initFavoriteButtons();
    initShareButtons();

    // Expor funções globalmente para uso em outros contextos
    window.JC_RankingActions = {
        getSavedNews: getSavedNews,
        showToast: showToast
    };
});
