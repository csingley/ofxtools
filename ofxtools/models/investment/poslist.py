# coding: utf-8
"""
Investment positions - OFX Section 13.9.2.6
"""
from ofxtools.Types import Bool, String, OneOf, Decimal, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, List
from ofxtools.models.investment import INVSUBACCTS
from ofxtools.models.investment.seclist import SECID
from ofxtools.models.bank import INV401KSOURCES
from ofxtools.models.i18n import CURRENCY


__all__ = ["INVPOS", "POSDEBT", "POSMF", "POSOPT", "POSOTHER", "POSSTOCK", "INVPOSLIST"]


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


class INVPOSLIST(List):
    """ OFX section 13.9.2.2 """

    dataTags = ["POSDEBT", "POSMF", "POSOPT", "POSOTHER", "POSSTOCK"]
