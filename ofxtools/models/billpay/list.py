# coding: utf-8
"""
Payee lists - OFX Section 12.9
"""
from ofxtools.Types import String, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import PAYEE, BANKACCTTO
from ofxtools.models.billpay import (
    EXTDPAYEE,
    #  PAYEETRNRQ,
    #  PAYEETRNRS,
)


__all__ = [
    "PAYEERQ",
    "PAYEERS",
    "PAYEEMODRQ",
    "PAYEEMODRS",
    "PAYEEDELRQ",
    "PAYEEDELRS",
    "PAYEETRNRQ",
    "PAYEETRNRS",
    #  "PAYEESYNCRQ",
    #  "PAYEESYNCRS",
]


class PAYEERQ(Aggregate):
    """ OFX Section 12.9.1.1 """
    payeeid = String(12)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    # FIXME - "O or more"
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PAYACCT.
    payacct = String(32)

    requiredMutexes = [("payeeid", "payee")]


class PAYEERS(Aggregate):
    """ OFX Section 12.9.1.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    extdpayee = SubAggregate(EXTDPAYEE)
    # FIXME - "O or more"
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PAYACCT.
    payacct = String(32)


class PAYEEMODRQ(Aggregate):
    """ OFX Section 12.9.2.1 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    # FIXME - "O or more"
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PAYACCT.
    payacct = String(32)


class PAYEEMODRS(Aggregate):
    """ OFX Section 12.9.2.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    # FIXME - "O or more"
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PAYACCT.
    payacct = String(32)
    extdpayee = SubAggregate(EXTDPAYEE)


class PAYEEDELRQ(Aggregate):
    """ OFX Section 12.9.3.1 """
    payeelstid = String(12, required=True)


class PAYEEDELRS(Aggregate):
    """ OFX Section 12.9.3.1 """
    payeelstid = String(12, required=True)


class PAYEETRNRQ(TrnRq):
    payeerq = SubAggregate(PAYEERQ)
    payeemodrq = SubAggregate(PAYEEMODRQ)
    payeedelrq = SubAggregate(PAYEEDELRQ)

    requiredMutexes = [('payeerq', 'payeemodrq', 'payeedelrq')]


class PAYEETRNRS(TrnRs):
    payeers = SubAggregate(PAYEERS)
    payeemodrs = SubAggregate(PAYEEMODRS)
    payeedelrs = SubAggregate(PAYEEDELRS)

    optionalMutexes = [('payeerq', 'payeemodrq', 'payeedelrq')]
