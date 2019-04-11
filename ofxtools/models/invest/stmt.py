# coding: utf-8
"""
Investments - OFX Section 13
"""
from ofxtools.Types import Bool, String, OneOf, Decimal, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.invest.acct import INVACCTFROM
from ofxtools.models.invest.transactions import INVTRANLIST
from ofxtools.models.invest.positions import INVPOSLIST
from ofxtools.models.invest.openorders import INVOOLIST
from ofxtools.models.bank.stmt import INCTRAN, BALLIST
from ofxtools.models.i18n import CURRENCY_CODES


__all__ = [
    "INCPOS", "INVSTMTRQ", "INVBAL", "INV401KBAL", "INVSTMTRS",
    "INVSTMTTRNRQ", "INVSTMTTRNRS",
]


class INCPOS(Aggregate):
    """ OFX section 13.9.1.2 """

    dtasof = DateTime()
    include = Bool(required=True)


class INVSTMTRQ(Aggregate):
    """ OFX section 13.9.1.2 """

    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    incoo = Bool(required=True)
    incpos = SubAggregate(INCPOS, required=True)
    incbal = Bool(required=True)
    inc401k = Bool()
    inc401kbal = Bool()
    inctranimg = Bool()


class INVBAL(Aggregate):
    """ OFX section 13.9.2.7 """

    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()
    ballist = SubAggregate(BALLIST)


class INV401KBAL(Aggregate):
    """ OFX section 13.9.2.9 """

    cashbal = Decimal()
    pretax = Decimal()
    aftertax = Decimal()
    match = Decimal()
    profitsharing = Decimal()
    rollover = Decimal()
    othervest = Decimal()
    othernonvest = Decimal()
    total = Decimal(required=True)
    ballist = SubAggregate(BALLIST)


class INVSTMTRS(Aggregate):
    """ OFX section 13.9.2.1 """

    dtasof = DateTime(required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)
    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    invtranlist = SubAggregate(INVTRANLIST)
    invposlist = SubAggregate(INVPOSLIST)
    invbal = SubAggregate(INVBAL)
    invoolist = SubAggregate(INVOOLIST)
    mktginfo = String(360)
    inv401k = Unsupported()
    inv401kbal = SubAggregate(INV401KBAL)

    @property
    def account(self):
        return self.invacctfrom

    @property
    def transactions(self):
        return self.invtranlist

    @property
    def positions(self):
        return self.invposlist

    @property
    def balances(self):
        return self.invbal


class INVSTMTTRNRQ(TrnRq):
    """ OFX section 13.9.1.1 """

    invstmtrq = SubAggregate(INVSTMTRQ, required=True)


class INVSTMTTRNRS(TrnRs):
    """ OFX section 13.9.2.1 """

    invstmtrs = SubAggregate(INVSTMTRS)

    @property
    def statement(self):
        return self.invstmtrs
