# coding: utf-8
"""
Data structures for bank wire transfers - OFX Section 11.9
"""
# local imports
from ofxtools.Types import String, Decimal, OneOf, DateTime, Bool, Time
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, List
from ofxtools.models.common import (
    MSGSETCORE,
    TrnRq,
    TrnRs,
    SyncRqList,
    SyncRsList,
)
from ofxtools.models.bank import (BANKACCTFROM, BANKACCTTO)
from ofxtools.models.i18n import (CURRENCY_CODES, COUNTRY_CODES)

__all__ = [
    "WIREBENEFICIARY", "EXTBANKDESC", "WIREDESTBANK",
    "WIRERQ", "WIRERS", "WIRECANRQ", "WIRECANRS",
    "WIRETRNRQ", "WIRETRNRS", "WIRESYNCRQ", "WIRESYNCRS",
    "WIREXFERMSGSRQV1", "WIREXFERMSGSRSV1", "WIREXFERMSGSETV1", "WIREXFERMSGSET",
]


class WIREBENEFICIARY(Aggregate):
    """ OFX section 11.9.1.1.1 """

    name = String(32, required=True)
    bankacctto = SubAggregate(BANKACCTTO, required=True)
    memo = String(255)


class EXTBANKDESC(Aggregate):
    """ OFX section 11.9.1.1.2 """

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
    """ OFX section 11.9.1.1.1 """

    extbankdesc = SubAggregate(EXTBANKDESC, required=True)


class WIRERQ(Aggregate):
    """ OFX section 11.9.1.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    wirebeneficiary = SubAggregate(WIREBENEFICIARY, required=True)
    wiredestbank = SubAggregate(WIREDESTBANK)
    trnamt = Decimal(required=True)
    dtdue = DateTime()
    payinstruct = String(255)


class WIRERS(Aggregate):
    """ OFX section 11.9.1.2 """

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

    optionalMutexes = [("dtxferprj", "dtposted")]


class WIRECANRQ(Aggregate):
    """ OFX section 11.9.2.1"""

    srvrtid = String(10, required=True)


class WIRECANRS(Aggregate):
    """ OFX section 11.9.2.2"""

    srvrtid = String(10, required=True)


class WIRETRNRQ(TrnRq):
    """ OFX section 11.9.2.1 """

    wirerq = SubAggregate(WIRERQ)
    wirecanrq = SubAggregate(WIRECANRQ)

    requiredMutexes = [("wirerq", "wirecanrq")]


class WIRETRNRS(TrnRs):
    """ OFX section 11.9.2.2 """

    wirers = SubAggregate(WIRERS)
    wirecanrs = SubAggregate(WIRECANRS)

    optionalMutexes = [("wirers", "wirecanrs")]


class WIRESYNCRQ(SyncRqList):
    """ OFX section 11.12.4.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dataTags = ["WIRETRNRQ"]


class WIRESYNCRS(SyncRsList):
    """ OFX section 11.12.4.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dataTags = ["WIRETRNRS"]


class WIREXFERMSGSRQV1(List):
    """ OFX section 11.13.1.4.1 """

    dataTags = ["WIRETRNRQ", "WIRESYNCRQ"]


class WIREXFERMSGSRSV1(List):
    """ OFX section 11.13.1.4.2 """

    dataTags = ["WIRETRNRS", "WIRESYNCRS"]


class WIREXFERMSGSETV1(Aggregate):
    """ OFX section 11.13.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    # FIXME
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PROCDAYSOFF.
    procdaysoff = Unsupported()
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class WIREXFERMSGSET(Aggregate):
    """ OFX section 11.13.5 """

    wirexfermsgsetv1 = SubAggregate(WIREXFERMSGSETV1, required=True)
