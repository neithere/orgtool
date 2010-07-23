# -*- coding: utf-8 -*-

from tool.ext import admin
from schema import *


class TrackedAdmin(admin.DocAdmin):
    exclude = TrackedDocument.meta.structure.keys()
