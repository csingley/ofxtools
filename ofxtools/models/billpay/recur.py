# coding: utf-8
"""
Recurring payments - OFX Section 12.7
"""
from ofxtools.Types import Bool, String, Decimal
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.billpay.common import PMTINFO, EXTDPAYEE
from ofxtools.models.bank.recur import RECURRINST


__all__ = [
    "RECPMTRQ", "RECPMTRS",
    "RECPMTMODRQ", "RECPMTMODRS",
    "RECPMTCANRQ", "RECPMTCANRS",
    "RECPMTTRNRQ", "RECPMTTRNRS",
]

class RECPMTRQ(Aggregate):
    """ OFX Section 12.7.1.1 """
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()


class RECPMTRS(Aggregate):
    """ OFX Section 12.7.1.2 """
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    extdpayee = SubAggregate(EXTDPAYEE)


class RECPMTMODRQ(Aggregate):
    """ OFX Section 12.7.2.1 """
    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    modpending = Bool(required=True)


class RECPMTMODRS(Aggregate):
    """ OFX Section 12.7.2.1 """
    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    modpending = Bool(required=True)


class RECPMTCANRQ(Aggregate):
    """ OFX Section 12.7.3.1 """
    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECPMTCANRS(Aggregate):
    """ OFX Section 12.7.3.1 """
    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECPMTTRNRQ(TrnRq):
    recpmtrq = SubAggregate(RECPMTRQ)
    recpmtmodrq = SubAggregate(RECPMTMODRQ)
    recpmtcanrq = SubAggregate(RECPMTCANRQ)

    requiredMutexes = [('recpmtrq', 'recpmtmodrq', 'recpmtcanrq')]


class RECPMTTRNRS(TrnRs):
    recpmtrs = SubAggregate(RECPMTRS)
    recpmtmodrs = SubAggregate(RECPMTMODRS)
    recpmtcanrs = SubAggregate(RECPMTCANRS)

    optionalMutexes = [('recpmtrs', 'recpmtmodrs', 'recpmtcanrs')]
