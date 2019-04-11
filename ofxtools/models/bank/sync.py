# coding: utf-8
"""
Data synchronization for banking - OFX Section 11.12
"""
# local imports
from ofxtools.Types import Bool, ListItem
from ofxtools.models.base import SubAggregate
from ofxtools.models.wrapperbases import SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM
from ofxtools.models.bank.xfer import INTRATRNRQ, INTRATRNRS
from ofxtools.models.bank.interxfer import INTERTRNRQ, INTERTRNRS
from ofxtools.models.bank.wire import WIRETRNRQ, WIRETRNRS
from ofxtools.models.bank.recur import (
    RECINTRATRNRQ, RECINTRATRNRS, RECINTERTRNRQ, RECINTERTRNRS,
)
from ofxtools.models.bank.mail import BANKMAILTRNRQ, BANKMAILTRNRS
from ofxtools.models.bank.stpchk import STPCHKTRNRQ, STPCHKTRNRS

__all__ = [
    "STPCHKSYNCRQ",
    "STPCHKSYNCRS",
    "INTRASYNCRQ",
    "INTRASYNCRS",
    "INTERSYNCRQ",
    "INTERSYNCRS",
    "WIRESYNCRQ",
    "WIRESYNCRS",
    "RECINTRASYNCRQ",
    "RECINTRASYNCRS",
    "RECINTERSYNCRQ",
    "RECINTERSYNCRS",
    "BANKMAILSYNCRQ",
    "BANKMAILSYNCRS",
]


class STPCHKSYNCRQ(SyncRqList):
    """ OFX section 11.12.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    stpchktrnrq = ListItem(STPCHKTRNRQ)


class STPCHKSYNCRS(SyncRsList):
    """ OFX section 11.12.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    stpchktrnrs = ListItem(STPCHKTRNRS)


class INTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    intratrnrq = ListItem(INTRATRNRQ)

    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTRASYNCRS(SyncRsList):
    """ OFX section 11.12.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    intratrnrs = ListItem(INTRATRNRS)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.3.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    intertrnrq = ListItem(INTERTRNRQ)

    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTERSYNCRS(SyncRsList):
    """ OFX section 11.12.3.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    intertrnrs = ListItem(INTERTRNRS)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class WIRESYNCRQ(SyncRqList):
    """ OFX section 11.12.4.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    wiretrnrq = ListItem(WIRETRNRQ)


class WIRESYNCRS(SyncRsList):
    """ OFX section 11.12.4.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    wiretrnrs = ListItem(WIRETRNRS)


class RECINTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    recintratrnrq = ListItem(RECINTRATRNRQ)

    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTRASYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    recintratrnrs = ListItem(RECINTRATRNRS)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class RECINTERSYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    recintertrnrq = ListItem(RECINTERTRNRQ)

    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTERSYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    recintertrnrs = ListItem(RECINTERTRNRS)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class BANKMAILSYNCRQ(SyncRqList):
    """ OFX section 11.12.7.1 """

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    bankmailtrnrq = ListItem(BANKMAILTRNRQ)

    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class BANKMAILSYNCRS(SyncRsList):
    """ OFX section 11.12.7.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    bankmailtrnrs = ListItem(BANKMAILTRNRS)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]
