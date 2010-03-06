# -*- coding: utf-8 -*-

# gh
from glashammer.utils import Response, get_app
from glashammer.bundles.i18n import setup_i18n, _
from glashammer.bundles.contrib.auth.repozewho import setup_repozewho

# 3rd-party
from glasnaegel.decorators import render_to
from glasnaegel.bundles.models import setup_models, storage
from glasnaegel.utils import Appliance, expose, paginated

# this appliance
from forms import GoalForm
from models import Goal, Task  # TODO many other models
import admin    # will register models automatically


class OrgBase(Appliance):

    def setup_appliance(self, app):
        #app.add_setup(setup_auth)
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
            'objects': objects,
            'pagination': pagination,
        }

    @expose('/tasks/<string:pk>/')
    #@login_required
    @render_to('task.html')
    def task(self, req, pk):
        return {
            'object': storage.get(Task, pk)
        }

