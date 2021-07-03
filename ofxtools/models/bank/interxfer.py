# coding: utf-8
"""
Interbank fund transfers - OFX Section 11.8
"""


__all__ = [
    "INTERRQ",
    "INTERRS",
    "INTERMODRQ",
    "INTERCANRQ",
    "INTERMODRS",
    "INTERCANRS",
    "INTERTRNRQ",
    "INTERTRNRS",
]


# local imports
from ofxtools.Types import String, OneOf, DateTime, SubAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.bank.xfer import XFERINFO, XFERPRCSTS
from ofxtools.models.i18n import CURRENCY_CODES


class INTERRQ(Aggregate):
    """OFX section 11.8.2.1"""

    xferinfo = SubAggregate(XFERINFO, required=True)


class INTERRS(Aggregate):
    """OFX section 11.8.2.2"""

    curdef = OneOf(*CURRENCY_CODES, required=True)
    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    dtxferprj = DateTime()
    dtposted = DateTime()
    refnum = String(32)
    recsrvrtid = String(10)
    xferprcsts = SubAggregate(XFERPRCSTS)

    optionalMutexes = [["dtxferprj", "dtposted"]]


class INTERMODRQ(Aggregate):
    """OFX section 11.8.3.1"""

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)


class INTERCANRQ(Aggregate):
    """OFX section 11.8.4.1"""

    srvrtid = String(10, required=True)


class INTERMODRS(Aggregate):
    """OFX section 11.8.3.2"""

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    xferprcsts = SubAggregate(XFERPRCSTS)


class INTERCANRS(Aggregate):
    """OFX section 11.8.4.2"""

    srvrtid = String(10, required=True)


class INTERTRNRQ(TrnRq):
    """OFX section 11.8.2.1"""

    interrq = SubAggregate(INTERRQ)
    intermodrq = SubAggregate(INTERMODRQ)
    intercanrq = SubAggregate(INTERCANRQ)

    requiredMutexes = [["interrq", "intermodrq", "intercanrq"]]


class INTERTRNRS(TrnRs):
    """OFX section 11.8.2.2"""

    interrs = SubAggregate(INTERRS)
    intermodrs = SubAggregate(INTERMODRS)
    intercanrs = SubAggregate(INTERCANRS)

    optionalMutexes = [["interrs", "intermodrs", "intercanrs"]]
