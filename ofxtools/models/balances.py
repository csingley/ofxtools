# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import (
    Aggregate,
    CURRENCY,
)
from ofxtools.Types import (
    String,
    OneOf,
    Decimal,
    DateTime,
)


class LEDGERBAL(Aggregate):
    """ """
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class AVAILBAL(Aggregate):
    """ """
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class INVBAL(Aggregate):
    """ OFX section 13.9.2.7 """
    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()

    _subaggregates = ('BALLIST',)


class BAL(CURRENCY):
    """ OFX section 3.1.4 """
    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()


class INV401KBAL(Aggregate):
    """ OFX section 13.9.2.9 """
    cashbal = Decimal()
    pretax = Decimal()
    aftertax = Decimal()
    match = Decimal()
    profitsharing = Decimal()
    rollover = Decimal()
    othervest = Decimal()
    othernonvest = Decimal()
    total = Decimal(required=True)

    _subaggregates = ('BALLIST',)
