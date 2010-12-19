# -*- coding: utf-8 -*-

from doqu import Field as f, Many

from orgtool.ext.tracking import TrackedDocument
#from orgtool.ext.events.schema import HierarchicalPlan as Plan, Event
from orgtool.ext.actors.schema import Actor
from orgtool.ext.events.schema import HierarchicalPlan, Plan, Event


__all__ = [
    'SystemUnderDevelopment', 'Need', 'Feature',
    'ReasonedPlan', 'ReasonedEvent',
]


class Need(TrackedDocument):  # потребность
    """
    Intention, goal, test (TDD), user story (XP), positive outome (GTD),
    backlog item (Scrum), requirement, need.
    """
    summary = f(unicode, required=True)
    details = f(unicode)
    stakeholders = f(Many(Actor))  #Person)
#    project = f(SystemUnderDevelopment)

    is_processed = f(bool)#, essential=True)

#   feature = f(Feature)   <-- adds complexity; workflow-specific
#      , query=lambda obj, q: q.where(project=obj.project))

    # does the stakeholder confirm this requirement's importance for them?
#    is_confirmed = f(bool, required=True)   <-- maybe workflow-specific
#    is_important = f(bool)  # <-- requires action?
    is_discarded = f(bool)

    # does the stakeholder consider this requirement satisfied?
    is_satisfied = f(bool, required=True)

#    is_risk = f(bool)  <-- "need" != "risk", gotta reformulate, eg "is_critical"
#    ...maybe Problem.is_solved would be optimal. However, needs are positive
#    outcomes while risks are, um, known dangers for these outcomes. Maybe
#    risks should refer needs. Just remember that a need is *not* a problem --
#    it's positive, and the problem is Need.is_satisfied=False + impediments.

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def is_active(self):
        if not self.is_processed:
            # requires user decision
            return True
        return not (self.is_discarded or self.is_satisfied)

    def get_events(self):
        """Returns events directly associated with this need. Does not include
        pre-planned events, i.e. events attached to plans.
        """
        all_events = ReasonedEvent.objects(self._saved_state.storage)
        return all_events.where(outcome=self)

    def get_plans(self):
        all_plans = ReasonedPlan.objects(self._saved_state.storage)
        return all_plans.where(outcome=self)

    def get_projects(self):
        objs = SystemUnderDevelopment.objects(self._saved_state.storage)
        return objs.where(needs__contains=self)


class ReasonedPlan(Plan):
    """
    Needs-driven plan. The motivation is explicit.
    """
    #responsible = f(unicode)  #Person)

    # why does the plan exist? what do we try to achieve?
#    implements = f(Need, required=True)
    outcome = f(Need, required=True)

    # what impedes the plan? why it can't be tackled right now?
#    depends_on = f(Need)  <-- ...makes the graph too complex


class ReasonedEvent(Event):
    """
    Needs-driven activity. The motivation is explicit.
    """
    outcome = f(Need, required=True)


class SystemUnderDevelopment(TrackedDocument):
    """
    A project. Usually involves multiple stakeholders and multiple activities.
    The *stakeholders* come up with an *agreement* that a *system* should be
    built to address their combined *needs*. This document describes such
    system and aggregates the needs. The needs, in turn, are referred by plans
    (planned activities). The plan can be finished or abandoned; the needs can
    be satisfied or discarded; the project can be successful or not. All that
    is a question of management.
    """
    summary = f(unicode, required=True)
    stakeholders = f(Many(Actor), essential=True)
#    is_agreed = field(bool)  <-- kinda "launched" or "active" but wf-specific
    needs = f(Many(Need), essential=True)

    label = 'system under development'
    label_plural = 'systems under development'

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def get_active_needs(self):
        if not self.needs:
            return None
        return [need for need in self.needs
                 if not (need.is_discarded or need.is_satisfied)]

    def is_active(self):
        return bool(self.get_active_needs())

    def get_plans(self):
        """
        Returns a list of plans that implement needs addressed by this project.
        """
        if not self.needs:
            return None
        all_plans = ReasonedPlan.objects(self._saved_state.storage)
        return all_plans.where(outcome__in=self.needs)


class Feature(TrackedDocument):
    summary = f(unicode, required=True)
    is_feature = f(bool, choices=[True])



