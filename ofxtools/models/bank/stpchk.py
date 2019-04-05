# coding: utf-8
"""
Bank stop check - OFX Section 11.6
"""
# local imports
from ofxtools.Types import String, Decimal, OneOf, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, List
from ofxtools.models.common import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.i18n import CURRENCY, ORIGCURRENCY, Origcurrency, CURRENCY_CODES


__all__ = [
    "CHKRANGE", "CHKDESC", "STPCHKNUM", "STPCHKRQ", "STPCHKRS",
    "STPCHKTRNRQ", "STPCHKTRNRS", "STPCHKSYNCRQ", "STPCHKSYNCRS",
]


class CHKRANGE(Aggregate):
    """ OFX section 11.6.1.1.1 """

    chknumstart = String(12, required=True)
    chknumend = String(12)


class CHKDESC(Aggregate):
    """ OFX section 11.6.1.1.2 """

    name = String(32, required=True)
    chknum = String(12)
    dtuser = DateTime()
    trnamt = Decimal()


class STPCHKRQ(Aggregate):
    """ OFX section 11.6.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    chkrange = SubAggregate(CHKRANGE)
    chkdesc = SubAggregate(CHKDESC)

    requiredMutexes = [("chkrange", "chkdesc")]


class STPCHKNUM(Aggregate, Origcurrency):
    """ OFX section 11.6.1.2.1 """

    checknum = String(12, required=True)
    name = String(32)
    dtuser = DateTime()
    trnamt = Decimal()
    chkstatus = OneOf("0", "1", "100", "101", required=True)
    chkerror = String(255)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)

    optionalMutexes = [("currency", "origcurrency")]


class STPCHKRS(List):
    """ OFX section 11.6.1.1 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    fee = Decimal(required=True)
    feemsg = String(80, required=True)

    dataTags = ["STPCHKNUM"]


class STPCHKTRNRQ(TrnRq):
    """ OFX section 11.6.1.1 """

    stpchkrq = SubAggregate(STPCHKRQ, required=True)


class STPCHKTRNRS(TrnRs):
    """ OFX section 11.6.1.2 """

    stpchkrs = SubAggregate(STPCHKRS)


class STPCHKSYNCRQ(SyncRqList):
    """ OFX section 11.12.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRQ"]


class STPCHKSYNCRS(SyncRsList):
    """ OFX section 11.12.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRS"]
