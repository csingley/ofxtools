# coding: utf-8
"""
Bill pay message sets - OFX Section 12.11
"""


__all__ = ["BILLPAYMSGSRQV1", "BILLPAYMSGSRSV1", "BILLPAYMSGSETV1", "BILLPAYMSGSET"]


# local imports
from ofxtools.Types import (
    Bool,
    Integer,
    Time,
    OneOf,
    ListElement,
    SubAggregate,
    ListAggregate,
)
from ofxtools.models.base import Aggregate, ElementList
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.billpay.pmt import PMTTRNRQ, PMTTRNRS, PMTINQTRNRQ, PMTINQTRNRS
from ofxtools.models.billpay.recur import RECPMTTRNRQ, RECPMTTRNRS
from ofxtools.models.billpay.sync import (
    PMTSYNCRQ,
    PMTSYNCRS,
    PAYEESYNCRQ,
    PAYEESYNCRS,
    RECPMTSYNCRQ,
    RECPMTSYNCRS,
)
from ofxtools.models.billpay.mail import (
    PMTMAILTRNRQ,
    PMTMAILTRNRS,
    PMTMAILSYNCRQ,
    PMTMAILSYNCRS,
)
from ofxtools.models.billpay.list import PAYEETRNRQ, PAYEETRNRS


DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


class BILLPAYMSGSRQV1(Aggregate):
    """OFX section 12.11.1.1"""

    pmttrnrq = ListAggregate(PMTTRNRQ)
    recpmttrnrq = ListAggregate(RECPMTTRNRQ)
    payeetrnrq = ListAggregate(PAYEETRNRQ)
    pmtinqtrnrq = ListAggregate(PMTINQTRNRQ)
    pmtmailtrnrq = ListAggregate(PMTMAILTRNRQ)
    pmtsyncrq = ListAggregate(PMTSYNCRQ)
    recpmtsyncrq = ListAggregate(RECPMTSYNCRQ)
    payeesyncrq = ListAggregate(PAYEESYNCRQ)
    pmtmailsyncrq = ListAggregate(PMTMAILSYNCRQ)


class BILLPAYMSGSRSV1(Aggregate):
    """OFX section 12.11.1.2"""

    pmttrnrs = ListAggregate(PMTTRNRS)
    recpmttrnrs = ListAggregate(RECPMTTRNRS)
    payeetrnrs = ListAggregate(PAYEETRNRS)
    pmtinqtrnrs = ListAggregate(PMTINQTRNRS)
    pmtmailtrns = ListAggregate(PMTMAILTRNRS)
    pmtsyncrs = ListAggregate(PMTSYNCRS)
    recpmtsyncrs = ListAggregate(RECPMTSYNCRS)
    payeesyncrs = ListAggregate(PAYEESYNCRS)
    pmtmailsyncrs = ListAggregate(PMTMAILSYNCRS)


class BILLPAYMSGSETV1(ElementList):
    """OFX section 12.11.2"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    dayswith = Integer(3, required=True)
    dfltdaystopay = Integer(3, required=True)
    xferdayswith = Integer(3, required=True)
    xferdfltdaystopay = Integer(3, required=True)
    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    modelwnd = Integer(3, required=True)
    postprocwnd = Integer(3, required=True)
    stsviamods = Bool(required=True)
    pmtbyaddr = Bool(required=True)
    pmtbyxfer = Bool(required=True)
    pmtbypayeeid = Bool(required=True)
    canaddpayee = Bool(required=True)
    hasextdpmt = Bool(required=True)
    canmodpmts = Bool(required=True)
    canmodmdls = Bool(required=True)
    difffirstpmt = Bool(required=True)
    difflastpmt = Bool(required=True)
    billpubcontext = Bool()


class BILLPAYMSGSET(Aggregate):
    """OFX section 12.11.2"""

    billpaymsgsetv1 = SubAggregate(BILLPAYMSGSETV1, required=True)
