# coding: utf-8
"""
Payment mail - OFX Section 12.8
"""


__all__ = [
    "PMTMAILRQ",
    "PMTMAILRS",
    "PMTMAILTRNRQ",
    "PMTMAILTRNRS",
    "PMTMAILSYNCRQ",
    "PMTMAILSYNCRS",
]


from ofxtools.Types import Bool, String, ListAggregate, SubAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.email import MAIL
from ofxtools.models.billpay.common import PMTINFO


class PMTMAILRQ(Aggregate):
    """OFX Section 12.8.1.1"""

    mail = SubAggregate(MAIL, required=True)
    srvrtid = String(10)
    pmtinfo = SubAggregate(PMTINFO)


class PMTMAILRS(Aggregate):
    """OFX Section 12.8.1.2"""

    mail = SubAggregate(MAIL, required=True)
    srvrtid = String(10)
    pmtinfo = SubAggregate(PMTINFO)


class PMTMAILTRNRQ(TrnRq):
    """OFX Section 12.8.1.1"""

    pmtmailrq = SubAggregate(PMTMAILRQ, required=True)


class PMTMAILTRNRS(TrnRs):
    """OFX Section 12.8.1.2"""

    pmtmailrs = SubAggregate(PMTMAILRS)


class PMTMAILSYNCRQ(SyncRqList):
    """OFX Section 12.8.2.1"""

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    pmtmailtrnrq = ListAggregate(PMTMAILTRNRQ)


class PMTMAILSYNCRS(SyncRsList):
    """OFX Section 12.8.2.2"""

    pmtmailtrnrs = ListAggregate(PMTMAILTRNRS)
