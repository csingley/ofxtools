# coding: utf-8
"""
Bank statement download - OFX Section 11.4
"""


__all__ = [
    "INV401KSOURCES",
    "ACCTTYPES",
    "TRNTYPES",
    "BANKACCTFROM",
    "BANKACCTTO",
    "BANKACCTINFO",
    "CCACCTFROM",
    "CCACCTTO",
    "CCACCTINFO",
    "INCTRAN",
    "LEDGERBAL",
    "AVAILBAL",
    "BALLIST",
    "PAYEE",
    "STMTTRN",
    "BANKTRANLIST",
    "STMTRQ",
    "STMTRS",
    "STMTTRNRQ",
    "STMTTRNRS",
    "REWARDINFO",
    "CCSTMTRQ",
    "CCSTMTRS",
    "CCSTMTTRNRQ",
    "CCSTMTTRNRS",
]


# local imports
from ofxtools.Types import (
    Bool,
    String,
    NagString,
    OneOf,
    Integer,
    Decimal,
    DateTime,
    ListItem,
)
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.common import SVCSTATUSES, BAL
from ofxtools.models.wrapperbases import TrnRq, TrnRs, TranList
from ofxtools.models.i18n import (
    CURRENCY,
    ORIGCURRENCY,
    Origcurrency,
    CURRENCY_CODES,
    COUNTRY_CODES,
)


# Enums used in aggregate validation
INV401KSOURCES = (
    "PRETAX",
    "AFTERTAX",
    "MATCH",
    "PROFITSHARING",
    "ROLLOVER",
    "OTHERVEST",
    "OTHERNONVEST",
)
# OFX section 11.3.1.1
ACCTTYPES = ("CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD")
TRNTYPES = (
    "CREDIT",
    "DEBIT",
    "INT",
    "DIV",
    "FEE",
    "SRVCHG",
    "DEP",
    "ATM",
    "POS",
    "XFER",
    "CHECK",
    "PAYMENT",
    "CASH",
    "DIRECTDEP",
    "DIRECTDEBIT",
    "REPEATPMT",
    "OTHER",
)


class BANKACCTFROM(Aggregate):
    """ OFX section 11.3.1 """

    bankid = String(9, required=True)
    branchid = String(22)
    acctid = String(22, required=True)
    accttype = OneOf(*ACCTTYPES, required=True)
    acctkey = String(22)


class BANKACCTTO(Aggregate):
    """ OFX section 11.3.1 """

    bankid = String(9, required=True)
    branchid = String(22)
    acctid = String(22, required=True)
    accttype = OneOf(*ACCTTYPES, required=True)
    acctkey = String(22)


class BANKACCTINFO(Aggregate):
    """ OFX section 11.3.3 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    suptxdl = Bool(required=True)
    xfersrc = Bool(required=True)
    xferdest = Bool(required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


class CCACCTFROM(Aggregate):
    """ OFX section 11.3.2 """

    acctid = String(22, required=True)
    acctkey = String(22)


class CCACCTTO(Aggregate):
    """ OFX section 11.3.2 """

    acctid = String(22, required=True)
    acctkey = String(22)


class CCACCTINFO(Aggregate):
    """ OFX section 11.3.4 """

    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    suptxdl = Bool(required=True)
    xfersrc = Bool(required=True)
    xferdest = Bool(required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


class INCTRAN(Aggregate):
    """ OFX section 11.4.2.1 """

    dtstart = DateTime()
    dtend = DateTime()
    include = Bool(required=True)


class STMTRQ(Aggregate):
    """ OFX section 11.4.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    includepending = Bool()
    inctranimg = Bool()


#  This class is defined here, rather than models.billpay, in order to avoid
#  circular imports.
class PAYEE(Aggregate):
    """ OFX section 12.5.2.1 """

    name = NagString(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32, required=True)


class STMTTRN(Aggregate, Origcurrency):
    """ OFX section 11.4.3 """

    trntype = OneOf(*TRNTYPES, required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    fitid = String(255, required=True)
    correctfitid = String(255)
    correctaction = OneOf("REPLACE", "DELETE")
    srvrtid = String(10)
    checknum = String(12)
    refnum = String(32)
    sic = Integer()
    payeeid = String(12)
    name = String(32)
    payee = SubAggregate(PAYEE)
    extdname = String(100)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    memo = String(255)
    imagedata = Unsupported()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)

    optionalMutexes = [
        ["name", "payee"],
        ["ccacctto", "bankacctto"],
        ["currency", "origcurrency"],
    ]


class BANKTRANLIST(TranList):
    """ OFX section 11.4.2.2 """

    stmttrn = ListItem(STMTTRN)


class LEDGERBAL(Aggregate):
    """ OFX section 11.4.2.2 """

    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class AVAILBAL(Aggregate):
    """ OFX section 11.4.2.2 """

    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class BALLIST(Aggregate):
    """ OFX section 11.4.2.2 & 13.9.2.7 """

    bal = ListItem(BAL)


class STMTRS(Aggregate):
    """ OFX section 11.4.2.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    banktranlist = SubAggregate(BANKTRANLIST)
    banktranlistp = Unsupported()
    ledgerbal = SubAggregate(LEDGERBAL, required=True)
    availbal = SubAggregate(AVAILBAL)
    cashadvbalamt = Decimal()
    intrate = Decimal()
    ballist = SubAggregate(BALLIST)
    mktginfo = String(360)

    @property
    def account(self):
        return self.bankacctfrom

    @property
    def transactions(self):
        return self.banktranlist

    @property
    def balance(self):
        return self.ledgerbal


class STMTTRNRQ(TrnRq):
    """ OFX section 11.4.2.1 """

    stmtrq = SubAggregate(STMTRQ, required=True)


class STMTTRNRS(TrnRs):
    """ OFX section 11.4.2.2 """

    stmtrs = SubAggregate(STMTRS)

    @property
    def statement(self):
        return self.stmtrs


class REWARDINFO(Aggregate):
    """ OFX section 11.4.3.2 """

    name = String(32, required=True)
    rewardbal = Decimal(required=True)
    rewardearned = Decimal()


class CCSTMTRQ(Aggregate):
    """ OFX section 11.4.3.1 """

    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    includepending = Bool()
    inctranimg = Bool()


class CCSTMTRS(Aggregate):
    """ OFX section 11.4.3.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    banktranlist = SubAggregate(BANKTRANLIST)
    banktranlistp = Unsupported()
    ledgerbal = SubAggregate(LEDGERBAL, required=True)
    availbal = SubAggregate(AVAILBAL)
    cashadvbalamt = Decimal()
    intratepurch = Decimal()
    intratecash = Decimal()
    intratexfer = Decimal()
    rewardinfo = SubAggregate(REWARDINFO)
    ballist = SubAggregate(BALLIST)
    mktginfo = String(360)

    @property
    def account(self):
        return self.ccacctfrom

    @property
    def transactions(self):
        return self.banktranlist

    @property
    def balance(self):
        return self.ledgerbal


class CCSTMTTRNRQ(TrnRq):
    """ OFX section 11.4.3.1 """

    ccstmtrq = SubAggregate(CCSTMTRQ, required=True)


class CCSTMTTRNRS(TrnRs):
    """ OFX section 11.4.3.2 """

    ccstmtrs = SubAggregate(CCSTMTRS)

    @property
    def statement(self):
        return self.ccstmtrs
