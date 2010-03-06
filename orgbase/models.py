# -*- coding: utf-8 -*-

# python
import datetime
from pymodels import *
P = Property

# bundles
#from glasnaegel.auth.models import User


#--- abstract models ---     (not really abstract, just not to be used directly)


class NamedModel(Model):
    title = P(required=True)

    class Meta:
        must_have = {'title__exists': True}

    def __unicode__(self):
        return self.title


class TrackedModel(Model):
    created = DateTime(required=True, default=datetime.datetime.now)
    updated = DateTime(required=True)

    class Meta:
        must_have = {'created__exists': True, 'updated__exists': True}

    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(TrackedModel, self).save(*args, **kwargs)


#--- categorizing models (boxes) ---


class Domain(NamedModel):
    class Meta:
        must_have = {'is_domain': True}


class ActionContext(NamedModel):
    class Meta:
        must_have = {'is_context': True}


class NoteCategory(NamedModel):
    class Meta:
        must_have = {'is_reference_category': True}


class Person(TrackedModel):
    first_name = Property(required=True)
    last_name = Property()

    class Meta:
        must_have = {'first_name__exists': True}

    def __unicode__(self):
        return ' '.join([self.first_name, self.last_name])


#--- concrete models (papers) ---


class Goal(NamedModel, TrackedModel):
    parent = Reference('self')
    domain = Reference(Domain)
    summary = P()
    is_accomplished = Boolean(default=False)
    is_cancelled = Boolean(default=False)

    class Meta:
        must_have = {'is_goal': True}


class Item(TrackedModel):
    summary = P(required=True)
    domain  = Reference(Domain)
    goal    = Reference(Goal)
    #is_processed  = Boolean(default=False)
    #is_deleted    = Boolean(default=False)
    #is_referenced = Boolean(default=False)
    #is_incubated  = Boolean(default=False)


class InboxItem(Item):
    # source = ...

    class Meta:
        must_have = {'is_processed': False}


class ProcessedItem(Item, NamedModel):
    summary = P(required=False)

    class Meta:
        must_have = {'is_processed': True}


class CancelledItem(ProcessedItem):
    class Meta:
        must_have = {'is_cancelled': True}


class Task(ProcessedItem):
    context  = Reference(ActionContext)
    due_date = Date()
    is_done  = Boolean(default=False)
    estimated_effort = Number() # in minutes

    class Meta:
        must_have = {'requires_action': True}

    def days_left(self):
        if self.due_date:
            delta = self.due_date - datetime.datetime.now().date()
            return delta.days


class DelegatedTask(Task):
    delegated_to = Reference(Person, required=True)

    class Meta:
        must_have = {'delegated_to__exists': True}


class ToDo(Task):
    class Meta:
        must_have = {'is_done': False, 'is_cancelled': False}


class CompletedTask(Task):
    spent_effort = Number() # in minutes

    class Meta:
        must_have = {'is_done': True}


class Note(ProcessedItem):
    note_category = Reference(NoteCategory)

    class Meta:
        must_have = {'note_category__exists': True}


class Someday(ProcessedItem):
    class Meta:
        must_have = {'requires_action': False}

"""

    # XXX the Action model is likely to be split in multiple by the "state" field:
    NEXT_ACTION, SOMEDAY, REFERENCE = 'next', 'someday', 'reference'
    STATE_CHOICES = (       # [(x,x) for x in ('inbox', 'next', 'scheduled', 'someday')]
        (NEXT_ACTION, _('next action')),
        #(SCHEDULED, _('scheduled')),
        (SOMEDAY, _('someday')),
        (REFERENCE, _('for reference')),    # xxx status (pending/done/cancelled) applies only to *actionable* items, not for references
    )
    PENDING, DONE, CANCELLED = 1, 2, 3
    STATUS_CHOICES = (
        (PENDING,   _('pending')),   # "new"/"open"
        (DONE,      _('done')),      # "fixed"/"closed"
        (CANCELLED, _('cancelled')), # "wontfix"
    )
    summary = TextField(_('summary'), blank=True)
    state = CharField(_('state'), choices=STATE_CHOICES, max_length=10, blank=True, default=NEXT_ACTION)
    due_date = DateField(_('due_date'), blank=True, null=True)  # can be set by assigning to "today", "tomorrow" or real date
    remind_date = DateField(_('remind date'), blank=True, null=True,
                           help_text=_('After this date entry will show up in Next Actions.'))
    status = IntegerField(_('status'), choices=STATUS_CHOICES, default=PENDING)
    # FIXME: "archived" should be filled using signals, now it's always left intact (which makes it deceiving)
    archived = DateField(_('date of archivation'), blank=True, null=True)  #, editable=False)
    delegated_to = CharField(_('delegated to'), max_length=255, blank=True, null=True) # xxx replace with FK to a Contact model
    context = ForeignKey(ActionContext, verbose_name=_('work context'), blank=True, null=True)
    estimated_duration = IntegerField(_('estimated duration'), blank=True, null=True)
    duration = IntegerField(_('real duration'), blank=True, null=True)
    cost = IntegerField(_('estimated cost'), blank=True, null=True)
    origin = ForeignKey(Stuff, blank=True, null=True, verbose_name=_('original idea'))

    objects = ActionManager()

    class Meta:
        ordering = ('sort_order', '-add_date')
        verbose_name, verbose_name_plural = _('action'), _('actions')

    def get_absolute_url(self):
        return reverse('organizer:action', kwargs={'pk': self.pk})

    def days_left(self):
        if not self.status == self.PENDING:
            return None
        if not self.due_date:
            return None
        delta = self.due_date - datetime.datetime.now().date()
        return delta.days
"""
