from tool.ext import admin
from orgtool.ext.tracking.admin import TrackedAdmin
from schema import Contact


NAMESPACE = 'contacts'


@admin.register_for(Contact)
class ContactAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = 'actor', 'kind', 'scope', 'value'
