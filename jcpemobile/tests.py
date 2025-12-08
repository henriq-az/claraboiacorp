from django.test import TestCase, Client
from django.utils import timezone
import datetime
from jcpemobile.models import Noticia, Visualizacao


class VisualizacaoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.noticia = Noticia.objects.create(
            slug='t-noticia',
            titulo='T',
            conteudo='x'
        )

    def test_visualizacao_por_ip_por_dia(self):
        """Testa que o mesmo IP no mesmo dia não gera visualização duplicada"""
        resp1 = self.client.get(f'/{self.noticia.slug}/?fake_ip=1.2.3.4')
        resp2 = self.client.get(f'/{self.noticia.slug}/?fake_ip=1.2.3.4')
        
        self.assertEqual(200, resp1.status_code)
        self.assertEqual(200, resp2.status_code)
        
        # Campo renomeado de ip_usuario para ip_address
        self.assertEqual(
            1,
            Visualizacao.objects.filter(
                noticia=self.noticia,
                ip_address='1.2.3.4'
            ).count()
        )

    def test_visualizacao_diferentes_ips(self):
        """Testa que IPs diferentes geram visualizações diferentes"""
        resp1 = self.client.get(f'/{self.noticia.slug}/?fake_ip=1.2.3.4')
        resp2 = self.client.get(f'/{self.noticia.slug}/?fake_ip=5.6.7.8')
        
        self.assertEqual(200, resp1.status_code)
        self.assertEqual(200, resp2.status_code)
        
        # Deve ter 2 visualizações
        self.assertEqual(2, Visualizacao.objects.filter(noticia=self.noticia).count())


class NoticiaTests(TestCase):
    def test_criacao_noticia(self):
        """Testa criação básica de notícia"""
        noticia = Noticia.objects.create(
            titulo='Teste',
            slug='teste',
            conteudo='Conteúdo de teste'
        )
        self.assertEqual(noticia.titulo, 'Teste')
        self.assertEqual(noticia.slug, 'teste')

    def test_noticia_str(self):
        """Testa representação em string da notícia"""
        noticia = Noticia.objects.create(
            titulo='Título de Teste',
            slug='titulo-teste',
            conteudo='Conteúdo'
        )
        self.assertEqual(str(noticia), 'Título de Teste')
