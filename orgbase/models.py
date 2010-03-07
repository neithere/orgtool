# -*- coding: utf-8 -*-

# python
import datetime
from pymodels import *
P = Property

# GH
from glashammer.utils import url_for

# bundles
from glasnaegel.bundles.admin import AdminSite
#from glasnaegel.auth.models import User


#--- admin decorators ---

def _get_url_for_object(obj):
    # our custom function to map model instances to views/endpoints
    model_name = obj._meta.label.replace(' ', '_')
    return url_for('orgbase/%s' % model_name, **{'pk': obj.pk})


def admin(model):
    """
    Registers given model with admin appliance.
    """

    excluded = []
    if issubclass(model, TrackedModel):
        excluded = ['created', 'updated']
    AdminSite.register(model, namespace='organizer', url=_get_url_for_object,
                       exclude=excluded)

    return model

#--- abstract models ---     (not really abstract, just not to be used directly)


class NamedModel(Model):
    title = P(required=True, label=u'название')

    class Meta:
        must_have = {'title__exists': True}

    def __unicode__(self):
        return self.title


class TrackedModel(Model):
    created = DateTime(required=True, default=datetime.datetime.now,
                       label=u'дата создания')
    updated = DateTime(required=True, label=u'дата обновления')

    class Meta:
        must_have = {'created__exists': True, 'updated__exists': True}

    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.now()
        return super(TrackedModel, self).save(*args, **kwargs)


#--- categorizing models (boxes) ---


@admin
class Domain(NamedModel):
    class Meta:
        must_have = {'is_domain': True}


@admin
class ActionContext(NamedModel):
    class Meta:
        must_have = {'is_context': True}


@admin
class NoteCategory(NamedModel):
    class Meta:
        must_have = {'is_reference_category': True}


@admin
class Person(TrackedModel):
    first_name = Property(required=True, label=u'имя')
    last_name = Property(label=u'фамилия')
    email = Property(label=u'e-mail')

    class Meta:
        must_have = {'first_name__exists': True}

    def __unicode__(self):
        return ' '.join([self.first_name, self.last_name])


#--- concrete models (papers) ---


@admin
class Goal(NamedModel, TrackedModel):
    parent = Reference('self', label=u'вышестоящая цель')
    domain = Reference(Domain, label=u'сфера деятельности')
    summary = P(label=u'')
    is_accomplished = Boolean(default=False, label=u'достигнута')
    is_cancelled = Boolean(default=False, label=u'отменена')

    class Meta:
        must_have = {'is_goal': True}


@admin
class Item(TrackedModel):
    summary = P(required=True, label=u'описание')
    domain  = Reference(Domain, label=u'сфера деятельности')
    goal    = Reference(Goal, label=u'цель')
    #is_processed  = Boolean(default=False)
    #is_deleted    = Boolean(default=False)
    #is_referenced = Boolean(default=False)
    #is_incubated  = Boolean(default=False)


@admin
class InboxItem(Item):
    # source = ...

    class Meta:
        must_have = {'is_processed': False}


@admin
class ProcessedItem(Item, NamedModel):
    summary = P(required=False, label=u'описание')

    class Meta:
        must_have = {'is_processed': True}


@admin
class CancelledItem(ProcessedItem):
    class Meta:
        must_have = {'is_cancelled': True}


@admin
class Task(ProcessedItem):
    context  = Reference(ActionContext, label=u'контекст')
    due_date = Date(label=u'дедлайн')
    is_done  = Boolean(default=False, label=u'готово')
    estimated_effort = Number(label=u'оценка затрат') # in minutes

    class Meta:
        must_have = {'requires_action': True}

    def days_left(self):
        if self.due_date:
            delta = self.due_date - datetime.datetime.now().date()
            return delta.days


@admin
class DelegatedTask(Task):
    delegated_to = Reference(Person, required=True, label=u'ответственное лицо')

    class Meta:
        must_have = {'delegated_to__exists': True}
        must_not_have = {'delegated_to': ''}


@admin
class ToDo(Task):
    class Meta:
        must_have = {'is_done': False, 'is_cancelled': False}

@admin
class CompletedTask(Task):
    spent_effort = Number(label=u'затраты (в минутах)') # in minutes

    class Meta:
        must_have = {'is_done': True}


@admin
class Note(ProcessedItem):
    note_category = Reference(NoteCategory, label=u'категория')

    class Meta:
        must_have = {'note_category__exists': True}


@admin
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
