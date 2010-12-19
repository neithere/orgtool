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
from tool.cli import arg
from doqu import Document
from tool.ext.documents import default_storage
from orgtool.ext.events import Plan
from schema import HamsterFact


# Hamster stores dates in local timezone, darn
# TODO: at least use config; maybe smth else?
#
# FIXME здесь полная путаница с часовыми поясами; я точно несколько раз забывал
# их поменять, так что придется всё импортировать ЗАНОВО.
# И просто необходимо какую-то сделать возм-ть указать точки смены часовых
# поясов. Или уже положить на Хамстер и делать свое приложение.
#
TIMEZONE = 'Asia/Yekaterinburg'


@arg('--date')
@arg('-d', '--dry-run', default=False, help='do not really save anything')
def import_facts(args):
    """Imports all available facts from Hamster. Checks uniqueness."""
    db = default_storage()
    if args.date:
        start_date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        imported = HamsterFact.objects(db).order_by('date_time', reverse=True)
        if imported:
            start_date = imported[0].date_time
        else:
            start_date = datetime.date(1980,1,1)

    print('Importing all facts since {0}'.format(start_date))
    if args.dry_run:
        print('(dry run, no data will be actually saved.)')

    imported_cnt = 0

    storage = hamster.client.Storage()

    for data in storage.get_facts(start_date, datetime.date.today()):
        saved = _import_fact(data, dry_run=args.dry_run)
        if saved:
            imported_cnt += 1

    print('Imported {imported_cnt} facts.'.format(**locals()))
    if args.dry_run:
        print('(None was actually saved in dry run mode.)')

@arg('-d', '--dry-run', default=False, help='do not update anything')
def update_facts(args):
    """Updates all facts previously imported from Hamster.

    Please note that this will only work for activity and category titles.
    Hamster does update records when they are changed. However, it *replaces*
    facts instead of updating them when other fields change their values, e.g.
    description or tags.
    """
    imported = HamsterFact.objects(db).order_by('date_time')
    start_date = imported[0].date_time if imported else datetime.date(1980,1,1)

    print('Updating all facts since {0}'.format(start_date))
    if args.dry_run:
        print('(dry run, no data will be actually updated.)')

    seen_cnt = updated_cnt = 0

    storage = hamster.client.Storage()

    for data in storage.get_facts(start_date, datetime.date.today()):
        updated = _update_fact(data, dry_run=args.dry_run)
        if updated:
            updated_cnt += 1
        seen_cnt += 1

    print('Updated {updated_cnt} facts of {seen_cnt}.'.format(**locals()))
    if args.dry_run:
        print('(None was actually saved in dry run mode.)')

@arg('-d', '--dry-run', default=False, help='do not delete anything')
def purge_facts(args):
    """Deletes all facts previously imported from Hamster and not currently
    present there.     WARNING: the command does *NOT* check if the "orphaned"
    facts are in the scope of given Hamster storage. That is, all facts
    gathered from an older storage will be DROPPED. This should be fixed later.
    """
    db = default_storage()
    imported = HamsterFact.objects(db).order_by('date_time')
    storage = hamster.client.Storage()

    seen_cnt = deleted_cnt = 0

    print('Purging orphaned facts...')
    if args.dry_run:
        print('(dry run, no data will be actually updated.)')

    for fact in imported:
        fact_id = int(fact.x_hamster_id)
        try:
            storage.get_fact(fact_id)
        except dbus.exceptions.DBusException:
            # fact is no more in Hamster
            # XXX TODO: check if the Hamster storage is not newer than known
            #           facts!!! if it is, we'll lose older data
            print 'DEL', fact, fact.get_duration()

            # check if the fact can be safely deleted.
            # FIXME this is a quick fix for plan references. We should instead
            # check for *all* attributes (via Document instance) and copy them
            # to the newer fact; if the newer fact cannot be found (e.g.
            # date/time were updated), then just leave it as is.
            # This should *not* apply to the created/updated tmestamps.
            plan_pk = fact.get('plan')
            plan = Plan.object(db, plan_pk) if plan_pk else None
            if plan:
                # try finding exact match by date/time (exact replacement)
                same_facts = imported.where(date_time=fact.date_time)
                same_facts = [f for f in same_facts if f.pk != fact.pk]
                replacement = same_facts[0] if same_facts else None
                if replacement:
                    print('  Copying plan to fact {0}'.format(replacement.pk))
                    assert not replacement.get('plan'), (
                        'the replacing fact must be freshly imported')
                    d = Document.object(db, replacement.pk)
                    d['plan'] = plan.pk
                    if not args.dry_run:
                        d.save()
                        fact.delete()
                    deleted_cnt += 1
                else:
                    print('  Not deleting: fact references plan {0}'.format(plan))
            else:
                if not args.dry_run:
                    fact.delete()
                deleted_cnt += 1
        seen_cnt += 1

    print('Deleted {deleted_cnt} facts of {seen_cnt}.'.format(**locals()))
    if args.dry_run:
        print('(None was actually deleted in dry run mode.)')

def _convert_date(date):
    if date is None:
        # this really can happen, e.g. importing current activity = no end time
        return
    timezone = pytz.timezone(TIMEZONE)
    local_date = timezone.localize(date)  # just add tzinfo
    utc_date = local_date.astimezone(pytz.utc)
    return pytz.utc.normalize(utc_date)

def _prepare_data(data):
    assert data.id
    return dict(
        summary = unicode(data.activity),
        details = unicode(data.description or ''),  # can be None
        date_time = _convert_date(data.start_time),
        date_time_end = _convert_date(data.end_time),
        tags = [unicode(x) for x in data.tags],

        x_hamster_type = u'fact',
        x_hamster_id = int(data.id),
        x_hamster_category = unicode(data.category),
        x_hamster_activity_id = int(data.activity_id),
        #x_hamster_delta = data['delta'],  # a datetime.timedelta obj!
    )

def _import_fact(data, dry_run=False):
    db = default_storage()
    assert data.id
    if HamsterFact.objects(db).where(x_hamster_id=int(data.id)).count():
        return False
    prepared = _prepare_data(data)
    fact = HamsterFact(**prepared)
    if not dry_run:
        fact.save(db)
    print 'ADD', fact
    return fact

def _update_fact(data, dry_run=False):
    db = default_storage()
    facts = HamsterFact.objects(db).where(x_hamster_id=int(data['id']))
    if not facts:
        print 'no fact with id', repr(data['id'])
        return False
    assert 1 == len(facts)
    fact = facts[0]
    prepared = _prepare_data(data)
    if prepared['tags'] == []:
        prepared['tags'] = None  # this is how the schema works
    for key in prepared:
        old_value = fact[key]
        if isinstance(old_value, datetime.datetime):
            old_value = pytz.utc.localize(old_value)
        if prepared[key] != old_value:
            print '---', fact
            print 'NOTEQ {0}: {1} vs. {2}'.format(
                key, repr(prepared[key]), repr(fact[key]))
            break
        #print 'EQ:', repr(prepared[key]), 'vs.', repr(fact[key])
    else:
        #print 'SAME', fact
        return False  # same data
    fact.update(**prepared)
    if not dry_run:
        fact.save()
    return fact
