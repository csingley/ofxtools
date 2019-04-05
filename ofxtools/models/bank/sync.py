# coding: utf-8
"""
Data synchronization for banking - OFX Section 11.12
"""
# local imports
from ofxtools.models.base import SubAggregate
from ofxtools.models.common import SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM

__all__ = [
    "INTRASYNCRQ", "INTRASYNCRS",
    "INTERSYNCRQ", "INTERSYNCRS",
    "WIRESYNCRQ", "WIRESYNCRS",
    "RECINTRASYNCRQ", "RECINTRASYNCRS",
    "RECINTERSYNCRQ", "RECINTERSYNCRS",
]


class INTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTRASYNCRS(SyncRsList):
    """ OFX section 11.12.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTRATRNRS"]
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

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTRASYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTRATRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


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


