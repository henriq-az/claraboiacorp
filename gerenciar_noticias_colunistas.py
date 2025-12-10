import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claraboiacorp.settings')
django.setup()

from jcpemobile.models import Autor, Noticia

# Listar todos os autores disponíveis
print("=" * 60)
print("COLUNISTAS DISPONÍVEIS:")
print("=" * 60)
autores = Autor.objects.all()
for idx, autor in enumerate(autores, 1):
    noticias_count = autor.noticias.count()
    print(f"{idx}. {autor.nome} (slug: {autor.slug}) - {noticias_count} notícias")

print("\n" + "=" * 60)
print("EXEMPLO DE USO:")
print("=" * 60)
print("""
# Para associar notícias a um colunista, use:

from jcpemobile.models import Autor, Noticia

# 1. Pegar o autor pelo slug
autor = Autor.objects.get(slug='cinthya-leite-e-equipe')

# 2. Pegar notícias específicas por ID
noticia = Noticia.objects.get(id=1)
noticia.autor = autor
noticia.save()

# 3. Ou atualizar múltiplas notícias de uma vez
noticias_ids = [1, 2, 3, 4, 5]  # IDs das notícias
Noticia.objects.filter(id__in=noticias_ids).update(autor=autor)

# 4. Ver notícias de um autor
autor = Autor.objects.get(slug='cinthya-leite-e-equipe')
noticias = autor.noticias.all()
for noticia in noticias:
    print(f"- {noticia.titulo}")
""")

print("\n" + "=" * 60)
print("NOTÍCIAS SEM AUTOR:")
print("=" * 60)
noticias_sem_autor = Noticia.objects.filter(autor__isnull=True)[:10]
if noticias_sem_autor:
    for noticia in noticias_sem_autor:
        print(f"ID {noticia.id}: {noticia.titulo[:60]}...")
    print(f"\nTotal de notícias sem autor: {Noticia.objects.filter(autor__isnull=True).count()}")
else:
    print("Todas as notícias já têm autor atribuído!")

print("\n" + "=" * 60)
print("SCRIPT RÁPIDO - Associar notícias a um colunista:")
print("=" * 60)
print("""
# Exemplo: Associar as primeiras 5 notícias à Cinthya Leite
from jcpemobile.models import Autor, Noticia

autor = Autor.objects.get(slug='cinthya-leite-e-equipe')
noticias = Noticia.objects.filter(autor__isnull=True)[:5]
for noticia in noticias:
    noticia.autor = autor
    noticia.save()
    print(f"✓ {noticia.titulo}")
""")
