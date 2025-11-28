from django.urls import path
from .views import (
    noticia_detalhe, index, cadastro_usuario, login_usuario, logout_usuario,
    salvos, salvar_noticia, remover_noticia_salva, verificar_noticia_salva, mais_lidas, enviar_feedback,
    admin_dashboard, admin_criar_noticia, admin_editar_noticia, admin_deletar_noticia,
    admin_criar_autor, neels, detalhe_enquete, lista_enquetes, painel_diario,
    listar_tags, noticias_por_tags, buscar_noticias_por_ids, atualizar_preferencias, noticias_personalizadas,
    api_preferencias, linha_do_tempo, lista_por_categoria,
    painel_linhas_tempo, criar_linha_tempo, editar_linha_tempo, deletar_linha_tempo,
    adicionar_noticia_linha_tempo, remover_noticia_linha_tempo
)

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_usuario, name='login_usuario'),
    path('cadastro/', cadastro_usuario, name='cadastro_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('salvos/', salvos, name='salvos'),
    path('mais-lidas/', mais_lidas, name='mais_lidas'),
    path('neels/', neels, name='neels'),
    path('linha-do-tempo/', linha_do_tempo, name='linha_do_tempo'),
    path('salvar-noticia/<int:noticia_id>/', salvar_noticia, name='salvar_noticia'),
    path('remover-noticia-salva/<int:noticia_id>/', remover_noticia_salva, name='remover_noticia_salva'),
    path('verificar-noticia-salva/<int:noticia_id>/', verificar_noticia_salva, name='verificar_noticia_salva'),
    path('feedback/enviar/', enviar_feedback, name='enviar_feedback'),
    path('categoria/<slug:slug>/', lista_por_categoria, name='categoria'),
    # API para tags, filtros e preferências
    path('api/tags/', listar_tags, name='api_listar_tags'),
    path('api/noticias/', buscar_noticias_por_ids, name='api_buscar_noticias_por_ids'),
    path('api/noticias/tags/', noticias_por_tags, name='api_noticias_por_tags'),
    path('api/preferencias/', api_preferencias, name='api_preferencias'),
    path('api/preferencias/tags/', atualizar_preferencias, name='api_atualizar_preferencias'),
    path('api/noticias/personalizadas/', noticias_personalizadas, name='api_noticias_personalizadas'),
    
    
    # Rotas de Admin (Painel Customizado)
    path('painel/', admin_dashboard, name='admin_dashboard'),
    path('painel/noticia/criar/', admin_criar_noticia, name='admin_criar_noticia'),
    path('painel/noticia/<int:noticia_id>/editar/', admin_editar_noticia, name='admin_editar_noticia'),
    path('painel/noticia/<int:noticia_id>/deletar/', admin_deletar_noticia, name='admin_deletar_noticia'),
    path('painel-diario/', painel_diario, name='painel_diario'),
    
    # Rotas de Linhas do Tempo (Painel)
    path('painel/linhas-tempo/', painel_linhas_tempo, name='painel_linhas_tempo'),
    path('painel/linhas-tempo/criar/', criar_linha_tempo, name='criar_linha_tempo'),
    path('painel/linhas-tempo/<int:linha_tempo_id>/editar/', editar_linha_tempo, name='editar_linha_tempo'),
    path('painel/linhas-tempo/<int:linha_tempo_id>/deletar/', deletar_linha_tempo, name='deletar_linha_tempo'),
    path('painel/linhas-tempo/<int:linha_tempo_id>/adicionar/<int:noticia_id>/', adicionar_noticia_linha_tempo, name='adicionar_noticia_linha_tempo'),
    path('painel/linhas-tempo/remover/<int:item_id>/', remover_noticia_linha_tempo, name='remover_noticia_linha_tempo'),
    

    # Rotas API para criar autor
    path('painel/api/autor/criar/', admin_criar_autor, name='admin_criar_autor'),

    path('<slug:slug>/', noticia_detalhe, name='noticia_detalhe'),
]
