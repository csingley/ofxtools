# coding: utf-8
"""
Common payments aggregates - OFX Section 12.5

PAYEE is defined in ``ofxtools.models.bank.stmt`` to avoid circular imports.
"""
from ofxtools.Types import String, OneOf, Integer, Decimal, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, List
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.bank.stmt import BANKACCTFROM, BANKACCTTO, PAYEE


__all__ = [
    "BPACCTINFO",
    "BILLPUBINFO",
    "PMTINFO",
    "DISCOUNT",
    "ADJUSTMENT",
    "LINEITEM",
    "INVOICE",
    "EXTDPMTINV",
    "EXTDPMT",
    "EXTDPAYEE",
    "PMTPRCSTS",
]


#  PAYEE is defined in ``ofxtools.models.bank.stmt`` to avoid circular imports.


class BPACCTINFO(Aggregate):
    """ OFX Section 12.5.1 """
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


class BILLPUBINFO(Aggregate):
    """ OFX Section 12.5.2 """
    billpub = String(32, required=True)
    billid = String(32, required=True)


class PMTINFO(List):
    """ OFX Section 12.5.2 """
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    trnamt = Decimal(required=True)
    payeeid = String(12)
    payee = SubAggregate(PAYEE)
    payeelstid = String(12)
    bankacctto = SubAggregate(BANKACCTTO)
    payacct = String(32, required=True)
    dtdue = DateTime(required=True)
    memo = String(255)
    billrefinfo = String(80)
    billpubinfo = SubAggregate(BILLPUBINFO)

    requiredMutexes = [("payeeid", "payee")]
    dataTags = ["EXTDPMT"]


class DISCOUNT(Aggregate):
    dscrate = Decimal(required=True)
    dscamt = Decimal(required=True)
    dscdate = DateTime()
    dscdesc = String(80, required=True)


class ADJUSTMENT(Aggregate):
    adjno = String(32)
    adjdesc = String(80, required=True)
    adjamt = Decimal(required=True)
    adjdate = DateTime()


class LINEITEM(Aggregate):
    litmamt = Decimal(required=True)
    litmdesc = String(80, required=True)


class INVOICE(List):
    invno = String(32, required=True)
    invtotalamt = Decimal(required=True)
    invpaidamt = Decimal(required=True)
    invdate = DateTime(required=True)
    invdesc = String(80, required=True)
    discount = SubAggregate(DISCOUNT)
    adjustment = SubAggregate(ADJUSTMENT)

    dataTags = ["LINEITEM"]


class EXTDPMTINV(List):
    """ OFX Section 12.5.2.2 """

    dataTags = ["INVOICE"]


class EXTDPMT(Aggregate):
    """ OFX Section 12.5.2.2 """
    extdpmtfor = OneOf("INDIVIDUAL", "BUSINESS")
    extdpmtchk = Integer(10)
    # FIXME
    # "At least one of the following"
    extdpmtdsc = String(255)
    extdpmtinv = SubAggregate(EXTDPMTINV)

    requiredMutexes = [("extdpmtdsc", "extdpmtinv")]


class EXTDPAYEE(Aggregate):
    """ OFX Section 12.5.2.6 """
    # FIXME
    # "If <PAYEEID> is present, <IDSCOPE> and <NAME> are required."
    payeeid = String(12)
    idscope = OneOf("GLOBAL", "USER")  # Required if <PAYEEID> is present.
    name = String(32)  # Required if <PAYEEID> is present.
    daystopay = Integer(3, required=True)


class PMTPRCSTS(Aggregate):
    """ OFX Section 12.5.2.7 """
    pmtprccode = OneOf("WILLPROCESSON", "PROCESSEDON", "NOFUNDSON", "FAILEDON",
                       "CANCELEDON", required=True)
    dtpmtprc = DateTime(required=True)
