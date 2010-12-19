import datetime
from doqu import Field as f
from orgtool.ext.talks import Message
from orgtool.ext.actors.schema import Actor
from orgtool.ext.contacts import Contact
from orgtool.ext.events import Plan


SMS_SOURCE = u'gammu-sms'
CONTACT_SOURCE = u'gammu-contact'
ACTOR_SOURCE = u'gammu-actor'
EVENT_SOURCE = u'gammu-plan'


class GammuSMS(Message):
    source = f(unicode, choices=[SMS_SOURCE], default=SMS_SOURCE)

    defaults = {
        'summary': u'No text',
    }


class GammuActor(Actor):
    source = f(unicode, choices=[ACTOR_SOURCE], default=ACTOR_SOURCE)

    # copy of Person fields, just non-essentian
    first_name = f(unicode)
    second_name = f(unicode)
    last_name = f(unicode)
    details = f(unicode)

    # extra fields
    company = f(unicode)  # TODO: reference to an Organization
    job_title = f(unicode)


class GammuContact(Contact):
    source = f(unicode, choices=[CONTACT_SOURCE], default=CONTACT_SOURCE)

    @classmethod
    def from_raw_elems(cls, elems):
        ACTOR_FIELDS = {
            'Text_Name': 'name',
            'Text_FirstName': 'first_name',
            'Text_LastName': 'last_name',
            'Text_JobTitle': 'job_title',
            'Text_Custom1': 'details',
            'Text_Company': 'company',
        }
        CONTACT_FIELDS = {
            'Number_General': (u'phone', u'primary'),
            'Number_Mobile': (u'phone', u'mobile'),
            'Number_Home': (u'phone', u'home'),
            'Number_Work': (u'phone', u'work'),
            'Text_Email': (u'email', u'primary'),
            'Text_URL': (u'url', u'primary'),
        }
        SKIPPED = 'PictureID', 'Number_Messaging'
        actor = GammuActor()
        contacts = []
        for key, value in elems:
            if key in SKIPPED:
                continue
            elif key in ACTOR_FIELDS:
                name = ACTOR_FIELDS[key]
                actor[name] = value
            elif key in CONTACT_FIELDS:
                kind, scope = CONTACT_FIELDS[key]
                contact = GammuContact(
                    kind = kind,
                    scope = scope,
                    value = value
                )
                contacts.append(contact)
            else:
                raise KeyError('Unknown element name {0}'.format(key))
        actor._fill_defaults()
        if actor.is_valid():
            for c in contacts:
                c.actor = actor
        return actor, contacts


class GammuPlan(Plan):
    tone_alarm_datetime = f(datetime.datetime)
    silent_alarm_datetime = f(datetime.datetime)

    source = f(unicode, choices=[EVENT_SOURCE], default=EVENT_SOURCE)
