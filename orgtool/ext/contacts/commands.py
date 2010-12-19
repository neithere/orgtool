# -*- coding: utf-8 -*-

import webbrowser

from tool.cli import arg, alias, CommandError, confirm, Fore, Style
from tool.ext.documents import default_storage
from orgtool.ext.actors.schema import Actor
from orgtool.ext.needs.helpers import (
    MultipleMatches, NotFound, get_single, fix_unicode
)

from .schema import Contact, CONTACT_TYPES


def find_actors(query):
    db = default_storage()
    return Actor.objects(db).where(name__matches_caseless=query)

def bright(string):
    return Style.BRIGHT + unicode(string) + Style.NORMAL


@alias('ls')
@arg('actor')
@arg('--type', nargs='+', help='Only show these types of contacts')
def list_contacts(args):
    "Lists contacts for matching actors."
    fix_unicode(args, 'actor', 'type')
    for actor in find_actors(args.actor):
        contacts = actor.contacts.order_by(['kind', 'scope'])
        if args.type:
            contacts = contacts.where(kind__in=args.type)
        if not contacts:
            continue
        yield(Style.BRIGHT + Fore.YELLOW +
              u'{0}:'.format(actor) +
              Fore.RESET + Style.NORMAL)
        yield('')
        for contact in contacts:
            summary = '' if contact.summary == actor.name else contact.summary
            scope = '' if contact.scope == 'primary' else contact.scope
            value = contact.value
            if contact.kind == 'text':
                value = contact.value.replace('\n', '\n   ')
                template = u'\n {style}{scope}{summary}{endstyle}\n   {value}\n'
            else:
                template = u' {value} {style}{scope}{summary}{endstyle}'
            scope = u'({0}) '.format(scope) if scope else ''
            style = Style.DIM
            endstyle = Style.NORMAL
            yield(template.format(**locals()))
        yield('')

@alias('add')
@arg('actor')
@arg('value')
@arg('-t', '--type', default='text', choices=CONTACT_TYPES)
def add_contact(args):
    "Adds a contact to given actor"
    fix_unicode(args, 'actor', 'value', 'type')
    actor = None
    try:
        actor = get_single(find_actors, args.actor)
    except MultipleMatches as e:
        raise CommandError(e)
    except NotFound as e:
        raise CommandError(u'No actor matches "{0}".'.format(args.actor))

    db = default_storage()
    qs = Contact.objects(db)
    dupes = qs.where(actor=actor, kind=args.type, value=args.value)
    if dupes.count():
        raise CommandError('Such contact already exists.')

    # FIXME Docu doesn't properly assign values from Contact(foo=bar)
    contact = Contact()
    contact.actor = actor
    contact.kind = args.type
    contact.value = args.value
    contact.save(db)

@alias('mv')
@arg('-f', '--from-actor')
@arg('-q', '--query')
@arg('-t', '--type', nargs='+')
@arg('new_actor')
def move_contact(args):
    "Moves matching contacts to given actor"
    fix_unicode(args, 'from_actor', 'query', 'type', 'new_actor')
    new_actor = None
    try:
        new_actor = get_single(find_actors, args.new_actor)
    except MultipleMatches as e:
        raise CommandError(e)
    except NotFound as e:
        raise CommandError(u'No actor matches "{0}".'.format(args.actor))

    assert args.from_actor or args.query, 'specify actor or auery'

    db = default_storage()
    contacts = Contact.objects(db).where_not(actor=new_actor.pk)
    if args.type:
        contacts = contacts.where(type__in=args.type)
    if args.query:
        contacts = contacts.where(value__matches_caseless=args.query)
    if args.from_actor:
        try:
            from_actor = get_single(find_actors, args.from_actor)
        except MultipleMatches as e:
            raise CommandError(e)
        except NotFound(e):
            raise CommandError('Bad --from-actor: no match for "{0}"'.format(
                args.from_actor))
        contacts = contacts.where(actor=from_actor.pk)

    if not len(contacts):
        raise CommandError('No suitable contacts were found.')

    yield('About to move these contacts:\n')
    for c in contacts:
        yield(u'- {actor}: {kind} {v}'.format(v=bright(c.value), **c))
    yield('')

    msg = u'Move these contacts to {0}'.format(bright(new_actor))
    if confirm(msg, default=True):
        for c in contacts:
            c.actor = new_actor
            c.save(db)
    else:
        yield('\nCancelled.')


@alias('go')
@arg('actor')
def open_urls(args):
    "Gathers URLs for matching actors and opens them is a web browser."
    actors = find_actors(args.actor)
    def _contacts():
        for a in actors:
            for c in a.contacts.where(kind='url'):
                yield c
    contacts = list(_contacts())
    yield('Found:\n')
    for c in contacts:
        yield(u'  {url} {actor}\n'.format(
            url=c.value, actor=Style.DIM+unicode(c.actor)+Style.NORMAL))
    if confirm('Open these URLs', default=True):
        for c in contacts:
            webbrowser.open_new_tab(c.value)
        yield('URLs were open in new tabs.')
    else:
        yield('\nCancelled.')
