# coding: utf-8
"""
Data structures for credit card download - OFX Section 11
"""
# local imports
from ofxtools.Types import (
    String, Decimal, OneOf, Bool,
    DateTime)
from ofxtools.models.base import (
    Aggregate, List, SubAggregate, Unsupported,
)
from ofxtools.models.common import (
    STATUS, MSGSETCORE,
)
from ofxtools.models.bank import (
    CCACCTFROM, INCTRAN, BANKTRANLIST, LEDGERBAL, AVAILBAL, BALLIST,
)
from ofxtools.models.i18n import (
    CURRENCY, ORIGCURRENCY, CURRENCY_CODES,
)


__all__ = ['LASTPMTINFO', 'REWARDINFO',
           'CCSTMTRQ', 'CCSTMTRS', 'CCSTMTTRNRQ', 'CCSTMTTRNRS',
           'CREDITCARDMSGSRQV1', 'CREDITCARDMSGSRSV1', 'CREDITCARDMSGSETV1',
           'CREDITCARDMSGSET', 'CCSTMTENDTRNRQ', 'CCSTMTENDTRNRS',
           'CCSTMTENDRQ', 'CCSTMTENDRS', 'CCCLOSING']


class LASTPMTINFO(Aggregate):
    """ OFX section 11.3.10 """
    lastpmtdate = DateTime(required=True)
    lastpmtamt = Decimal(required=True)


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


class CCSTMTTRNRQ(Aggregate):
    """ OFX section 11.4.3.1 """
    trnuid = String(36, required=True)
    ccstmtrq = SubAggregate(CCSTMTRQ)


class CCSTMTTRNRS(Aggregate):
    """ OFX section 11.4.3.2 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    ccstmtrs = SubAggregate(CCSTMTRS)

    @property
    def statement(self):
        return self.ccstmtrs


class CCCLOSING(Aggregate):
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
    ccclosing = SubAggregate(CCCLOSING)


class CCSTMTENDTRNRQ(Aggregate):
    """ OFX section 11.4.3.1 """
    trnuid = String(36, required=True)
    ccstmtendrq = SubAggregate(CCSTMTENDRQ)


class CCSTMTENDTRNRS(Aggregate):
    """ OFX section 11.4.3.2 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    ccstmtendrs = SubAggregate(CCSTMTENDRS)

    @property
    def statement(self):
        return self.ccstmtendrs


class CREDITCARDMSGSRQV1(List):
    """ OFX section 11.13.1.1.1 """
    dataTags = ['CCSTMTTRNRQ', 'CCSTMTENDTRNRQ']


class CREDITCARDMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    dataTags = ['CCSTMTTRNRS', 'CCSTMTENDTRNRS']

    @property
    def statements(self):
        return [trnrs.statement for trnrs in self]


class CREDITCARDMSGSETV1(Aggregate):
    """ OFX section 11.13.3 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    closingavail = Bool(required=True)
    pendingavail = Bool()
    imageprof = Unsupported()


class CREDITCARDMSGSET(Aggregate):
    """ OFX section 11.13.3 """
    creditcardmsgsetv1 = SubAggregate(CREDITCARDMSGSETV1, required=True)
