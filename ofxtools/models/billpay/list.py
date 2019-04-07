# coding: utf-8
"""
Payee lists - OFX Section 12.9
"""
from ofxtools.Types import Bool, String, Decimal
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.bank.stmt import PAYEE, BANKACCTTO
from ofxtools.models.billpay.common import EXTDPAYEE


__all__ = [
    "PAYEERQ",
    "PAYEERS",
    "PAYEEMODRQ",
    "PAYEEMODRS",
    "PAYEEDELRQ",
    "PAYEEDELRS",
    "PAYEESYNCRQ",
    "PAYEESYNCRS",
]


class PAYEERQ(Aggregate):
    """ OFX Section 12.9.1.1 """
    payeeid = String(12)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = String(32)

    requiredMutexes = [("payeeid", "payee")]


class PAYEERS(Aggregate):
    """ OFX Section 12.9.1.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    extdpayee = SubAggregate(EXTDPAYEE)
    payacct = String(32)


class PAYEEMODRQ(Aggregate):
    """ OFX Section 12.9.2.1 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = String(32)


class PAYEEMODRS(Aggregate):
    """ OFX Section 12.9.2.2 """
    payeelstid = String(12, required=True)
    payee = SubAggregate(PAYEE)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = String(32)
    extdpayee = SubAggregate(EXTDPAYEE)


class PAYEEDELRQ(Aggregate):
    """ OFX Section 12.9.3.1 """
    payeelstid = String(12, required=True)


class PAYEEDELRS(Aggregate):
    """ OFX Section 12.9.3.1 """
    payeelstid = String(12, required=True)


class PAYEESYNCRQ(SyncRqList):
    """ OFX Section 12.9.4.1 """

    dataTags = ["PAYEETRNRQ"]


class PAYEESYNCRS(SyncRsList):
    """ OFX Section 12.9.4.2 """

    dataTags = ["PAYEETRNRS"]
