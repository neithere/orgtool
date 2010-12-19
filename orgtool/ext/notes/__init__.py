"""
Notes
=====
"""
from tool.plugins import BasePlugin
from tool.ext.templating import as_html, register_templates

from schema import *
import admin
from views import *


class NotesPlugin(BasePlugin):
    """Web interface.
    """
    def make_env(self):
        register_templates(__name__)
