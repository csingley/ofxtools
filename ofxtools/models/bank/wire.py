# coding: utf-8
"""
Wire fund transfers - OFX Section 11.9
"""

__all__ = [
    "WIREBENEFICIARY",
    "EXTBANKDESC",
    "WIREDESTBANK",
    "WIRERQ",
    "WIRERS",
    "WIRECANRQ",
    "WIRECANRS",
    "WIRETRNRQ",
    "WIRETRNRS",
]


# local imports
from ofxtools.Types import String, Decimal, OneOf, DateTime, SubAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.bank.stmt import BANKACCTFROM, BANKACCTTO
from ofxtools.models.i18n import CURRENCY_CODES, COUNTRY_CODES


class WIREBENEFICIARY(Aggregate):
    """OFX section 11.9.1.1.1"""

    name = String(32, required=True)
    bankacctto = SubAggregate(BANKACCTTO, required=True)
    memo = String(255)


class EXTBANKDESC(Aggregate):
    """OFX section 11.9.1.1.2"""

    name = String(32, required=True)
    bankid = String(9, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32)


class WIREDESTBANK(Aggregate):
    """OFX section 11.9.1.1.1"""

    extbankdesc = SubAggregate(EXTBANKDESC, required=True)


class WIRERQ(Aggregate):
    """OFX section 11.9.1.1.1"""

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    wirebeneficiary = SubAggregate(WIREBENEFICIARY, required=True)
    wiredestbank = SubAggregate(WIREDESTBANK)
    trnamt = Decimal(required=True)
    dtdue = DateTime()
    payinstruct = String(255)


class WIRERS(Aggregate):
    """OFX section 11.9.1.2"""

    curdef = OneOf(*CURRENCY_CODES, required=True)
    srvrtid = String(10, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    wirebeneficiary = SubAggregate(WIREBENEFICIARY, required=True)
    wiredestbank = SubAggregate(WIREDESTBANK)
    trnamt = Decimal(required=True)
    dtdue = DateTime()
    payinstruct = String(255)
    dtxferprj = DateTime()
    dtposted = DateTime()
    fee = Decimal()
    confmsg = String(255)

    optionalMutexes = [["dtxferprj", "dtposted"]]


class WIRECANRQ(Aggregate):
    """OFX section 11.9.2.1"""

    srvrtid = String(10, required=True)


class WIRECANRS(Aggregate):
    """OFX section 11.9.2.2"""

    srvrtid = String(10, required=True)


class WIRETRNRQ(TrnRq):
    """OFX section 11.9.2.1"""

    wirerq = SubAggregate(WIRERQ)
    wirecanrq = SubAggregate(WIRECANRQ)

    requiredMutexes = [["wirerq", "wirecanrq"]]


class WIRETRNRS(TrnRs):
    """OFX section 11.9.2.2"""

    wirers = SubAggregate(WIRERS)
    wirecanrs = SubAggregate(WIRECANRS)

    optionalMutexes = [["wirers", "wirecanrs"]]
