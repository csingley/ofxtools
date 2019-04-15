# coding: utf-8
"""
email - OFX Section 9
"""
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import Bool, String, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.billpay import (
    PMTTRNRQ, PMTTRNRS, RECPMTTRNRQ, RECPMTTRNRS, PAYEETRNRQ, PAYEETRNRS,
)


__all__ = [
    "PMTSYNCRQ", "PMTSYNCRS", "RECPMTSYNCRQ", "RECPMTSYNCRS", "PAYEESYNCRQ", "PAYEESYNCRS",
]


class PMTSYNCRQ(SyncRqList):
    """ OFX Section 12.10.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    pmttrnrq = ListItem(PMTTRNRQ)


class PMTSYNCRS(SyncRsList):
    """ OFX Section 12.10.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    pmttrnrs = ListItem(PMTTRNRS)


class RECPMTSYNCRQ(SyncRqList):
    """ OFX Section 12.10.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    recpmttrnrq = ListItem(RECPMTTRNRQ)


class RECPMTSYNCRS(SyncRsList):
    """ OFX Section 12.10.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    recpmttrnrs = ListItem(RECPMTTRNRS)


class PAYEESYNCRQ(SyncRqList):
    """ OFX Section 12.9.4.1 """
    payeetrnrq = ListItem(PAYEETRNRQ)


class PAYEESYNCRS(SyncRsList):
    """ OFX Section 12.9.4.2 """
    payeetrnrs = ListItem(PAYEETRNRS)
