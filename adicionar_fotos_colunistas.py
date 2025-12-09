import os
import django
import requests
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claraboiacorp.settings')
django.setup()

from jcpemobile.models import Autor

# URLs de fotos de exemplo para cada colunista
fotos_colunistas = {
    'cinthya-leite-e-equipe': 'https://randomuser.me/api/portraits/women/44.jpg',
    'mirella-araujo-e-equipe': 'https://randomuser.me/api/portraits/women/65.jpg',
    'roberta-soares-e-equipe': 'https://randomuser.me/api/portraits/women/68.jpg',
    'joao-silva': 'https://randomuser.me/api/portraits/men/32.jpg',
    'ana-pereira': 'https://randomuser.me/api/portraits/women/47.jpg',
    'lucas-fernandes': 'https://randomuser.me/api/portraits/men/54.jpg',
}

print("Adicionando fotos aos colunistas...")

for slug, foto_url in fotos_colunistas.items():
    try:
        autor = Autor.objects.get(slug=slug)
        
        # Baixar a imagem
        response = requests.get(foto_url)
        if response.status_code == 200:
            # Salvar a imagem no campo foto
            filename = f"{slug}.jpg"
            autor.foto.save(filename, ContentFile(response.content), save=True)
            print(f"✓ Foto adicionada para {autor.nome}")
        else:
            print(f"✗ Erro ao baixar foto para {autor.nome}")
    except Autor.DoesNotExist:
        print(f"✗ Colunista com slug '{slug}' não encontrado")
    except Exception as e:
        print(f"✗ Erro ao processar {slug}: {str(e)}")

print("\nProcesso concluído!")
