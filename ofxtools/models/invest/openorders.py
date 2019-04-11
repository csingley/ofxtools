# coding: utf-8
"""
Investments - OFX Section 13
"""
from ofxtools.Types import Bool, String, OneOf, Decimal, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.invest.acct import INVSUBACCTS
from ofxtools.models.invest.transactions import (
    BUYTYPES, SELLTYPES, OPTBUYTYPES, OPTSELLTYPES
)
from ofxtools.models.invest.securities import SECID
from ofxtools.models.bank import INV401KSOURCES
from ofxtools.models.i18n import CURRENCY


__all__ = [
    "UNITTYPES",
    "OO",
    "OOBUYDEBT", "OOBUYMF", "OOBUYOPT", "OOBUYOTHER", "OOBUYSTOCK",
    "OOSELLDEBT", "OOSELLMF", "OOSELLOPT", "OOSELLOTHER", "OOSELLSTOCK",
    "SWITCHMF",
    "INVOOLIST",
]


UNITTYPES = ("SHARES", "CURRENCY")


class OO(Aggregate):
    """ OFX section 13.9.2.5.1 - General open order aggregate """

    fitid = String(255, required=True)
    srvrtid = String(10)
    secid = SubAggregate(SECID, required=True)
    dtplaced = DateTime(required=True)
    units = Decimal(required=True)
    subacct = OneOf(*INVSUBACCTS, required=True)
    duration = OneOf("DAY", "GOODTILCANCEL", "IMMEDIATE", required=True)
    restriction = OneOf("ALLORNONE", "MINUNITS", "NONE", required=True)
    minunits = Decimal()
    limitprice = Decimal()
    stopprice = Decimal()
    memo = String(255)
    currency = SubAggregate(CURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class OOBUYDEBT(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    auction = Bool(required=True)
    dtauction = DateTime()


class OOBUYMF(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    buytype = OneOf(*BUYTYPES, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOBUYOPT(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    optbuytype = OneOf(*OPTBUYTYPES, required=True)


class OOBUYOTHER(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOBUYSTOCK(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    buytype = OneOf(*BUYTYPES, required=True)


class OOSELLDEBT(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)


class OOSELLMF(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    selltype = OneOf(*SELLTYPES, required=True)
    unittype = OneOf(*UNITTYPES, required=True)
    sellall = Bool(required=True)


class OOSELLOPT(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    optselltype = OneOf(*OPTSELLTYPES, required=True)


class OOSELLOTHER(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOSELLSTOCK(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    selltype = OneOf(*SELLTYPES, required=True)


class SWITCHMF(Aggregate):
    """ OFX section 13.9.2.5.2 """

    oo = SubAggregate(OO, required=True)
    secid = SubAggregate(SECID, required=True)
    unittype = OneOf(*UNITTYPES, required=True)
    switchall = Bool(required=True)


class INVOOLIST(Aggregate):
    """ OFX section 13.9.2.2 """

    oobuydebt = ListItem(OOBUYDEBT)
    oobuymf = ListItem(OOBUYMF)
    oobuyopt = ListItem(OOBUYOPT)
    oobuyother = ListItem(OOBUYOTHER)
    oobuystock = ListItem(OOBUYSTOCK)
    ooselldebt = ListItem(OOSELLDEBT)
    oosellmf = ListItem(OOSELLMF)
    oosellopt = ListItem(OOSELLOPT)
    oosellother = ListItem(OOSELLOTHER)
    oosellstock = ListItem(OOSELLSTOCK)
    switchmf = ListItem(SWITCHMF)
