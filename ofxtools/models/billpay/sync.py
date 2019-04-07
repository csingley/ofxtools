# coding: utf-8
"""
email - OFX Section 9
"""
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import Bool, String, DateTime
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import BANKACCTFROM


__all__ = ["PMTSYNCRQ", "PMTSYNCRS", "RECPMTSYNCRQ", "RECPMTSYNCRS"]


class PMTSYNCRQ(SyncRqList):
    """ OFX Section 12.10.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["PMTTRNRQ"]


class PMTSYNCRS(SyncRsList):
    """ OFX Section 12.10.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["PMTTRNRS"]


class RECPMTSYNCRQ(SyncRqList):
    """ OFX Section 12.10.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["RECPMTTRNRQ"]


class RECPMTSYNCRS(SyncRsList):
    """ OFX Section 12.10.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["RECPMTTRNRS"]
