# -*- coding: utf-8 -*-
"""
Commands for importing data from `Project Hamster`_, a time tracking tool.

.. _Project Hamster: http://projecthamster.wordpress.com/

.. warning::

    We cannot guarantee accurate import/export because Hamster does not update
    facts when user edits them — it deletes the old fact and creates a new one.
    Every time. Even if you only change the description. So we only can import
    new facts, update existing ones and purge orphaned. It seems that updating
    does not make sense with regard to Hamster's way of dealing with fact IDs.

    So be careful: if you edit a fact in *orgtool* and then update it in
    Hamster, you will lose local changes after the next purge. And you have to
    purge the facts to avoid duplicates.

    So there. Not very nice. But anyway.

"""

import datetime
import dbus.exceptions
import hamster.client
import pytz
import tool.cli
from tool.ext.documents import db
from schema import HamsterFact


# Hamster stores dates in local timezone, darn
TIMEZONE = 'Asia/Yekaterinburg'


@tool.cli.command()
def import_hamster_facts():
    """Imports all available facts from Hamster. Checks uniqueness."""
    imported = HamsterFact.objects(db).order_by('date_time', reverse=True)
    start_date = imported[0].date_time if imported else datetime.date(1980,1,1)

    print('Importing all facts since {0}'.format(start_date))

    imported_cnt = 0

    storage = hamster.client.Storage()

    for data in storage.get_facts(start_date, datetime.date.today()):
        saved = _import_fact(data)
        if saved:
            imported_cnt += 1

    print 'Imported {imported_cnt} facts.'.format(**locals())

@tool.cli.command()
def update_hamster_facts():
    """Updates all facts previously imported from Hamster.
    Looks like this command doesn't make sense since Hamster replaces facts
    instead of updating them.""" #XXX
    imported = HamsterFact.objects(db).order_by('date_time')
    start_date = imported[0].date_time if imported else datetime.date(1980,1,1)

    print('Updating all facts since {0}'.format(start_date))

    seen_cnt = updated_cnt = 0

    storage = hamster.client.Storage()

    for data in storage.get_facts(start_date, datetime.date.today()):
        updated = _update_fact(data)
        if updated:
            updated_cnt += 1
        seen_cnt += 1

    print 'Updated {updated_cnt} facts of {seen_cnt}.'.format(**locals())

@tool.cli.command()
def purge_hamster_facts():
    """Deletes all facts previously imported from Hamster and not currently
    present there.
    """
    imported = HamsterFact.objects(db).order_by('date_time')
    storage = hamster.client.Storage()

    seen_cnt = deleted_cnt = 0

    print('Purging orphaned facts...')

    for fact in imported:
        fact_id = int(fact.x_hamster_id)
        try:
            storage.get_fact(fact_id)
        except dbus.exceptions.DBusException:
            print 'DEL', fact, fact.get_duration()
            #fact.delete()
            deleted_cnt += 1
        seen_cnt += 1

    print 'Deleted {deleted_cnt} facts of {seen_cnt}.'.format(**locals())

def _convert_date(date):
    timezone = pytz.timezone(TIMEZONE)
    local_date = timezone.localize(date)  # just add tzinfo
    utc_date = local_date.astimezone(pytz.utc)
    return pytz.utc.normalize(utc_date)

def _prepare_data(data):
    return dict(
        summary = unicode(data['name']),
        details = unicode(data['description']),
        date_time = _convert_date(data['start_time']),
        date_time_end = _convert_date(data['end_time']),
        tags = [unicode(x) for x in data['tags']],

        x_hamster_type = u'fact',
        x_hamster_id = int(data['id']),
        x_hamster_category = unicode(data['category']),
        x_hamster_activity_id = int(data['activity_id']),
        #x_hamster_delta = data['delta'],  # a datetime.timedelta obj!
    )

def _import_fact(data):
    if HamsterFact.objects(db).where(x_hamster_id=int(data['id'])).count():
        return False
    prepared = _prepare_data(data)
    fact = HamsterFact(**prepared)
    fact.save(db)
    return fact

def _update_fact(data):
    facts = HamsterFact.objects(db).where(x_hamster_id=int(data['id']))
    if not facts:
        print 'no fact with id', repr(data['id'])
        return False
    assert 1 == len(facts)
    fact = facts[0]
    prepared = _prepare_data(data)
    for key in prepared:
        old_value = fact[key]
        if isinstance(old_value, datetime.datetime):
            old_value = pytz.utc.localize(old_value)
        if prepared[key] != old_value:
            print '---', fact
            print 'NOTEQ:', repr(prepared[key]), 'vs.', repr(fact[key])
            break
        print 'EQ:', repr(prepared[key]), 'vs.', repr(fact[key])
    else:
        print 'SAME', fact
        return False  # same data
    fact.update(**prepared)
    fact.save()
    return fact
