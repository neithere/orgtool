from tool.ext import admin
from orgtool.ext.tracking.admin import TrackedAdmin
from schema import *


NAMESPACE = 'events'


#-- basic schemata


@admin.register_for(Plan)
class PlanAdmin(TrackedAdmin):
    namespace = NAMESPACE
    #exclude = ['dates_rrule', 'next_date_time'] + TrackedAdmin.exclude
    exclude = ['dates_rrule'] + TrackedAdmin.exclude
    list_names = 'summary', 'is_accomplished'
    search_names = ['summary']


@admin.register_for(Event)
class EventAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = ['date_time', 'summary', 'plan']
    order_by = 'date_time'
    order_reversed = True
    search_names = ['summary']


#-- extended schemata


@admin.register_for(CategorizedPlan)
class CategorizedPlanAdmin(PlanAdmin):
    pass


@admin.register_for(HierarchicalPlan)
class HierarchicalPlanAdmin(PlanAdmin):
    pass


admin.register(PlanCategory, namespace=NAMESPACE)
