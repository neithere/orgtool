# -*- coding: utf-8 -*-
"""
Talks
=====

Communication tracker.
"""
from tool.plugins import BasePlugin
from tool.ext.templating import register_templates
from schema import *
from views import *
import admin


class TalksPlugin(BasePlugin):
    """Web interface.
    """
    def make_env(self):
        register_templates(__name__)

# just an idea:
#from tool.app import App
#
#app = App(__name__)
#app.register_templates()
#app.register_routing('views')
