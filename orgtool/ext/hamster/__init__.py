"""
Time tracker: Hamster
=====================
"""
from tool.dist import check_dependencies
from tool.plugins import BasePlugin

check_dependencies(__name__)

from schema import *
from commands import import_facts, update_facts, purge_facts


class HamsterPlugin(BasePlugin):
    """CLI interface.
    """
    identity = 'hamster'
    requires = ('tool.ext.documents',)
    commands = [import_facts, update_facts, purge_facts]
