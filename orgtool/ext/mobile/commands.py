# -*- coding: utf-8 -*-

import datetime
import gammu      # XXX cannot be installed via pip, only as part of gammu dist

from tool import cli
from tool import context
from tool.ext.documents import db

from schema import GammuSMS, GammuContact, GammuPlan


def _get_my_number():
    bundle_name = '.'.join(__name__.split('.')[:-1])
    conf = context.app.get_settings_for_bundle(bundle_name)
    my_number = conf.get('my_number')
    assert my_number, 'Gammu integration requires "my_number" setting'
    if isinstance(my_number, int):
        return u'+{0}'.format(my_number)
    return unicode(my_number)


def _import_one_sms(data):
    # define who's the actor and who's the receiver
    my_number = _get_my_number()
    other_number = unicode(data['Number'])
    if data['State'] == 'Sent':
        sent_by, sent_to = my_number, other_number
    else:
        sent_by, sent_to = other_number, my_number

    fields = dict(
        sent_by = sent_by,
        sent_to = sent_to,
        date_time = data['DateTime'],
        #is_confirmed = True,  # it is sent, yup
        summary = data['Text'],
    )
    search_fields = dict(fields).pop('summary')

    if not GammuSMS.objects(db).where(**fields).count():
        print 'SAVING', sent_by, '->', sent_to, fields['date_time'], fields['summary'][:20]
        return GammuSMS(**fields).save(db)

def _get_state_machine():
    print 'Connecting to the phone...'

    sm = gammu.StateMachine()
    sm.ReadConfig()
    sm.Init()

    phone_info = sm.GetManufacturer(), sm.GetModel()[0]
    print '%s %s connected' % phone_info

    return sm

@cli.command()
def import_mobile_contacts():
    sm = _get_state_machine()
    memory = 'ME'    # TODO: allow importing from SIM memory, too

    # NOTE: GetNextMemory is not implemented as of python-gammu 1.28.0, so we
    # cannot reuse the iteration code from _iterate_results.
    #
    # Also, we have to iterate the whole lot of slots despite there can be
    # actually a very few records at the very beginning of the list. The import
    # process may seem too long because of this.
    seen_cnt = saved_cnt = 0
    location = 0
    while True:
        location += 1
        try:
            item = sm.GetMemory(Type=memory, Location=location)
        except gammu.ERR_EMPTY:
            # empty records are not always at the end
            continue
        except gammu.ERR_INVALIDLOCATION:
            # aha, looks like there are no more slots
            break
        else:
            seen_cnt += 1
            elems = [(x['Type'], x['Value']) for x in item['Entries']]
            person, contacts = GammuContact.from_raw_elems(elems)

            def _contact_exists(contact):
                conditions = {'kind': contact.kind, 'value': contact.value}
                duplicates = GammuContact.objects(db).where(**conditions)
                return bool(duplicates.count())

            contacts = [c for c in contacts if not _contact_exists(c)]

            if not contacts:
                # even the Person instance is not saved if there's no new
                # contact information (the contacts could be moved btw)
                continue

            # this could be improved so that details don't matter, etc.
            person, created = db.get_or_create(type(person), **person)
            for contact in contacts:
                contact.person = person
                contact.save(db)

    print 'Imported {saved_cnt} of {seen_cnt}.'.format(**locals())

@cli.command()
def import_mobile_sms():
    sm = _get_state_machine()

    seen_cnt = saved_cnt = 0
    for data in _iterate_results(sm.GetNextSMS, Folder=0):
        saved = _import_one_sms(data)
        if saved:
            saved_cnt += 1
        seen_cnt += 1

    print 'Imported {saved_cnt} of {seen_cnt}.'.format(**locals())

    # TODO: check msg['UDH'] -- it contains info on concatenated msgs:
    #
    #  'UDH': {'Text': 'hello',
    #          'ID16bit': -1,
    #          'AllParts': 2,
    #          'ID8bit': 0,
    #          'PartNumber': 2,
    #          'Type': 'ConcatenatedMessages'}

@cli.command()
def import_mobile_plans():
    sm = _get_state_machine()

    for data in _iterate_results(sm.GetNextCalendar):
        type_ = data['Type']
        entries = data['Entries']  # list of dicts

        print 'type:', type_
        print 'entries:', [(e['Type'], e['Value']) for e in entries]

        raise NotImplementedError('sorry!')

        # TODO: GammuPlan(...)


def _iterate_results(method, **kwargs):
    # XXX this weird idiom (along with the non-PEP-8 names) is taken straight
    # from the examples (see python-gammu documentation)
    location = None
    start = True
    while True:
        try:
            if start:
                entry = method(Start=start, **kwargs)
                start = False
            else:
                entry = method(Location=location, Start=start, **kwargs)
                #              ^^^^^^^^^^^^^^^^^ WTF, prev. loc.!?
        except gammu.ERR_EMPTY:
            break
        else:
            # This is sick but we have to work with it
            if isinstance(entry, list):
                location = entry[0]['Location']
                yield entry[0]
            else:
                location = entry['Location']
                yield entry
