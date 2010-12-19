from argh import alias, arg, command
from tool import app

from .schema import Event


@command
@alias('ls')
def list_events(query=None, format=u'{date_time} {summary}', date=None):
    "Displays a list of matching events."
    db = app.get_feature('document_storage').default_db
    events = Event.objects(db)
    if query:
        events = events.where(summary__matches_caseless=query)
    for event in events:
        yield format.format(**event)
