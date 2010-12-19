# -*- coding: utf-8 -*-
"""
Contacts
========
"""
from tool.plugins import BasePlugin
#from tool.ext.templating import register_templates

from schema import *
import admin
#from views import *
from commands import (
    list_contacts, open_urls, add_contact, move_contact
)


class ContactsCLI(BasePlugin):
    """A stripped-down CLI-only contacts management plugin.
    """
    features = 'contacts'
    requires = ('{document_storage}',)
    commands = [list_contacts, open_urls, add_contact, move_contact]


class ContactsWeb(ContactsCLI):
    """A CLI- and web-enabled contacts management plugin. Integrates with
    WebAdmin.
    """
    requires = ContactsCLI.requires + (
        '{routing}', '{templating}',
        'tool.ext.admin.AdminWeb',
    )

    def make_env(self):
        templating = self.app.get_feature('templating')
        templating.register_templates(__name__)
