# -*- coding: utf-8 -*-

from orgtool.ext.events.admin import PlanAdmin, EventAdmin
from tool.ext import admin
from schema import Contract, Payment


NAMESPACE = 'finances'


@admin.register_for(Contract)
class ContractAdmin(PlanAdmin):
    namespace = NAMESPACE
    list_names = [
        'summary', 'dates_rrule_text', 'fee', 'total_fee', 'currency'
    ]
    order_by = 'summary'


@admin.register_for(Payment)
class PaymentAdmin(EventAdmin):
    namespace = NAMESPACE
    list_names = ['date_time', 'plan', 'amount', 'currency', 'summary']
    order_by = 'date_time'
    order_reversed = True
