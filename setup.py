#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Orgtool is an extremely flexible organizer.
#    Copyright © 2009—2010  Andrey Mikhaylenko
#
#    This file is part of Orgtool.
#
#    Orgtool is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Orgtool is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Orgtool.  If not, see <http://gnu.org/licenses/>.


import os
from setuptools import find_packages, setup

from _version import version


readme = open(os.path.join(os.path.dirname(__file__), 'README')).read()
print find_packages()
assert 1==0
setup(
    # overview
    name             = 'orgtool',
    description      = 'An extremely flexible organizer platform.',
    long_description = readme,

    # technical info
    version  = version,
    packages = find_packages(),
    requires = [
        'python (>= 2.6)',
        'docu (>=0.23)',    # data storage & query
        'tool (>=0.3)',     # web / cli / signals
        'lepl (>=4.3)',     # parsing strings (e.g. fancy dates)
        'dateutil (>=1.5)', # recurring dates, etc.
    ],
    provides = ['orgtool'],

    # optional features
    #   NOTE: if e.g. Sphinx or nosetests die because of endpoints, try:
    #   $ rm -rf orgtool.egg-info
    #   $ pip install .
    extras_require = {
        # NOTE: hamster doesn't export __version__ and N/A at PyPI
        'Hamster': ['hamster>=2.31', 'pytz>=2010h', 'dbus>=0.83'],
        # NOTE: gammu is N/A at PyPI, only as part of the gammu distribution
        'Mobile': ['gammu>=1.28.0'],
    },
    entry_points = {
        'extensions': [
            'hamster = orgtool.ext.hamster [Hamster]',
            'mobile = orgtool.ext.mobile [Mobile]',
        ],
    },

    # copyright
    author   = 'Andrey Mikhaylenko',
    author_email = 'andy@neithere.net',
    license  = 'GNU Lesser General Public License (LGPL), Version 3',

    # more info
    url          = 'http://bitbucket.org/neithere/orgtool/',
    download_url = 'http://bitbucket.org/neithere/orgtool/src/',

    # categorization
    keywords     = ('query database api model models orm key/value '
                    'orgtoolment-oriented non-relational tokyo cabinet mongodb'),
    classifiers  = [
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    # release sanity check
    test_suite = 'nose.collector',
)
