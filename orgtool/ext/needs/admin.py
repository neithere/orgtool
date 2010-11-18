# -*- coding: utf-8 -*-

from tool.ext import admin
from orgtool.ext.tracking.admin import TrackedAdmin
from orgtool.ext.events.admin import PlanAdmin, EventAdmin
from schema import SystemUnderDevelopment, Need, ReasonedPlan, ReasonedEvent


NAMESPACE = 'tasks'


@admin.register_for(SystemUnderDevelopment)
class ProjectAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = [
        'summary'
    ]
    order_by = 'summary'
    search_names = ['summary']


@admin.register_for(Need)
class NeedAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = [
        'summary', 'is_satisfied'
    ]
    order_by = 'summary'
    search_names = ['summary']


@admin.register_for(ReasonedPlan)
class ReasonedPlanAdmin(PlanAdmin):
    namespace = NAMESPACE
    list_names = ['summary', 'outcome']
    order_by = 'outcome'
    search_names = ['summary']


@admin.register_for(ReasonedEvent)
class ReasonedEventAdmin(EventAdmin):
    namespace = NAMESPACE
    list_names = ['summary', 'outcome']
    order_by = 'outcome'
    search_names = ['summary']
