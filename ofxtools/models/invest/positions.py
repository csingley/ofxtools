# coding: utf-8
"""
Investment positions - OFX Section 13.9.2.6
"""


__all__ = [
    "INVPOS",
    "POSDEBT",
    "POSMF",
    "POSOPT",
    "POSOTHER",
    "POSSTOCK",
    "INVPOSLIST",
]


# Local imports
from ofxtools.Types import Bool, String, OneOf, Decimal, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.invest.acct import INVSUBACCTS
from ofxtools.models.invest.securities import SECID
from ofxtools.models.bank import INV401KSOURCES
from ofxtools.models.i18n import CURRENCY


class INVPOS(Aggregate):
    """ OFX section 13.9.2.6.1 """

    secid = SubAggregate(SECID, required=True)
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf("SHORT", "LONG", required=True)
    units = Decimal(required=True)
    unitprice = Decimal(required=True)
    mktval = Decimal(required=True)
    avgcostbasis = Decimal()
    dtpriceasof = DateTime(required=True)
    currency = SubAggregate(CURRENCY)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(Aggregate):
    """ OFX section 13.9.2.6.1 """

    invpos = SubAggregate(INVPOS, required=True)


class POSMF(Aggregate):
    """ OFX section 13.9.2.6.1 """

    invpos = SubAggregate(INVPOS, required=True)
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(Aggregate):
    """ OFX section 13.9.2.6.1 """

    invpos = SubAggregate(INVPOS, required=True)
    secured = OneOf("NAKED", "COVERED")


class POSOTHER(Aggregate):
    """ OFX section 13.9.2.6.1 """

    invpos = SubAggregate(INVPOS, required=True)


class POSSTOCK(Aggregate):
    """ OFX section 13.9.2.6.1 """

    invpos = SubAggregate(INVPOS, required=True)
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()


class INVPOSLIST(Aggregate):
    """ OFX section 13.9.2.2 """

    posdebt = ListItem(POSDEBT)
    posmf = ListItem(POSMF)
    posopt = ListItem(POSOPT)
    posother = ListItem(POSOTHER)
    posstock = ListItem(POSSTOCK)
