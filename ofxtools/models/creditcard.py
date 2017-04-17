# coding: utf-8
"""
Data structures for credit card download - OFX Section 11
"""
# local imports
from ofxtools.Types import (
    String,
    Decimal,
    OneOf,
)
from ofxtools.models.base import (
    Aggregate,
    List,
    SubAggregate,
    Unsupported,
)
from ofxtools.models.common import (
    STATUS,
)
from ofxtools.models.bank import (
    CCACCTFROM,
    BANKTRANLIST,
    LEDGERBAL, AVAILBAL, BALLIST,
)
from ofxtools.models.i18n import (
    CURRENCY_CODES,
)


class REWARDINFO(Aggregate):
    """ OFX section 11.4.3.2 """
    name = String(32, required=True)
    rewardbal = Decimal(required=True)
    rewardearned = Decimal()


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

    # Human-friendly attribute aliases
    @property
    def currency(self):
        return self.curdef

    @property
    def account(self):
        return self.ccacctfrom

    @property
    def transactions(self):
        return self.banktranlist

    @property
    def balance(self):
        return self.ledgerbal


class CCSTMTTRNRS(Aggregate):
    """ OFX section 11.4.3.2 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    ccstmtrs = SubAggregate(CCSTMTRS)

    @property
    def statement(self):
        return self.ccstmtrs


class CREDITCARDMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    memberTags = ['CCSTMTTRNRS', ]

    @property
    def statements(self):
        return [trnrs.ccstmtrs for trnrs in self]
