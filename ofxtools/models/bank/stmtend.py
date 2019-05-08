# coding: utf-8
"""
Statement closing information - OFX Section 11.5
"""


__all__ = [
    "CLOSING",
    "STMTENDRQ",
    "STMTENDRS",
    "STMTENDTRNRQ",
    "STMTENDTRNRS",
    "LASTPMTINFO",
    "CCCLOSING",
    "CCSTMTENDRQ",
    "CCSTMTENDRS",
    "CCSTMTENDTRNRQ",
    "CCSTMTENDTRNRS",
]


# local imports
from ofxtools.Types import Bool, String, Decimal, OneOf, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM, REWARDINFO
from ofxtools.models.i18n import (
    CURRENCY,
    ORIGCURRENCY,
    Origcurrency,
    CURRENCY_CODES,
)


class CLOSING(Aggregate, Origcurrency):
    """ OFX section 11.5.2 """

    fitid = String(255, required=True)
    dtopen = DateTime()
    dtclose = DateTime(required=True)
    dtnext = DateTime()
    balopen = Decimal()
    balclose = Decimal(required=True)
    balmin = Decimal()
    depandcredit = Decimal()
    chkanddebit = Decimal()
    totalfees = Decimal()
    totalint = Decimal()
    dtpoststart = DateTime(required=True)
    dtpostend = DateTime(required=True)
    mktginfo = String(360)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)


class STMTENDRQ(Aggregate):
    """ OFX section 11.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dtstart = DateTime()
    dtend = DateTime()


class STMTENDRS(Aggregate):
    """ OFX section 11.5.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    closing = ListItem(CLOSING)


class STMTENDTRNRQ(TrnRq):
    """ OFX section 11.5.1 """

    stmtendrq = SubAggregate(STMTENDRQ, required=True)


class STMTENDTRNRS(TrnRs):
    """ OFX section 11.5.2 """

    stmtendrs = SubAggregate(STMTENDRS)


class LASTPMTINFO(Aggregate):
    """ OFX section 11.3.10 """

    lastpmtdate = DateTime(required=True)
    lastpmtamt = Decimal(required=True)


class CCCLOSING(Aggregate):
    """ OFX Section 11.5.4.2 """

    fitid = String(255, required=True)
    dtopen = DateTime()
    dtclose = DateTime(required=True)
    dtnext = DateTime()
    balopen = Decimal()
    balclose = Decimal(required=True)
    intytd = Decimal()
    dtpmtdue = DateTime()
    minpmtdue = Decimal()
    pastdueamt = Decimal()
    latefeeamt = Decimal()
    finchg = Decimal()
    intratepurch = Decimal()
    intratecash = Decimal()
    intratexfer = Decimal()
    payandcredit = Decimal()
    purandadv = Decimal()
    debadj = Decimal()
    creditlimit = Decimal()
    cashadvcreditlimit = Decimal()
    dtpoststart = DateTime(required=True)
    dtpostend = DateTime(required=True)
    autopay = Bool()
    lastpmtinfo = SubAggregate(LASTPMTINFO)
    rewardinfo = SubAggregate(REWARDINFO)
    mktginfo = String(360)
    imagedata = Unsupported()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)


class CCSTMTENDRQ(Aggregate):
    """ OFX section 11.5.3 """

    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    dtstart = DateTime()
    dtend = DateTime()
    incstmtimg = Bool()


class CCSTMTENDRS(Aggregate):
    """ OFX section 11.5.4 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    ccclosing = ListItem(CCCLOSING)


class CCSTMTENDTRNRQ(TrnRq):
    """ OFX section 11.4.3.1 """

    ccstmtendrq = SubAggregate(CCSTMTENDRQ, required=True)


class CCSTMTENDTRNRS(TrnRs):
    """ OFX section 11.4.3.2 """

    ccstmtendrs = SubAggregate(CCSTMTENDRS)

    @property
    def statement(self):
        return self.ccstmtendrs
