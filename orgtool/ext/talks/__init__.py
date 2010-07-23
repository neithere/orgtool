# -*- coding: utf-8 -*-

from tool.ext.templating import register_templates
from schema import *
from views import *
import admin


register_templates(__name__)


# just an idea:
#from tool.app import App
#
#app = App(__name__)
#app.register_templates()
#app.register_routing('views')
