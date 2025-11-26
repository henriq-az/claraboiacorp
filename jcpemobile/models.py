# jcpemobile/models.py
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
    
class Autor(models.Model):
    nome = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to="autores/", blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

class Tag(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Noticia(models.Model):
    SECAO_CHOICES = [
        ('noticia_do_dia', 'Notícia do Dia'),
        ('social1', 'Social1'),
        ('jc360', 'JC360'),
        ('pernambuco', 'Pernambuco'),
        ('blog_do_torcedor', 'Blog do Torcedor'),
        ('ultimas_noticias', 'Últimas Notícias'),
        ('receita_da_boa', 'Receita da Boa'),
    ]
    
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    resumo = models.TextField(max_length=300, blank=True, null=True)
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to="noticias/", blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name="noticias")
    autor = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True, related_name="noticias")
    tags = models.ManyToManyField(Tag, blank=True, related_name="noticias")
    secao = models.CharField(max_length=50, choices=SECAO_CHOICES, default='noticia_do_dia', verbose_name='Seção')
    data_publicacao = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        
        # Processar imagem para proporção 5:3 se foi feito upload
        if self.imagem:
            self._processar_imagem()
        
        super().save(*args, **kwargs)

    def _processar_imagem(self):
        """Redimensiona e corta a imagem para proporção 2:1"""
        try:
            # Abrir a imagem
            img = Image.open(self.imagem)
            
            # Converter para RGB se necessário (para PNG com transparência)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Proporção desejada: 2:1 (largura / altura = 2.0)
            proporcao_alvo = 2.0
            largura_original, altura_original = img.size
            proporcao_original = largura_original / altura_original
            
            # Calcular dimensões para corte centralizado
            if proporcao_original > proporcao_alvo:
                # Imagem mais larga - cortar largura
                nova_largura = int(altura_original * proporcao_alvo)
                nova_altura = altura_original
                x_offset = (largura_original - nova_largura) // 2
                y_offset = 0
            else:
                # Imagem mais alta - cortar altura
                nova_largura = largura_original
                nova_altura = int(largura_original / proporcao_alvo)
                x_offset = 0
                y_offset = (altura_original - nova_altura) // 2
            
            # Cortar imagem
            img_cortada = img.crop((
                x_offset,
                y_offset,
                x_offset + nova_largura,
                y_offset + nova_altura
            ))
            
            # Redimensionar para tamanho otimizado (máximo 1200px de largura)
            largura_maxima = 1200
            if img_cortada.width > largura_maxima:
                altura_proporcional = int(largura_maxima / proporcao_alvo)
                img_cortada = img_cortada.resize((largura_maxima, altura_proporcional), Image.Resampling.LANCZOS)
            
            # Salvar imagem processada
            output = BytesIO()
            img_cortada.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            # Atualizar campo de imagem
            nome_arquivo = os.path.splitext(os.path.basename(self.imagem.name))[0]
            self.imagem.save(
                f"{nome_arquivo}_processada.jpg",
                ContentFile(output.read()),
                save=False
            )
        except Exception as e:
            # Se houver erro no processamento, manter imagem original
            print(f"Erro ao processar imagem: {e}")
            pass

    def visualizacoes_do_dia(self):
        # Conta visualizações únicas (por IP) do dia atual
        hoje = timezone.now().date()
        return self.visualizacoes.filter(data=hoje).values('ip_address').distinct().count()

    def total_visualizacoes(self):
        return self.visualizacoes.count()

    def __str__(self):
        return self.titulo

class Visualizacao(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="visualizacoes")
    ip_address = models.GenericIPAddressField()  # Renamed from ip_usuario
    data_visualizacao = models.DateTimeField(auto_now_add=True)  # For precise timestamp
    data = models.DateField(null=True, blank=True)  # For daily view counting

    class Meta:
        unique_together = ('noticia', 'ip_address', 'data')
        indexes = [
            models.Index(fields=['data']),
        ]

    def __str__(self):
        return f"Visualização em {self.noticia.titulo} ({self.data})"

class Feedback(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    avaliacao = models.IntegerField(
        choices=[
            (1, 'Ruim'),
            (2, 'Regular'),
            (3, 'Bom'),
            (4, 'Muito bom'),
            (5, 'Excelente'),
        ]
    )
    comentario = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='feedbacks/', blank=True, null=True)
    data_envio = models.DateTimeField(auto_now_add=True)
    respondido = models.BooleanField(default=False)

    def __str__(self):
        return f"Feedback de {self.nome} - {self.get_avaliacao_display()}"

class NoticaSalva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="noticias_salvas")
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name="salvamentos")
    data_salvamento = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'noticia')
        ordering = ['-data_salvamento']

    def __str__(self):
        return f"{self.usuario.username} salvou {self.noticia.titulo}"


class PerfilUsuario(models.Model):
    """Perfil simples para guardar tags e categorias preferidas do usuário."""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tags_preferidas = models.ManyToManyField(Tag, blank=True, related_name='usuarios_preferidos')
    categorias_preferidas = models.ManyToManyField(Categoria, blank=True, related_name='usuarios_interessados')

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """Cria um perfil associado quando um User é criado."""
    if created:
        PerfilUsuario.objects.create(usuario=instance)

class Enquete(models.Model):
    titulo = models.CharField(max_length=255)
    pergunta = models.CharField(max_length=255)
    noticia = models.OneToOneField(Noticia, on_delete=models.CASCADE, related_name="enquete", null=True, blank=True)

    def __str__(self):
        return self.titulo

    def total_votos(self):
        return sum(opcao.votos.count() for opcao in self.opcoes.all())


class Opcao(models.Model):
    enquete = models.ForeignKey(Enquete, on_delete=models.CASCADE, related_name="opcoes")
    texto = models.CharField(max_length=200)

    def __str__(self):
        return self.texto

    def percentual(self):
        total = self.enquete.total_votos()
        return (self.votos.count() / total * 100) if total > 0 else 0


class Voto(models.Model):
    opcao = models.ForeignKey(Opcao, on_delete=models.CASCADE, related_name="votos")
    ip_usuario = models.GenericIPAddressField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voto em {self.opcao.texto} ({self.ip_usuario})"


class NoticiaLinhaDoTempo(models.Model):
    """
    Modelo para armazenar as notícias que aparecem na linha do tempo global.
    """
    noticia = models.OneToOneField(
        Noticia, 
        on_delete=models.CASCADE, 
        related_name="na_linha_tempo",
        verbose_name="Notícia"
    )
    ordem = models.PositiveIntegerField(
        default=0, 
        verbose_name="Ordem de Exibição",
        help_text="Ordem em que a notícia aparece na linha do tempo (menor número aparece primeiro)"
    )
    ativa = models.BooleanField(
        default=True,
        verbose_name="Ativa",
        help_text="Se marcado, a notícia aparecerá na linha do tempo"
    )
    adicionada_em = models.DateTimeField(auto_now_add=True, verbose_name="Adicionada em")
    atualizada_em = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Notícia na Linha do Tempo"
        verbose_name_plural = "Notícias na Linha do Tempo"
        ordering = ['ordem', '-adicionada_em']

    def __str__(self):
        return f"{self.ordem}. {self.noticia.titulo}"
