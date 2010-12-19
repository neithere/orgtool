# -*- coding: utf-8 -*-

from tool.ext import admin

from orgtool.ext.tracking import TrackedDocument
from schema import *


NAMESPACE = 'notes'


@admin.register_for(Idea)
class IdeaAdmin(admin.DocAdmin):
    exclude = TrackedDocument.meta.structure.keys()
    order_by = ['date_time_created']
    ordering_reversed = True
    namespace = NAMESPACE
    list_names = ['summary', 'is_reviewed', 'is_needed']
    search_names = ['summary']


@admin.register_for(Bookmark)
class BookmarkAdmin(admin.DocAdmin):
    list_names = ['summary', 'url', 'tags']
    search_names = ['summary']
    exclude = TrackedDocument.meta.structure.keys()
    order_by = ['date_time']
    ordering_reversed = True
    namespace = NAMESPACE
