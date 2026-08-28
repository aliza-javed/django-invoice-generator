import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

try:
    from weasyprint import HTML
    PDF_ENGINE = 'weasyprint'
except ImportError:
    from xhtml2pdf import pisa
    PDF_ENGINE = 'xhtml2pdf'


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    
    if PDF_ENGINE == 'weasyprint':
        pdf = HTML(string=html).write_pdf()
    else:
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if pdf.err:
            return None
        pdf = result.getvalue()
    
    return pdf