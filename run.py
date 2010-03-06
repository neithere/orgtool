#!/usr/bin/env python
# -*- coding: utf-8 -*-

# gh
from glashammer.application import make_app
from glashammer.utils import run_very_simple

# apps
from orgbase import OrgBase


@make_app
def wsgi_app(app):
    app.add_shared('', app.instance_dir+'/shared/')
    app.add_template_searchpath('templates/')

    app.add_setup(OrgBase(mountpoint_path='/'))

    # XXX this should read "app.conf.change_single(...)", but it raises KeyError
    # as if bundle "auth" did not define this variable -- though it did!
    app.add_config_var('auth/secret', unicode, 'i34jgg89e3n')

if __name__ == '__main__':
    print
    print 'RULES:'
    max_len = max(len(unicode(rule)) for rule in wsgi_app.map._rules)
    for rule in wsgi_app.map._rules:
        print '   %(rule)s %(padding)s %(endpoint)s %(arguments)s' % {
            'rule': rule,
            'padding': '.' * (max_len - len(unicode(rule)) + 2),
            'endpoint': rule.endpoint,
            'arguments': tuple(rule.arguments) if rule.arguments else '',
        }
    print

    run_very_simple(wsgi_app)
