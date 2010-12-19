# -*- coding: utf-8 -*-

import datetime

from doqu.validators import ValidationError

from tool.routing import url, redirect_to
from tool.ext.who import requires_auth
from tool.ext.documents import default_storage
from tool.ext.templating import as_html
from tool.ext.breadcrumbs import entitled

# TODO: move to a higher level of utils
from orgtool.ext.finances.utils import render_rel_delta, is_date_within_a_day
from orgtool.ext.finances import Payment

from schema import (
    HierarchicalPlan, Plan, ReasonedPlan, Event, Need,
    SystemUnderDevelopment
)


"""
@url('/')
@entitled(u'Plans')
@as_html('devel_tasks/dashboard.html')
def dashboard(request):
    contracts = Contract.objects(db).order_by('next_date_time')
    payments = Payment.objects(db).order_by('date_time')
    return {
        'plans': plans,
        'render_rel_delta': render_rel_delta,
#        'today': datetime.datetime.today(),
    }
"""

#--- projects (project = system under development)

@url('/projects/')
@requires_auth
@entitled(u'Projects')
@as_html('needs/project_index.html')
def project_index(request):
    db = default_storage()
    projects = SystemUnderDevelopment.objects(db).order_by('summary')
    return {
        'object_list': projects,
    }

@url('/projects/<string:pk>')
@requires_auth
@entitled(lambda pk: u'{0}'.format(default_storage().get(SystemUnderDevelopment,pk)))
@as_html('needs/project_detail.html')
def project(request, pk):
    db = default_storage()
    obj = db.get(SystemUnderDevelopment, pk)
    return {'object': obj}


#--- needs

@url('/needs/')
@requires_auth
@entitled(u'Needs')
@as_html('needs/need_index.html')
def need_index(request):
    db = default_storage()
    needs = Need.objects(db).order_by('summary')
    return {
        'object_list': needs,
    }

@url('/needs/add')
@requires_auth
@entitled(u'Add a need')
@as_html('needs/add_need.html')
def add_need(request):
    db = default_storage()

    ###
    import wtforms
#    from doqu.ext.forms import document_form_factory
#    BaseNeedForm = document_form_factory(Need, storage=db)
    class NeedForm(wtforms.Form):
        summary = wtforms.TextField('summary')
        stakeholders = wtforms.FieldList(wtforms.TextField('stakeholders'),
            min_entries=1)

    ###

    form = NeedForm(request.values)
    if request.method == 'POST':
        form = NeedForm(request.values)
        if form.validate():
            obj = Need()
            form.populate_obj(obj)
            obj.save(db)
            return redirect_to('needs.need', pk=obj.pk)
    return {'form': form}

@url('/needs/<string:pk>')
@requires_auth
@entitled(lambda pk: u'{0}'.format(default_storage().get(Need,pk)))
@as_html('needs/need_detail.html')
def need(request, pk):
    db = default_storage()
    obj = db.get(Need, pk)
    return {'object': obj}

#--- plans

@url('/plans/')
@requires_auth
@entitled(u'Plans')
@as_html('needs/plan_index.html')
def plan_index(request):
    db = default_storage()
    plans = Plan.objects(db).order_by('valid_until', reverse=True)
            #.where(unlocks_plan__in=[None])
            #.order_by('next_date_time')
    return {
        'object_list': plans,
        'render_rel_delta': render_rel_delta,
        'is_date_within_a_day': is_date_within_a_day,
    }

@url('/plans/<string:pk>')
@requires_auth
@entitled(lambda pk: u'{0}'.format(default_storage().get(Plan,pk)))
@as_html('needs/plan_detail.html')
def plan(request, pk):
    db = default_storage()
    # TODO: drop hierarchy, stick to semantics (reference to Need document)
    plan = HierarchicalPlan.object(db, pk)

    # task-related stats
    # TODO aggregate data from nested plans
    durations = (e.get_duration() for e in plan.events if e.get_duration())
    total_duration = sum(durations, datetime.timedelta(0)) # <- initial value

    # financial stats
    # TODO: aggregate data from nested plans
    payments = Payment.objects(db).where(plan=plan)
    total_amount = sum(p.get_amount_as() for p in payments)

    try:
        reasoned = ReasonedPlan.object(db, pk)
        outcome = reasoned.outcome
    except ValidationError:
        outcome = None

    return {
        'object': plan,
        'outcome': outcome,
        'total_duration': total_duration,
        'total_amount': total_amount,
        'render_rel_delta': render_rel_delta,
    }
""" TODO: archive of completed tasks (events)
@url('/payments/')
@url('/payments/<int(4):year>/')
@url('/payments/<int(4):year>/<int(2):month>/')
@url('/payments/<int(4):year>/<int(2):month>/<int(2):day>/')
@entitled(u'Payments')
@as_html('finances/event_index.html')
def event_index(request, year=None, month=None, day=None):
    events = Payment.objects(db).order_by('date_time', reverse=True)
    if year:
        events = events.where(date_time__year=year)
        if month:
            events = event.where(date_time__month=month)
            if day:
                events = events.where(date_time__day=day)
    return {'object_list': events}
"""
