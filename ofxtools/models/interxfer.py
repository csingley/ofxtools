# coding: utf-8
"""
Data structures for interbank ACH transfers - OFX Section 11.8
"""
# stdlib imports
import unittest
from copy import deepcopy
# local imports
from ofxtools.Types import String, Decimal, Integer, OneOf, DateTime, Bool
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, List
from ofxtools.models.common import (
    MSGSETCORE, SVCSTATUSES, TrnRq, TrnRs, TranList, SyncRqList, SyncRsList,
)
from ofxtools.models.bank import (
    BANKACCTFROM, CCACCTFROM, XFERINFO, XFERPRCSTS, XFERPROF, RECURRINST,
)
from ofxtools.models.i18n import CURRENCY_CODES

__all__ = [
    "INTERRQ", "INTERRS", "INTERMODRQ", "INTERCANRQ", "INTERMODRS", "INTERCANRS",
    "INTERTRNRQ", "INTERTRNRS", "INTERSYNCRQ", "INTERSYNCRS",
    "RECINTERRQ", "RECINTERRS",
    "RECINTERMODRQ", "RECINTERMODRS", "RECINTERCANRQ", "RECINTERCANRS",
    "RECINTERTRNRQ", "RECINTERTRNRS", "RECINTERSYNCRQ", "RECINTERSYNCRS",
    "INTERXFERMSGSRQV1", "INTERXFERMSGSRSV1", "INTERXFERMSGSETV1", "INTERXFERMSGSET",
]


class INTERRQ(Aggregate):
    """ OFX section 11.8.2.1 """

    xferinfo = SubAggregate(XFERINFO, required=True)


class INTERRS(Aggregate):
    """ OFX section 11.8.2.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    dtxferprj = DateTime()
    dtposted = DateTime()
    refnum = String(32)
    recsrvrtid = String(10)
    xferprcsts = SubAggregate(XFERPRCSTS)

    optionalMutexes = [("dtxferprj", "dtposted")]


class INTERMODRQ(Aggregate):
    """ OFX section 11.8.3.1 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)


class INTERCANRQ(Aggregate):
    """ OFX section 11.8.4.1"""

    srvrtid = String(10, required=True)


class INTERMODRS(Aggregate):
    """ OFX section 11.8.3.2 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    xferprcsts = SubAggregate(XFERPRCSTS)


class INTERCANRS(Aggregate):
    """ OFX section 11.8.4.2 """

    srvrtid = String(10, required=True)


class INTERTRNRQ(TrnRq):
    """ OFX section 11.8.2.1 """

    interrq = SubAggregate(INTERRQ)
    intermodrq = SubAggregate(INTERMODRQ)
    intercanrq = SubAggregate(INTERCANRQ)

    requiredMutexes = [("interrq", "intermodrq", "intercanrq")]


class INTERTRNRS(TrnRs):
    """ OFX section 11.8.2.2 """

    interrs = SubAggregate(INTERRS)
    intermodrs = SubAggregate(INTERMODRS)
    intercanrs = SubAggregate(INTERCANRS)

    optionalMutexes = [
        ("interrs", "intermodrs", "intercanrs")
    ]


class RECINTERRQ(Aggregate):
    """ OFX section 11.10.4.1 """

    recurrinst = SubAggregate(RECURRINST, required=True)
    interrq = SubAggregate(INTERRQ, required=True)


class RECINTERRS(Aggregate):
    """ OFX section 11.10.4.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    interrs = SubAggregate(INTERRS, required=True)


class RECINTERMODRQ(Aggregate):
    """ OFX section 11.10.5.1 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    interrq = SubAggregate(INTERRQ, required=True)
    modpending = Bool(required=True)


class RECINTERMODRS(Aggregate):
    """ OFX section 11.10.5.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    interrs = SubAggregate(INTERRS, required=True)
    modpending = Bool(required=True)


class RECINTERCANRQ(Aggregate):
    """ OFX section 11.10.6.1 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTERCANRS(Aggregate):
    """ OFX section 11.10.6.2 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTERTRNRQ(TrnRq):
    """ OFX section 11.10.5.1 """

    recinterrq = SubAggregate(RECINTERRQ)
    recintermodrq = SubAggregate(RECINTERMODRQ)
    recintercanrq = SubAggregate(RECINTERCANRQ)

    requiredMutexes = [("recinterrq", "recintermodrq", "recintercanrq")]


class RECINTERTRNRS(TrnRs):
    """ OFX section 11.10.5.2 """

    recinterrs = SubAggregate(RECINTERRS)
    recintermodrs = SubAggregate(RECINTERMODRS)
    recintercanrs = SubAggregate(RECINTERCANRS)

    optionalMutexes = [("recinterrs", "recintermodrs", "recintercanrs")]


class RECINTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTERTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTERSYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTERTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.3.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTERTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRS(SyncRsList):
    """ OFX section 11.12.3.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTERTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class INTERXFERMSGSRQV1(List):
    """ OFX section 11.13.1.3.1 """

    dataTags = [
        "INTERTRNRQ",
        "RECINTERTRNRQ",
        "INTERSYNCRQ",
        "RECINTERSYNCRQ",
    ]


class INTERXFERMSGSRSV1(List):
    """ OFX section 11.13.1.3.2 """

    dataTags = [
        "INTERTRNRS",
        "RECINTERTRNRS",
        "INTERSYNCRS",
        "RECINTERSYNCRS",
    ]


class INTERXFERMSGSETV1(Aggregate):
    """ OFX section 11.13.4 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    xferprof = SubAggregate(XFERPROF, required=True)
    canbillpay = Bool(required=True)
    cancwnd = Integer(3, required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class INTERXFERMSGSET(Aggregate):
    """ OFX section 11.13.4 """

    interxfermsgsetv1 = SubAggregate(INTERXFERMSGSETV1, required=True)
