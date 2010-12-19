# -*- coding: utf-8 -*-
"""
Needs management
================
"""
from tool.plugins import BasePlugin
#from tool.ext.templating import register_templates
from commands import (
    list_needs, view_need, add_need, rename_need, mark_need, move_need,
    delete_need
)
import admin


class NeedsCLI(BasePlugin):
    "A stripped-down lightweight needs management plugin (CLI only)"
    features = 'needs'
    requires = ['{document_storage}']
    commands = [
        list_needs, view_need, add_need, rename_need, mark_need, move_need,
        delete_need
    ]


class NeedsPlugin(NeedsCLI):
    "The basic full-blown plugin for needs management."
    requires = NeedsCLI.requires + ['{templating}']

    def make_env(self):
        templating = self.app.get_feature('templating')
        templating.register_templates(__name__)
