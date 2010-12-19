# -*- coding: utf-8 -*-

import datetime
from dateutil.rrule import rrule
from werkzeug import cached_property

from doqu import Document, Field as f
from doqu import validators

from orgtool.ext.tracking import TrackedDocument

def informal_rrule(*args, **kwargs):
    "A wrapper for informal_rrule that does lazy import"
    from orgtool.utils.dates import informal_rrule
    return informal_rrule(*args, **kwargs)


class Plan(TrackedDocument):
    summary = f(unicode, required=True)
    details = f(unicode)

    next_date_time = f(datetime.datetime)#, essential=True)
    dates_rrule_text = f(unicode)#, essential=True)
    # TODO: dates_rrule = f(rrule, essential=True, pickled=True)
    dates_rrule = f(rrule, pickled=True)

    # accuracy = ...

    # OLD FIELDS, TO BE PUSHED TO RRULE AND THEN DELETED
    # нам, в сущности, не надо дату начала -- достаточно самих фактов.
    valid_since = f(datetime.date, essential=True)  # None, если неопр. срок
    # дата окончания нужна ли? все равно генерится только один факт обычно.
    # или хочется именно прогнозировать полные затраты? а это возможно ли,
    # вообще? мб лучше оставить для более конкретных и полных документов
    # NOTE: not "valid through" but "valid through the day before this";
    # another name would be "invalid_since":
    valid_until = f(datetime.date, essential=True)  # None, если неопр. срок
    #repeat_frequency = f(int, default=1)
    #repeat_month = f(int)
    #repeat_day = f(int)
    #next_occurence_date_time = f(datetime.datetime)   # FIXME occuRRence
    is_accomplished = f(bool)#, essential=True)

    # cancelled: valid_until(cancelling date) + is_accomplished = False

    # events like birthdays do not require our confirmation; they just happen.
    # so the system should skip them instead of waiting for us to confirm and
    # "materialize" these plans as event reports.
    skip_past_events = f(bool, default=False)

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def save(self, *args, **kwargs):
        fields = ('dates_rrule_text', 'next_date_time',
                  'valid_since', 'valid_until')
        if any(self.is_field_changed(x) for x in fields):
            self.update_dates_rrule()
        return super(Plan, self).save(*args, **kwargs)

    def update_dates_rrule(self, last_event=None):
        # NOTE: we are not trying to be too smart here, just some basic guesses
        # apart from the straightforward logic. Facts will *not* fit the plans
        # most of the time.
        if self.dates_rrule_text:

            # FIXME HACK
            if self.dates_rrule_text.startswith('once '):
                rrule_text = self.dates_rrule_text.replace('once ', 'every ')
            else:
                rrule_text = self.dates_rrule_text

            #print 'text defined'

            # looks like rrule will pick now() if valid_since is None even if
            # after(x) is given, so we pass the first event date in this case
            since = self.valid_since or (
                self.events.order_by('date_time')[0].date_time if self.events else None)
            self.dates_rrule = informal_rrule(rrule_text,
                since = since,
                until = self.valid_until
            )
            #print 'rrule created'
            if not last_event and self.events:
                #print 'no explicit last event but there are some'
                # XXX NOTE: assumed that payments are sorted by date DESC (most
                # recent on top):
                last_event = self.events[0]
            if last_event:
                #print 'got explicit last event', last_event
                self.next_date_time = self.dates_rrule.after(last_event.date_time)
            elif self.skip_past_events:
                now = datetime.datetime.utcnow()  # or better yesterday?
                self.next_date_time = self.dates_rrule.after(now)
            else:
                #print 'no last event at all, picking 1st rrule event'
                try:
                    self.next_date_time = self.dates_rrule[0]
                except IndexError:
                    self.next_date_time = None

            # FIXME HACK
            if self.dates_rrule_text.startswith('once '):
                self.dates_rrule = None
        else:
            #print 'no rrule text'
            self.dates_rrule = self.next_date_time = None
            if self.valid_until:
                self.next_date_time = datetime.datetime.combine(
                    self.valid_until, datetime.time())

    def is_active(self):
        if self.is_accomplished or self.is_future() or self.is_expired():
            return False
        return True

    def is_stalled(self):
        """
        Returns True if this plan is valid but no related events have been
        recorded yet. This usually means that something is not clear about the
        plan so the work can't start at this point.

        The "stalled" status is a shade of "active", not an alternative.
        """
        if self.is_active():
            if self.events is None or not self.events.count():
                return True
        return False

    def is_future(self):
        today = datetime.datetime.now().date()
        if self.valid_since and today < self.valid_since:
            return True
        return False

    def is_expired(self):
        """
        Returns True if this plan is expired.

        .. note::

            "valid_until" is interpreted as "invalid_since".

        """
        today = datetime.datetime.utcnow().date()
        if self.valid_until and self.valid_until <= today:
            return True
        return False

    def is_cancelled(self):
        """
        Returns True is this plan is inactive, not accomplished and not in
        the future.
        """
        today = datetime.datetime.utcnow().date()
        if not self.is_active():
            if not self.is_accomplished and self.valid_since < today:
                return True
        return False

    @cached_property
    def events(self):
        return self.get_events()

    def get_events(self):
        if not self.pk:
            return None
        all_events = Event.objects(self._saved_state.storage)
        return all_events.where(plan=self).order_by('date_time', reverse=True)

    def is_next_event_overdue(self):
        if self.next_date_time < datetime.datetime.utcnow():
            return True

#admin.register(Plan, namespace=NAMESPACE, exclude=['dates_rrule'])

class PlanCategory(Document):
    summary = f(unicode, required=True)
    is_plan_category = f(bool, choices=[True])
    def __unicode__(self): return u'{summary}'.format(**self)
class CategorizedPlan(Plan):
    category = f(PlanCategory, required=True)
class HierarchicalPlan(Plan):
    unlocks_plan = f(Plan, essential=True)    # not 'self': any plan will do

    @cached_property
    def depends_on(self):
        db = self._saved_state.storage
        return self.__class__.objects(db).where(unlocks_plan=self)

    @cached_property
    def blocked_by(self):
        today = datetime.date.today()
        valid = self.depends_on.where_not(valid_until__lte=today)
        return valid.where(is_accomplished=False)

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
        now = datetime.datetime.utcnow()
        dt = prev_dt
        delta_days = (self.repeat_day or 0) + (30*(self.repeat_month or 0))
        delta = datetime.timedelta(days=delta_days)
        while True:
            if now < dt:
                return dt
            dt += delta
'''

class Event(TrackedDocument):
    """
    Event record. Planned events are known as "plans". Actual events —
    confirmed facts — are known as "events".
    """
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
