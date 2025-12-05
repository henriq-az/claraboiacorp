/* ===================================================
   BUSCA.JS - JORNAL DO COMMERCIO
   Sistema de Busca e Filtros
   =================================================== */

// ===================================================
// INICIALIZAÇÃO
// ===================================================

document.addEventListener('DOMContentLoaded', () => {
    inicializarBusca();
});

function inicializarBusca() {
    // Botão de busca
    configurarBotaoBusca();

    // Campo de busca
    configurarCampoBusca();

    // Filtros
    configurarFiltros();

    // Sugestões
    configurarSugestoes();

    // Busca por voz
    configurarBuscaVoz();
}

// ===================================================
// TOGGLE BUSCA
// ===================================================

function configurarBotaoBusca() {
    // Seleciona todos os botões de busca da página (header e menu inferior)
    const botoesBusca = document.querySelectorAll('.botao-busca');
    const barraBusca = document.getElementById('barraBusca');

    if (!botoesBusca || botoesBusca.length === 0 || !barraBusca) return;

    botoesBusca.forEach(botao => {
        // garantir que não será submetido como form
        botao.type = botao.type || 'button';
        botao.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleBusca();
        });
    });
}

function toggleBusca() {
    const barraBusca = document.getElementById('barraBusca');
    const campoBusca = document.querySelector('.campo-busca');
    const isAberta = barraBusca.classList.contains('ativa');
    if (isAberta) {
        fecharBusca();
    } else {
        abrirBusca();
    }
}

function abrirBusca() {
    const barraBusca = document.getElementById('barraBusca');
    const campoBusca = document.querySelector('.campo-busca');
    const botoesBusca = document.querySelectorAll('.botao-busca');

    barraBusca.classList.add('ativa');
    barraBusca.setAttribute('aria-hidden', 'false');
    window.JC.state.buscaAberta = true;

    // Adicionar classe ativo aos botões de busca (para ícone vermelho)
    botoesBusca.forEach(botao => botao.classList.add('ativo'));

    // Focar no campo após animação
    setTimeout(() => {
        campoBusca.focus();
    }, 300);
}

function fecharBusca() {
    const barraBusca = document.getElementById('barraBusca');
    const botoesBusca = document.querySelectorAll('.botao-busca');

    barraBusca.classList.remove('ativa');
    barraBusca.setAttribute('aria-hidden', 'true');
    window.JC.state.buscaAberta = false;

    // Remover classe ativo dos botões de busca (ícone volta ao normal)
    botoesBusca.forEach(botao => botao.classList.remove('ativo'));

    // Fechar filtros também
    fecharFiltros();

    // Limpar sugestões
    limparSugestoes();
}

// ===================================================
// CAMPO DE BUSCA
// ===================================================

function configurarCampoBusca() {
    const campoBusca = document.querySelector('.campo-busca');

    if (!campoBusca) return;

    // Input com debounce
    const buscarComDebounce = window.JC.utils.debounce((termo) => {
        if (termo.length >= 2) {
            buscarNoticias(termo);
            mostrarSugestoes(termo);
        } else {
            limparSugestoes();
        }
    }, 300);

    campoBusca.addEventListener('input', (e) => {
        const termo = e.target.value.trim();
        buscarComDebounce(termo);
    });

    // Enter para buscar
    campoBusca.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const termo = e.target.value.trim();
            if (termo) {
                executarBusca(termo);
            }
        }
    });

    // Limpar busca
    campoBusca.addEventListener('search', (e) => {
        if (e.target.value === '') {
            limparResultadosBusca();
        }
    });
}

// ===================================================
// FILTROS
// ===================================================

function configurarFiltros() {
    const botaoFiltros = document.querySelector('.botao-filtros');
    const filtrosBusca = document.getElementById('filtrosBusca');

    if (!botaoFiltros || !filtrosBusca) return;

    botaoFiltros.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFiltros();
    });

    // Aplicar filtros ao mudar
    const selects = filtrosBusca.querySelectorAll('select');
    selects.forEach(select => {
        select.addEventListener('change', aplicarFiltros);
    });
}

function toggleFiltros() {
    const filtrosBusca = document.getElementById('filtrosBusca');
    const isAberto = filtrosBusca.classList.contains('ativo');

    if (isAberto) {
        fecharFiltros();
    } else {
        abrirFiltros();
    }
}

function abrirFiltros() {
    const filtrosBusca = document.getElementById('filtrosBusca');
    filtrosBusca.classList.add('ativo');
    window.JC.state.filtrosAbertos = true;
}

function fecharFiltros() {
    const filtrosBusca = document.getElementById('filtrosBusca');
    filtrosBusca.classList.remove('ativo');
    window.JC.state.filtrosAbertos = false;
}

function aplicarFiltros() {
    const filtroData = document.querySelector('.filtro-data').value;
    const filtroCategoria = document.querySelector('.filtro-categoria').value;
    const filtroOrdenar = document.querySelector('.filtro-ordenar').value;

    const filtros = {
        data: filtroData,
        categoria: filtroCategoria,
        ordenar: filtroOrdenar
    };

    console.log('Aplicando filtros:', filtros);

    // Buscar com filtros
    const campoBusca = document.querySelector('.campo-busca');
    const termo = campoBusca.value.trim();

    if (termo) {
        buscarNoticias(termo, filtros);
    }
}

// ===================================================
// SUGESTÕES
// ===================================================

function configurarSugestoes() {
    // Criar container de sugestões se não existir
    if (!document.getElementById('sugestoesBusca')) {
        const barraBusca = document.getElementById('barraBusca');
        const sugestoesDiv = document.createElement('div');
        sugestoesDiv.id = 'sugestoesBusca';
        sugestoesDiv.className = 'sugestoes-busca';
        barraBusca.appendChild(sugestoesDiv);
    }
}

function mostrarSugestoes(termo) {
    const sugestoesDiv = document.getElementById('sugestoesBusca');

    // Simular sugestões (em produção viria do backend)
    const sugestoes = obterSugestoes(termo);

    if (sugestoes.length === 0) {
        sugestoesDiv.style.display = 'none';
        return;
    }

    // Criar HTML das sugestões
    const html = sugestoes.map(sugestao => `
        <div class="sugestao-item" data-termo="${sugestao}">
            <i class="fas fa-search"></i>
            <span>${destacarTermo(sugestao, termo)}</span>
        </div>
    `).join('');

    sugestoesDiv.innerHTML = html;
    sugestoesDiv.style.display = 'block';

    // Adicionar eventos
    sugestoesDiv.querySelectorAll('.sugestao-item').forEach(item => {
        item.addEventListener('click', () => {
            const termoSugestao = item.dataset.termo;
            document.querySelector('.campo-busca').value = termoSugestao;
            executarBusca(termoSugestao);
            limparSugestoes();
        });
    });
}

function obterSugestoes(termo) {
    // Sugestões mockadas - em produção viria do backend
    const todasSugestoes = [
        'política pernambuco',
        'política nacional',
        'eleições 2024',
        'economia brasil',
        'esportes recife',
        'sport recife',
        'cultura pernambuco',
        'educação pública',
        'mobilidade urbana',
        'saúde pública',
        'covid pernambuco',
        'vacinação recife'
    ];

    return todasSugestoes
        .filter(s => s.toLowerCase().includes(termo.toLowerCase()))
        .slice(0, 5);
}

function destacarTermo(texto, termo) {
    const regex = new RegExp(`(${termo})`, 'gi');
    return texto.replace(regex, '<strong>$1</strong>');
}

function limparSugestoes() {
    const sugestoesDiv = document.getElementById('sugestoesBusca');
    if (sugestoesDiv) {
        sugestoesDiv.innerHTML = '';
        sugestoesDiv.style.display = 'none';
    }
}

// ===================================================
// BUSCA POR VOZ
// ===================================================

function configurarBuscaVoz() {
    // Verificar se o navegador suporta
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        console.log('Busca por voz não suportada');
        return;
    }

    // Adicionar botão de voz
    adicionarBotaoVoz();
}

function adicionarBotaoVoz() {
    const buscarContainer = document.querySelector('.busca-container');
    if (!buscarContainer) return;

    const botaoVoz = document.createElement('button');
    botaoVoz.className = 'botao-voz';
    botaoVoz.innerHTML = '<i class="fas fa-microphone"></i>';
    botaoVoz.setAttribute('aria-label', 'Busca por voz');

    buscarContainer.appendChild(botaoVoz);

    botaoVoz.addEventListener('click', iniciarBuscaVoz);
}

function iniciarBuscaVoz() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = 'pt-BR';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    const botaoVoz = document.querySelector('.botao-voz');
    botaoVoz.classList.add('gravando');

    recognition.start();

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.querySelector('.campo-busca').value = transcript;
        executarBusca(transcript);
        botaoVoz.classList.remove('gravando');
    };

    recognition.onerror = (event) => {
        console.error('Erro na busca por voz:', event.error);
        botaoVoz.classList.remove('gravando');
        mostrarMensagem('Erro ao capturar áudio', 'erro');
    };

    recognition.onend = () => {
        botaoVoz.classList.remove('gravando');
    };
}

// ===================================================
// EXECUÇÃO DA BUSCA
// ===================================================

function buscarNoticias(termo, filtros = {}) {
    console.log('Buscando:', termo, 'Filtros:', filtros);

    // Mostrar loading
    mostrarLoadingBusca();

    // Simular busca (em produção seria uma chamada API)
    setTimeout(() => {
        const resultados = simularResultadosBusca(termo, filtros);
        mostrarResultadosBusca(resultados, termo);
        esconderLoadingBusca();
    }, 500);
}

function executarBusca(termo) {
    console.log('Executando busca completa:', termo);

    // Salvar no histórico
    salvarHistoricoBusca(termo);

    // Aplicar filtros se existirem
    const filtros = {
        data: document.querySelector('.filtro-data')?.value,
        categoria: document.querySelector('.filtro-categoria')?.value,
        ordenar: document.querySelector('.filtro-ordenar')?.value
    };

    // Navegar para a rota de busca do servidor, incluindo filtros
    const params = new URLSearchParams();
    params.set('q', termo);
    if (filtros.data) params.set('data', filtros.data);
    if (filtros.categoria) params.set('categoria', filtros.categoria);
    if (filtros.ordenar) params.set('ordenar', filtros.ordenar);

    // Redirecionar para a view Django que já pesquisa por título/resumo/conteúdo
    window.location.href = '/buscar/?' + params.toString();
}

function simularResultadosBusca(termo, filtros) {
    // Simulação de resultados
    const todasNoticias = [
        {
            id: 1,
            titulo: 'Governo anuncia novas medidas econômicas',
            categoria: 'economia',
            data: new Date('2024-01-15'),
            relevancia: 10
        },
        {
            id: 2,
            titulo: 'Sport vence clássico e assume liderança',
            categoria: 'esportes',
            data: new Date('2024-01-14'),
            relevancia: 8
        },
        {
            id: 3,
            titulo: 'Nova linha de metrô é inaugurada no Recife',
            categoria: 'mobilidade',
            data: new Date('2024-01-13'),
            relevancia: 9
        }
    ];

    // Filtrar por termo
    let resultados = todasNoticias.filter(n =>
        n.titulo.toLowerCase().includes(termo.toLowerCase())
    );

    // Aplicar filtros
    if (filtros.categoria) {
        resultados = resultados.filter(n => n.categoria === filtros.categoria);
    }

    // Ordenar
    if (filtros.ordenar === 'recentes') {
        resultados.sort((a, b) => b.data - a.data);
    } else if (filtros.ordenar === 'relevancia') {
        resultados.sort((a, b) => b.relevancia - a.relevancia);
    }

    return resultados;
}

// ===================================================
// EXIBIÇÃO DE RESULTADOS
// ===================================================

function mostrarResultadosBusca(resultados, termo) {
    const feedNoticias = document.getElementById('feedNoticias');

    if (resultados.length === 0) {
        feedNoticias.innerHTML = `
            <div class="sem-resultados">
                <i class="fas fa-search"></i>
                <h3>Nenhum resultado para "${termo}"</h3>
                <p>Tente buscar com outras palavras</p>
            </div>
        `;
        return;
    }

    // Criar cards de resultado
    const html = resultados.map(noticia => criarCardResultado(noticia)).join('');

    feedNoticias.innerHTML = `
        <div class="resultados-busca">
            <div class="resultados-header">
                <h2>${resultados.length} resultados para "${termo}"</h2>
                <button class="botao-limpar-busca">Limpar busca</button>
            </div>
            <div class="resultados-lista">
                ${html}
            </div>
        </div>
    `;

    // Botão limpar
    document.querySelector('.botao-limpar-busca').addEventListener('click', limparResultadosBusca);
}

function criarCardResultado(noticia) {
    return `
        <article class="cartao-noticia">
            <div class="cartao-conteudo">
                <span style="font-size: 0.75rem; font-weight: 500; color: #dc2626; text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 8px;">${noticia.categoria}</span>
                <h3 class="cartao-titulo">${noticia.titulo}</h3>
                <time class="cartao-tempo">${window.JC.utils.formatarData(noticia.data)}</time>
            </div>
        </article>
    `;
}

function limparResultadosBusca() {
    location.reload(); // Recarregar para mostrar feed normal
}

// ===================================================
// LOADING
// ===================================================

function mostrarLoadingBusca() {
    const feedNoticias = document.getElementById('feedNoticias');
    feedNoticias.innerHTML = `
        <div class="loading-busca">
            <div class="spinner"></div>
            <p>Buscando notícias...</p>
        </div>
    `;
}

function esconderLoadingBusca() {
    // O loading é substituído pelos resultados
}

// ===================================================
// HISTÓRICO
// ===================================================

function salvarHistoricoBusca(termo) {
    let historico = JSON.parse(localStorage.getItem('historicoBusca') || '[]');

    // Remover duplicatas
    historico = historico.filter(h => h !== termo);

    // Adicionar no início
    historico.unshift(termo);

    // Limitar a 10 itens
    historico = historico.slice(0, 10);

    localStorage.setItem('historicoBusca', JSON.stringify(historico));
}

// ===================================================
// ESTILOS ADICIONAIS
// ===================================================

const style = document.createElement('style');
style.textContent = `
    .sugestoes-busca {
        position: absolute;
        top: 100%;
        left: var(--espacamento-mobile);
        right: var(--espacamento-mobile);
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-top: 8px;
        display: none;
        z-index: 100;
    }

    .sugestao-item {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: background 0.2s;
    }

    .sugestao-item:hover {
        background: #F3F4F6;
    }

    .sugestao-item i {
        color: #9CA3AF;
        font-size: 14px;
    }

    .botao-voz {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F3F4F6;
        border-radius: 50%;
        color: #6B7280;
    }

    .botao-voz.gravando {
        background: #DC2626;
        color: white;
        animation: pulse 1.5s infinite;
    }

    .loading-busca {
        text-align: center;
        padding: 48px;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid #F3F4F6;
        border-top-color: #DC2626;
        border-radius: 50%;
        margin: 0 auto 16px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .sem-resultados {
        text-align: center;
        padding: 48px;
        color: #6B7280;
    }

    .sem-resultados i {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
    }

    .resultados-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding: 0 var(--espacamento-mobile);
    }

    .botao-limpar-busca {
        padding: 8px 16px;
        background: #F3F4F6;
        color: #6B7280;
        border-radius: 6px;
        font-size: 14px;
    }
`;
document.head.appendChild(style);