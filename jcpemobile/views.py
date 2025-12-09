# jcpemobile/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, Max
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Noticia, Visualizacao, NoticaSalva, Categoria, Autor, Feedback, Enquete, Voto, Opcao, Tag, PerfilUsuario, NoticiaLinhaDoTempo
from .forms import CadastroUsuarioForm, NoticiaForm, FeedbackForm
from django.db import IntegrityError
import json
from django.core.paginator import Paginator

def get_client_ip(request):
    fake_ip_post = request.POST.get('fake_ip')
    if fake_ip_post:
        return fake_ip_post

    fake_ip = request.GET.get('fake_ip')  # Exemplo: http://127.0.0.1:8000/noticias/noticia_teste/?fake_ip=222.222.222.222
    if fake_ip:
        return fake_ip

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def index(request):
    """View para a página inicial"""
    hoje = timezone.now().date()

    # Verificar se há preferências de categorias ANTES de buscar notícias
    categorias_preferidas = None

    # Se usuário está logado, buscar preferências do perfil
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)
        if perfil:
            categorias_preferidas = list(perfil.categorias_preferidas.values_list('slug', flat=True))

    # Se não está logado ou não tem preferências no perfil, tentar ler do cookie
    if not categorias_preferidas:
        # Tentar ler do cookie (para visitantes)
        categorias_cookie = request.COOKIES.get('categorias_preferidas', '')
        print(f"[DEBUG] Cookie raw recebido: {repr(categorias_cookie)}")
        if categorias_cookie:
            try:
                # O cookie pode estar URL encoded, então precisamos decodificar
                from urllib.parse import unquote
                categorias_cookie_decoded = unquote(categorias_cookie)
                print(f"[DEBUG] Cookie decodificado: {repr(categorias_cookie_decoded)}")

                categorias_preferidas = json.loads(categorias_cookie_decoded)
                if not isinstance(categorias_preferidas, list):
                    categorias_preferidas = None
                else:
                    print(f"[DEBUG] Categorias do cookie: {categorias_preferidas}")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[DEBUG] Erro ao parsear cookie: {e}")
                categorias_preferidas = None

        # Fallback: tentar GET param
        if not categorias_preferidas:
            categorias_param = request.GET.get('categorias', '')
            if categorias_param:
                categorias_preferidas = [c.strip() for c in categorias_param.split(',') if c.strip()]

    # Buscar notícias mais vistas do dia (aplicando filtro de categorias se houver)
    noticias_query = Noticia.objects.all()

    if categorias_preferidas:
        print(f"[DEBUG] Filtrando por categorias: {categorias_preferidas}")
        noticias_query = noticias_query.filter(categoria__slug__in=categorias_preferidas)

    noticias_mais_vistas = noticias_query.annotate(
        visualizacoes_dia=Count('visualizacoes', filter=Q(visualizacoes__data=hoje))
    ).order_by('-visualizacoes_dia', '-data_publicacao')[:9]

    # Filtrar todas as notícias por categorias preferidas se existirem
    if categorias_preferidas:
        todas_noticias = Noticia.objects.filter(
            categoria__slug__in=categorias_preferidas
        ).select_related('categoria', 'autor').order_by('-data_publicacao')
        print(f"[DEBUG] Total de notícias filtradas: {todas_noticias.count()}")
    else:
        # Pegar todas as notícias se não houver preferências
        todas_noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')
        print(f"[DEBUG] Sem filtro - Total de notícias: {todas_noticias.count()}")

    # Filtrar notícias por seção
    noticias_do_dia = todas_noticias.filter(secao='noticia_do_dia')[:4]
    noticias_social1 = todas_noticias.filter(secao='social1')[:6]
    noticias_jc360 = todas_noticias.filter(secao='jc360')[:6]
    noticias_pernambuco = todas_noticias.filter(secao='pernambuco')[:6]
    noticias_blog_torcedor = todas_noticias.filter(secao='blog_do_torcedor')[:6]
    noticias_ultimas = todas_noticias.filter(secao='ultimas_noticias')[:4]
    noticias_receita = todas_noticias.filter(secao='receita_da_boa')[:6]

    # Top 3 notícias mais vistas para o ranking
    noticias_ranking = noticias_mais_vistas[:3]

    context = {
        'noticias_mais_vistas': noticias_mais_vistas,
        'noticias_ranking': noticias_ranking,
        'todas_noticias': todas_noticias,
        'noticias_do_dia': noticias_do_dia,
        'noticias_social1': noticias_social1,
        'noticias_jc360': noticias_jc360,
        'noticias_pernambuco': noticias_pernambuco,
        'noticias_blog_torcedor': noticias_blog_torcedor,
        'noticias_ultimas': noticias_ultimas,
        'noticias_receita': noticias_receita,
    }
    return render(request, 'index.html', context)

def lista_por_categoria(request, slug):
    todas_noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao') 
    hoje = timezone.now().date()

    print(f"[DEBUG] Total geral: {todas_noticias.count()}")

    # Filtrar pela categoria
    noticias_categoria = todas_noticias.filter(categoria__slug=slug)

    print(f"[DEBUG] Categoria {slug} - Total filtrado: {noticias_categoria.count()}")
    
    noticias_salvas_ids = []
    if request.user.is_authenticated:
        noticias_salvas_ids = NoticaSalva.objects.filter(usuario=request.user).values_list('noticia_id', flat=True) 

    noticia_principal = noticias_categoria.first()

    destaque_categoria = (
    noticias_categoria
    .annotate(
        num_visualizacoes=Count(
            'visualizacoes',
            filter=Q(visualizacoes__data=hoje)
        )
    )
    .filter(num_visualizacoes__gt=0)
    .order_by('-num_visualizacoes')[:15]
)


    # noticias relacionadas com a noticia mais recente da categoria
    noticias_relacionadas = []
    if noticia_principal:
        tags_ids = noticia_principal.tags.values_list('id', flat=True)

        if tags_ids:
            noticias_relacionadas = Noticia.objects.filter(
                categoria__slug=slug,
                tags__id__in=tags_ids
            ).exclude(
                id=noticia_principal.id
            ).distinct().select_related(
                'categoria', 'autor'
            ).order_by('-data_publicacao')[:2] # buscar 2 relacionadas

        # Se não encontrou relacionadas por tags, buscar apenas da mesma categoria
        if len(noticias_relacionadas) < 2:
            faltam = 2 - len(noticias_relacionadas)

            outras = Noticia.objects.filter(
                categoria__slug=slug
            ).exclude(
                id__in=[noticia_principal.id] + [n.id for n in noticias_relacionadas]
            ).select_related(
                'categoria', 'autor'
            ).order_by('-data_publicacao')[:faltam]

            # juntar resultados sem duplicar
            noticias_relacionadas = list(noticias_relacionadas) + list(outras)

    context = {
        'categoria': Categoria.objects.get(slug=slug),
        'noticias': noticias_categoria,
        'noticias_salvas_ids': noticias_salvas_ids,
        "noticias_relacionadas": noticias_relacionadas,
        "destaque_categoria": destaque_categoria,
    }

    return render(request, 'categoria.html', context)


# Página com todas as enquetes
def lista_enquetes(request):
    enquetes = Enquete.objects.all()
    return render(request, 'enquetes.html', {'enquetes': enquetes})


# Página de detalhe/votação de uma enquete
def detalhe_enquete(request, enquete_id):
    enquete = get_object_or_404(Enquete, id=enquete_id)

    # IMPORTANT: get_client_ip agora lê POST/GET fake_ip também
    ip_usuario = get_client_ip(request)
    ja_votou = Voto.objects.filter(opcao__enquete=enquete, ip_usuario=ip_usuario).exists()

    if request.method == 'POST':
        if ja_votou:
            # avisar que já votou
            messages.warning(request, "Você já votou nesta enquete com o IP atual.")
        else:
            opcao_id = request.POST.get('opcao')
            # validação adicional: opcao_id existe
            opcao = get_object_or_404(Opcao, id=opcao_id, enquete=enquete)
            Voto.objects.create(opcao=opcao, ip_usuario=ip_usuario)
            messages.success(request, "Voto registrado com sucesso!")
        # redireciona para a mesma página para evitar reenvio de formulário
        # preservando querystring (ex.: ?fake_ip=1.2.3.4) para conveniência de testes
        redirect_url = request.path
        qs = request.META.get('QUERY_STRING')
        if qs:
            redirect_url = f"{redirect_url}?{qs}"
        return redirect(redirect_url)

    opcoes = enquete.opcoes.all()
    total_votos = enquete.total_votos()

    contexto = {
        'enquete': enquete,
        'opcoes': opcoes,
        'total_votos': total_votos,
        'ja_votou': ja_votou,
    }

    return render(request, 'detalhe_enquete.html', contexto)


def neels(request):
    """View para a página Neels"""
    # Pegar apenas notícias que possuem imagem vertical, ordenadas por data de publicação
    noticias = Noticia.objects.select_related('categoria', 'autor').filter(
        imagem_vertical__isnull=False
    ).exclude(imagem_vertical='').order_by('-data_publicacao')

    context = {
        'noticias': noticias,
    }
    return render(request, 'neels.html', context)

def noticia_detalhe(request, slug):
    noticia = get_object_or_404(Noticia, slug=slug)
    ip = get_client_ip(request)

    # Cria uma visualização apenas se o IP ainda não tiver registrado essa notícia hoje
    if not Visualizacao.objects.filter(noticia=noticia, ip_address=ip, data=timezone.now().date()).exists():
        Visualizacao.objects.create(
            noticia=noticia,
            ip_address=ip,
            data=timezone.now().date()  # Set the date field
        )

    # Verificar se o usuário já salvou esta notícia
    noticia_salva = False
    if request.user.is_authenticated:
        noticia_salva = NoticaSalva.objects.filter(usuario=request.user, noticia=noticia).exists()

    # Processar votação da enquete se houver
    ja_votou_enquete = False
    enquete = None
    if hasattr(noticia, 'enquete'):
        enquete = noticia.enquete

        # Verificar se já votou
        ja_votou_enquete = Voto.objects.filter(
            opcao__enquete=enquete,
            ip_usuario=ip
        ).exists()

        # Processar voto se for POST
        if request.method == 'POST' and not ja_votou_enquete:
            opcao_id = request.POST.get('opcao_id')
            if opcao_id:
                try:
                    opcao = Opcao.objects.get(id=opcao_id, enquete=enquete)
                    Voto.objects.create(opcao=opcao, ip_usuario=ip)
                    ja_votou_enquete = True
                    messages.success(request, 'Voto registrado com sucesso!')
                    return redirect('noticia_detalhe', slug=slug)
                except Opcao.DoesNotExist:
                    messages.error(request, 'Opção inválida.')
        elif request.method == 'POST' and ja_votou_enquete:
            messages.warning(request, 'Você já votou nesta enquete.')

    # Buscar linhas do tempo que contêm esta notícia
    from .models import LinhaDoTempo

    linhas_tempo_noticia = NoticiaLinhaDoTempo.objects.filter(
        noticia=noticia,
        linha_tempo__ativa=True
    ).select_related('linha_tempo').prefetch_related(
        'linha_tempo__noticias__noticia__categoria'
    )

    # Preparar dados das linhas do tempo para o template
    linhas_tempo_data = []
    for item in linhas_tempo_noticia:
        linha_tempo = item.linha_tempo

        # Buscar todas as notícias desta linha do tempo, ordenadas por data de publicação
        noticias_linha = NoticiaLinhaDoTempo.objects.filter(
            linha_tempo=linha_tempo
        ).select_related('noticia__categoria', 'noticia__autor').order_by('-noticia__data_publicacao')

        linhas_tempo_data.append({
            'linha_tempo': linha_tempo,
            'noticias': [item.noticia for item in noticias_linha],
            'total_noticias': noticias_linha.count()
        })

    # Buscar notícias relacionadas (sempre exibir)
    noticias_relacionadas = []

    # Buscar notícias relacionadas automaticamente
    if noticia.categoria:
        # Obter IDs das tags da notícia atual
        tags_ids = noticia.tags.values_list('id', flat=True)

        if tags_ids:
            # Buscar notícias da mesma categoria que compartilham pelo menos uma tag
            noticias_relacionadas = Noticia.objects.filter(
                categoria=noticia.categoria,
                tags__id__in=tags_ids
            ).exclude(
                id=noticia.id
            ).distinct().select_related('categoria', 'autor').order_by('-data_publicacao')[:6]

        # Se não encontrou notícias com tags em comum, buscar apenas da mesma categoria
        if len(noticias_relacionadas) == 0:
            noticias_relacionadas = Noticia.objects.filter(
                categoria=noticia.categoria
            ).exclude(
                id=noticia.id
            ).select_related('categoria', 'autor').order_by('-data_publicacao')[:6]

    return render(request, 'detalhes_noticia.html', {
        'noticia': noticia,
        'noticia_salva': noticia_salva,
        'noticias_relacionadas': noticias_relacionadas,
        'linhas_tempo': linhas_tempo_data,
        'enquete': enquete,
        'ja_votou_enquete': ja_votou_enquete
    })


@require_http_methods(["GET", "POST"])
def cadastro_usuario(request):
    """View para cadastro de novo usuário"""
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                form = CadastroUsuarioForm(data)
                
                if form.is_valid():
                    user = form.save()
                    login(request, user)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Cadastro realizado com sucesso.',
                        'redirect_url': '/'
                    })
                else:
                    errors = {}
                    for field, error_list in form.errors.items():
                        errors[field] = error_list[0] if error_list else ''
                    
                    return JsonResponse({
                        'success': False,
                        'errors': errors
                    })
            
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': 'Erro ao processar dados.'}
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': str(e)}
                })
        else:
            form = CadastroUsuarioForm(request.POST)
            
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'Cadastro realizado com sucesso.')
                return redirect('index')
            else:
                for error in form.non_field_errors():
                    messages.error(request, error)
    
    # Se não for POST, redireciona para a home (cadastro agora é apenas modal)
    return redirect('index')



def login_usuario(request):
    """View para login de usuário"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        # Verificar se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        # Tenta encontrar o usuário pelo email
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(email=email)
            # Autentica usando o username
            user = authenticate(request, username=user.username, password=senha)
            
            if user is not None:
                login(request, user)
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Login realizado com sucesso!',
                        'redirect_url': '/'
                    })
                else:
                    messages.success(request, 'Login realizado com sucesso!')
                    return redirect('index')
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'E-mail ou senha incorretos.'
                    })
                else:
                    messages.error(request, 'E-mail ou senha incorretos.')
        except User.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'E-mail ou senha incorretos.'
                })
            else:
                messages.error(request, 'E-mail ou senha incorretos.')
    
    return redirect('index')


def logout_usuario(request):
    """View para logout de usuário"""
    logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('index')


def salvos(request):
    """View para página de notícias salvas"""
    salvos_list = []
    if request.user.is_authenticated:
        salvos_list = NoticaSalva.objects.filter(usuario=request.user).select_related('noticia', 'noticia__categoria', 'noticia__autor').order_by('-data_salvamento')
    
    return render(request, 'salvos.html', {'salvos_list': salvos_list})


def mais_lidas(request):
    """View para página de notícias mais lidas"""
    hoje = timezone.now().date()
    semana_atras = hoje - timezone.timedelta(days=7)
    mes_atras = hoje - timezone.timedelta(days=30)

    noticias = Noticia.objects.all()

    # Hoje
    noticias_hoje = noticias.annotate(
        num_visualizacoes=Count(
            'visualizacoes',
            filter=Q(visualizacoes__data=hoje)
        )
    ).filter(num_visualizacoes__gt=0).order_by('-num_visualizacoes')[:15]

    # Semana
    noticias_semana = noticias.annotate(
        num_visualizacoes=Count(
            'visualizacoes',
            filter=Q(visualizacoes__data__gte=semana_atras)
        )
    ).filter(num_visualizacoes__gt=0).order_by('-num_visualizacoes')[:15]

    # Mês
    noticias_mes = noticias.annotate(
        num_visualizacoes=Count(
            'visualizacoes',
            filter=Q(visualizacoes__data__gte=mes_atras)
        )
    ).filter(num_visualizacoes__gt=0).order_by('-num_visualizacoes')[:15]

    # Todos os tempos
    noticias_geral = noticias.annotate(
        total_visualizacoes=Count('visualizacoes')
    ).filter(total_visualizacoes__gt=0).order_by('-total_visualizacoes')[:15]


    noticias_salvas_ids = []
    if request.user.is_authenticated:
        noticias_salvas_ids = NoticaSalva.objects.filter(usuario=request.user).values_list('noticia_id', flat=True)
        
    context = { 
        'noticias_hoje': noticias_hoje,
        'noticias_semana': noticias_semana,
        'noticias_mes': noticias_mes,
        'noticias_geral': noticias_geral,
        'noticias_salvas_ids': noticias_salvas_ids,
    }

    return render(request, 'mais_lidas.html', context)



def painel_diario(request):
    """View para a página Painel Diário"""
    return render(request, 'painel_diario.html')


@require_http_methods(["POST"])
def salvar_noticia(request, noticia_id):
    """View para salvar uma notícia"""
    # Verificar autenticação
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Faça login para salvar notícias'
        }, status=401)

    noticia = get_object_or_404(Noticia, id=noticia_id)

    try:
        # Tenta criar o salvamento
        NoticaSalva.objects.create(usuario=request.user, noticia=noticia)
        return JsonResponse({
            'success': True,
            'message': 'Notícia salva com sucesso!',
            'salva': True
        })
    except IntegrityError:
        # Se já existe, significa que o usuário está tentando salvar novamente
        return JsonResponse({
            'success': False,
            'message': 'Você já salvou esta notícia.',
            'salva': True
        })


@require_http_methods(["POST"])
def remover_noticia_salva(request, noticia_id):
    """View para remover uma notícia salva"""
    # Verificar autenticação
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Faça login para gerenciar notícias salvas'
        }, status=401)

    noticia = get_object_or_404(Noticia, id=noticia_id)

    try:
        noticia_salva = NoticaSalva.objects.get(usuario=request.user, noticia=noticia)
        noticia_salva.delete()
        return JsonResponse({
            'success': True,
            'message': 'Notícia removida dos salvos!',
            'salva': False
        })
    except NoticaSalva.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Esta notícia não está nos seus salvos.',
            'salva': False
        })


def verificar_noticia_salva(request, noticia_id):
    """View para verificar se uma notícia está salva"""
    # Se não estiver autenticado, retornar que não está salva
    if not request.user.is_authenticated:
        return JsonResponse({
            'salva': False
        })

    noticia = get_object_or_404(Noticia, id=noticia_id)

    salva = NoticaSalva.objects.filter(usuario=request.user, noticia=noticia).exists()

    return JsonResponse({
        'salva': salva
    })


@require_http_methods(["POST"])
def enviar_feedback(request):
    """View para processar o envio de feedback"""
    try:
        # Verificar o Content-Type para decidir como processar
        content_type = request.content_type

        if content_type and 'application/json' in content_type:
            # Dados enviados via JSON
            try:
                data = json.loads(request.body)
                form = FeedbackForm(data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Erro ao processar os dados. Por favor, tente novamente.'
                }, status=400)
        else:
            # Dados enviados via FormData (multipart/form-data ou application/x-www-form-urlencoded)
            form = FeedbackForm(request.POST, request.FILES)

        if form.is_valid():
            feedback = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Obrigado pelo seu feedback! Sua opinião é muito importante para nós.'
            })
        else:
            # Retorna os erros do formulário
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else ''

            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': 'Por favor, corrija os erros no formulário.'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao enviar feedback: {str(e)}'
        }, status=500)


# ========== VIEWS DE ADMIN ==========

def is_staff(user):
    """Verifica se o usuário é staff/admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_staff, login_url='login_usuario')
def admin_dashboard(request):
    """View para o painel administrativo"""
    hoje = timezone.now().date()

    # Estatísticas
    total_noticias = Noticia.objects.count()
    total_categorias = Categoria.objects.count()
    total_autores = Autor.objects.count()
    visualizacoes_hoje = Visualizacao.objects.filter(data=hoje).count()

    # Listar todas as notícias
    noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')

    context = {
        'total_noticias': total_noticias,
        'total_categorias': total_categorias,
        'total_autores': total_autores,
        'visualizacoes_hoje': visualizacoes_hoje,
        'noticias': noticias,
    }

    return render(request, 'admin_dashboard.html', context)


@user_passes_test(is_staff, login_url='login_usuario')
def admin_criar_noticia(request):
    """View para criar uma nova notícia"""
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save()

            # Processar enquete se existir
            tem_enquete = request.POST.get('tem_enquete') == 'on'
            if tem_enquete:
                titulo_enquete = request.POST.get('titulo_enquete', '').strip()
                pergunta_enquete = request.POST.get('pergunta_enquete', '').strip()

                if titulo_enquete and pergunta_enquete:
                    # Criar enquete
                    enquete = Enquete.objects.create(
                        titulo=titulo_enquete,
                        pergunta=pergunta_enquete,
                        noticia=noticia
                    )

                    # Criar opções
                    opcoes = request.POST.getlist('opcao[]')
                    opcoes_criadas = 0
                    for texto_opcao in opcoes:
                        texto_opcao = texto_opcao.strip()
                        if texto_opcao:
                            Opcao.objects.create(enquete=enquete, texto=texto_opcao)
                            opcoes_criadas += 1
                    
                    # Validar se pelo menos 2 opções foram criadas
                    if opcoes_criadas < 2:
                        enquete.delete()
                        messages.warning(request, f'Notícia criada, mas a enquete precisa ter no mínimo 2 opções.')
                    else:
                        messages.success(request, f'Notícia "{noticia.titulo}" criada com sucesso com enquete!')
                        return redirect('admin_dashboard')
                else:
                    messages.warning(request, f'Notícia criada, mas a enquete precisa ter título e pergunta.')
            else:
                messages.success(request, f'Notícia "{noticia.titulo}" criada com sucesso!')
            
            return redirect('admin_dashboard')
    else:
        form = NoticiaForm()

    return render(request, 'admin_form_noticia.html', {'form': form})


@user_passes_test(is_staff, login_url='login_usuario')
def admin_editar_noticia(request, noticia_id):
    """View para editar uma notícia existente"""
    noticia = get_object_or_404(Noticia, id=noticia_id)

    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            noticia = form.save()

            # Processar enquete
            tem_enquete = request.POST.get('tem_enquete') == 'on'

            if tem_enquete:
                titulo_enquete = request.POST.get('titulo_enquete', '').strip()
                pergunta_enquete = request.POST.get('pergunta_enquete', '').strip()

                if titulo_enquete and pergunta_enquete:
                    # Atualizar ou criar enquete
                    try:
                        enquete = noticia.enquete
                        # Enquete já existe, atualizar
                        enquete.titulo = titulo_enquete
                        enquete.pergunta = pergunta_enquete
                        enquete.save()
                        # Deletar opções antigas
                        enquete.opcoes.all().delete()
                    except Enquete.DoesNotExist:
                        # Enquete não existe, criar nova
                        enquete = Enquete.objects.create(
                            titulo=titulo_enquete,
                            pergunta=pergunta_enquete,
                            noticia=noticia
                        )

                    # Criar opções
                    opcoes = request.POST.getlist('opcao[]')
                    opcoes_criadas = 0
                    for texto_opcao in opcoes:
                        texto_opcao = texto_opcao.strip()
                        if texto_opcao:
                            Opcao.objects.create(enquete=enquete, texto=texto_opcao)
                            opcoes_criadas += 1
                    
                    # Validar se pelo menos 2 opções foram criadas
                    if opcoes_criadas < 2:
                        enquete.delete()
                        messages.warning(request, f'Notícia atualizada, mas a enquete foi removida (precisa ter no mínimo 2 opções).')
                    else:
                        messages.success(request, f'Notícia "{noticia.titulo}" atualizada com sucesso!')
                else:
                    messages.warning(request, f'Notícia atualizada, mas a enquete precisa ter título e pergunta.')
            else:
                # Se não tem enquete mas tinha antes, deletar
                try:
                    noticia.enquete.delete()
                    messages.success(request, f'Notícia "{noticia.titulo}" atualizada e enquete removida.')
                except Enquete.DoesNotExist:
                    messages.success(request, f'Notícia "{noticia.titulo}" atualizada com sucesso!')

            return redirect('admin_dashboard')
    else:
        form = NoticiaForm(instance=noticia)

    return render(request, 'admin_form_noticia.html', {'form': form, 'noticia': noticia})


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def admin_deletar_noticia(request, noticia_id):
    """View para deletar uma notícia"""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    titulo = noticia.titulo
    noticia.delete()
    messages.success(request, f'Notícia "{titulo}" deletada com sucesso!')
    return redirect('admin_dashboard')


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def admin_criar_autor(request):
    """View API para criar um novo autor via AJAX"""
    try:
        data = json.loads(request.body)
        nome = data.get('nome', '').strip()
        bio = data.get('bio', '').strip()
        
        if not nome:
            return JsonResponse({
                'success': False,
                'error': 'O nome do autor é obrigatório.'
            }, status=400)
        
        # Verificar se já existe um autor com esse nome
        if Autor.objects.filter(nome=nome).exists():
            return JsonResponse({
                'success': False,
                'error': 'Já existe um autor com esse nome.'
            }, status=400)
        
        # Criar o novo autor
        autor = Autor.objects.create(nome=nome, bio=bio)
        
        return JsonResponse({
            'success': True,
            'autor': {
                'id': autor.id,
                'nome': autor.nome
            },
            'message': f'Autor "{autor.nome}" criado com sucesso!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar dados.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ========== API PARA TAGS, FILTROS E PREFERÊNCIAS ==========
def listar_tags(request):
    """Retorna lista de tags e contagem de notícias por tag (JSON)."""
    tags = Tag.objects.all().annotate(noticias_count=Count('noticias'))
    data = [{'id': t.id, 'nome': t.nome, 'noticias_count': t.noticias_count} for t in tags]
    return JsonResponse({'tags': data})


def noticias_por_tags(request):
    """Lista notícias filtradas por tags.

    Query params:
      - tags: lista separada por vírgula de ids ou nomes (ex: tags=1,2 ou tags=politica,esporte)
      - match: 'any' (default) ou 'all' — 'all' tenta exigir todas as tags (apenas para ids)
    """
    tags_param = request.GET.get('tags', '')
    match = request.GET.get('match', 'any')

    if not tags_param:
        noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')[:50]
    else:
        tag_list = [x.strip() for x in tags_param.split(',') if x.strip()]
        tag_ids = [int(x) for x in tag_list if x.isdigit()]
        tag_names = [x for x in tag_list if not x.isdigit()]

        if match == 'all' and tag_ids:
            # Filtrar notícias que tenham todas as tags informadas (por id)
            noticias = Noticia.objects.all()
            for tid in tag_ids:
                noticias = noticias.filter(tags__id=tid)
            noticias = noticias.select_related('categoria', 'autor').distinct().order_by('-data_publicacao')[:200]
        else:
            q = Q()
            if tag_ids:
                q |= Q(tags__id__in=tag_ids)
            if tag_names:
                q |= Q(tags__nome__in=tag_names)
            noticias = Noticia.objects.filter(q).select_related('categoria', 'autor').distinct().order_by('-data_publicacao')[:200]

    def serialize(n):
        return {
            'id': n.id,
            'titulo': n.titulo,
            'slug': n.slug,
            'resumo': n.resumo,
            'data_publicacao': n.data_publicacao.isoformat() if n.data_publicacao else None,
            'categoria': n.categoria.nome if n.categoria else None,
            'autor': n.autor.nome if n.autor else None,
            'tags': [t.nome for t in n.tags.all()]
        }

    data = [serialize(n) for n in noticias]
    return JsonResponse({'noticias': data})

def buscar(request):
    q = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)

    noticias = Noticia.objects.none()
    if q:
        noticias = Noticia.objects.filter(
            Q(titulo__icontains=q) |
            Q(resumo__icontains=q) |
            Q(conteudo__icontains=q)
        ).select_related('categoria', 'autor').order_by('-data_publicacao')

    paginator = Paginator(noticias, 20)  # 20 por página
    page_obj = paginator.get_page(page)

    return render(request, 'busca.html', {
        'q': q,
        'page_obj': page_obj,
        'total': noticias.count()
    })

def buscar_noticias_por_ids(request):
    """API para buscar notícias por IDs (para localStorage)

    Query params:
      - ids: lista separada por vírgula de IDs (ex: ids=1,2,3)
    """
    ids_param = request.GET.get('ids', '')

    if not ids_param:
        return JsonResponse([],  safe=False)

    try:
        ids = [int(x.strip()) for x in ids_param.split(',') if x.strip().isdigit()]

        noticias = Noticia.objects.filter(id__in=ids).select_related('categoria', 'autor')

        data = []
        for n in noticias:
            data.append({
                'id': n.id,
                'titulo': n.titulo,
                'slug': n.slug,
                'resumo': n.resumo,
                'imagem': n.imagem.url if n.imagem else None,
                'categoria': n.categoria.nome if n.categoria else 'Notícia',
                'data_publicacao': n.data_publicacao.isoformat() if n.data_publicacao else None,
            })

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def atualizar_preferencias(request):
    """Atualiza as tags preferidas do usuário.

    Requisição: POST JSON {"tags": [1,2,3]} - ids de tags.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Use POST'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)

    tag_ids = data.get('tags', [])
    if not isinstance(tag_ids, (list, tuple)):
        return JsonResponse({'success': False, 'message': 'tags deve ser uma lista de ids'}, status=400)

    tags = Tag.objects.filter(id__in=tag_ids)
    perfil = getattr(request.user, 'perfil', None)
    if perfil is None:
        # Criar perfil se por algum motivo não existir
        from .models import PerfilUsuario
        perfil = PerfilUsuario.objects.create(usuario=request.user)

    perfil.tags_preferidas.set(tags)
    return JsonResponse({'success': True, 'tags_count': tags.count()})


@login_required
def noticias_personalizadas(request):
    """Retorna notícias personalizadas com base nas tags preferidas do usuário."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil:
        return JsonResponse({'noticias': []})

    tags = list(perfil.tags_preferidas.all())
    if not tags:
        # Se usuário não tem preferência, retornar últimas notícias
        noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')[:50]
        data = [{'id': n.id, 'titulo': n.titulo, 'slug': n.slug, 'resumo': n.resumo} for n in noticias]
        return JsonResponse({'noticias': data})

    noticias = Noticia.objects.filter(tags__in=tags).annotate(
        match_count=Count('tags', filter=Q(tags__in=tags))
    ).order_by('-match_count', '-data_publicacao').distinct()[:200]

    data = []
    for n in noticias:
        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'slug': n.slug,
            'resumo': n.resumo,
            'match_count': getattr(n, 'match_count', 0)
        })

    return JsonResponse({'noticias': data})


# ========== API PARA PREFERÊNCIAS DE CATEGORIAS ==========
@require_http_methods(["GET", "POST"])
def api_preferencias(request):
    """API para gerenciar preferências de categorias do usuário."""

    if request.method == 'GET':
        # Retornar preferências salvas
        if request.user.is_authenticated:
            perfil = getattr(request.user, 'perfil', None)
            if perfil:
                categorias = list(perfil.categorias_preferidas.values_list('slug', flat=True))
                return JsonResponse({
                    'success': True,
                    'categorias': categorias
                })

        return JsonResponse({
            'success': True,
            'categorias': []
        })

    elif request.method == 'POST':
        # Salvar preferências
        try:
            data = json.loads(request.body)
            categorias_slugs = data.get('categorias', [])

            if not isinstance(categorias_slugs, list):
                return JsonResponse({
                    'success': False,
                    'message': 'categorias deve ser uma lista'
                }, status=400)

            # Se usuário está logado, salvar no perfil
            if request.user.is_authenticated:
                perfil = getattr(request.user, 'perfil', None)
                if not perfil:
                    perfil = PerfilUsuario.objects.create(usuario=request.user)

                # Buscar categorias pelos slugs
                categorias = Categoria.objects.filter(slug__in=categorias_slugs)
                perfil.categorias_preferidas.set(categorias)

                return JsonResponse({
                    'success': True,
                    'message': 'Preferências salvas com sucesso!',
                    'categorias': list(categorias.values_list('slug', flat=True))
                })
            else:
                # Visitante - retornar sucesso (será salvo no localStorage pelo JS)
                return JsonResponse({
                    'success': True,
                    'message': 'Preferências salvas localmente!',
                    'categorias': categorias_slugs
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao salvar preferências: {str(e)}'
            }, status=500)


# ========== LINHA DO TEMPO ==========
def linha_do_tempo(request):
    """View para página de linha do tempo - agrupa notícias cronologicamente."""
    from collections import defaultdict
    from datetime import datetime

    # Buscar todas as notícias ordenadas da mais recente para a mais antiga
    todas_noticias = Noticia.objects.select_related('categoria', 'autor').prefetch_related('tags').order_by('-data_publicacao')

    # Agrupar notícias por ano e mês
    timeline_data = defaultdict(lambda: defaultdict(list))

    for noticia in todas_noticias:
        ano = noticia.data_publicacao.year
        mes = noticia.data_publicacao.month
        timeline_data[ano][mes].append(noticia)

    # Converter para lista ordenada para o template
    timeline_list = []
    for ano in sorted(timeline_data.keys(), reverse=True):
        meses_data = []
        for mes in sorted(timeline_data[ano].keys(), reverse=True):
            # Nome do mês em português
            meses_pt = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }

            meses_data.append({
                'numero': mes,
                'nome': meses_pt[mes],
                'noticias': timeline_data[ano][mes]
            })

        timeline_list.append({
            'ano': ano,
            'meses': meses_data
        })

    # Buscar todas as categorias e tags para filtros
    categorias = Categoria.objects.all()
    tags = Tag.objects.all()

    context = {
        'timeline': timeline_list,
        'categorias': categorias,
        'tags': tags,
    }

    return render(request, 'linha_do_tempo.html', context)


# ========== PAINEL - GERENCIAR LINHAS DO TEMPO ==========

@user_passes_test(is_staff, login_url='login_usuario')
def painel_linhas_tempo(request):
    """View para listar todas as linhas do tempo"""
    from .models import LinhaDoTempo

    linhas_tempo = LinhaDoTempo.objects.all().order_by('-criada_em')

    context = {
        'linhas_tempo': linhas_tempo,
    }

    return render(request, 'painel_linhas_tempo.html', context)


@user_passes_test(is_staff, login_url='login_usuario')
def criar_linha_tempo(request):
    """View para criar uma nova linha do tempo"""
    from .models import LinhaDoTempo

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        ativa = request.POST.get('ativa') == 'on'

        if not titulo:
            messages.error(request, 'O título é obrigatório.')
            return redirect('criar_linha_tempo')

        try:
            linha_tempo = LinhaDoTempo.objects.create(
                titulo=titulo,
                descricao=descricao if descricao else None,
                ativa=ativa
            )
            messages.success(request, f'Linha do tempo "{linha_tempo.titulo}" criada com sucesso!')
            return redirect('editar_linha_tempo', linha_tempo_id=linha_tempo.id)
        except Exception as e:
            messages.error(request, f'Erro ao criar linha do tempo: {str(e)}')
            return redirect('criar_linha_tempo')

    return render(request, 'painel_criar_linha_tempo.html')


@user_passes_test(is_staff, login_url='login_usuario')
def editar_linha_tempo(request, linha_tempo_id):
    """View para editar uma linha do tempo e gerenciar suas notícias"""
    from .models import LinhaDoTempo

    linha_tempo = get_object_or_404(LinhaDoTempo, id=linha_tempo_id)

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        ativa = request.POST.get('ativa') == 'on'

        if not titulo:
            messages.error(request, 'O título é obrigatório.')
        else:
            linha_tempo.titulo = titulo
            linha_tempo.descricao = descricao if descricao else None
            linha_tempo.ativa = ativa
            linha_tempo.save()
            messages.success(request, f'Linha do tempo "{linha_tempo.titulo}" atualizada com sucesso!')
            return redirect('editar_linha_tempo', linha_tempo_id=linha_tempo.id)

    # Buscar notícias desta linha do tempo (ordenadas por data de publicação)
    noticias_linha = NoticiaLinhaDoTempo.objects.filter(
        linha_tempo=linha_tempo
    ).select_related('noticia__categoria', 'noticia__autor').order_by('-noticia__data_publicacao')

    # Buscar todas as notícias disponíveis (que não estão nesta linha do tempo)
    ids_na_linha = noticias_linha.values_list('noticia_id', flat=True)
    noticias_disponiveis = Noticia.objects.exclude(
        id__in=ids_na_linha
    ).select_related('categoria', 'autor').order_by('-data_publicacao')

    context = {
        'linha_tempo': linha_tempo,
        'noticias_linha': noticias_linha,
        'noticias_disponiveis': noticias_disponiveis,
        'total_noticias': noticias_linha.count(),
    }

    return render(request, 'painel_editar_linha_tempo.html', context)


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def deletar_linha_tempo(request, linha_tempo_id):
    """View para deletar uma linha do tempo"""
    from .models import LinhaDoTempo

    linha_tempo = get_object_or_404(LinhaDoTempo, id=linha_tempo_id)
    titulo = linha_tempo.titulo
    linha_tempo.delete()

    messages.success(request, f'Linha do tempo "{titulo}" deletada com sucesso!')
    return redirect('painel_linhas_tempo')


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def adicionar_noticia_linha_tempo(request, linha_tempo_id, noticia_id):
    """Adiciona uma notícia a uma linha do tempo específica"""
    from django.http import JsonResponse
    from .models import LinhaDoTempo

    linha_tempo = get_object_or_404(LinhaDoTempo, id=linha_tempo_id)
    noticia = get_object_or_404(Noticia, id=noticia_id)

    # Verificar se já está na linha do tempo
    if NoticiaLinhaDoTempo.objects.filter(linha_tempo=linha_tempo, noticia=noticia).exists():
        # Se for uma requisição AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': 'Já estava adicionada'})
        
        messages.warning(request, f'A notícia "{noticia.titulo}" já está nesta linha do tempo.')
        return redirect('editar_linha_tempo', linha_tempo_id=linha_tempo.id)

    # Criar entrada na linha do tempo
    NoticiaLinhaDoTempo.objects.create(
        linha_tempo=linha_tempo,
        noticia=noticia,
        ordem=0  # Será ordenado por data
    )

    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'message': 'Adicionada com sucesso'})

    messages.success(request, f'Notícia "{noticia.titulo}" adicionada à linha do tempo!')
    return redirect('editar_linha_tempo', linha_tempo_id=linha_tempo.id)

@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def remover_noticia_linha_tempo(request, item_id):
    """Remove uma notícia de uma linha do tempo"""
    item = get_object_or_404(NoticiaLinhaDoTempo, id=item_id)
    linha_tempo_id = item.linha_tempo.id
    titulo = item.noticia.titulo
    item.delete()

    messages.success(request, f'Notícia "{titulo}" removida da linha do tempo!')
    return redirect('editar_linha_tempo', linha_tempo_id=linha_tempo_id)


@user_passes_test(is_staff, login_url='login_usuario')
def api_linhas_tempo_noticia(request, noticia_id):
    """API para listar todas as linhas do tempo e indicar quais incluem a notícia"""
    from django.http import JsonResponse
    from .models import LinhaDoTempo, NoticiaLinhaDoTempo, Noticia
    
    try:
        noticia = get_object_or_404(Noticia, id=noticia_id)
        linhas_tempo = LinhaDoTempo.objects.filter(ativa=True).order_by('-criada_em')
        
        # Buscar quais linhas do tempo já incluem esta notícia
        noticias_incluidas = set(
            NoticiaLinhaDoTempo.objects.filter(noticia=noticia)
            .values_list('linha_tempo_id', flat=True)
        )
        
        data = {
            'linhas_tempo': [
                {
                    'id': linha.id,
                    'titulo': linha.titulo,
                    'descricao': linha.descricao,
                    'noticia_incluida': linha.id in noticias_incluidas
                }
                for linha in linhas_tempo
            ]
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def remover_noticia_linha_tempo_api(request):
    """Remove uma notícia de uma linha do tempo via API"""
    from django.http import JsonResponse
    import json
    
    try:
        data = json.loads(request.body)
        linha_tempo_id = data.get('linha_tempo_id')
        noticia_id = data.get('noticia_id')
        
        if not linha_tempo_id or not noticia_id:
            return JsonResponse({'success': False, 'error': 'Parâmetros inválidos'}, status=400)
        
        # Buscar e deletar a relação
        item = NoticiaLinhaDoTempo.objects.filter(
            linha_tempo_id=linha_tempo_id,
            noticia_id=noticia_id
        ).first()
        
        if item:
            item.delete()
            return JsonResponse({'success': True, 'message': 'Removida com sucesso'})
        else:
            return JsonResponse({'success': True, 'message': 'Não estava na linha do tempo'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def preferencias(request):
    """View para a página de preferências."""
    return render(request, 'preferencias.html')

