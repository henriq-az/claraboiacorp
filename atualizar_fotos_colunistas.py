import os
import django
import requests
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claraboiacorp.settings')
django.setup()

from jcpemobile.models import Autor

# URLs das fotos que já estão no index.html
fotos_colunistas = {
    'mirella-araujo-e-equipe': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/03/26/105x105/1_enem_2__2_-34210893.png',
    'roberta-soares-e-equipe': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/04/29/105x105/1_terezinhanunes_1-34365315.png',
    'cinthya-leite-e-equipe': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/03/26/105x105/1_lucas_2-34211038.png',
    'joao-silva': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/05/26/105x105/1_rmo5-34517370.png',
    'ana-pereira': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/03/26/105x105/1_seguranca_1-34210929.png',
    'lucas-fernandes': 'https://imagens.ne10.uol.com.br/veiculos/_midias/png/2025/03/26/105x105/1_igor_maciel_1-34210948.png',
}

print("Atualizando fotos dos colunistas com as imagens do index.html...")

for slug, foto_url in fotos_colunistas.items():
    try:
        autor = Autor.objects.get(slug=slug)
        
        # Baixar a imagem
        response = requests.get(foto_url)
        if response.status_code == 200:
            # Salvar a imagem no campo foto
            filename = f"{slug}.png"
            autor.foto.save(filename, ContentFile(response.content), save=True)
            print(f"✓ Foto atualizada para {autor.nome}")
        else:
            print(f"✗ Erro ao baixar foto para {autor.nome} (Status: {response.status_code})")
    except Autor.DoesNotExist:
        print(f"✗ Colunista com slug '{slug}' não encontrado")
    except Exception as e:
        print(f"✗ Erro ao processar {slug}: {str(e)}")

print("\nProcesso concluído!")
