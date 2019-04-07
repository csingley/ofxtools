# coding: utf-8
"""
Intrabank funds transfer  - OFX Section 11.6
"""
# local imports
from ofxtools.Types import String, Decimal, OneOf, DateTime
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.bank.stmt import BANKACCTFROM, BANKACCTTO, CCACCTFROM, CCACCTTO
from ofxtools.models.i18n import CURRENCY_CODES


__all__ = [
    "FREQUENCIES",
    "XFERINFO",
    "XFERPRCSTS",
    "INTRARQ",
    "INTRARS",
    "INTRAMODRQ",
    "INTRACANRQ",
    "INTRAMODRS",
    "INTRACANRS",
    "INTRATRNRQ",
    "INTRATRNRS",
]


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


class XFERINFO(Aggregate):
    """ OFX section 11.3.5 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    trnamt = Decimal(required=True)
    dtdue = DateTime()

    requiredMutexes = [("bankacctfrom", "ccacctfrom"), ("bankacctto", "ccacctto")]


class INTRARQ(Aggregate):
    """ OFX section 11.7.1.1 """

    xferinfo = SubAggregate(XFERINFO, required=True)


class XFERPRCSTS(Aggregate):
    """ OFX section 11.3.6 """

    xferprccode = OneOf(
        "WILLPROCESSON",
        "POSTEDON",
        "NOFUNDSON",
        "CANCELEDON",
        "FAILEDON",
        required=True,
    )
    dtxferprc = DateTime(required=True)


class INTRARS(Aggregate):
    """ OFX section 11.7.1.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    dtxferprj = DateTime()
    dtposted = DateTime()
    recsrvrtid = String(10)
    xferprcsts = SubAggregate(XFERPRCSTS)

    optionalMutexes = [("dtxferprj", "dtposted")]


class INTRAMODRQ(Aggregate):
    """ OFX section 11.7.2.1 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)


class INTRACANRQ(Aggregate):
    """ OFX section 11.7.3.1 """

    srvrtid = String(10, required=True)


class INTRAMODRS(Aggregate):
    """ OFX section 11.7.2.2 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    xferprcsts = SubAggregate(XFERPRCSTS)


class INTRACANRS(Aggregate):
    """ OFX section 11.7.3.2 """

    srvrtid = String(10, required=True)


class INTRATRNRQ(TrnRq):
    """ OFX section 11.7.1.1 """

    intrarq = SubAggregate(INTRARQ)
    intramodrq = SubAggregate(INTRAMODRQ)
    intracanrq = SubAggregate(INTRACANRQ)

    requiredMutexes = [("intrarq", "intramodrq", "intracanrq")]


class INTRATRNRS(TrnRs):
    """ OFX section 11.7.1.2 """

    intrars = SubAggregate(INTRARS)
    intramodrs = SubAggregate(INTRAMODRS)
    intracanrs = SubAggregate(INTRACANRS)

    optionalMutexes = [("intrars", "intramodrs", "intracanrs")]
