# -*- coding: utf-8 -*-

from tool.routing import url
from tool.ext.documents import default_storage
from tool.ext.templating import as_html
from tool.ext.breadcrumbs import entitled

from schema import Actor, Contact


@url('/')
@entitled(u'People and Organizations')
@as_html('contacts/index.html')
def index(request):
    db = default_storage()
    people = Actor.objects(db).order_by('name')
    return {'object_list': people}

@url('/<string:pk>')
@entitled(lambda pk: u'{0}'.format(default_storage().get(Actor,pk)))
@as_html('contacts/person.html')
def person(request, pk):
    person = default_storage().get(Actor, pk)
    return {'object': person}
