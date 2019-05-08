# coding: utf-8
"""
Common payments aggregates - OFX Section 12.5

PAYEE is defined in ``ofxtools.models.bank.stmt`` to avoid circular imports.
"""


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


from ofxtools.Types import String, OneOf, Integer, Decimal, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.bank.stmt import BANKACCTFROM, BANKACCTTO, PAYEE


#  PAYEE is defined in ``ofxtools.models.bank.stmt`` to avoid circular imports.


class BPACCTINFO(Aggregate):
    """ OFX Section 12.5.1 """
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


class BILLPUBINFO(Aggregate):
    """ OFX Section 12.5.2 """
    billpub = String(32, required=True)
    billid = String(32, required=True)


class DISCOUNT(Aggregate):
    """ OFX Section 12.5.2.3 """
    dscrate = Decimal(required=True)
    dscamt = Decimal(required=True)
    dscdate = DateTime()
    dscdesc = String(80, required=True)


class ADJUSTMENT(Aggregate):
    """ OFX Section 12.5.2.4 """
    adjno = String(32)
    adjdesc = String(80, required=True)
    adjamt = Decimal(required=True)
    adjdate = DateTime()


class LINEITEM(Aggregate):
    """ OFX Section 12.5.2.5 """
    litmamt = Decimal(required=True)
    litmdesc = String(80, required=True)


class INVOICE(Aggregate):
    """ OFX Section 12.5.2.3 """
    invno = String(32, required=True)
    invtotalamt = Decimal(required=True)
    invpaidamt = Decimal(required=True)
    invdate = DateTime(required=True)
    invdesc = String(80, required=True)
    discount = SubAggregate(DISCOUNT)
    adjustment = SubAggregate(ADJUSTMENT)
    lineitem = ListItem(LINEITEM)


class EXTDPMTINV(Aggregate):
    """ OFX Section 12.5.2.2 """
    invoice = ListItem(INVOICE)


class EXTDPMT(Aggregate):
    """ OFX Section 12.5.2.2 """
    extdpmtfor = OneOf("INDIVIDUAL", "BUSINESS")
    extdpmtchk = Integer(10)
    extdpmtdsc = String(255)
    extdpmtinv = ListItem(EXTDPMTINV)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # "At least one of the following: <EXTDPMTDSC>, or <EXTDPMTINV>"
        listitems = [arg.__class__.__name__ for arg in args]
        if "EXTDPMTINV" not in listitems and "extdpmtdsc" not in kwargs:
            msg = "{} must contain at least one of [EXTDPMTDSC, EXTPMTINV]"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class PMTINFO(Aggregate):
    """ OFX Section 12.5.2 """
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    trnamt = Decimal(required=True)
    payeeid = String(12)
    payee = SubAggregate(PAYEE)
    payeelstid = String(12)
    bankacctto = SubAggregate(BANKACCTTO)
    extdpmt = ListItem(EXTDPMT)
    payacct = String(32, required=True)
    dtdue = DateTime(required=True)
    memo = String(255)
    billrefinfo = String(80)
    billpubinfo = SubAggregate(BILLPUBINFO)

    requiredMutexes = [
        ["payeeid", "payee" ],
    ]


class EXTDPAYEE(Aggregate):
    """ OFX Section 12.5.2.6 """
    payeeid = String(12)
    idscope = OneOf("GLOBAL", "USER")  # Required if <PAYEEID> is present.
    name = String(32)  # Required if <PAYEEID> is present.
    daystopay = Integer(3, required=True)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # "If <PAYEEID> is present, <IDSCOPE> and <NAME> are required."
        payeeid = kwargs.get("payeeid", None)
        if payeeid:
            requiredGroup = ("idscope", "name")
            if not all(kwargs.get(attr, None) for attr in requiredGroup):
                msg = "{}(payeeid={}) must contain all of {}"
                raise ValueError(msg.format(cls.__name__, payeeid, requiredGroup))

        super().validate_args(*args, **kwargs)


class PMTPRCSTS(Aggregate):
    """ OFX Section 12.5.2.7 """
    pmtprccode = OneOf("WILLPROCESSON", "PROCESSEDON", "NOFUNDSON", "FAILEDON",
                       "CANCELEDON", required=True)
    dtpmtprc = DateTime(required=True)
