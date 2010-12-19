# -*- coding: utf-8 -*-
"""
Functions for parsing "informal" date definitions.
"""

import datetime
from dateutil.rrule import *
from lepl import *
import logging


__all__ = ['informal_rrule']


logger = logging.getLogger(__name__)


# The mappings are ordered because the parser must not match "week" before it
# sees "weeks". Note that `Or` in *not* greedy and will stop at first match.
FREQUENCIES = (
#    ('daily', DAILY),
    ('days', DAILY),
    ('day', DAILY),
#    ('weekly', WEEKLY),
    ('weeks', WEEKLY),
    ('week', WEEKLY),
#    ('monthly', MONTHLY),
    ('months', MONTHLY),
    ('month', MONTHLY),
#    ('yearly', YEARLY),
    ('years', YEARLY),
    ('year', YEARLY),
)

FREQ_NAMES = [x[0] for x in FREQUENCIES]  # order matters
WEEKDAYS = (
    ('Monday', MO),
    ('mon', MO),
    ('Tuesday', TU),
    ('tue', TU),
    ('Wednesday', WE),
    ('wed', WE),
    ('Thursday', TH),
    ('thu', TH),
    ('Friday', FR),
    ('fri', FR),
    ('Saturday', SA),
    ('sat', SA),
    ('Sunday', SU),
    ('sun', SU),
)

WDAY_NAMES = [x[0] for x in WEEKDAYS]
MONTHS = (
    ('january', 1),
    ('jan', 1),
    ('february', 2),
    ('feb', 2),
    ('march', 3),
    ('mar', 3),
    ('april', 4),
    ('apr', 4),
    ('may', 5),
    ('june', 6),
    ('jun', 6),
    ('july', 7),
    ('jul', 7),
    ('august', 8),
    ('aug', 8),
    ('september', 9),
    ('sep', 9),
    ('october', 10),
    ('sep', 9),
    ('november', 11),
    ('nov', 11),
    ('december', 12),
    ('dec', 12),
)
MONTH_NAMES = [x[0] for x in MONTHS]


def _make_date_parser():
    #comma = Drop(',')
    #weekday = Or(*[Literal(x) for x in wday_names])[:, comma] > 'weekday'
    with Separator(~Regexp(r',?\s+|,')):
        ordinal = Drop(Literal('st')|'nd'|'th')[0:1]
        swearing = Drop(Literal('bloody ')|'damn '|'freaking ')[0:1]
        prefix = Literal('every ')[0:1]

        interval = Integer()                            >> int  > 'interval'
        _frq = lambda arg: dict(FREQUENCIES)[arg]
        freq = Or(*[Literal(x) for x in FREQ_NAMES])    >> _frq > 'freq'

        # frequency names
        _wd = lambda arg: dict(WEEKDAYS)[arg]
        weekday = Or(*[Literal(x) for x in WDAY_NAMES]) >> _wd  > 'byweekday'
        day = And(Integer(), ordinal)                   >> int  > 'bymonthday'
        _mon = lambda arg: dict(MONTHS)[arg]
        month = Or(*[Literal(x) for x in MONTH_NAMES])  >> _mon > 'bymonth'

        # date
        date = (
            ( day[1:] & month[1:])
            | month[1:]
            | ( interval & weekday[1:] | weekday[1:] )
            | day[1:] & Drop(Literal('day of every month'))
            | day[1:] & Drop(Literal('of every month'))
            | day[1:]
        )

        # time
        at_ = Drop(Literal('@') | 'at ')
        hour = Integer()                                >> int > 'byhour'
        timesep = Drop(Literal(':'))
        minute = Integer()                              >> int > 'byminute'
        time_full = And(hour, timesep, minute)
        time = time_full | And(at_, time_full | hour)

        # date and time
        date_time = date&time | date

        # all together
        defs = freq&time | freq | interval&freq | date_time | interval
        spec = And(prefix, swearing, defs) > Node  #& Drop(Eof()) > Node

    return spec.get_parse_string()

date_parser = _make_date_parser()

def informal_rrule(string, since=None, until=None):
    """
    Expects a string like "every day at 9:30" or "every tue, fri @9" or
    "every 28 mar" or even "every bloody week" (that's a rule for repeating
    events, right?) and returns a `rrule` object that can be used to easily
    generate sequences of dates based on the rule. See the `dateutil
    documentation`_ and RFC2445_ for details.

    .. _dateutil documentation: http://labix.org/python-dateutil
    .. _RFC2445: http://ietf.org/rfc/rfc2445.txt

    Same results can be yielded by::

        rrulestr("DTSTART:19830328\nRRULE:FREQ=DAILY;WKST=TU")

        rrule(DAILY, bymonth=3, bymonthday=28,
              dtstart=datetime.date(1983,3,28))

        informal_rrule('every Tuesday', since=datetime.date(1983,3,28))

    """
    string = string.strip()
    if not any([string, since, until]):
        return None
    assert string

    #print 'got', repr(string), 'since', since, 'until', until
    # TODO: wrap LEPL exceptions
    node = date_parser(string)[0]

    kwargs = {
        'freq': DAILY,
        'dtstart': since,
        'until': until,
    }

    names = (
        'freq', 'interval', 'byyear',
        'bymonth', 'bymonthday',
        'byweek', 'byweekday',
        'byhour', 'byminute',
    )
    for name in names:
        if hasattr(node, name):
            value = getattr(node, name)
            if name in ('freq', 'interval'):
                value = value[0]
            kwargs[name] = value

    logger.debug(u'rrule(**{0})'.format(kwargs))

    return rrule(**kwargs)

# TODO: move this to tests
"""
parser = spec.get_parse_string()
#print (((Integer() | wdays) & spaces)[:2] & Drop(Eof()) > Node).parse('12 b,a')[0]
print
strings = [

    'every 1', 'every day', 'every 2 day', 'every 2 mar', 'every tue',
    'every tue,wed', 'every 3 tue,wed', 'every week', 'every 2 week',
    'every month', 'every jun', 'every year', 'every 2 year',
    'every day @9', 'every day at 9', 'every day 9:00', 'every tue @9',
    'every mon, wed, fri at 15:30',
    'every 27 mar, jul, nov',  # elektr rz
    'every 21 nov',  # my domain
    'every 25',  # phone, net
    'every day',  # hosting
]
#strings = ['every tue, wed']
for string in strings:
    print '---'
    print '>>>', repr(string)
    print parser(string)[0]
    # or, better, parser(string)[0].weekday
    # hmm.. we'll have to use hasattr(node, key) and then getattr().
"""

if __name__=='__main__':
    import sys
    string = ' '.join(sys.argv[1:])
    if string:
        print '-------------------------------------------------------'
        print '>>>', repr('every ' + string)
        print date_parser(string)[0]
        rrule = informal_rrule(string)
        print rrule
        print u'Next occurence: {0} ({1} days left)'.format(rrule[0],
                   (rrule[0] - datetime.datetime.today()).days)
