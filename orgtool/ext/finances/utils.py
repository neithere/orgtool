# -*- coding: utf-8 -*-

import datetime
import decimal
import logging
import urllib2
import re
import yaml

from tool import app


ROOT_MODULE = __name__.rpartition('.')[0]

logger = logging.getLogger(ROOT_MODULE)


class CalculationError(Exception):
    pass


def convert_currency(currency_from, currency_to, amount=1):
    """
    Converts currency using Google API. Does not cache rates. It is a good idea
    to store the rates in a local database and periodically update them using
    this function.
    """
    if currency_from == currency_to:
        return amount
    logger.debug('Converting {amount} {currency_from} to {currency_to} using '
                 'Google currency calculator'.format(**locals()))
    url_tmpl = ('http://google.com/ig/calculator?'
                'q={amount}{currency_from}%3D%3F{currency_to}')
    url = url_tmpl.format(**locals())
    response = urllib2.urlopen(url)
    # data string example:
    #   {lhs: "1 U.S. dollar",rhs: "0.767224183 Euros",error: "",icc: true}
    data_string = response.read().replace('\xa0', '') # strip separators
    data = yaml.load(data_string)
    if data['error']:
        raise CalculationError('Got error {error}'.format(**data))
    rate = re.search(r'^(\d+\.\d+)', data['rhs'])
    if not rate:
        raise CalculationError('Unexpected rate format: {rhs}'.format(**data))
    return decimal.Decimal(rate.group(1).strip())


def get_default_currency():
    ext = app.get_feature('money')
    return unicode(ext.env['default_currency'])


# TODO: move this to Dark(?)
# Origin:
#     http://stackoverflow.com/questions/488670/calculate-exponential-moving-average-in-python
def calculate_ema(s, n=2, safe_period=True, ensure_series=True):
    """
    returns an n period exponential moving average for
    the time series s

    s is a list ordered from oldest (index 0) to most
    recent (index -1)
    n is an integer

    :param safe_period:
        automatically shrinks period if it's too large for given data set
    :param ensure_series:
        automatically prepends the series with a zero value if there's only one
        value in the series (this ensures a chart can be built).

    returns a numeric array of the exponential moving average
    """
    if not n:
        return

    s = list(s)
    if 1 == len(s):
        s = [0] + s
#        print 'single item:', s
#        return s

    ema = []

    if len(s) <= n:
        if safe_period:
            n = len(s) / 2
        else:
            raise ValueError('period {period} is too large for {cnt} data '
                             'items.'.format(period=n, cnt=len(s)))

    #get n sma first and calculate the next n period ema
    sma = sum(s[:n]) / n
    multiplier = 2 / float(1 + n)
    ema.append(sma)

    #EMA(current) = ( (Price(current) - EMA(prev) ) x Multiplier) + EMA(prev)
    ema.append(( (s[n] - sma) * multiplier) + sma)

    #now calculate the rest of the values
    j = 1
    for i in s[n+1:]:
       ema.append(ema[j] + (multiplier * (i - ema[j])))
       j += 1

    return ema

# TODO: extract this to a template filter
def _get_rel_delta(dt, precision=2):
    from dateutil.relativedelta import relativedelta
    import datetime
    now = datetime.datetime.utcnow()
    if not isinstance(dt, datetime.datetime):
        now = now.date()
    if dt < now:
        delta = relativedelta(now, dt)
    else:
        delta = relativedelta(dt, now)
    if delta.days or delta.months or delta.years:
        # TODO: i18n and i10n (ngettext, etc.)
        mapping = (
            (delta.years, u'years'),
            (delta.months, u'months'),
            (delta.days, u'days'),
        )
        parts = [(v,t) for v,t in mapping if v]
        used_parts = parts[:precision]
        is_past = bool(dt < now)
        return used_parts, is_past
    else:
        return [], False

def render_rel_delta(dt):
    parts, is_past = _get_rel_delta(dt)
    if parts:
        parts = [u'{0} {1}'.format(v,t) for v,t in parts]
        template = u'{0} ago' if is_past else u'in {0}'
        return template.format(' '.join(parts).strip())
    else:
        # _within_ a day; may be another calendar day
        return u'<strong>today</strong>'

def is_date_within_a_day(dt):
    parts, is_past = _get_rel_delta(dt)
    return not bool(parts)

def chart_url_for_payments(payments, width=300, height=100, only_smooth=True,
                           max_days=None, currency=None):
    payments = payments.where_not(amount=None).order_by('date_time')  # NOT reversed
    if max_days:
        min_date = datetime.datetime.utcnow() - datetime.timedelta(days=max_days)
        payments = payments.where(date_time__gte=min_date)
    if not payments:
        return None

    # http://chart.apis.google.com/chart?cht=lc&chs=400x200&chd=t:10,-20,60,40&chco=318CE7&chds=-20,60&chxt=r,r&chxr=0,-20,60|1,-20,60&chxtc=1,-400&chxp=1,0&chxs=1,0000dd,13,-1,t,FF0000&chxl=1:|zero

    main_color, smooth_color = 'FFBF00', '8DB600', #'318CE7'   #, #'FE6F5E'# 'FAE7B5'
    """
    url_template = (
        'http://chart.apis.google.com/chart?'
        #'cht=lc&'                                 # line chart
        'cht=lc:nda&'                             # hide axis
        + (
            'chd=t:{smooth_series}&'  # data series
            if only_smooth else
            'chd=t:{smooth_series}|{amount_series}&'  # data series
        ) +
        'chds={min_amount},{max_amount}&'         # fix axis range
        'chs={width}x{height}&'                             # image size
        #'chm=H,FF0000,0,0,1&'              # mark zero amount
        'chxt=r&'                                 # show ticks on the right side
        # axis labels:
        'chxl=0:|{min_amount}|zero|{max_amount}&chxp=0,0|-100,100&chxr=0,{min_amount},{max_amount},0&chxtc=0,-{width}&'
        'chco={main_color},{smooth_color}&'
        'chm={annotations}&'
    )
    """
    #print payments
    amounts = [float(p.get_amount_as(currency) if currency else p.amount)
               for p in payments if p.amount is not None]
    #print 'amounts', amounts
    _flat = lambda xs: ','.join(['{0:.2f}'.format(x) for x in xs])
    #amount_series = _flat(amounts)
    smoothing_period = len(amounts) / 3 or len(amounts) # 120->30, 14->6..10, 80->30

#    for i in reversed(range(1,10)):
#        if i < len(amounts) / 2:
#            smoothing_period = len(amounts) / i
#            break
    # (len(amounts) / 10 if 10 < len(amounts) else 5) or 3
    smooth_data = calculate_ema(amounts, smoothing_period)
    if not smooth_data:
        return ''

    #smooth_series = _flat(smooth_data)
    min_amount = min(smooth_data if only_smooth else amounts) - 1
    max_amount = max(smooth_data if only_smooth else amounts) + 1
    if max_amount < 0:
        max_amount = 0
    if 0 < min_amount:
        min_amount = 0
#        if min_amount == max_amount:
#            min_amount = 0 if 0 < min_amount else -max_amount

    #'''
    # FIXME HACK -- this is broken by design:
    year_marks = {}
    for i, payment in enumerate(payments):
        year_marks.setdefault(payment.date_time.year, (i, payment))
    annotations = '|'.join([ 'A{text},,1,{point},{size}'.format(
        text = year_marks[year][1].date_time.strftime('%b %Y'),
        # HACK: fixing "ensure_series"
        point = year_marks[year][0] if 1 < len(amounts) else year_marks[year][0]+1,  # payment index in query AND amount index
        size = 8,
    ) for year in sorted(year_marks)])


    #return url_template.format(**locals())
    #'''


    from pygooglechart import Chart
    from pygooglechart import SimpleLineChart
    from pygooglechart import Axis
    import math

    def _prep_boundary(x):
        value = math.ceil(abs(x))
        return -value if x < 0 else value
    min_y, max_y = [_prep_boundary(x) for x in (min_amount, max_amount)]

    chart = SimpleLineChart(width, height, y_range=[min_y, max_y])

    chart.add_data(smooth_data)
    if not only_smooth:
        chart.add_data(amounts)
    chart.set_colours([smooth_color, main_color])

    chart.set_axis_labels(Axis.RIGHT, [min_y, max_y])
    chart_url = chart.get_url()

    chxr = 'chxr=0,{min_y},{max_y}'.format(**locals())

    # NOTE: pygooglechart does not support some stuff we need here
    return '&'.join([
        chart_url,
        # visible axes
        'chxt=r,r',

        # scale with custom range
        'chds={min_y},{max_y}'.format(**locals()),

        # axis ranges
        'chxr=0,{min_y},{max_y}|1,{min_y},{max_y}'.format(**locals()),

        # axis tick styles
        'chxtc=1,-{width}'.format(**locals()),

        # axis labels
        'chxl=1:|sea level',

        # axis label positions
        'chxp=1,0',

        # axis label styles
        'chxs=1,318CE7,13,-1,t,318CE7', #550000',

#        chxr,
#        'chxl=0:{min_y},zero,{max_y}'.format(**locals()),
#        'chxp=0,{min_y},0,{max_y}'.format(**locals()),
##        'chxs=|0N*sz2*,0000FF'
##        zeromark

        # annotations
        'chm={annotations}&'.format(**locals()),
    ])

