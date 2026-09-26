import os
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from xhtml2pdf import pisa

def link_callback(uri, rel):
    """
    Convertit les URIs HTML (static & media) en chemins de fichiers absolus sur le disque.
    """
    # 1. Gestion des fichiers STATIC (/static/...)
    if uri.startswith(settings.STATIC_URL):
        path = uri.replace(settings.STATIC_URL, "")
        result = finders.find(path)
        if result:
            if isinstance(result, (list, tuple)):
                result = result[0]
            return result
        return os.path.join(settings.STATIC_ROOT, path)

    # 2. Gestion des fichiers MEDIA (/media/...)
    elif uri.startswith(settings.MEDIA_URL):
        path = uri.replace(settings.MEDIA_URL, "")
        result = os.path.join(settings.MEDIA_ROOT, path)
        return result

    # 3. Chemin absolu déjà fourni
    return uri


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # Injection du link_callback
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), 
        result, 
        link_callback=link_callback
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None