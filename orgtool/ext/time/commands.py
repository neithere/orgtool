# -*- coding: utf-8 -*-
"""
Commands
========

These commands form a command-line time tracker. Any activity
(:class:`~orgtool.ext.schema.Event` object) can be linked to
an outcome (a :class:`~orgtool.ext.needs.schema.Need` object).


"""
import re
from itertools import chain

from tool.cli import (
    # commands
    arg, alias, CommandError, confirm,
    # colors
    Fore, Back, Style
)
from tool.ext.documents import default_storage

from orgtool.ext.events.schema import Event
from orgtool.ext.needs.schema import (
    Need, SystemUnderDevelopment, ReasonedEvent
)
from orgtool.ext.needs.helpers import (
    MultipleMatches, NotFound, get_single, fix_unicode
)
#from .helpers import *


#__all__ = ['start', 'stop', 'cancel', 'update', 'note', 'log', 'recall']


@alias('ls')
@arg('--count', default=False,
     help='only display the number of matching events')
@arg('-q', '--query', help='events must match this regex')
@arg('--format', help='a Python string format for events')
def show_history(args):
    """Displays events filtered by given query or given date.

    Concerning format: the `Python string formatting` rules apply. For the list
    of available fields see the :class:`orgtool.ext.events.schema.Event`
    document. Also available is keyword "delta".

    .. _Python string formatting: http://docs.python.org/library/string.html
    """
    fix_unicode(args, 'query', 'format')
    # TODO this lists *all* events, whether related to time tracking or not.
    # here we only need a subset of them: the *user's* activities!

    # FIXME
    import warnings
    warnings.warn('FIXME: for some reason "ls|wc -l" and "ls --count" '
                  'return slightly different results')

    db = default_storage()
    events = Event.objects(db).order_by('date_time')
    if args.query:
        events = events.where(summary__matches_caseless=args.query)
    if args.count:
        yield events.count()
    else:
        for event in events:
            template = args.format or u'{date_time} {summary}'
            delta = ''
            if 'delta' in template:
                if event.date_time_end:
                    delta = event.date_time_end - event.date_time
            yield template.format(delta=delta, **event)

@alias('current')
def get_current_activity(args):
    raise NotImplementedError

@alias('start')
def start_activity(args):
    raise NotImplementedError

@alias('stop')
def stop_current_event(args):
    # XXX paused or cancelled or finished
    raise NotImplementedError

@alias('cancel')
def cancel_current_event(args):
    raise NotImplementedError

@alias('update')
def update_current_event(args):
    raise NotImplementedError

@alias('note')
def comment_current_event(args):
    "Add note to current activity."
    raise NotImplementedError

@alias('log')
def add_past_event(args):
    raise NotImplementedError
