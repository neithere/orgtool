# -*- coding: utf-8 -*-
import datetime
import decimal
Decimal = decimal.Decimal    # we need the module, too
import logging
from werkzeug import cached_property
import dark
from doqu import Document, Field as f
from orgtool.ext.events import Event, Plan
from orgtool.ext.events.admin import PlanAdmin
from orgtool.ext.tracking import TrackedDocument
from tool.ext import admin

import utils

logger = logging.getLogger('orgtool.ext.finances')


__all__ = ['Contract', 'Payment', 'CurrencyRate']


NAMESPACE = 'finances'


def utc_today():
    "Returns the UTC equivalent for datetime.date.today()."
    return datetime.datetime.utcnow().date()


class Contract(Plan):
    """
    An agreement between stakeholders (2..n) that a certain service will be
    provided in exchange for a certain amount of money. Supports long-term
    recurrent payments. Ideally, each payment should be confirmed before the
    next one is unblocked.

    It is a good idea to close the agreement and create another once the fee
    changes.

    Can describe one-time payments but usually that would be overkill. Great
    for describing, explaining and predicting the bulk of income and expenses.
    """
#    summary = f(unicode, required=True)    # "доступ к сети Интернет"
    currency = f(unicode, required=True)   # "RUB"
    fee = f(Decimal, required=True)        # -390   (positive = income, negative = expenses)
    daily_fee = f(Decimal)
    is_fee_fixed = f(bool, default=True)   # if False, `fee` is an estimate
#    frequency = f(int)     # 30    (или там опред. число мес.?)
    #repeat_month = f(int)   # 0
    #repeat_day = f(int)     # 25
    # if next_payment is in the past, that payment is not yet confirmed.
    # if next_payment is None, the agreement is closed.
    #next_payment = f(datetime.date)  # если дата в прошлом, надо подтвердить
    stakeholder = f(unicode)  # "U-tel". Can be m2m but later  (agent)
    service_id = f(unicode)   # contract number, phone number, login, etc.
    is_automated = f(bool)    # e.g. bank unconditionally withdraws money from
                              # the account according to an agreement

    def __unicode__(self):
        return u'{summary}'.format(**self)

    def calc_daily_fee(self):
        "Returns actual daily fee for related Payment objects."
        db = self._saved_state.storage
        payments = Payment.objects(db).where(plan=self)
        payments = payments.order_by('date_time')
        total_fee = sum(p.amount for p in payments)
        cnt = payments.count()
        if not cnt:
            return
        if cnt == 1:
            return total_fee / 30
        first = payments[0]
        last = payments[cnt - 1]
        date_delta = last.date_time - first.date_time
        days = date_delta.days
        return total_fee / days
#admin.register(Contract, namespace=NAMESPACE,
#               list_names=['summary', 'fee', 'currency'])

    def get_events(self):
        if not self.pk:
            return None
        payments = Payment.objects(self._saved_state.storage)
        return payments.where(plan=self).order_by('date_time', reverse=True)

    @cached_property
    def payments(self):
        import warnings
        warnings.warn('Contract.payments is deprecated, use Contract.events',
                        DeprecationWarning)
        return self.events

    @cached_property
    def expected_daily_fee(self):
        if not self.fee:
            return Decimal(0)
        if not self.valid_since and not self.valid_until:
            return Decimal(0)
        since = self.valid_since or utc_today()
        until = self.valid_until or self.next_payment_date #datetime.date.today()
        assert since < until
        delta = until - since
        # XXX we don't know the frequency so we can't multiply the fee by it
        # XXX err, we need to know the date of our NEXT PAYMENT, that's it
        raise NotImplementedError

    @cached_property
    def actual_daily_fee(self):
        logger.debug('CALCULATING DAILY FEE FOR {0}'.format(self))
        if not self.payments:
            return Decimal('0')

        # XXX assuming that payments are sorted by date REVERSED
        first, last = self.payments[-1], self.payments[0]

        logger.debug('first: {first}, last: {last}'.format(**locals()))

        if self.valid_since and self.valid_until:
            logger.debug('fixed start, end')
            delta = self.valid_until - self.valid_since
        elif self.valid_since:
            logger.debug('fixed start')
            delta = last.date_time.date() - self.valid_since
        elif self.valid_until:
            logger.debug('fixed end')
            delta = self.valid_until - first.date_time.date()
        else:
            if first == last:
                logger.debug('first is last')
                #return self.actual_total_fee
                delta = datetime.datetime.utcnow() - first.date_time
            else:
                logger.debug('last - first')
                delta = last.date_time - first.date_time

        logger.debug('delta: {0}'.format(delta))

        if delta and delta.days:
            logger.debug('daily fee = {0} {1} / {2} days'.format(
                self.actual_total_fee, self.currency, delta.days))
            return (self.actual_total_fee / delta.days).quantize(Decimal('0.01'))
        else:
            return self.actual_total_fee

#        result = self.total_fee / delta.days if delta and delta.days else
#        self.total_fee
#        return result.quantize(Decimal('0.01'))

    @cached_property
    def actual_monthly_fee(self):
        #k = 1 if 1 == len(self.payments) else 30
        k = 30
        return (self.actual_daily_fee * k).quantize(Decimal('0.01'))

    @cached_property
    def actual_total_fee(self):
        return sum(p.amount for p in self.payments)

    @cached_property
    def expected_payment_amount(self):
        """
        Returns expected amount for the next payment, based on the payments
        history. Uses qu0.75 (median value of the last quarter of payments
        history).

        .. note::

            The aggregation method will produce more or less accurate results
            only for homogenous history of regular payments. It will fail on
            mixed data because it uses median value instead of average. You'll
            need separate plans for each type of payments. For example, if
            there are two kinds of payments within a certain plan (monthly fee
            and annual refunds), you'll need to split them into "Service ABC:
            Fee" and "Service ABD: Refunds" in order to have accurate
            predictions for each of them.

        """
        if self.is_fee_fixed:
            return self.fee
        else:
            return dark.Qu3('amount').count_for(self.events)

    def get_expected_payment_amount_as(self, currency=None):
        currency = currency or utils.get_default_currency()
        amount_str = str(self.expected_payment_amount)
        try:
            amount = Decimal(amount_str)
        except decimal.InvalidOperation:
            # e.g. 'N/A' as returned by Dark aggregators in some cases
            return 0
        if amount == 0:
            return 0
        db = self._saved_state.storage
        x = CurrencyRate.convert(db, self.currency, currency, amount)
        return x.quantize(Decimal('0.01'))


'''
class Account(Document):
    name = f(unicode, required=True)
    currency = f(unicode, required=True)
    state = f(Decimal, required=True)
    owner = f(Actor)
    number = f(unicode)
'''


class Payment(Event):
    plan = f(Contract)  # overriding Event's definition
    #time = f(datetime.time)
    #from_account = f(Account)
    #to_account = f(Account)
    purpose = f(unicode)  # more or less formal
    details = f(unicode)
    #summary = f(unicode)  # additional info
    amount = f(Decimal, required=True)
    currency = f(unicode, default=lambda p: p.plan.currency)
    #logged = f(datetime.datetime, default=datetime.datetime.utcnow)
    balance = f(Decimal, label=u'account balance after the payment')

    defaults = {'summary': u'payment'}

    def __unicode__(self):
        if self.plan:
            return u'{date_time} {amount} {currency} for {plan}'.format(**self)
        return u'{date_time} {amount} {currency}'.format(**self)

    def get_amount_as(self, currency=None):
        """
        Returns amount converted to given currency.

        :param currency:
            Currency name, e.g. "EUR" or "USD". If `None`, bundle setting
            ``default_currency` if used.
        """
        currency = currency or utils.get_default_currency()
        if self.amount == 0:
            return 0
        db = self._saved_state.storage
        return CurrencyRate.convert(db, self.currency, currency, self.amount)


class CurrencyRate(TrackedDocument):
    from_currency = f(unicode, required=True)
    to_currency = f(unicode, required=True)
    rate = f(Decimal, required=True)
    date = f(datetime.date, default=utc_today, required=True)

    _cache = {}
    _cache_date = utc_today()

    def __unicode__(self):
        return u'1 {from_currency} = {rate} {to_currency}'.format(**self)

    def save(self, *args, **kwargs):
        self.date = utc_today()   # reset, force today
        return super(CurrencyRate, self).save(*args, **kwargs)

    @classmethod
    def convert(cls, db, from_currency, to_currency, amount):
        """
        Converts given amount of money from one currency to another. Exchange
        rates are provided by Google and cached in given local database. The
        cache expires on the next calendar day.

        :param db:
            storage adapter for local caching of exchange rates
        :param from_currency:
            string — currency from which to convert (e.g. "EUR")
        :param to_currency:
            string — currency to which to convert (e.g. "USD")
        :param amount:
            Decimal — the amount of money to convert
        """
        if from_currency == to_currency:
            return amount
        # TODO: class-level memory cache (avoid hitting the database)
        _from, _to = sorted([from_currency, to_currency]) # keep single direction

        rate = None

        # memory cache
        if cls._cache_date == utc_today():
            rate = cls._cache.get(_from, {}).get(_to)
        else:
            # reset memory cache
            cls._cache = {}
            cls._cache_date = utc_today()
            logging.debug('No memory-cached rate for '
                          '{from_currency}→{to_currency}'.format(**locals()))

        # DB cache
        if rate is None:
            cached = cls.objects(db).where(from_currency=_from, to_currency=_to)
            if cached:
                logging.debug('Found DB-cached rate for '
                              '{from_currency}→{to_currency}'.format(**locals()))

            obj = cached[0] if cached else cls(from_currency=_from, to_currency=_to)
            if not obj.date or obj.date < utc_today():
                # update DB cache (fetch data from external service)
                obj.rate = utils.convert_currency(_from, _to, 1)
                obj.save(db)
            rate = obj.rate

            # update memory cache
            cls._cache.setdefault(_from, {})[_to] = rate

        # TODO: check amount type (decimal vs float vs int)
        if _from == from_currency:
            return amount * rate
        else:
            return amount / rate

