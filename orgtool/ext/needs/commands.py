# -*- coding: utf-8 -*-
"""
Commands
========

"""
import re
from itertools import chain

from tool.cli import arg, alias
from tool.ext.documents import default_storage

from schema import Need, SystemUnderDevelopment


__all__ = ['ls', 'add', 'mv', 'rm']


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

def find_needs(query=None, exclude=None, project=None):
    db = default_storage()
    if project:
        needs = project.needs
        if needs and query:
            # FIXME sud.needs should return a query instead of list (Docu bug)
            needs = [n for n in needs if re.match(ur'.*{0}.*'.format(query),
                                                  n.summary,
                                                  re.UNICODE|re.IGNORECASE)]
        if needs:
            for need in needs:
                yield need
    else:
        needs = Need.objects(db)
        if query:
            needs = needs.where(summary__matches_caseless=query)
        if exclude:
            needs = needs.where_not(summary__matches_caseless=exclude)
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
        print(u'More than one object matching {0} {1}:'.format(args, kwargs))
        for item in items:
            print('- {0}'.format(item))
        raise MultipleMatches()
    return items[0]

def fix_unicode(namespace, *argnames):
    for argname in argnames:
        value = getattr(namespace, argname)
        if isinstance(value, str):
            decoded_value = value.decode('utf-8')
            setattr(namespace, argname, decoded_value)

def remove_need(need, dry_run=False):
    "Safely removes the Need object from the database."
    projects = need.get_projects()
    for project in projects:
        print(u'  unlinking from {summary}'.format(**project))
        pks = [n.pk for n in project.needs]
        project.needs.pop(pks.index(need.pk))
        if not dry_run:
            project.save()
    if not dry_run:
        need.delete()

@alias('list')
@arg('-q', '--query', help='Filter by summary (case-insensitive)')
@arg('-p', '--project', help='Filter by project summary (case-insensitive)')
@arg('-Q', '--exclude', help='Exclude given patterns from query by summary')
@arg('-P', '--exclude-project',
     help='Exclude given patterns from project query by project summary')
@arg('-k', '--show-keys', default=False,
     help='Display primary keys along with items')
@arg('-a', '--all', default=False,
     help='Display orphaned items along with those bound to projects')
@arg('-o', '--only-orphans', default=False,
     help='Display only orphaned needs (without projects)')
def ls(args):
    """Lists all existing needs. By default needs are grouped by project (the
    relation is m2m so any need may appear multiple times within a query).
    Orphaned needs (without projects) are not displayed unless the switches
    --no-grouping or --only-orphans are provided.

    Note that --only-orphans works slowly due to implementation details.
    """
    fix_unicode(args, 'project', 'query')
    assert not all([args.project, args.all]), (
        'Switch --project cannot be used together with --no-grouping.')
    assert not all([args.project, args.only_orphans]), (
        'Switch --project cannot be used together with --only-orphans.')
    if args.all or args.only_orphans:
        projects = [None]
    else:
        try:
            projects = ensure_results(find_projects, args.project,
                                      exclude=args.exclude_project)
        except NotFound as e:
            return

    for project in projects:
        needs = list(find_needs(project=project, query=args.query,
                                exclude=args.exclude))
        if not needs:
            continue

        if not args.all and not args.only_orphans:
            print(u'{0}:'.format(project or '(Orphaned needs)'))
            print('')

        tmpl = u'{pk} {summary}' if args.show_keys else u'- {summary}'
        for need in needs:
            if project is None and args.only_orphans:
                if need.get_projects().count():
                    continue
            print(tmpl.format(pk=need.pk, **need))
        print('')

@arg('summary')
@arg('-p', '--project', help='Project name to which the need should be added.')
def add(args):
    """Creates a need with given text. Project name can be incomplete but
    unambiguous.
    """
    fix_unicode(args, 'summary', 'project')
    db = default_storage()
    # FIXME Docu seems to fail at filling default values such as "is_satisfied"
    need = Need(summary=args.summary, is_satisfied=False)
    project = None
    if args.project:
        qs = SystemUnderDevelopment.objects(db)
        qs = qs.where(summary__matches_caseless=args.project)
        if not qs:
            print('No projects matching "{0}"'.format(args.project))
            return
        if 1 < len(qs):
            print('Found {0} projects matching "{1}". Which to use?'.format(
                    len(qs), args.project))
            for candidate in qs:
                print(u'- {summary}'.format(**candidate))
            return
        project = qs[0]

    # TODO: check for duplicates; require --force to add with dupes
    pk = need.save(db)    # redundant?
    print(u'Added need: {0}'.format(need.summary))
    if project:
        project.needs.append(need.pk)
        project.save()
        print(u'  to project: {0}.'.format(project.summary))
    print('  primary key: {0}.'.format(pk))

@arg('-q', '--query', help='source need\'s summary must match this')
@arg('-p', '--project', help='source project\'s summary must match this')
@arg('-k', '--primary-key', help='source need\'s primary key')
@arg('-t', '--target-project', default='')
@arg('--steal', default=False, help='steal needs from other projects (if any)')
@arg('-d', '--dry-run', default=False)
def mv(args):
    """Moves matching needs to given target project. If the target is empty,
    does nothing. If the target is empty and --steal flag is set, the needs
    become orphaned (without projects). If target is specified and --steal flag
    is set, the needs are moved from old project to the target; otherwise they
    become listed in both.
    """
    fix_unicode(args, 'query', 'project', 'target_project')
    if args.target_project:
        try:
            target = get_single(find_projects, args.target_project)
        except (NotFound, MultipleMatches) as e:
            print(u'Bad target "{0}": {1}'.format(args.target_project, e))
            return
        print(u'Moving matching needs to project {0.summary}...'.format(target))
    else:
        target = None
        if not args.steal:
            print('Cannot use empty --target-project without --steal.')
            return
        print(u'Unlinking matching needs from their projects...')

    # iterate *source* projects (if none specified, use dummy None project)
    projects = find_projects(query=args.project) if args.project else [None]
    for project in projects:
        if project and project == target:
            continue
        needs = find_needs(project=project, query=args.query)
        for need in needs:
            print(u'* {0}'.format(need.summary))
            if args.primary_key:
                print(u'  primary key: {0}'.format(need.pk))
            if target:
                if need not in target.needs:
                    target.needs.append(need)
                    print(u'  added to {0}'.format(target.summary))
            if args.steal:
                # remove item from current project (and leave in others; if
                # user needs to remove from certain or all projects, they
                # specify filtering in --project (empty = all)
                # If no project pattern was given, then we are using a dummy
                # empty project (None) and need to use the Need's own method to
                # gather information on related projects
                related = need.get_projects() if project is None else [project]
                for p in related:
                    pks = [x.pk for x in p.needs]
                    p.needs.pop(pks.index(need.pk))
                    p.save()
                    print(u'  unlinked from {0}'.format(p.summary))
    if target:
        target.save()
        pass

    if args.dry_run:
        print('Simulation: nothing was actually changed in the database.')

@arg('-p', '--project')
@arg('-q', '--query')
@arg('-k', '--primary-key')
@arg('-d', '--dry-run', default=False)
def rm(args):
    """Deletes needs with given primary key or with summary matching given
    query. If the query matches more than one item, the operation is cancelled.
    """
    if args.primary_key:
        print('Deleting need with primary key {0}'.format(args.primary_key))
        db = default_storage()
        need = db.get(Need, args.primary_key)
        remove_need(need, dry_run=args.dry_run)
    elif args.query or args.project:
        try:
            needs = ensure_results(find_needs, project=args.project,
                                   query=args.query)
        except NotFound as e:
            print('Cannot delete items: {0}'.format(e))
            return
        print('Deleting needs:')
        for need in needs:
            print(u'- {summary}'.format(**need))
            print('  primary key: {0}'.format(need.pk))
            remove_need(need, dry_run=args.dry_run)
    else:
        print('Please specify either --primary-key or --query/--project.')

    if args.dry_run:
        print('Simulation: nothing was actually changed in the database.')
