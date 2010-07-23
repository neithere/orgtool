# -*- coding: utf-8 -*-

import datetime
from docu import Document, Field as f


class TrackedDocument(Document):
    """
    A document which automatically tracks date and time of its creation and of
    the last update. Of course it only tracks the changes made to records by
    saving them via TrackedDocument instances or its subclasses' instances.
    """
    date_time_created = f(datetime.datetime, essential=True,
                          default=datetime.datetime.now)
    date_time_updated = f(datetime.datetime, essential=True,
                          default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        self['date_time_updated'] = datetime.datetime.now()
        return super(TrackedDocument, self).save(*args, **kwargs)
