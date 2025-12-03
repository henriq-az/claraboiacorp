(function() {
    const wrapper = document.getElementById('reelsWrapper');
    const container = document.getElementById('reelsContainer');
    const slides = document.querySelectorAll('.reel-slide');
    const indicatorsContainer = document.getElementById('reelsIndicators');

    let currentIndex = 0;
    let startY = 0;
    let currentY = 0;
    let isDragging = false;
    let isScrolling = false;
    const threshold = 50;
    const scrollCooldown = 500; // tempo em ms entre scrolls

    // Criar indicadores
    slides.forEach((_, i) => {
        const dot = document.createElement('div');
        dot.className = 'reel-indicator' + (i === 0 ? ' active' : '');
        dot.addEventListener('click', () => goToSlide(i));
        indicatorsContainer.appendChild(dot);
    });

    function goToSlide(index) {
        if (index < 0 || index >= slides.length) return;

        currentIndex = index;
        const offset = -currentIndex * 100;
        wrapper.style.transition = 'transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        wrapper.style.transform = `translateY(${offset}vh)`;

        // Atualiza indicadores
        document.querySelectorAll('.reel-indicator').forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
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
        // Ignora se clicar no conteúdo de texto ou se estiver expandido
        if (e.target.closest('.reel-content')) {
            const content = e.target.closest('.reel-content');
            if (content.classList.contains('expanded')) {
                return;
            }
            // Permite o clique no texto para expandir, mas não inicia drag
            return;
        }

        startY = e.touches[0].clientY;
        isDragging = true;
        wrapper.style.transition = 'none';
    }, { passive: true });

    container.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        currentY = e.touches[0].clientY;
    }, { passive: true });

    container.addEventListener('touchend', () => {
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

    // Ações (like, save, share)
    document.querySelectorAll('.reel-action').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const action = btn.dataset.action;

            if (action === 'like') {
                btn.classList.toggle('liked');
            } else if (action === 'save') {
                btn.classList.toggle('saved');
                showToast(btn.classList.contains('saved') ? 'Notícia salva!' : 'Removida dos salvos');
            } else if (action === 'share') {
                shareContent();
            }
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
