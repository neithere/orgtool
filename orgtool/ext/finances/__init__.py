# -*- coding: utf-8 -*-
"""
Finances
========
"""
from tool.plugins import BasePlugin
from tool.ext.templating import register_templates
from schema import *
from views import *
import admin


class WebMoneyTracker(BasePlugin):
    """Money tracker: web interface.
    """
    features = 'money'
    requires = ['{templating}', '{routing}']

    def make_env(self, default_currency='EUR'):
        register_templates(__name__)
        return {'default_currency': default_currency}
