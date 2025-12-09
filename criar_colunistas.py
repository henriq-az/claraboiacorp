import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claraboiacorp.settings')
django.setup()

from jcpemobile.models import Autor
from django.utils.text import slugify

# Lista de colunistas da página inicial
colunistas = [
    {
        'nome': 'Cinthya Leite e Equipe',
        'bio': 'Especialista em Saúde e Bem-Estar, trazendo as melhores informações sobre medicina, qualidade de vida e cuidados com a saúde.'
    },
    {
        'nome': 'Mirella Araújo e Equipe',
        'bio': 'Focada em Educação e Enem, oferecendo dicas, análises e orientações para estudantes e educadores.'
    },
    {
        'nome': 'Roberta Soares e Equipe',
        'bio': 'Especialista em Mobilidade Urbana, cobrindo transportes, trânsito e infraestrutura das cidades.'
    },
    {
        'nome': 'João Silva',
        'bio': 'Colunista de Cultura, trazendo o melhor do cinema, teatro, música e artes em geral.'
    },
    {
        'nome': 'Ana Pereira',
        'bio': 'Analista de Economia, com foco em mercado, negócios e desenvolvimento regional.'
    },
    {
        'nome': 'Lucas Fernandes',
        'bio': 'Especialista em Tecnologia e Inovação, cobrindo startups, energia renovável e transformação digital.'
    }
]

print("=== CRIANDO COLUNISTAS ===\n")

for col in colunistas:
    autor, created = Autor.objects.get_or_create(
        nome=col['nome'],
        defaults={
            'bio': col['bio'],
            'slug': slugify(col['nome'])
        }
    )
    
    if created:
        print(f"✓ Criado: {autor.nome}")
        print(f"  Slug: {autor.slug}")
        print(f"  Bio: {autor.bio}")
    else:
        print(f"○ Já existe: {autor.nome}")
        print(f"  Slug: {autor.slug}")
    print()

print("\n=== TODOS OS AUTORES NO SISTEMA ===\n")
for autor in Autor.objects.all():
    print(f"- {autor.nome} (slug: {autor.slug})")
    print(f"  URL: http://127.0.0.1:8000/autor/{autor.slug}/")
    print()
