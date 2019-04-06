# coding: utf-8
"""
Data synchronization for banking - OFX Section 11.12
"""
# local imports
from ofxtools.Types import Bool
from ofxtools.models.base import SubAggregate
from ofxtools.models.wrapperbases import SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM

__all__ = [
    "STPCHKSYNCRQ", "STPCHKSYNCRS",
    "INTRASYNCRQ", "INTRASYNCRS",
    "INTERSYNCRQ", "INTERSYNCRS",
    "WIRESYNCRQ", "WIRESYNCRS",
    "RECINTRASYNCRQ", "RECINTRASYNCRS",
    "RECINTERSYNCRQ", "RECINTERSYNCRS",
    "BANKMAILSYNCRQ", "BANKMAILSYNCRS",
]


class STPCHKSYNCRQ(SyncRqList):
    """ OFX section 11.12.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRQ"]


class STPCHKSYNCRS(SyncRsList):
    """ OFX section 11.12.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRS"]

class INTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["INTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTRASYNCRS(SyncRsList):
    """ OFX section 11.12.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["INTRATRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.3.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["INTERTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRS(SyncRsList):
    """ OFX section 11.12.3.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["INTERTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class WIRESYNCRQ(SyncRqList):
    """ OFX section 11.12.4.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dataTags = ["WIRETRNRQ"]


class WIRESYNCRS(SyncRsList):
    """ OFX section 11.12.4.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dataTags = ["WIRETRNRS"]


class RECINTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["RECINTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTRASYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["RECINTRATRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class RECINTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["RECINTERTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTERSYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["RECINTERTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class BANKMAILSYNCRQ(SyncRqList):
    """ OFX section 11.12.7.1 """

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["BANKMAILTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class BANKMAILSYNCRS(SyncRsList):
    """ OFX section 11.12.7.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    dataTags = ["BANKMAILTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]
