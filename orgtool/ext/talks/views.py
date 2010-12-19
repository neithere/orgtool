# -*- coding: utf-8 -*-

import calendar

from tool.routing import url
from tool.ext.breadcrumbs import entitled
from tool.ext.documents import default_storage
from tool.ext.templating import as_html

from schema import Message


def _get_month_name(number):
    try:
        return unicode(calendar.month_name[number])
    except (KeyError, TypeError):
        pass


@url('/')
@url('/<int(4):year>/')
@url('/<int(4):year>/<int(2):month>/')
@url('/<int(4):year>/<int(2):month>/<int(2):day>/')
@entitled(lambda **kw: unicode(kw.get('day') or
                               _get_month_name(kw.get('month')) or
                               kw.get('year') or u'Messages'))
@as_html('talks/message_index.html')
def message_index(request, year=None, month=None, day=None):
    db = default_storage()
    messages = Message.objects(db).order_by('date_time', reverse=True)
    if year:
        messages = messages.where(date_time__year=year)
        if month:
            messages = messages.where(date_time__month=month)
            if day:
                messages = messages.where(date_time__day=day)
    for name in 'sent_by', 'sent_to':
        if name in request.values:
            print repr(request.values[name])
            messages = messages.where(**{name: request.values[name]})
#    if 'state' in request.values:
#        messages = messages.where(state=request.values['state'])
    if 'q' in request.values:
        messages = messages.where(summary__contains=request.values['q'])
    print messages._conditions
    return {'object_list': messages}
