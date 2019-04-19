# coding: utf-8
"""
Payments Functions - OFX Section 12.6
"""
from ofxtools.Types import String, OneOf
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.models.billpay.common import PMTINFO, EXTDPAYEE, PMTPRCSTS


__all__ = [
    "PMTRQ", "PMTRS",
    "PMTMODRQ", "PMTMODRS",
    "PMTCANCRQ", "PMTCANCRS",
    "PMTTRNRQ", "PMTTRNRS",
    "PMTINQRQ", "PMTINQRS",
    "PMTINQTRNRQ", "PMTINQTRNRS",
]


class PMTRQ(Aggregate):
    """ OFX section 12.6.1.1 """
    pmtinfo = SubAggregate(PMTINFO, required=True)


class PMTRS(Aggregate):
    """ OFX section 12.6.1.2 """
    srvrtid = String(10, required=True)
    payeelstid = String(12, required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    extdpayee = SubAggregate(EXTDPAYEE)
    checknum = String(12)
    pmtprcsts = SubAggregate(PMTPRCSTS, required=True)
    recsrvrtid = String(10)


class PMTMODRQ(Aggregate):
    """ OFX section 12.6.2.2 """
    srvrtid = String(10, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)


class PMTMODRS(Aggregate):
    """ OFX section 12.6.2.3 """
    srvrtid = String(10, required=True)
    pmtinfo = SubAggregate(PMTINFO, required=True)
    pmtprcsts = SubAggregate(PMTPRCSTS)


class PMTCANCRQ(Aggregate):
    """ OFX section 12.6.3.1 """
    srvrtid = String(10, required=True)


class PMTCANCRS(Aggregate):
    """ OFX section 12.6.3.2 """
    srvrtid = String(10, required=True)


class PMTTRNRQ(TrnRq):
    pmtrq = SubAggregate(PMTRQ)
    pmtmodrq = SubAggregate(PMTMODRQ)
    pmtcancrq = SubAggregate(PMTCANCRQ)

    requiredMutexes = [('pmtrq', 'pmtmodrq', 'pmtcancrq')]


class PMTTRNRS(TrnRs):
    pmtrs = SubAggregate(PMTRS)
    pmtmodrs = SubAggregate(PMTMODRS)
    pmtcancrs = SubAggregate(PMTCANCRS)

    optionalMutexes = [('pmtrs', 'pmtmodrs', 'pmtcancrs')]


class PMTINQRQ(Aggregate):
    """ OFX section 12.6.4.1 """
    srvrtid = String(10, required=True)


class PMTINQRS(Aggregate):
    """ OFX section 12.6.4.2 """
    srvrtid = String(10, required=True)
    pmtprcsts = SubAggregate(PMTPRCSTS, required=True)
    checknum = String(12)


class PMTINQTRNRQ(TrnRq):
    pmtinqrq = SubAggregate(PMTINQRQ, required=True)


class PMTINQTRNRS(TrnRs):
    pmtinqrs = SubAggregate(PMTINQRS)
