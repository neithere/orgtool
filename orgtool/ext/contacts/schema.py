# -*- coding: utf-8 -*-

from docu import Document, Field as f
from werkzeug import cached_property
from orgtool.ext.tracking import TrackedDocument


__all__ = ['Actor', 'Organization', 'Person', 'Contact']


CONTACT_TYPES = (
    u'email', #u'E-mail'),
    u'phone', #u'Phone number'),
    u'url', #u'Website'),
    u'text', #u'Text details'),
)

CONTACT_SCOPES = (
    u'primary',# u'Primary'),
    u'home',# u'Home'),
    u'work',# u'Work'),
    u'mobile',
)


class Actor(TrackedDocument):
    name = f(unicode, required=True)
    is_actor = f(bool, choices=[True])

    def __unicode__(self):
        return u'{name}'.format(**self)

    @cached_property
    def contacts(self):
        db = self._saved_state.storage
        return Contact.objects(db).where(actor=self.pk)


class Organization(Actor):
    is_organization = f(bool, choices=[True])


class Person(Actor):
    name = f(unicode, required=True,
             default=lambda d: ' '.join([d.first_name or '',
                                         d.last_name or '']).strip())
    first_name = f(unicode, essential=True)
    second_name = f(unicode, essential=True)
    last_name = f(unicode, essential=True)
    details = f(unicode)
#    birth_date =


class Contact(TrackedDocument):
    summary = f(unicode, required=True,
                default=lambda d: d.person.name if d.person else None)
    actor = f(Actor)

    kind = f(unicode, required=True, choices=CONTACT_TYPES)
    scope = f(unicode, choices=CONTACT_SCOPES, default=CONTACT_SCOPES[0][0])
    value = f(unicode, required=True)

    # XXX validators?

    """
    # contact data; maybe should be references.
    # also validators should be added.
    email = f(unicode)
    phone = f(unicode,
              default=lambda d: d.phone_mobile or d.phone_home or d.phone_work)
    phone_mobile = f(unicode)
    phone_home = f(unicode)
    phone_work = f(unicode)
    url = f(unicode)
    """

    def __unicode__(self):
        return u'{summary} {kind} {value} ({scope})'.format(**self)

