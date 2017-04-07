# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import (
    Aggregate,
    CURRENCY,
    SECID,
    INVSUBACCTS,
    INV401KSOURCES,
)
from ofxtools.Types import (
    Bool,
    String,
    OneOf,
    Decimal,
    DateTime,
)


class INVPOS(SECID, CURRENCY):
    """ """
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    dtpriceasof = DateTime(required=True)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    """ """
    pass


class POSMF(INVPOS):
    """ """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(INVPOS):
    """ """
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    """ """
    pass


class POSSTOCK(INVPOS):
    """ """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
