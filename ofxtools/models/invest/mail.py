# coding: utf-8
"""
Investment Email - OFX Section 13.10
"""
# local imports
from ofxtools.Types import Bool, SubAggregate, ListAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.email import MAIL
from ofxtools.models.invest.acct import INVACCTFROM


class INVMAILRQ(Aggregate):
    """OFX Section 13.10.1.1"""

    invacctfrom = SubAggregate(INVACCTFROM)
    mail = SubAggregate(MAIL)


class INVMAILRS(Aggregate):
    """OFX Section 13.10.1.2"""

    invacctfrom = SubAggregate(INVACCTFROM)
    mail = SubAggregate(MAIL)


class INVMAILTRNRQ(TrnRq):
    invmailrq = SubAggregate(INVMAILRQ)


class INVMAILTRNRS(TrnRs):
    invmailrs = SubAggregate(INVMAILRS)


class INVMAILSYNCRQ(SyncRqList):
    """OFX Section 13.10.2.1"""

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    invacctfrom = SubAggregate(INVACCTFROM)
    invmailtrnrq = ListAggregate(INVMAILTRNRQ)


class INVMAILSYNCRS(SyncRsList):
    """OFX Section 13.10.2.2"""

    invacctfrom = SubAggregate(INVACCTFROM)
    invmailtrnrs = ListAggregate(INVMAILTRNRS)
