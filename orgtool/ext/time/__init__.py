# -*- coding: utf-8 -*-
"""
Time tracking
=============
"""

from tool.plugins import BasePlugin
#from tool.ext.templating import register_templates
from commands import *
#import admin


class TimeCLI(BasePlugin):
    "A stripped-down lightweight time tracking plugin (CLI only)"
    requires = ['{document_storage}']
    features = 'time-tracker'
    commands = [
        start_activity, stop_current_event, cancel_current_event,
        update_current_event, comment_current_event, add_past_event,
        show_history,
    ]


#class TimeWeb(TimeCLI):
#    "The basic full-blown plugin for needs management."
#    requires = NeedsCLI.requires + ['tool.ext.templating']
#
#    def make_env(self):
#        register_templates(__name__)
