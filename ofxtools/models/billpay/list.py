# coding: utf-8
"""
Payee lists - OFX Section 12.9
"""
from ofxtools.Types import String, ListItem, ListElement
from ofxtools.models.base import Aggregate, SubAggregate, ElementList
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


class PAYEERQ(ElementList):
    """ OFX Section 12.9.1.1 """
    payeeid = String(12)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = ListElement(String(32))

    requiredMutexes = [("payeeid", "payee")]


class PAYEERS(ElementList):
    """ OFX Section 12.9.1.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    extdpayee = SubAggregate(EXTDPAYEE)
    payacct = ListElement(String(32))


class PAYEEMODRQ(ElementList):
    """ OFX Section 12.9.2.1 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = ListElement(String(32))


class PAYEEMODRS(ElementList):
    """ OFX Section 12.9.2.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = ListElement(String(32))
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

    optionalMutexes = [('payeers', 'payeemodrs', 'payeedelrs')]
