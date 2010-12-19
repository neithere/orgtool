# -*- coding: utf-8 -*-

import datetime
import gammu      # XXX cannot be installed via pip, only as part of gammu dist

from tool.cli import arg, CommandError
from tool import app

from schema import GammuSMS, GammuContact, GammuPlan


def _get_my_numbers():
    bundle_name = '.'.join(__name__.split('.')[:-1])
    my_numbers = app.get_feature('mobile').get('my_numbers')
    assert my_numbers, ('Gammu integration requires "my_numbers" setting. '
                        'It must be a dictionary like {"work": "123"}.')
    assert isinstance(my_numbers, dict)
    def _normalize(value):
        if isinstance(value, int):
            return u'+{0}'.format(value)
        return unicode(value)
    return dict((k,_normalize(v)) for k,v in my_numbers.iteritems())

def _import_one_sms(data, current_number=None, dry_run=False):
    # define who's the actor and who's the receiver
    other_number = unicode(data['Number'])
    if data['State'] == 'Sent':
        sent_by, sent_to = current_number, other_number
    else:
        sent_by, sent_to = other_number, current_number

    fields = dict(
        sent_by = sent_by,
        sent_to = sent_to,
        date_time = data['DateTime'],
        #is_confirmed = True,  # it is sent, yup
        summary = data['Text'] or u'[text missing]',  # u'' is invalid, None not accepted
    )
    search_fields = dict(fields)
    search_fields.pop('summary')

    # workaround: we don't know which number was "current" when the message was
    # last imported, so we look for any "our" number.
    my_numbers = _get_my_numbers()
    k = 'sent_by' if data['State']=='Sent' else 'sent_to'
    search_fields.pop(k)
    search_fields.update({'{0}__in'.format(k): my_numbers.values()})

    db = app.get_feature('document_storage').default_db
    if not GammuSMS.objects(db).where(**search_fields).count():
        #print 'NOT FOUND:', search_fields
        print u'SAVING {0} {1} → {2} {3}{4}'.format(
            fields['date_time'], sent_by, sent_to, fields['summary'][:20],
            u'…' if 20 < len(fields['summary']) else '')
        if dry_run:
            return '(stub: dry run)'
        else:
            return GammuSMS(**fields).save(db)

def _get_state_machine():
    print 'Connecting to the phone...'

    sm = gammu.StateMachine()
    sm.ReadConfig()
    sm.Init()

    phone_info = sm.GetManufacturer(), sm.GetModel()[0]
    print '%s %s connected' % phone_info

    return sm

def import_contacts():
    db = app.get_feature('document_storage').default_db
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

@arg('-p', '--current-phone')
@arg('-f', '--full-archive', default=False, help='scan the whole SMS archive')
@arg('-d', '--dry-run', default=False, help='do not save imported messages')
def import_sms(args):
    """Imports SMS from mobile phone.

    :param current_phone:
        Expects "current phone" so that incoming and outgoing messages can be
        correctly populated with both sender and receiver numbers (the phone only
        stores the "other" number) and you have to manually specify yours). Can be
        omitted if there's only one "my number" in the settings.

        Note that you should specify the label (e.g. "personal", "work" or
        "primary") instead of the number itself. The labels are defined in the
        "my_numbers" setting for the bundle::

            extensions:
                orgtool.ext.mobile.MobileETL:
                    my_numbers:
                        home: +1234567890
                        work: +0987654321

    :param full_archive:
        If True, attempts to import all messages in the phone. Despite this
        implies checking for duplicates, the process takes longer and issues
        with dates and phone numbers may arise. By default this option is off
        and only "new" messages are imported. Message is considered "new" if
        its date is greater than the last known message's date. Time is
        ignored in this check.

    :param dry_run:
        If True, newly imported messages are not saved. Use this for testing.
        Default is False.

    """
    if args.dry_run:
        yield 'Dry run, no data will be changed.'

    db = app.get_feature('document_storage').default_db
    my_numbers = _get_my_numbers()
    current_number = None
    if args.current_phone:
        assert args.current_phone in my_numbers, (
            'unknown number label "{0}"'.format(args.current_phone))
        current_number = my_numbers[args.current_phone]
    else:
        if len(my_numbers) != 1:
            raise CommandError('Which phone (SIM card) is that? Choices: '
                               '{0}'.format(', '.join(my_numbers)))
        the_only_label = my_numbers.keys()[0]
        current_number = my_numbers[the_only_label]
    assert current_number

    # find latest known message date
    if args.full_archive:
        last_imported_date = None
        yield 'Importing all messages from the phone...'
    else:
        msgs = GammuSMS.objects(db).order_by('date_time', reverse=True)
        last_imported_date = msgs[0].date_time.date() if msgs.count() else None
        yield 'Importing messages since {0}...'.format(last_imported_date)

    sm = _get_state_machine()

    seen_cnt = saved_cnt = 0
    for data in _iterate_results(sm.GetNextSMS, Folder=0):
        if last_imported_date and not args.full_archive:
            # skip message without full check if a later message had been
            # already imported
            if data['DateTime'].date() < last_imported_date:
                continue
        saved = _import_one_sms(data, current_number, dry_run=args.dry_run)
        if saved:
            saved_cnt += 1
        seen_cnt += 1

    yield 'Imported {saved_cnt} of {seen_cnt}.'.format(**locals())
    if args.dry_run:
        yield '(Dry run, nothing really changed.)'

    # TODO: check msg['UDH'] -- it contains info on concatenated msgs:
    #
    #  'UDH': {'Text': 'hello',
    #          'ID16bit': -1,
    #          'AllParts': 2,
    #          'ID8bit': 0,
    #          'PartNumber': 2,
    #          'Type': 'ConcatenatedMessages'}

def import_plans():
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
