# -*- coding: utf-8 -*-

from doqu import Document, Field as f
from werkzeug import cached_property
from orgtool.ext.tracking import TrackedDocument


__all__ = ['Actor', 'Organization', 'Person']


class Actor(TrackedDocument):
    name = f(unicode, required=True)
    is_actor = f(bool, choices=[True], default=True)

    def __unicode__(self):
        return u'{name}'.format(**self)

#    @cached_property
#    def contacts(self):
#        db = self._saved_state.storage
#        return Contact.objects(db).where(actor=self.pk)


class Organization(Actor):
    is_organization = f(bool, choices=[True], default=True)


class Person(Actor):
    name = f(unicode, required=True,
             default=lambda d: ' '.join([d.first_name or '',
                                         d.last_name or '']).strip())
    first_name = f(unicode, essential=True)
    second_name = f(unicode, essential=True)
    last_name = f(unicode, essential=True)
    details = f(unicode)
#    birth_date =
