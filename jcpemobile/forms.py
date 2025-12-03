from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Noticia, Categoria, Autor, Tag, Feedback
import re

class CadastroUsuarioForm(forms.ModelForm):
    """Formulário de cadastro de novo usuário"""
    
    nome = forms.CharField(
        max_length=150,
        required=True,
        error_messages={
            'required': 'O nome é obrigatório.',
            'max_length': 'O nome deve ter no máximo 150 caracteres.'
        }
    )
    
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'O e-mail é obrigatório.',
            'invalid': 'Digite um e-mail válido.'
        }
    )
    
    senha = forms.CharField(
        min_length=8,
        required=True,
        error_messages={
            'required': 'A senha é obrigatória.',
            'min_length': 'A senha deve ter no mínimo 8 caracteres.'
        }
    )
    
    confirmar_senha = forms.CharField(
        required=True,
        error_messages={
            'required': 'A confirmação de senha é obrigatória.'
        }
    )
    
    class Meta:
        model = User
        fields = ['nome', 'email', 'senha']
    
    def clean_email(self):
        """Valida se o e-mail já está cadastrado"""
        email = self.cleaned_data.get('email')
        
        if email:
            # Verifica formato do e-mail
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise ValidationError('Digite um e-mail válido.')
            
            # Verifica se e-mail já existe
            if User.objects.filter(email=email).exists():
                raise ValidationError('E-mail já registrado.')
        
        return email
    
    def clean_senha(self):
        """Valida o tamanho mínimo da senha"""
        senha = self.cleaned_data.get('senha')
        
        if senha and len(senha) < 8:
            raise ValidationError('A senha deve ter no mínimo 8 caracteres.')
        
        return senha
    
    def clean(self):
        """Valida se as senhas coincidem"""
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError({'confirmar_senha': 'As senhas não coincidem.'})
        
        return cleaned_data
    
    def save(self, commit=True):
        """Cria o usuário com os dados validados"""
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['senha'],
            first_name=self.cleaned_data['nome']
        )
        return user


class NoticiaForm(forms.ModelForm):
    """Formulário para criar e editar notícias"""

    class Meta:
        model = Noticia
        fields = ['titulo', 'subtitulo', 'resumo', 'conteudo', 'imagem', 'imagem_vertical', 'categoria', 'autor', 'secao']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título da notícia'
            }),
            'subtitulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o subtítulo da notícia'
            }),
            'resumo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Versão resumida da notícia (máx. 300 caracteres)'
            }),
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Versão completa da notícia com todos os detalhes'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'imagem_vertical': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'autor': forms.Select(attrs={
                'class': 'form-control'
            }),
            'secao': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'titulo': 'Título',
            'subtitulo': 'Subtítulo',
            'resumo': 'Versão Curta',
            'conteudo': 'Versão Longa',
            'imagem': 'Imagem',
            'imagem_vertical': 'Imagem Vertical (Neels)',
            'categoria': 'Categoria',
            'autor': 'Autor',
            'secao': 'Seção',
        }
        help_texts = {
            'subtitulo': 'Subtítulo complementar ao título principal',
            'resumo': 'Versão resumida para exibição em listagens (máximo de 300 caracteres)',
            'conteudo': 'Versão completa da notícia com todos os detalhes e informações',
            'imagem_vertical': 'Imagem vertical para exibição na aba Neels (proporção 9:16, típico de reels/stories)',
            'secao': 'Escolha em qual seção da página inicial esta notícia será exibida',
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 10:
            raise ValidationError('O título deve ter pelo menos 10 caracteres.')
        return titulo

    def clean_resumo(self):
        resumo = self.cleaned_data.get('resumo')
        if resumo and len(resumo) > 300:
            raise ValidationError('O resumo não pode ter mais de 300 caracteres.')
        return resumo


class CategoriaForm(forms.ModelForm):
    """Formulário para criar e editar categorias"""

    class Meta:
        model = Categoria
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            })
        }


class AutorForm(forms.ModelForm):
    """Formulário para criar e editar autores"""

    class Meta:
        model = Autor
        fields = ['nome', 'bio', 'foto']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do autor'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Biografia do autor'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }


class FeedbackForm(forms.ModelForm):
    """Formulário para envio de feedback"""

    class Meta:
        model = Feedback
        fields = ['nome', 'email', 'avaliacao', 'comentario', 'imagem']

    def clean_avaliacao(self):
        """Valida se a avaliação está entre 1 e 5"""
        avaliacao = self.cleaned_data.get('avaliacao')
        if avaliacao and (avaliacao < 1 or avaliacao > 5):
            raise ValidationError('A avaliação deve estar entre 1 e 5.')
        return avaliacao

    def clean_comentario(self):
        """Valida o tamanho máximo do comentário"""
        comentario = self.cleaned_data.get('comentario')
        if comentario and len(comentario) > 140:
            raise ValidationError('O comentário não pode ter mais de 140 caracteres.')
        return comentario
