from tool.ext import admin
from orgtool.ext.tracking.admin import TrackedAdmin
from schema import *


NAMESPACE = 'events'


@admin.register_for(Plan)
class PlanAdmin(TrackedAdmin):
    namespace = NAMESPACE
    exclude = ['dates_rrule', 'next_date_time'] + TrackedAdmin.exclude
    list_names = 'summary', 'is_accomplished'


@admin.register_for(Event)
class EventAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = ['date_time', 'summary', 'plan']
    order_by = 'date_time'
    order_reversed = True


admin.register(PlanCategory, namespace=NAMESPACE)
admin.register(CategorizedPlan, namespace=NAMESPACE)
admin.register(HierarchicalPlan, namespace=NAMESPACE)
