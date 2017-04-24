# coding: utf-8
"""
Data structures for credit card download - OFX Section 11
"""
# local imports
from ofxtools.Types import (
    String, Decimal, OneOf, Bool,
)
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
    CURRENCY_CODES,
)


__all__ = ['REWARDINFO', 'CCSTMTRS', 'CCSTMTRQ', 'CCSTMTTRNRS',
           'CREDITCARDMSGSRQV1', 'CREDITCARDMSGSRSV1', 'CREDITCARDMSGSETV1',
           'CREDITCARDMSGSET', ]


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


class CREDITCARDMSGSRQV1(List):
    """ OFX section 11.13.1.1.1 """
    memberTags = ['CCSTMTTRNRQ', ]


class CREDITCARDMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    memberTags = ['CCSTMTTRNRS', ]

    @property
    def statements(self):
        return [trnrs.ccstmtrs for trnrs in self]


class CREDITCARDMSGSETV1(Aggregate):
    """ OFX section 11.13.3 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    closingavail = Bool(required=True)
    pendingavail = Bool()
    imageprof = Unsupported()


class CREDITCARDMSGSET(Aggregate):
    """ OFX section 11.13.3 """
    creditcardmsgsetv1 = SubAggregate(CREDITCARDMSGSETV1, required=True)
