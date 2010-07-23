# -*- coding: utf-8 -*-

from tool.routing import url
from tool.ext.documents import db
from tool.ext.templating import as_html
from tool.ext.breadcrumbs import entitled

from schema import Actor, Contact


@url('/')
@entitled(u'People and Organizations')
@as_html('contacts/index.html')
def index(request):
    people = Actor.objects(db).order_by('name')
    return {'object_list': people}

@url('/<string:pk>')
@entitled(lambda pk: u'{0}'.format(db.get(Actor,pk)))
@as_html('contacts/person.html')
def person(request, pk):
    person = db.get(Actor, pk)
    return {'object': person}
