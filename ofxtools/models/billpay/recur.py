# coding: utf-8
"""
Recurring payments - OFX Section 12.7
"""


__all__ = [
    "RECPMTRQ",
    "RECPMTRS",
    "RECPMTMODRQ",
    "RECPMTMODRS",
    "RECPMTCANCRQ",
    "RECPMTCANCRS",
    "RECPMTTRNRQ",
    "RECPMTTRNRS",
]


from ofxtools.Types import Bool, String, Decimal, OneOf, SubAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.models.billpay.common import PMTINFO, EXTDPAYEE
from ofxtools.models.bank.recur import RECURRINST


class RECPMTRQ(Aggregate):
    """OFX Section 12.7.1.1"""

    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()


class RECPMTRS(Aggregate):
    """OFX Section 12.7.1.2"""

    recsrvrtid = String(10, required=True)
    payeelstid = String(12, required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    extdpayee = SubAggregate(EXTDPAYEE)


class RECPMTMODRQ(Aggregate):
    """OFX Section 12.7.2.1"""

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    modpending = Bool(required=True)


class RECPMTMODRS(Aggregate):
    """OFX Section 12.7.2.1"""

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    initialamt = Decimal()
    finalamt = Decimal()
    modpending = Bool(required=True)


class RECPMTCANCRQ(Aggregate):
    """OFX Section 12.7.3.1"""

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECPMTCANCRS(Aggregate):
    """OFX Section 12.7.3.2"""

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECPMTTRNRQ(TrnRq):
    """OFX Section 12.7.1.1"""

    recpmtrq = SubAggregate(RECPMTRQ)
    recpmtmodrq = SubAggregate(RECPMTMODRQ)
    recpmtcancrq = SubAggregate(RECPMTCANCRQ)

    requiredMutexes = [["recpmtrq", "recpmtmodrq", "recpmtcancrq"]]


class RECPMTTRNRS(TrnRs):
    """OFX Section 12.7.1.2"""

    recpmtrs = SubAggregate(RECPMTRS)
    recpmtmodrs = SubAggregate(RECPMTMODRS)
    recpmtcancrs = SubAggregate(RECPMTCANCRS)

    optionalMutexes = [["recpmtrs", "recpmtmodrs", "recpmtcancrs"]]
