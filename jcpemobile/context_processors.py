from .models import Categoria

def categorias_menu(request):
    return {
        'categorias_menu': Categoria.objects.all()
    }
