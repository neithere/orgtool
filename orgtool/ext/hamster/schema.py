from doqu import Field as f
from orgtool.ext.events import Event


class HamsterFact(Event):
    tags = f(list)

    x_hamster_type = f(unicode, required=True,
                       choices=[u'fact', u'category', u'activity'])
    x_hamster_id = f(int, required=True)
    x_hamster_category = f(unicode, essential=True)
    x_hamster_activity_id = f(int, essential=True)
    x_hamster_delta = f(unicode)  # '0:18:00', basically just cached timedelta

    source = f(unicode, required=True,
               default=u'hamster-client', choices=[u'hamster-client'])


