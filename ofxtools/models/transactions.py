# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import (
    Aggregate,
    ORIGCURRENCY,
    SECID,
    INV401KSOURCES, INVSUBACCTS,
    BUYTYPES, SELLTYPES, INCOMETYPES,
)
from ofxtools.Types import (
    Bool,
    String,
    OneOf,
    Integer,
    Decimal,
    DateTime,
    NagString,
)
from ofxtools.lib import COUNTRY_CODES


class PAYEE(Aggregate):
    """ """
    # name = String(32, required=True)
    name = NagString(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32, required=True)


class TRAN(Aggregate):
    """ Base class (not in OFX spec) for *TRN """
    fitid = String(255, required=True)
    srvrtid = String(10)


class STMTTRN(TRAN, ORIGCURRENCY):
    """ OFX section 11.4.4.1 """
    trntype = OneOf('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                    'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                    'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                    'OTHER', required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    correctfitid = String(255)
    correctaction = OneOf('REPLACE', 'DELETE')
    checknum = String(12)
    refnum = String(32)
    sic = Integer()
    payeeid = String(12)
    name = String(32)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)

    payee = None
    bankacctto = None
    ccacctto = None

    _subaggregates = ("CCACCTTO", "BANKACCTTO", "PAYEE")

    @staticmethod
    def _verify(elem):
        """
        Throw an error for Elements containing sub-Elements that are
        mutually exclusive per the OFX spec, and which will cause
        problems for _flatten()
        """
        super(STMTTRN, STMTTRN)._verify(elem)

        mutexes = [("CCACCTTO", "BANKACCTTO"), ("NAME", "PAYEE")]
        STMTTRN._mutex(elem, mutexes)


class INVBANKTRAN(STMTTRN):
    """ """
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(TRAN):
    """ """
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = String(255)
    memo = String(255)


class INVBUY(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    markup = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = String(32)
    loanprincipal = Decimal()
    loaninterest = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = DateTime()
    prioryearcontrib = Bool()


class INVSELL(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    markdown = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    withholding = Decimal()
    taxexempt = Bool()
    total = Decimal(required=True)
    gain = Decimal()
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = String(32)
    statewithholding = Decimal()
    penalty = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class BUYDEBT(INVBUY):
    """ """
    accrdint = Decimal()


class BUYMF(INVBUY):
    """ """
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = String(255)


class BUYOPT(INVBUY):
    """ """
    optbuytype = OneOf('BUYTOOPEN', 'BUYTOCLOSE', required=True)
    shperctrct = Integer(required=True)


class BUYOTHER(INVBUY):
    """ """
    pass


class BUYSTOCK(INVBUY):
    """ """
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(INVTRAN, SECID):
    """ """
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE')
    units = Decimal(required=True)
    shperctrct = Integer(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = String(255)
    gain = Decimal()


class INCOME(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = Bool()
    withholding = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(INVTRAN):
    """ """
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = Decimal(required=True)


class JRNLSEC(INVTRAN, SECID):
    """ """
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)


class MARGININTEREST(INVTRAN, ORIGCURRENCY):
    """ """
    total = Decimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class REINVEST(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    taxexempt = Bool()
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID, ORIGCURRENCY):
    """ """
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    """ """
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
    accrdint = Decimal()


class SELLMF(INVSELL):
    """ """
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = String(255)


class SELLOPT(INVSELL):
    """ """
    optselltype = OneOf('SELLTOCLOSE', 'SELLTOOPEN', required=True)
    shperctrct = Integer(required=True)
    relfitid = String(255)
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


class SELLOTHER(INVSELL):
    """ """
    pass


class SELLSTOCK(INVSELL):
    """ """
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(INVTRAN, SECID):
    """ """
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    oldunits = Decimal(required=True)
    newunits = Decimal(required=True)
    numerator = Decimal(required=True)
    denominator = Decimal(required=True)
    fraccash = Decimal()
    subacctfund = OneOf(*INVSUBACCTS)
    inv401ksource = OneOf(*INV401KSOURCES)


class TRANSFER(INVTRAN, SECID):
    """ """
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)
    tferaction = OneOf('IN', 'OUT', required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    avgcostbasis = Decimal()
    unitprice = Decimal()
    dtpurchase = DateTime()
    inv401ksource = OneOf(*INV401KSOURCES)
