# -*- coding: utf-8 -*-

from tool.routing import url
from tool.ext.breadcrumbs import entitled
from tool.ext.documents import db
from tool.ext.templating import as_html, register_templates

from schema import Bookmark, Idea


@url('/ideas/')
@entitled(u'Ideas')
@as_html('notes/ideas.html')
def idea_index(request, tag=None):
    ideas = Idea.objects(db).order_by('date_time', reverse=True)
    if 'q' in request.values:
        # TODO: multiple fields
        ideas = ideas.where(summary__contains=request.values['q'])
    # TODO: generic facet filtering
    if 'is_reviewed' in request.values:
        value = bool(int(request.values['is_reviewed']))
        ideas = ideas.where(is_reviewed=value)
    if 'is_needed' in request.values:
        value = bool(int(request.values['is_needed']))
        ideas = ideas.where(is_needed=value)
    return {'object_list': ideas}

@url('/bookmarks/')
@url('/bookmarks/<string:tag>')
@entitled(u'Bookmarks')
@as_html('notes/bookmarks.html')
def bookmark_index(request, tag=None):
    bookmarks = Bookmark.objects(db).order_by('date_time', reverse=True)
    if tag:
        tag = tag.strip().split()
        bookmarks = bookmarks.where(tags__contains_all=tag)
    if 'q' in request.values:
        # TODO: multiple fields
        bookmarks = bookmarks.where(summary__contains=request.values['q'])
    return {'object_list': bookmarks}
