# coding: utf-8
"""
Data synchronization for payments - OFX Section 12.10
"""


__all__ = [
    "PMTSYNCRQ",
    "PMTSYNCRS",
    "RECPMTSYNCRQ",
    "RECPMTSYNCRS",
    "PAYEESYNCRQ",
    "PAYEESYNCRS",
]


# local imports
from ofxtools.Types import ListAggregate, SubAggregate
from ofxtools.models.wrapperbases import SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.billpay.pmt import PMTTRNRQ, PMTTRNRS
from ofxtools.models.billpay.recur import RECPMTTRNRQ, RECPMTTRNRS
from ofxtools.models.billpay.list import PAYEETRNRQ, PAYEETRNRS


class PMTSYNCRQ(SyncRqList):
    """OFX Section 12.10.1.1"""

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    pmttrnrq = ListAggregate(PMTTRNRQ)


class PMTSYNCRS(SyncRsList):
    """OFX Section 12.10.1.2"""

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    pmttrnrs = ListAggregate(PMTTRNRS)


class RECPMTSYNCRQ(SyncRqList):
    """OFX Section 12.10.2.1"""

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    recpmttrnrq = ListAggregate(RECPMTTRNRQ)


class RECPMTSYNCRS(SyncRsList):
    """OFX Section 12.10.2.2"""

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    recpmttrnrs = ListAggregate(RECPMTTRNRS)


class PAYEESYNCRQ(SyncRqList):
    """OFX Section 12.9.4.1"""

    payeetrnrq = ListAggregate(PAYEETRNRQ)


class PAYEESYNCRS(SyncRsList):
    """OFX Section 12.9.4.2"""

    payeetrnrs = ListAggregate(PAYEETRNRS)
