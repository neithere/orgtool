# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from werkzeug import cached_property
from docu import Document, Field as f
from orgtool.ext.events import Event, Plan
from orgtool.ext.events.admin import PlanAdmin
from tool.ext import admin


NAMESPACE = 'finances'


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
        since = self.valid_since or datetime.date.today()
        until = self.valid_until or self.next_payment_date #datetime.date.today()
        assert since < until
        delta = until - since
        # XXX we don't know the frequency so we can't multiply the fee by it
        # XXX err, we need to know the date of our NEXT PAYMENT, that's it
        raise NotImplementedError

    @cached_property
    def actual_daily_fee(self):
        print '---'
        print 'DAILY FEE FOR', self
        if not self.payments:
            return Decimal('0')

        # XXX assuming that payments are sorted by date REVERSED
        first, last = self.payments[-1], self.payments[0]

        print 'first:', first
        print 'last:', last

        if self.valid_since and self.valid_until:
            print 'fixed start, end'
            delta = self.valid_until - self.valid_since
        elif self.valid_since:
            print 'fixed start'
            delta = last.date_time.date() - self.valid_since
        elif self.valid_until:
            print 'fixed end'
            delta = self.valid_until - first.date_time.date()
        else:
            if first == last:
                print 'first is last'
                #return self.actual_total_fee
                delta = datetime.datetime.now() - first.date_time
            else:
                print 'last - first'
                delta = last.date_time - first.date_time

        print 'delta:', delta

        if delta and delta.days:
            print 'daily fee = {0} {1} / {2} days'.format(self.actual_total_fee,
                                            self.currency, delta.days)
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


@admin.register_for(Contract)
class ContractAdmin(PlanAdmin):
    namespace = NAMESPACE
    list_names = [
        'summary', 'dates_rrule_text', 'fee', 'total_fee', 'currency'
    ]
    order_by = 'summary'


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
    #logged = f(datetime.datetime, default=datetime.datetime.now)
    balance = f(Decimal, label=u'account balance after the payment')

    defaults = {'summary': u'payment'}

    def __unicode__(self):
        if self.plan:
            return u'{date_time} {amount} {currency} for {plan}'.format(**self)
        return u'{date_time} {amount} {currency}'.format(**self)

#    def save(self, *args, **kw):
#        self
#        return super(Payment, self).save(*args, **kwargs)
admin.register(Payment, namespace=NAMESPACE,
               list_names=['date_time', 'plan', 'amount', 'currency', 'summary'],
               ordering={'names': ['date_time'], 'reverse': True})
