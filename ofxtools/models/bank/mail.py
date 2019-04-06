# coding: utf-8
"""
Bank email & customer notification - OFX Section 11.11
"""
# local imports
from ofxtools.Types import String, Decimal, DateTime, Bool
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM
from ofxtools.models.email import MAIL


__all__ = [
    "BANKMAILRQ",
    "BANKMAILRS",
    "DEPMAILRS",
    "CHKMAILRS",
    "BANKMAILTRNRQ",
    "BANKMAILTRNRS",
]


class BANKMAILRQ(Aggregate):
    """ OFX section 11.11.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    mail = SubAggregate(MAIL, required=True)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class BANKMAILRS(Aggregate):
    """ OFX section 11.11.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    mail = SubAggregate(MAIL, required=True)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class CHKMAILRS(Aggregate):
    """ OFX section 11.11.3.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    mail = SubAggregate(MAIL, required=True)
    checknum = String(12, required=True)
    trnamt = Decimal()
    dtuser = DateTime()
    fee = Decimal()


class DEPMAILRS(Aggregate):
    """ OFX section 11.11.3.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    mail = SubAggregate(MAIL, required=True)
    trnamt = Decimal(required=True)
    dtuser = DateTime()
    fee = Decimal()


class BANKMAILTRNRQ(TrnRq):
    """ OFX section 11.11.1.1 """

    bankmailrq = SubAggregate(BANKMAILRQ, required=True)


class BANKMAILTRNRS(TrnRs):
    """ OFX section 11.11.1.2 """

    bankmailrs = SubAggregate(BANKMAILRS)
    chkmailrs = SubAggregate(CHKMAILRS)
    depmailrs = SubAggregate(DEPMAILRS)

    optionalMutexes = [("bankmailrs", "chkmailrs", "depmailrs")]
