"""
Mobile phones (Gammu)
=====================

Incremental importing of the SMS archive from a mobile phone using
`python-gammu`_.

.. _python-gammu: http://wammu.eu/python-gammu/

Settings example (in YAML)::

    bundles:
        orgtool.ext.gammu:
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

Adds commands:

* import-mobile-sms
* import-mobile-contacts
* import-mobile-plans

"""
from tool.dist import check_dependencies

check_dependencies(__name__)

import commands
