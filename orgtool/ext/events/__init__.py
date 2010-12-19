"""
Events
======

This extension provides one of the most important schemata in the *OrgTool*
ecosystem. *Event* is the core model for messages, payments, etc.
"""
from schema import *
from commands import list_events
import admin


def event_extension(app, conf):
    """Provides a simple CLI for event management.
    """
    assert not conf
    app.cli_parser.add_commands([list_events], namespace='events')
