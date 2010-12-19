# -*- coding: utf-8 -*-
from tool import app
from tool.routing import url
from tool.ext.templating import as_html
from tool.ext.breadcrumbs import entitled

from schema import Page

# FIXME
BASE_IMAGE_URL = u'/media/scanned_papers/'

@url('/')
@entitled(u'Pages')
@as_html('papers/page_index.html')
def page_index(request):
    db = app.get_feature('document_storage').default_db
    pages = Page.objects(db).order_by('date_time')
    for p in pages:
        print p.pk, p, p.summary, p.image
    return {'pages': pages,
            'thumbnail': _get_thumbnail}

@url('/<string:pk>')
@entitled(lambda pk: u'{0}'.format(
    app.get_feature('document_storage').default_db.get(Page,pk)))
@as_html('papers/page_detail.html')
def page_detail(request, pk):
    db = app.get_feature('document_storage').default_db
    page = db.get(Page, pk)
    return {'page': page,
            'thumbnail': _get_thumbnail}


def _get_thumbnail(image, w=100, h=100):
    import Image
    import os
    appendix = '.thumbnail_{0}x{1}.{2}'.format(w, h, 'JPEG')# image.file.format)
    th_full_path = image.full_path + appendix
    if not os.path.exists(th_full_path):
        print 'NOT CACHED'
        image.file.thumbnail((w,h), Image.ANTIALIAS)
        image.file.save(th_full_path, 'JPEG')
    # FIXME
    return os.path.join(BASE_IMAGE_URL, image.path) + appendix
