from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import linebreaks

register = template.Library()

@register.filter(name='inserir_anuncios')
def inserir_anuncios(texto):
    """
    Converte texto em HTML com parágrafos e insere anúncios após o 1º e 3º parágrafos.
    """
    if not texto:
        return ''
    
    # Converte o texto em HTML com parágrafos
    html_com_paragrafos = linebreaks(texto)
    
    # Divide o HTML em parágrafos
    paragrafos = html_com_paragrafos.split('</p>')
    
    # Remove itens vazios
    paragrafos = [p for p in paragrafos if p.strip()]
    
    # HTML do banner de anúncio
    banner_anuncio = '''
    <div class="anuncio-inline" style="margin: 24px 0; width: 100%; text-align: center;">
        <img src="https://jc.uol.com.br/img/selo_revista_recall.png" alt="Publicidade" style="max-width: 100%; height: auto; border-radius: 8px;">
    </div>
    '''
    
    resultado = []
    
    for i, paragrafo in enumerate(paragrafos):
        # Adiciona o parágrafo
        resultado.append(paragrafo + '</p>')
        
        # Insere anúncio após o 1º parágrafo (índice 0)
        if i == 0:
            resultado.append(banner_anuncio)
        
        # Insere anúncio após o 3º parágrafo (índice 2)
        elif i == 2:
            resultado.append(banner_anuncio)
    
    return mark_safe(''.join(resultado))
