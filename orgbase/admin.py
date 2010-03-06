# -*- coding: utf-8 -*-

"""
Administrative interface for this appliance.
"""

# GH
from glashammer.utils import url_for

# 3rd-party
from glasnaegel.bundles.admin import AdminSite

# this app
from models import Goal, Task  # TODO many other models


def urlgetter(obj):
    # our custom function to map model instances to views/endpoints
    model_name = type(obj).__name__.lower()
    return url_for('orgbase/%s' % model_name, **{'pk': obj.pk})

for model in Goal, Task:
    AdminSite.register(model, namespace='organizer', url=urlgetter,
                       exclude=['created', 'updated'])

