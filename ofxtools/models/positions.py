# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import (
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
    """ OFX section 13.9.2.6.1 """
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    avgcostbasis = Decimal()
    dtpriceasof = DateTime(required=True)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    """ OFX section 13.9.2.6.1 """
    """ """
    pass


class POSMF(INVPOS):
    """ OFX section 13.9.2.6.1 """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(INVPOS):
    """ OFX section 13.9.2.6.1 """
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    """ OFX section 13.9.2.6.1 """
    pass


class POSSTOCK(INVPOS):
    """ OFX section 13.9.2.6.1 """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
