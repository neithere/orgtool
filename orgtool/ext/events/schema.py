# -*- coding: utf-8 -*-

import datetime
from dateutil.rrule import rrule
from werkzeug import cached_property

from docu import Document, Field as f
from docu import validators

from orgtool.ext.tracking import TrackedDocument
from orgtool.utils.dates import informal_rrule


class Plan(TrackedDocument):
    summary = f(unicode, required=True)
    details = f(unicode)

    next_date_time = f(datetime.datetime)#, essential=True)
    dates_rrule_text = f(unicode)#, essential=True)
    # TODO: dates_rrule = f(rrule, essential=True, pickled=True)
    dates_rrule = f(rrule, pickled=True)

    # OLD FIELDS, TO BE PUSHED TO RRULE AND THEN DELETED
    # нам, в сущности, не надо дату начала -- достаточно самих фактов.
    valid_since = f(datetime.date, essential=True)  # None, если неопр. срок
    # дата окончания нужна ли? все равно генерится только один факт обычно.
    # или хочется именно прогнозировать полные затраты? а это возможно ли,
    # вообще? мб лучше оставить для более конкретных и полных документов
    valid_until = f(datetime.date, essential=True)  # None, если неопр. срок
    #repeat_frequency = f(int, default=1)
    #repeat_month = f(int)
    #repeat_day = f(int)
    #next_occurence_date_time = f(datetime.datetime)   # FIXME occuRRence
    is_accomplished = f(bool)#, essential=True)

    # cancelled: valid_until(cancelling date) + is_accomplished = False

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def save(self, *args, **kwargs):
        fields = 'dates_rrule_text', 'valid_since', 'valid_until'
        if any(self.is_field_changed(x) for x in fields):
            self.update_dates_rrule()
        return super(Plan, self).save(*args, **kwargs)

    def update_dates_rrule(self, last_event=None):
        # NOTE: we are not trying to be too smart here, just some basic guesses
        # apart from the straightforward logic. Facts will *not* fit the plans
        # most of the time.
        if self.dates_rrule_text:
            print 'text defined'
            self.dates_rrule = informal_rrule(
                self.dates_rrule_text,
                since = self.valid_since,
                until = self.valid_until
            )
            print 'rrule created'
            if not last_event and self.get_events:
                print 'no explicit last event but there are some'
                # XXX NOTE: assumed that payments are sorted by date DESC (most
                # recent on top):
                last_event = self.events[0]
            if last_event:
                print 'got explicit last event', last_event
                self.next_date_time = self.dates_rrule.after(last_event.date_time)
            else:
                print 'no last event at all, picking 1st rrule event'
                self.next_date_time = self.dates_rrule[0]
        else:
            'no rrule text'
            self.dates_rrule = self.next_date_time = None

    def is_active(self):
        today = datetime.date.today()
        if self.valid_since and today < self.valid_since:
            return False
        if self.valid_until and self.valid_until < today:
            return False
        if self.is_accomplished:
            return False
        return True

    @cached_property
    def events(self):
        return self.get_events()

    def get_events(self):
        all_events = Event.objects(self._saved_state.storage)
        return all_events.where(plan=self).order_by('date_time', reverse=True)
#admin.register(Plan, namespace=NAMESPACE, exclude=['dates_rrule'])

class PlanCategory(Document):
    summary = f(unicode, required=True)
    is_plan_category = f(bool, choices=[True])
    def __unicode__(self): return u'{summary}'.format(**self)
class CategorizedPlan(Plan):
    category = f(PlanCategory, required=True)
class HierarchicalPlan(Plan):
    unlocks_plan = f('self', essential=True)

'''

class OLD__Plan(Document):
    """
    A plan for a chain of events (or a single event). Recurrence is stored as
    a) a rule (not intended for lookups; can be pretty complex), and b) next
    occurrence (intended for lookups). The next occurrence date must represent
    a *planned* event, not an existing one. If the date is in the future, then
    the plan is pending. If the date is today, then the plan is on the today's
    task list. If the date is in the past, then the event must be confirmed or
    ignored and the next date calculated. It is possible that multiple events
    are missed; then it it up to the user (of client code) whether they should
    be materialized or just skipped.
    """
    # TODO: support easy iCalendar import/export as methods? See http://vobject.skyhouseconsulting.com/usage.html
    #       may be too complex, at least for starters.
    summary = f(unicode, required=True)
    valid_since = f(datetime.date, essential=True)  # None, если неопр. срок
    valid_until = f(datetime.date, essential=True)  # None, если неопр. срок
    # recurring
    repeat_frequency = f(int, essential=True, default=1)
    repeat_month = f(int)
    repeat_day = f(int)
    next_occurence_date_time = f(datetime.datetime)   # FIXME occuRRence

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def is_recurrent(self):
        return bool(self.repeat_month or self.repeat_day)

    def describe_recurrence(self):
        if not self.repeat_frequency:
            return u''
        if self.repeat_frequency == 1:
            frequency = u''
        else:
            frequency = u'{0}th '.format(self.repeat_frequency)
        day = self.repeat_day
        month = self.repeat_month
        d = u'{0} day'.format(day if day else u'each')
        m = u'{0} month'.format(month if month else u'each')
        factor = ' of '.join([d, m])
        return u'every {frequency}{factor}'.format(
            frequency=frequency,
            factor=factor)

    def get_events(self):
        all_events = Event.objects(self._saved_state.storage)
        return all_events.where(plan=self).order_by('date_time', reverse=True)

    def calc_next_occurence(self, skip_missed=True):
        if not skip_missed:
            raise NotImplementedError
        if self.repeat_frequency and self.repeat_frequency != 1:
            raise NotImplementedError
        assert self.repeat_day or self.repeat_month
        # TODO: use dateutil ?
        # http://labix.org/python-dateutil
        # http://stackoverflow.com/questions/1336824/python-dateutil-rrule-is-incredibly-slow
        # http://stackoverflow.com/questions/618910/dateutil-rrule-rrule-between-gives-only-dates-after-now
        # http://stackoverflow.com/questions/tagged/dateutil
        # http://stackoverflow.com/questions/tagged/python+calendar
        events = self.get_events()
        cnt = events.count()
        if cnt:
            prev_dt = events[cnt - 1].date_time
        else:
            assert self.valid_since
            prev_dt = datetime.combine(self.valid_since, datetime.time(0))
        now = datetime.datetime.now()
        dt = prev_dt
        delta_days = (self.repeat_day or 0) + (30*(self.repeat_month or 0))
        delta = datetime.timedelta(days=delta_days)
        while True:
            if now < dt:
                return dt
            dt += delta
'''

class Event(TrackedDocument):
    # I think we don't really want prototyping.
    # So there should be concrete "events" and abstract "plans".
    # An event cannot contain recurrence information.
    # So "payment" will be an event, and "agreement" will be a plan.
    date_time = f(datetime.datetime, required=True)
    date_time_end = f(datetime.datetime)
    summary = f(unicode, required=True)
    details = f(unicode)
    plan = f(Plan)

    def __unicode__(self):
        return u'{date_time} {summary}'.format(**self)

    def save(self, *args, **kwargs):
        # TODO: replace with signals; call this only on creation/deletion
        if self.plan:
            self.plan.update_dates_rrule()
            self.plan.save()
        return super(Event, self).save(*args, **kwargs)

    def get_duration(self):
        if not self.date_time_end:
            return None
        return self.date_time_end - self.date_time
