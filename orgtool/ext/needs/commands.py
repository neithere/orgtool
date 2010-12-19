# -*- coding: utf-8 -*-
"""
Commands
========

These commands form a powerful command-line interface for manipulating needs.
"""
import re
from itertools import chain

from tool import app
from tool.cli import (
    # commands
    arg, alias, CommandError, confirm,
    # colors
    Fore, Back, Style
)

from .schema import Need, SystemUnderDevelopment
from .helpers import *


__all__ = ['ls', 'add', 'mv', 'rm']


@alias('view')
@arg('-k', '--primary-key')
@arg('-q', '--query')
@arg('-p', '--project')
def view_need(args):
    fix_unicode(args, 'project', 'query')
    if (not (args.primary_key or args.query) or
        (args.primary_key and args.query)):
        raise CommandError('Please specify either --query or --primary-key')
    need = None
    try:
        project = get_single(find_projects, query=args.project)
    except MultipleMatches:
        project = None
    if args.query:
        try:
            need = get_single(find_needs, query=args.query, project=project)
        except MultipleMatches as e:
            yield(str(e))
            raise NotImplementedError # TODO
    if args.primary_key:
        db = app.get_feature('document_storage').default_db
        need = db.get(Need, args.primary_key)
    if need:
        yield(need.dump())

@alias('ls')
@arg('-q', '--query', nargs='+', help='Filter by summary (case-insensitive)')
@arg('-p', '--project', nargs='+',
     help='Filter by project summary (case-insensitive)')
@arg('-Q', '--exclude', nargs='+',
     help='Exclude given patterns from query by summary')
@arg('-P', '--exclude-project', nargs='+',
     help='Exclude given patterns from project query by project summary')
@arg('-k', '--show-keys', default=False,
     help='Display primary keys along with items')
@arg('-a', '--all', default=False,
     help='Display orphaned items along with those bound to projects')
@arg('-o', '--only-orphans', default=False,
     help='Display only orphaned needs (without projects)')
@arg('--no-headings', default=False, help='Hide project headings')
@arg('--done', default=False, help='Only display satisfied needs')
@arg('--todo', default=False, help='Only display unsatisfied needs')
def list_needs(args):
    """Lists all existing needs. By default needs are grouped by project (the
    relation is m2m so any need may appear multiple times within a query).
    Orphaned needs (without projects) are not displayed unless the switches
    --no-grouping or --only-orphans are provided.

    Note that --only-orphans works slowly due to implementation details.
    """
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'project', 'query', 'exclude', 'exclude_project')
    assert not all([args.project, args.all]), (
        'Switch --project cannot be used together with --all.')
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

    extra = {}
    if args.todo and not args.done:
        extra = {'is_satisfied': False}
    elif args.done and not args.todo:
        extra = {'is_satisfied': True}

    show_heading = (not args.no_headings and
                    not args.all and
                    not args.only_orphans)

    for project in projects:
        needs = list(find_needs(project=project, query=args.query,
                                exclude=args.exclude, extra=extra))
        if not needs:
            continue

        if show_heading:
            tmpl = (Fore.YELLOW + Style.BRIGHT + u'{0}:' +
                    Style.NORMAL + Fore.RESET)
            yield tmpl.format(project or '(Orphaned needs)')
            yield('')

        if args.show_keys:
            tmpl = u'{style}{flag} {pk} {summary}'
        else:
            tmpl = u'{style}{flag} {summary}'
        tmpl = tmpl + Fore.RESET + Style.NORMAL

        for need in needs:
            if project is None and args.only_orphans:
                if need.get_projects().count():
                    continue
            flag = '+' if need.is_satisfied else '-'
            style = Style.DIM if need.is_satisfied else Style.NORMAL
            line = tmpl.format(pk=need.pk, style=style, flag=flag, **need)
            hl_tmpl = ur'{hl_back}{hl_style}\1{line_style}{line_back}'.format(
                hl_back=Back.BLUE, hl_style=Style.NORMAL,
                line_back=Back.RESET, line_style=style)
            hl = re.sub(ur'(?ui)({0})'.format(args.query), hl_tmpl, line)
            yield(hl)

        if show_heading:
            yield('')

@alias('add')
@arg('summary', nargs='+')
@arg('-p', '--project', nargs='+', help='Target project name')
def add_need(args):
    """Creates a need with given text. Project name can be incomplete but
    unambiguous.
    """
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'project', 'summary')
    db = app.get_feature('document_storage').default_db
    # FIXME Docu seems to fail at filling default values such as "is_satisfied"
    need = Need(summary=args.summary, is_satisfied=False)
    project = None
    if args.project:
        qs = SystemUnderDevelopment.objects(db)
        qs = qs.where(summary__matches_caseless=args.project)
        if not qs:
            yield('No projects matching "{0}"'.format(args.project))
            return
        if 1 < len(qs):
            yield('Found {0} projects matching "{1}". Which to use?'.format(
                    len(qs), args.project))
            for candidate in qs:
                yield(u'- {summary}'.format(**candidate))
            return
        project = qs[0]

    # TODO: check for duplicates; require --force to add with dupes
    pk = need.save(db)    # redundant?
    yield(u'Added need: {0}'.format(need.summary))
    if project:
        project.needs.append(need.pk)
        project.save()
        yield(u'  to project: {0}.'.format(project.summary))
    yield('  primary key: {0}.'.format(pk))

@alias('ren')
#@arg('-k', '--primary-key')
@arg('-p', '--project')
@arg('-q', '--query')
@arg('-k', '--primary-key')
@arg('-d', '--dry-run', default=False)
#@arg('-t', '--to')
@arg('to', nargs='+')
def rename_need(args):
    """Renames matching item. Requires exactly one match.
    If `summary` is in the form "/foo/bar/", it is interpreted as a regular
    expression.

    Usage::

        $ needs rename -q "teh stuff" the stuff
        $ needs rename -q "teh stuff" /teh/the/

    """
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'query', 'project', 'to')
    summary = args.to.strip() if args.to else None
    assert summary
    if args.primary_key:
        db = app.get_feature('document_storage').default_db
        need = db.get(Need, args.primary_key)
    else:
        try:
            # TODO: support batch renames (with regex only?)
            need = get_single(find_needs, query=args.query)
        except (NotFound, MultipleMatches) as e:
            yield(u'Bad query "{0}": {1}'.format(args.query, e))

    # if new value looks like a regex, then use it that way
    match = re.match('^/([^/]+?)/([^/]+?)/$', summary)
    if match:
        old, new = match.groups()
        yield(u'Using regex: replacing "{old}" with "{new}"'.format(**locals()))
        summary = re.sub(old, new, need.summary)

    if need.summary == summary:
        yield(u'Nothing changed.')
    else:
        yield(u'Renaming "{0}" to "{1}"'.format(need.summary, summary))
        if args.dry_run:
            yield('Simulation: nothing was actually changed in the database.')
        else:
            need.summary = summary
            need.save()

@alias('mv')
@arg('-q', '--query', help='source need\'s summary must match this')
@arg('-p', '--project', help='source project\'s summary must match this')
@arg('-k', '--primary-key', help='source need\'s primary key')
@arg('-t', '--target-project', default='')
@arg('--steal', default=False, help='steal needs from other projects (if any)')
@arg('-d', '--dry-run', default=False)
def move_need(args):
    """Moves matching needs to given target project. If the target is empty,
    does nothing. If the target is empty and --steal flag is set, the needs
    become orphaned (without projects). If target is specified and --steal flag
    is set, the needs are moved from old project to the target; otherwise they
    become listed in both.
    """
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'query', 'project', 'target_project')
    if args.target_project:
        try:
            target = get_single(find_projects, args.target_project)
        except (NotFound, MultipleMatches) as e:
            yield(u'Bad target "{0}": {1}'.format(args.target_project, e))
            return
        yield(u'Moving matching needs to project {0.summary}...'.format(target))
    else:
        target = None
        if not args.steal:
            yield('Cannot use empty --target-project without --steal.')
            return
        yield(u'Unlinking matching needs from their projects...')

    # iterate *source* projects (if none specified, use dummy None project)
    projects = find_projects(query=args.project) if args.project else [None]
    for project in projects:
        if project and project == target:
            continue
        needs = find_needs(project=project, query=args.query)
        for need in needs:
            yield(u'* {0}'.format(need.summary))
            if args.primary_key:
                yield(u'  primary key: {0}'.format(need.pk))
            if target and target.needs:  # target.needs may be None
                if need not in target.needs:
                    target.needs.append(need)
                    yield(u'  added to {0}'.format(target.summary))
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
                    yield(u'  unlinked from {0}'.format(p.summary))
    if target:
        target.save()
        pass

    if args.dry_run:
        yield('Simulation: nothing was actually changed in the database.')

@alias('rm')
@arg('-p', '--project')
@arg('-q', '--query')
@arg('-k', '--primary-key')
@arg('-d', '--dry-run', default=False)
def delete_need(args):
    """Deletes needs with given primary key or with summary matching given
    query. If the query matches more than one item, the operation is cancelled.
    """
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'query', 'project')
    if args.primary_key:
        yield('Deleting need with primary key {0}'.format(args.primary_key))
        db = app.get_feature('document_storage').default_db
        need = db.get(Need, args.primary_key)
        if confirm(u'Delete need {summary}'.format(**need)):
            if not args.dry_run:
                remove_need(need, dry_run=args.dry_run)
        else:
            yield('Operation cancelled.')
    elif args.query or args.project:
        try:
            needs = ensure_results(find_needs, project=args.project,
                                   query=args.query)
        except NotFound as e:
            raise CommandError('Cannot delete items: {0}'.format(e))
        yield('Matching needs:')
        for need in needs:
            yield(u'- {summary}'.format(**need))
            yield('  primary key: {0}'.format(need.pk))
        if confirm('Delete these items'):
            if not args.dry_run:
                for need in needs:
                    yield('Dropping {summary}…'.format(**need))
                    remove_need(need, dry_run=args.dry_run)
        else:
            yield('Operation cancelled.')
    else:
        yield('Please specify either --primary-key or --query/--project.')

    if args.dry_run:
        yield('Simulation: nothing was actually changed in the database.')

@alias('mark')
@arg('-p', '--project')
@arg('-q', '--query')
@arg('-k', '--primary-key')
@arg('--satisfied', default=False)#, help='mark the need as satisfied')
@arg('--unsatisfied', default=False)#, help='mark the need as not satisfied')
@arg('--important', default=False)
@arg('--unimportant', default=False)
@arg('-y', '--yes', default=False, help='answer "yes" instead of prompting')
@arg('-d', '--dry-run', default=False)
def mark_need(args):
    "Marks matching needs as satisfied."
    for func in flatten_nargs_plus, fix_unicode:
        func(args, 'query', 'project')
    assert not (args.important and args.unimportant)
    assert not (args.satisfied and args.unsatisfied)
    assert any([args.satisfied, args.unsatisfied,
                args.important, args.unimportant]), 'A flag must be chosen'
    if args.primary_key:
        assert not (args.query or args.project), (
            '--primary-key cannot be combined with --query/--project')
        db = app.get_feature('document_storage').default_db
        needs = [db.get(Need, args.primary_key)]
    else:
        needs = ensure_results(find_needs, project=args.project, query=args.query)
    for need in needs:
        satisfied = 'satisfied' if need.is_satisfied else 'unsatisfied'
        important = 'important' if not need.is_discarded else 'unimportant'
        yield(u'- {summary} ({satisfied}, {important})'.format(
            satisfied=satisfied, important=important, **need))
    yield('')
    if confirm('Apply changes to these items', default=True, skip=args.yes):
        if args.dry_run:
            yield('Simulation: nothing was actually changed in the database.')
        else:
            for need in needs:
                yield(u'Marking "{summary}"...'.format(**need))
                if args.satisfied and not need.is_satisfied:
                    yield(u'  + unsatisfied → satisfied')
                    need.is_satisfied = True
                if args.unsatisfied and need.is_satisfied:
                    yield(u'  + satisfied → unsatisfied')
                    need.is_satisfied = False
                if args.important and need.is_discarded:
                    need.is_discarded = False
                    yield(u'  + discarded → important')
                if args.unimportant and not need.is_discarded:
                    yield(u'  + important → discarded')
                    need.is_discarded = True
                need.save()
            yield('Changes have been applied.')
    else:
        yield('Operation cancelled.')
