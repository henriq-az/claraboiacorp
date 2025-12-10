/* ===================================================
   PREFERENCIAS.JS - JORNAL DO COMMERCIO
   Gerenciamento de Preferências de Categorias
   =================================================== */

// ===================================================
// UTILITÁRIOS DE COOKIES
// ===================================================

/**
 * Define um cookie
 * @param {string} name - Nome do cookie
 * @param {string} value - Valor do cookie
 * @param {number} days - Dias até expirar (padrão: 365)
 */
function setCookie(name, value, days = 365) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + encodeURIComponent(value) + ";" + expires + ";path=/";
}

/**
 * Deleta um cookie
 * @param {string} name - Nome do cookie
 */
function deleteCookie(name) {
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}

/**
 * Verifica de forma robusta se o usuário está autenticado
 * @returns {boolean} true se o usuário está logado, false caso contrário
 */
function verificarUsuarioLogado() {
    const authAttr = document.body.dataset.userAuthenticated;
    return authAttr === 'true';
}

// ===================================================
// INICIALIZAÇÃO
// ===================================================

document.addEventListener('DOMContentLoaded', () => {
    inicializarPreferencias();
});

function inicializarPreferencias() {
    console.log('Inicializando sistema de preferências...');

    // Elementos do DOM
    const btnAbrirPreferencias = document.getElementById('btnAbrirPreferencias');
    const btnFecharPreferencias = document.getElementById('fecharModalPreferencias');
    const btnSalvarPreferencias = document.getElementById('btnSalvarPreferencias');
    const btnLimparPreferencias = document.getElementById('btnLimparPreferencias');
    const modalPreferencias = document.getElementById('modalPreferencias');

    if (!btnAbrirPreferencias) {
        console.error('Botão de preferências não encontrado');
        return;
    }

    // Event Listeners
    btnAbrirPreferencias.addEventListener('click', abrirModalPreferencias);

    if (btnFecharPreferencias) {
        btnFecharPreferencias.addEventListener('click', fecharModalPreferencias);
    }

    if (btnSalvarPreferencias) {
        btnSalvarPreferencias.addEventListener('click', salvarPreferencias);
    }

    if (btnLimparPreferencias) {
        btnLimparPreferencias.addEventListener('click', limparPreferencias);
    }

    // Fechar ao clicar fora do modal
    if (modalPreferencias) {
        modalPreferencias.addEventListener('click', (e) => {
            if (e.target === modalPreferencias) {
                fecharModalPreferencias();
            }
        });
    }

    // Tecla ESC para fechar
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalPreferencias.classList.contains('ativo')) {
            fecharModalPreferencias();
        }
    });

    // Carregar preferências salvas ao iniciar
    carregarPreferencias();

    // Verificar e exibir barra de preferências ativas
    verificarPreferenciasAtivas();

    // Configurar botão de limpar filtro
    const btnLimparFiltro = document.getElementById('btnLimparFiltro');
    if (btnLimparFiltro) {
        btnLimparFiltro.addEventListener('click', limparTodasPreferencias);
    }

    console.log('Sistema de preferências inicializado com sucesso');
}

// ===================================================
// MODAL
// ===================================================

function abrirModalPreferencias() {
    const modalPreferencias = document.getElementById('modalPreferencias');

    if (modalPreferencias) {
        // Carregar preferências antes de abrir
        carregarPreferencias();

        modalPreferencias.classList.add('ativo');
        document.body.style.overflow = 'hidden';

        // Fechar o menu lateral se estiver aberto
        if (window.JC && window.JC.state && window.JC.state.menuAberto) {
            fecharMenu();
        }

        console.log('Modal de preferências aberto');
    }
}

function fecharModalPreferencias() {
    const modalPreferencias = document.getElementById('modalPreferencias');

    if (modalPreferencias) {
        modalPreferencias.classList.remove('ativo');
        document.body.style.overflow = '';

        console.log('Modal de preferências fechado');
    }
}

// ===================================================
// CARREGAR PREFERÊNCIAS
// ===================================================

function carregarPreferencias() {
    console.log('Carregando preferências...');

    // Verificar se usuário está logado
    const usuarioLogado = verificarUsuarioLogado();

    let categoriasSelecionadas = [];

    if (usuarioLogado) {
        // Carregar do servidor
        fetch('/api/preferencias/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.categorias) {
                categoriasSelecionadas = data.categorias;
                aplicarPreferenciasNoModal(categoriasSelecionadas);
                console.log('Preferências carregadas do servidor:', categoriasSelecionadas);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar preferências do servidor:', error);
            // Fallback para localStorage
            carregarPreferenciasLocal();
        });
    } else {
        // Carregar do localStorage (visitante)
        carregarPreferenciasLocal();
    }
}

function carregarPreferenciasLocal() {
    // Tentar carregar do cookie primeiro
    const preferenciasCookie = getCookie('categorias_preferidas');

    if (preferenciasCookie) {
        try {
            const categoriasSelecionadas = JSON.parse(preferenciasCookie);
            aplicarPreferenciasNoModal(categoriasSelecionadas);
            console.log('Preferências carregadas do cookie:', categoriasSelecionadas);
            return;
        } catch (e) {
            console.error('Erro ao parsear preferências do cookie:', e);
        }
    }

    // Fallback para localStorage
    const preferencias = localStorage.getItem('categorias_preferidas');

    if (preferencias) {
        try {
            const categoriasSelecionadas = JSON.parse(preferencias);
            aplicarPreferenciasNoModal(categoriasSelecionadas);
            console.log('Preferências carregadas do localStorage:', categoriasSelecionadas);

            // Migrar para cookie
            setCookie('categorias_preferidas', preferencias);
        } catch (e) {
            console.error('Erro ao parsear preferências do localStorage:', e);
        }
    }
}

function aplicarPreferenciasNoModal(categorias) {
    const checkboxes = document.querySelectorAll('.categoria-checkbox input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.checked = categorias.includes(checkbox.value);
    });
}

// ===================================================
// SALVAR PREFERÊNCIAS
// ===================================================

function salvarPreferencias() {
    console.log('Salvando preferências...');

    // Coletar categorias selecionadas
    const checkboxes = document.querySelectorAll('.categoria-checkbox input[type="checkbox"]:checked');
    const categoriasSelecionadas = Array.from(checkboxes).map(cb => cb.value);

    console.log('Categorias selecionadas:', categoriasSelecionadas);

    // Verificar se usuário está logado
    const usuarioLogado = verificarUsuarioLogado();

    if (usuarioLogado) {
        // Salvar no servidor
        salvarPreferenciasServidor(categoriasSelecionadas);
    } else {
        // Salvar no localStorage
        salvarPreferenciasLocal(categoriasSelecionadas);
    }

    // Fechar modal
    fecharModalPreferencias();

    // Redirecionar para a página inicial com preferências aplicadas
    setTimeout(() => {
        window.location.href = '/';
    }, 300);
}

function salvarPreferenciasServidor(categorias) {
    fetch('/api/preferencias/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'include',
        body: JSON.stringify({
            categorias: categorias
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Preferências salvas no servidor:', data);
        mostrarMensagemSucesso('Preferências salvas com sucesso!');

        // Também salvar no localStorage como backup
        salvarPreferenciasLocal(categorias);
    })
    .catch(error => {
        console.error('Erro ao salvar preferências no servidor:', error);
        // Fallback: salvar apenas no localStorage
        salvarPreferenciasLocal(categorias);
        mostrarMensagemSucesso('Preferências salvas localmente!');
    });
}

function salvarPreferenciasLocal(categorias) {
    try {
        const categoriasJSON = JSON.stringify(categorias);

        // Salvar em cookie (principal)
        setCookie('categorias_preferidas', categoriasJSON);
        console.log('Preferências salvas no cookie');
        console.log('Valor do cookie:', categoriasJSON);
        console.log('Categorias:', categorias);

        // Verificar se foi salvo corretamente
        const cookieVerificacao = getCookie('categorias_preferidas');
        console.log('Cookie verificado:', cookieVerificacao);

        // Também salvar no localStorage como backup
        localStorage.setItem('categorias_preferidas', categoriasJSON);
        console.log('Preferências salvas no localStorage (backup)');
    } catch (e) {
        console.error('Erro ao salvar preferências:', e);
    }
}

// ===================================================
// LIMPAR PREFERÊNCIAS
// ===================================================

function limparPreferencias() {
    console.log('Limpando preferências...');

    // Desmarcar todos os checkboxes
    const checkboxes = document.querySelectorAll('.categoria-checkbox input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });

    console.log('Todas as categorias desmarcadas');
}

// ===================================================
// BARRA DE PREFERÊNCIAS ATIVAS
// ===================================================

function verificarPreferenciasAtivas() {
    const usuarioLogado = verificarUsuarioLogado();
    let temPreferencias = false;

    if (usuarioLogado) {
        // Verificar no servidor
        fetch('/api/preferencias/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.categorias && data.categorias.length > 0) {
                mostrarBarraPreferencias();
            }
        })
        .catch(error => {
            console.error('Erro ao verificar preferências:', error);
            verificarPreferenciasLocal();
        });
    } else {
        verificarPreferenciasLocal();
    }
}

function verificarPreferenciasLocal() {
    // Verificar cookie primeiro
    const preferenciasCookie = getCookie('categorias_preferidas');

    if (preferenciasCookie) {
        try {
            const categorias = JSON.parse(preferenciasCookie);
            if (categorias && categorias.length > 0) {
                mostrarBarraPreferencias();
                return;
            }
        } catch (e) {
            console.error('Erro ao verificar preferências do cookie:', e);
        }
    }

    // Fallback para localStorage
    const preferencias = localStorage.getItem('categorias_preferidas');
    if (preferencias) {
        try {
            const categorias = JSON.parse(preferencias);
            if (categorias && categorias.length > 0) {
                mostrarBarraPreferencias();
            }
        } catch (e) {
            console.error('Erro ao verificar preferências locais:', e);
        }
    }
}

function mostrarBarraPreferencias() {
    const barra = document.getElementById('barraPreferenciasAtivas');
    if (barra) {
        barra.style.display = 'block';
        document.body.classList.add('preferencias-ativas');
    }
}

function ocultarBarraPreferencias() {
    const barra = document.getElementById('barraPreferenciasAtivas');
    if (barra) {
        barra.style.display = 'none';
        document.body.classList.remove('preferencias-ativas');
    }
}

function limparTodasPreferencias() {
    if (!confirm('Deseja remover todas as preferências e ver todas as notícias?')) {
        return;
    }

    const usuarioLogado = verificarUsuarioLogado();

    // Limpar cookie
    deleteCookie('categorias_preferidas');
    console.log('Cookie de preferências removido');

    // Limpar localStorage
    localStorage.removeItem('categorias_preferidas');

    // Se logado, limpar no servidor
    if (usuarioLogado) {
        fetch('/api/preferencias/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include',
            body: JSON.stringify({
                categorias: []
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Preferências removidas do servidor');
        })
        .catch(error => {
            console.error('Erro ao remover preferências do servidor:', error);
        });
    }

    // Ocultar barra e recarregar
    ocultarBarraPreferencias();

    setTimeout(() => {
        window.location.reload();
    }, 300);
}

// ===================================================
// UTILITÁRIOS
// ===================================================

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

function mostrarMensagemSucesso(texto) {
    const mensagem = document.createElement('div');
    mensagem.className = 'mensagem-toast mensagem-sucesso';
    mensagem.textContent = texto;
    mensagem.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: #4CAF50;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10001;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        animation: slideUp 0.3s ease;
    `;

    document.body.appendChild(mensagem);

    // Remover após 3 segundos
    setTimeout(() => {
        mensagem.style.opacity = '0';
        mensagem.style.transform = 'translateX(-50%) translateY(20px)';
        mensagem.style.transition = 'all 0.3s ease';
        setTimeout(() => mensagem.remove(), 300);
    }, 3000);
}

// ===================================================
// EXPORTAR FUNÇÕES GLOBAIS
// ===================================================

window.PreferenciasJC = {
    abrir: abrirModalPreferencias,
    fechar: fecharModalPreferencias,
    salvar: salvarPreferencias,
    limpar: limparPreferencias,
    carregar: carregarPreferencias
};
