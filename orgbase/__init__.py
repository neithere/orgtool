# -*- coding: utf-8 -*-

# gh
from glashammer.utils import Pagination, Response, get_app
from glashammer.bundles.i18n import setup_i18n, _
from glashammer.bundles.contrib.auth.repozewho import setup_repozewho

# 3rd-party
from glasnaegel.decorators import render_to
from glasnaegel.bundles.models import setup_models, storage
from glasnaegel.bundles.auth import setup_auth, login_required
from glasnaegel.utils import Appliance, expose

# this appliance
from forms import GoalForm
from models import Goal, Task  # TODO many other models


class OrgBase(Appliance):

    def setup_appliance(self, app):
        app.add_setup(setup_auth)
        app.add_setup(setup_i18n)
        app.add_setup(setup_models)

    #-- VIEWS ------------------------------------------------------------------

    @expose('/goals/')
    #@login_required
    @render_to('goals.html')
    def goals(self, req):
        return {
            'objects': Goal.objects(storage),
        }

    @expose('/goals/<string:pk>/')
    #@login_required
    @render_to('goal.html')
    def goal(self, req, pk):
        return {
            'object': storage.get(Goal, pk)
        }

    #@expose('/goals/<string:pk>/edit/')
    #@login_required
    #@render_to('goal_edit.html')
    #def goal_edit(self, req, pk):
    #    ... forms ...
    #    return {
    #        'object': storage.get(Goal, pk)
    #    }

    @expose('/tasks/')
    @render_to('tasks.html')
    def tasks(self, req):
        query = Task.objects(storage).order_by('-created')
        objects, pagination = paginated(query, req)
        return {
            'objects': objects,   # TODO: pagination (offset via backend?)
            'pagination': pagination,
        }

    @expose('/tasks/<string:pk>/')
    #@login_required
    @render_to('task.html')
    def task(self, req, pk):
        return {
            'object': storage.get(Task, pk)
        }


def paginated(query, req, url_args=None):
    page = int(req.values.get('page', 1))
    per_page = int(req.values.get('per_page', 15))
    total = query.count()
    url_args = url_args or {}
    pagination = Pagination(req.endpoint, page, per_page, total, url_args)
    offset = (page-1) * per_page
    limit = offset + per_page
    paginated_objects = query[offset:limit]
    return paginated_objects, pagination
