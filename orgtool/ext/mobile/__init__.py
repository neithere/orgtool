"""
Mobile phones (Gammu)
=====================

Incremental importing of the SMS archive from a mobile phone using
`python-gammu`_.

.. _python-gammu: http://wammu.eu/python-gammu/

Configuration
-------------

Settings example (in YAML)::

    extensions:
        orgtool.ext.mobile.MobileETL:
            my_number: "+1234567890"

.. note::

    The phone does not store sender and receiver numbers in the message;
    instead, it stores only the number from which the message was received or
    to which it was sent. Unfortunately we cannot get or restore "our" number.
    You must specify it explicitly in settings (as in the example above).

.. note::

    It seems that Gammu returns incorrect folder names. Moreover, this could
    not be fixed because the exact order seems to depend on the phone model. We
    just omit the folder.

Commands
--------

This extension provides following commands within namespace "mobile":

* import-sms
* import-contacts
* import-plans

API reference
-------------
"""
from tool.dist import check_dependencies
from tool.plugins import features, requires #, BasePlugin

check_dependencies(__name__)

from commands import (
    import_contacts, import_sms, import_plans,
)


@features('mobile')
@requires('{document_storage}')
def setup(app, conf):
    "Tool extension for importing data from mobile phones."
    assert isinstance(conf.get('my_numbers'), dict)
    commands = (import_contacts, import_sms, import_plans)
    app.cli_parser.add_commands(commands, namespace='mobile')
    return conf

'''
class MobileETL(BasePlugin):
    "Tool extension for importing data from mobile phones."
    features = 'mobile'
    requires = ('{document_storage}',)
    commands = (import_contacts, import_sms, import_plans)

    def make_env(self, my_numbers):
        assert isinstance(my_numbers, dict)
        return {'my_numbers': my_numbers}
'''
