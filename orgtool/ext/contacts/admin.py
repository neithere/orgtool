from tool.ext import admin
from orgtool.ext.tracking.admin import TrackedAdmin
from schema import Actor, Organization, Person, Contact


NAMESPACE = 'contacts'


@admin.register_for(Actor)
class ActorAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = 'name',


@admin.register_for(Organization)
class OrganizationAdmin(ActorAdmin):
    namespace = NAMESPACE


@admin.register_for(Person)
class PersonAdmin(ActorAdmin):
    namespace = NAMESPACE
    list_names = 'name', 'first_name', 'last_name'


@admin.register_for(Contact)
class ContactAdmin(TrackedAdmin):
    namespace = NAMESPACE
    list_names = 'actor', 'kind', 'scope', 'value'
