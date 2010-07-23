# -*- coding: utf-8 -*-

from tool.ext import admin
from orgtool.ext.events.admin import EventAdmin
from schema import Message


NAMESPACE = 'talks'


@admin.register_for(Message)
class MessageAdmin(EventAdmin):
    namespace = NAMESPACE
    list_names = ['date_time', 'sent_by', 'sent_to', 'summary']
    order_by = 'date_time'
    ordering_reversed = True
