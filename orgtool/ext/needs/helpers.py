# -*- coding: utf-8 -*-
import re

from tool.ext.documents import default_storage

from .schema import SystemUnderDevelopment, Need


class NotFound(Exception):
    pass

class MultipleMatches(Exception):
    pass


def find_projects(query=None, exclude=None):
    db = default_storage()
    suds = SystemUnderDevelopment.objects(db)
    if query:
        suds = suds.where(summary__matches_caseless=query)
    if exclude:
        suds = suds.where_not(summary__matches_caseless=exclude)
    return suds

def find_needs(query=None, exclude=None, project=None, extra=None):
    db = default_storage()
    extra = extra or {}
    if project:
        needs = project.needs
        if needs is None:
            return
        if query:
            # FIXME sud.needs should return a query instead of list (Docu bug)
            needs = (n for n in needs if re.match(ur'.*{0}.*'.format(query),
                                                  n.summary,
                                                  re.UNICODE|re.IGNORECASE))

        # filter by extra conditions - should be done via query API, too
        for k,v in extra.items():
            needs = (n for n in needs if n[k] == v)
        for need in needs:
            yield need
    else:
        needs = Need.objects(db)
        if query:
            needs = needs.where(summary__matches_caseless=query)
        if exclude:
            needs = needs.where_not(summary__matches_caseless=exclude)
        if extra:
            needs = needs.where(**extra)
        for need in needs:
            yield need

def ensure_results(finder, *args, **kwargs):
    items = list(finder(*args, **kwargs))
    if not items:
        raise NotFound('No matching items.')
    return items

def get_single(finder, *args, **kwargs):
    items = list(ensure_results(finder, *args, **kwargs))
    if 1 < len(items):
#        print(u'More than one object matches query:')# matching {0} {1}:'.format(args, kwargs))
#        for item in items:
#            print(u'- {summary}'.format(**item))
        choices = '\n'.join(u'- {0}'.format(unicode(item)) for item in items)
        choices = choices.encode('utf-8')
        raise MultipleMatches('More than one object matches query:\n'+choices)
    return items[0]

def fix_unicode(namespace, *argnames):
    for argname in argnames:
        value = getattr(namespace, argname)
        if isinstance(value, str):
            decoded_value = value.decode('utf-8')
            setattr(namespace, argname, decoded_value)

def flatten_nargs_plus(namespace, *argnames):
    "Converts list of values from ``nargs='+'`` to a string."
    for argname in argnames:
        value = getattr(namespace, argname)
        if isinstance(value, list):
            flat_value = ' '.join(value)
            setattr(namespace, argname, flat_value)

def remove_need(need, dry_run=False):
    "Safely removes the Need object from the database."
    projects = need.get_projects()
    for project in projects:
#        print project
#        print(u'  unlinking from {summary}'.format(**project))
        pks = [n.pk for n in project.needs]
        project.needs.pop(pks.index(need.pk))
        if not dry_run:
            project.save()
    if not dry_run:
        need.delete()
