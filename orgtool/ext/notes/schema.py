# -*- coding: utf-8 -*-

import datetime
from dateutil.rrule import rrule

from docu import Document, Field as f
from docu import validators

from orgtool.ext.tracking import TrackedDocument


class Idea(TrackedDocument):
    summary = f(unicode, required=True, label=u'Описание')
    is_reviewed = f(bool, essential=True, label=u'Рассмотрена', default=False)
    is_needed = f(bool, essential=True, label=u'Нужна', default=False)
    #is_accepted = f(bool, essential=True, label=u'Принята', default=False)
    #is_done = f(bool, essential=True, label=u'Реализована', default=False)
    # TODO: topic/tags/category/whatever

    def __unicode__(self):
        return u'[{0}] [{1}] {2}'.format(
            'R' if self.is_reviewed else '_',
            'N' if self.is_needed else '_',
            self.summary)


class Bookmark(TrackedDocument):
    url = f(unicode, required=True)
    summary = f(unicode)
    details = f(unicode)
    tags = f(list)
    date_time = f(datetime.datetime)
    shared = f(bool)
    # TODO: validate url

    def __unicode__(self):
        return u'{url} — {summary}'.format(**self)
