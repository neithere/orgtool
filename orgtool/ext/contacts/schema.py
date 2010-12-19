# -*- coding: utf-8 -*-

from doqu import Document, Field as f
from werkzeug import cached_property
from orgtool.ext.tracking import TrackedDocument
from orgtool.ext.actors.schema import Actor


__all__ = ['Contact']


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


class Contact(TrackedDocument):
    summary = f(unicode, required=True,
                default=lambda d: unicode(d.actor) or None)
    actor = f(Actor)

    kind = f(unicode, required=True, choices=CONTACT_TYPES, default='text')
    scope = f(unicode, choices=CONTACT_SCOPES, default=CONTACT_SCOPES[0])
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

# class Actor(...):
#    @cached_property
#    def contacts(self):
#        db = self._saved_state.storage
#        return Contact.objects(db).where(actor=self.pk)

# TODO use Docu's reverse relationship API when it's ready
Actor.contacts = cached_property(lambda self: Contact.objects(self._saved_state.storage).where(actor=self.pk))

