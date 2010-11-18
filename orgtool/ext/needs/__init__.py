# -*- coding: utf-8 -*-

from tool.plugins import BasePlugin
from tool.ext.templating import register_templates
from commands import ls, add, mv, rm
import admin


class NeedsPlugin(BasePlugin):
    identity = 'needs'
    commands = [ls, add, mv, rm]

    def make_env(self):
        register_templates(__name__)
