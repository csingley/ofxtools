# coding: utf-8
"""
Recurring funds transfer - OFX Section 11.10
"""


__all__ = [
    "FREQUENCIES",
    "RECURRINST",
    "RECINTRARQ",
    "RECINTRARS",
    "RECINTRAMODRQ",
    "RECINTRAMODRS",
    "RECINTRACANRQ",
    "RECINTRACANRS",
    "RECINTRATRNRQ",
    "RECINTRATRNRS",
    "RECINTERRQ",
    "RECINTERRS",
    "RECINTERMODRQ",
    "RECINTERMODRS",
    "RECINTERCANRQ",
    "RECINTERCANRS",
    "RECINTERTRNRQ",
    "RECINTERTRNRS",
]


# local imports
from ofxtools.Types import String, Integer, OneOf, Bool
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.bank.xfer import INTRARQ, INTRARS
from ofxtools.models.bank.interxfer import INTERRQ, INTERRS


FREQUENCIES = (
    "WEEKLY",
    "BIWEEKLY",
    "TWICEMONTHLY",
    "MONTHLY",
    "FOURWEEKS",
    "BIMONTHLY",
    "QUARTERLY",
    "SEMIANNUALLY",
    "ANNUALLY",
)


class RECURRINST(Aggregate):
    """ OFX section 10.2 """

    ninsts = Integer(3)
    freq = OneOf(*FREQUENCIES, required=True)


class RECINTRARQ(Aggregate):
    """ OFX section 11.10.1.1 """

    recurrinst = SubAggregate(RECURRINST, required=True)
    intrarq = SubAggregate(INTRARQ, required=True)


class RECINTRARS(Aggregate):
    """ OFX section 11.10.1.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrars = SubAggregate(INTRARS, required=True)


class RECINTRAMODRQ(Aggregate):
    """ OFX section 11.10.2.1 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrarq = SubAggregate(INTRARQ, required=True)
    modpending = Bool(required=True)


class RECINTRAMODRS(Aggregate):
    """ OFX section 11.10.2.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrars = SubAggregate(INTRARS, required=True)
    modpending = Bool(required=True)


class RECINTRACANRQ(Aggregate):
    """ OFX section 11.10.3.1 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTRACANRS(Aggregate):
    """ OFX section 11.10.3.2 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTRATRNRQ(TrnRq):
    """ OFX section 11.10.1.1 """

    recintrarq = SubAggregate(RECINTRARQ)
    recintramodrq = SubAggregate(RECINTRAMODRQ)
    recintracanrq = SubAggregate(RECINTRACANRQ)

    requiredMutexes = [
        ["recintrarq", "recintramodrq", "recintracanrq"],
    ]


class RECINTRATRNRS(TrnRs):
    """ OFX section 11.10.1.2 """

    recintrars = SubAggregate(RECINTRARS)
    recintramodrs = SubAggregate(RECINTRAMODRS)
    recintracanrs = SubAggregate(RECINTRACANRS)

    optionalMutexes = [
        ["recintrars", "recintramodrs", "recintracanrs"],
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

    requiredMutexes = [
        ["recinterrq", "recintermodrq", "recintercanrq"],
    ]


class RECINTERTRNRS(TrnRs):
    """ OFX section 11.10.5.2 """

    recinterrs = SubAggregate(RECINTERRS)
    recintermodrs = SubAggregate(RECINTERMODRS)
    recintercanrs = SubAggregate(RECINTERCANRS)

    optionalMutexes = [
        ["recinterrs", "recintermodrs", "recintercanrs"],
    ]
