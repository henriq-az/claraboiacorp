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
    # Pegar todas as notícias ordenadas por data de publicação
    noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')
    
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

    # Buscar notícias relacionadas para a linha do tempo
    # Prioridade: notícias adicionadas manualmente na linha do tempo
    noticias_relacionadas = []
    
    # Buscar notícias da linha do tempo global (gerenciada pelo painel)
    noticias_linha_tempo = NoticiaLinhaDoTempo.objects.filter(
        ativa=True
    ).select_related('noticia__categoria', 'noticia__autor').order_by('ordem')[:6]
    
    if noticias_linha_tempo.exists():
        noticias_relacionadas = [item.noticia for item in noticias_linha_tempo]
    else:
        # Fallback: se não houver linha do tempo configurada, buscar relacionadas automaticamente
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
    # Pegar notícias mais vistas hoje
    noticias_hoje = Noticia.objects.all().annotate(
        visualizacoes_dia=Count('visualizacoes', filter=Q(visualizacoes__data=timezone.now().date()))
    ).filter(visualizacoes_dia__gt=0).order_by('-visualizacoes_dia')
    # Pegar notícias mais vistas da semana
    data_semana_atras = timezone.now().date() - timezone.timedelta(days=7)
    noticias_semana = Noticia.objects.all().annotate(
        visualizacoes_semana=Count('visualizacoes', filter=Q(visualizacoes__data__gte=data_semana_atras))
    ).filter(visualizacoes_semana__gt=0).order_by('-visualizacoes_semana')
    
    # Pegar notícias mais vistas do mês
    data_mes_atras = timezone.now().date() - timezone.timedelta(days=30)
    noticias_mes = Noticia.objects.all().annotate(
        visualizacoes_mes=Count('visualizacoes', filter=Q(visualizacoes__data__gte=data_mes_atras))
    ).filter(visualizacoes_mes__gt=0).order_by('-visualizacoes_mes')
    
    context = {
        'noticias_hoje': noticias_hoje[:15],
        'noticias_semana': noticias_semana[:15],
        'noticias_mes': noticias_mes[:15],
    }
    
    return render(request, 'mais_lidas.html', context)


def painel_diario(request):
    """View para a página Painel Diário"""
    return render(request, 'painel_diario.html')


@login_required
@require_http_methods(["POST"])
def salvar_noticia(request, noticia_id):
    """View para salvar uma notícia"""
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


@login_required
@require_http_methods(["POST"])
def remover_noticia_salva(request, noticia_id):
    """View para remover uma notícia salva"""
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


@login_required
def verificar_noticia_salva(request, noticia_id):
    """View para verificar se uma notícia está salva"""
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
                    for texto_opcao in opcoes:
                        texto_opcao = texto_opcao.strip()
                        if texto_opcao:
                            Opcao.objects.create(enquete=enquete, texto=texto_opcao)

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
                    if hasattr(noticia, 'enquete'):
                        enquete = noticia.enquete
                        enquete.titulo = titulo_enquete
                        enquete.pergunta = pergunta_enquete
                        enquete.save()
                        # Deletar opções antigas
                        enquete.opcoes.all().delete()
                    else:
                        enquete = Enquete.objects.create(
                            titulo=titulo_enquete,
                            pergunta=pergunta_enquete,
                            noticia=noticia
                        )

                    # Criar opções
                    opcoes = request.POST.getlist('opcao[]')
                    for texto_opcao in opcoes:
                        texto_opcao = texto_opcao.strip()
                        if texto_opcao:
                            Opcao.objects.create(enquete=enquete, texto=texto_opcao)
            else:
                # Se não tem enquete mas tinha antes, deletar
                if hasattr(noticia, 'enquete'):
                    noticia.enquete.delete()

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


# ========== PAINEL - GERENCIAR LINHA DO TEMPO ==========
@user_passes_test(is_staff, login_url='login_usuario')
def painel_linha_tempo(request):
    """View para gerenciar notícias na linha do tempo"""
    noticias_linha_tempo = NoticiaLinhaDoTempo.objects.select_related(
        'noticia__categoria', 'noticia__autor'
    ).order_by('ordem')
    
    # Buscar todas as notícias disponíveis
    todas_noticias = Noticia.objects.select_related('categoria', 'autor').order_by('-data_publicacao')
    
    # Filtrar notícias que não estão na linha do tempo
    ids_na_linha = noticias_linha_tempo.values_list('noticia_id', flat=True)
    noticias_disponiveis = todas_noticias.exclude(id__in=ids_na_linha)
    
    context = {
        'noticias_linha_tempo': noticias_linha_tempo,
        'noticias_disponiveis': noticias_disponiveis,
        'total_linha_tempo': noticias_linha_tempo.count(),
    }
    
    return render(request, 'painel_linha_tempo.html', context)


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def adicionar_noticia_linha_tempo(request, noticia_id):
    """Adiciona uma notícia à linha do tempo"""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    
    # Verificar se já está na linha do tempo
    if NoticiaLinhaDoTempo.objects.filter(noticia=noticia).exists():
        messages.warning(request, f'A notícia "{noticia.titulo}" já está na linha do tempo.')
        return redirect('painel_linha_tempo')
    
    # Obter a próxima ordem
    ultima_ordem = NoticiaLinhaDoTempo.objects.aggregate(Max('ordem'))['ordem__max'] or 0
    
    # Criar entrada na linha do tempo
    NoticiaLinhaDoTempo.objects.create(
        noticia=noticia,
        ordem=ultima_ordem + 1,
        ativa=True
    )
    
    messages.success(request, f'Notícia "{noticia.titulo}" adicionada à linha do tempo!')
    return redirect('painel_linha_tempo')


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def remover_noticia_linha_tempo(request, item_id):
    """Remove uma notícia da linha do tempo"""
    item = get_object_or_404(NoticiaLinhaDoTempo, id=item_id)
    titulo = item.noticia.titulo
    item.delete()
    
    messages.success(request, f'Notícia "{titulo}" removida da linha do tempo!')
    return redirect('painel_linha_tempo')


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def reordenar_linha_tempo(request):
    """Reordena as notícias na linha do tempo"""
    try:
        data = json.loads(request.body)
        ordens = data.get('ordens', [])  # Lista de {'id': item_id, 'ordem': nova_ordem}
        
        for item_data in ordens:
            item_id = item_data.get('id')
            nova_ordem = item_data.get('ordem')
            
            if item_id and nova_ordem is not None:
                NoticiaLinhaDoTempo.objects.filter(id=item_id).update(ordem=nova_ordem)
        
        return JsonResponse({
            'success': True,
            'message': 'Ordem atualizada com sucesso!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@user_passes_test(is_staff, login_url='login_usuario')
@require_http_methods(["POST"])
def toggle_ativa_linha_tempo(request, item_id):
    """Ativa/desativa uma notícia na linha do tempo"""
    item = get_object_or_404(NoticiaLinhaDoTempo, id=item_id)
    item.ativa = not item.ativa
    item.save()
    
    status = "ativada" if item.ativa else "desativada"
    messages.success(request, f'Notícia "{item.noticia.titulo}" {status}!')
    return redirect('painel_linha_tempo')


