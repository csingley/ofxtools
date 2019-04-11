# coding: utf-8
"""
Investments - OFX Section 13
"""
from ofxtools.Types import Bool, String, OneOf, Integer, Decimal, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TranList
from ofxtools.models.invest.acct import INVSUBACCTS, INVACCTFROM
from ofxtools.models.invest.securities import SECID
from ofxtools.models.bank import STMTTRN, INV401KSOURCES
from ofxtools.models.i18n import CURRENCY, ORIGCURRENCY, Origcurrency


__all__ = [
    "BUYTYPES", "SELLTYPES", "OPTBUYTYPES", "OPTSELLTYPES", "INCOMETYPES",
    "INVBANKTRAN", "INVTRAN", "INVBUY", "INVSELL",
    "BUYDEBT", "BUYMF", "BUYOPT", "BUYOTHER", "BUYSTOCK",
    "SELLDEBT", "SELLMF", "SELLOPT", "SELLOTHER", "SELLSTOCK",
    "REINVEST", "RETOFCAP", "SPLIT", "TRANSFER", "CLOSUREOPT",
    "INCOME", "INVEXPENSE", "JRNLFUND", "JRNLSEC", "MARGININTEREST",
    "INVTRANLIST",
]


BUYTYPES = ("BUY", "BUYTOCOVER")
SELLTYPES = ("SELL", "SELLSHORT")
OPTBUYTYPES = ("BUYTOOPEN", "BUYTOCLOSE")
OPTSELLTYPES = ("SELLTOCLOSE", "SELLTOOPEN")
INCOMETYPES = ("CGLONG", "CGSHORT", "DIV", "INTEREST", "MISC")


class INVBANKTRAN(Aggregate):
    """ OFX section 13.9.2.3 """

    stmttrn = SubAggregate(STMTTRN, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(Aggregate):
    """ OFX section 13.9.2.4.2 """

    fitid = String(255, required=True)
    srvrtid = String(10)
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = String(255)
    memo = String(255)


class INVBUY(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.3 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    units = Decimal(required=True)
    unitprice = Decimal(required=True)
    markup = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    total = Decimal(required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = String(32)
    loanprincipal = Decimal()
    loaninterest = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = DateTime()
    prioryearcontrib = Bool()


class INVSELL(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.3 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    units = Decimal(required=True)
    unitprice = Decimal(required=True)
    markdown = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    withholding = Decimal()
    taxexempt = Bool()
    total = Decimal(required=True)
    gain = Decimal()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = String(32)
    statewithholding = Decimal()
    penalty = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class BUYDEBT(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invbuy = SubAggregate(INVBUY, required=True)
    accrdint = Decimal()


class BUYMF(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invbuy = SubAggregate(INVBUY, required=True)
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = String(255)


class BUYOPT(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invbuy = SubAggregate(INVBUY, required=True)
    optbuytype = OneOf(*OPTBUYTYPES, required=True)
    shperctrct = Integer(required=True)


class BUYOTHER(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invbuy = SubAggregate(INVBUY, required=True)


class BUYSTOCK(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invbuy = SubAggregate(INVBUY, required=True)
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    optaction = OneOf("EXERCISE", "ASSIGN", "EXPIRE", required=True)
    units = Decimal(required=True)
    shperctrct = Integer(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = String(255)
    gain = Decimal()


class INCOME(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = Bool()
    withholding = Decimal()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = Decimal(required=True)


class JRNLSEC(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)


class MARGININTEREST(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    total = Decimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)


class REINVEST(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)
    unitprice = Decimal(required=True)
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    taxexempt = Bool()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invsell = SubAggregate(INVSELL, required=True)
    sellreason = OneOf("CALL", "SELL", "MATURITY", required=True)
    accrdint = Decimal()


class SELLMF(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invsell = SubAggregate(INVSELL, required=True)
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = String(255)


class SELLOPT(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invsell = SubAggregate(INVSELL, required=True)
    optselltype = OneOf(*OPTSELLTYPES, required=True)
    shperctrct = Integer(required=True)
    relfitid = String(255)
    reltype = OneOf("SPREAD", "STRADDLE", "NONE", "OTHER")
    secured = OneOf("NAKED", "COVERED")


class SELLOTHER(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invsell = SubAggregate(INVSELL, required=True)


class SELLSTOCK(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invsell = SubAggregate(INVSELL, required=True)
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(Aggregate, Origcurrency):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    oldunits = Decimal(required=True)
    newunits = Decimal(required=True)
    numerator = Decimal(required=True)
    denominator = Decimal(required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    fraccash = Decimal()
    subacctfund = OneOf(*INVSUBACCTS)
    inv401ksource = OneOf(*INV401KSOURCES)


class TRANSFER(Aggregate):
    """ OFX section 13.9.2.4.4 """

    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)
    tferaction = OneOf("IN", "OUT", required=True)
    postype = OneOf("SHORT", "LONG", required=True)
    invacctfrom = SubAggregate(INVACCTFROM)
    avgcostbasis = Decimal()
    unitprice = Decimal()
    dtpurchase = DateTime()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVTRANLIST(TranList):
    """ OFX section 13.9.2.2 """

    invbanktran = ListItem(INVBANKTRAN)
    buydebt = ListItem(BUYDEBT)
    buymf = ListItem(BUYMF)
    buyopt = ListItem(BUYOPT)
    buyother = ListItem(BUYOTHER)
    buystock = ListItem(BUYSTOCK)
    closureopt = ListItem(CLOSUREOPT)
    income = ListItem(INCOME)
    invexpense = ListItem(INVEXPENSE)
    jrnlfund = ListItem(JRNLFUND)
    jrnlsec = ListItem(JRNLSEC)
    margininterest = ListItem(MARGININTEREST)
    reinvest = ListItem(REINVEST)
    retofcap = ListItem(RETOFCAP)
    selldebt = ListItem(SELLDEBT)
    sellmf = ListItem(SELLMF)
    sellopt = ListItem(SELLOPT)
    sellother = ListItem(SELLOTHER)
    sellstock = ListItem(SELLSTOCK)
    split = ListItem(SPLIT)
    transfer = ListItem(TRANSFER)
