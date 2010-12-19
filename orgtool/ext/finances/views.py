# -*- coding: utf-8 -*-

import datetime

from tool.routing import url
from tool.ext.documents import default_storage
from tool.ext.templating import as_html
from tool.ext.breadcrumbs import entitled

from schema import Contract, Payment
from utils import (
    get_default_currency, render_rel_delta, chart_url_for_payments
)


@url('/')
@entitled(u'Finances')
@as_html('finances/dashboard.html')
def dashboard(request):
    db = default_storage()
    contracts = Contract.objects(db).order_by('next_date_time')
    payments = Payment.objects(db).order_by('date_time')
    return {
        'contracts': contracts,
        'payments': payments,
        'render_rel_delta': render_rel_delta,
        'chart_url_for_payments': chart_url_for_payments,
        'today': datetime.datetime.today(),
        'default_currency': get_default_currency(),
    }

@url('/contracts/')
@entitled(u'Contracts')
@as_html('finances/plan_index.html')
def plan_index(request):
    db = default_storage()
    plans = Contract.objects(db).order_by('next_date_time')
    return {
        'object_list': plans,
#        'total_monthly_fee': sum(p.actual_monthly_fee for p in plans)
    }

@url('/contracts/<string:pk>')
@entitled(lambda pk: u'{0}'.format(default_storage().get(Contract,pk)))
@as_html('finances/plan_detail.html')
def plan(request, pk):
    db = default_storage()
    plan = db.get(Contract, pk)
    return {
        'object': plan,
        'chart_url_for_payments': chart_url_for_payments,
    }

@url('/payments/')
@url('/payments/<int(4):year>/')
@url('/payments/<int(4):year>/<int(2):month>/')
@url('/payments/<int(4):year>/<int(2):month>/<int(2):day>/')
@entitled(u'Payments')
@as_html('finances/event_index.html')
def event_index(request, year=None, month=None, day=None):
    db = default_storage()
    events = Payment.objects(db).order_by('date_time', reverse=True)
    if year:
        events = events.where(date_time__year=year)
        if month:
            events = event.where(date_time__month=month)
            if day:
                events = events.where(date_time__day=day)
    return {'object_list': events}
