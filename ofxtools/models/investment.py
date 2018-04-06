# vim: set fileencoding=utf-8
"""
Python object model for transactions,
"""
# local imports
from ofxtools.models.base import (
    Aggregate, List, TranList, SubAggregate, Unsupported,
)
from ofxtools.models.common import (
    STATUS, OFXEXTENSION, MSGSETCORE,
)
from ofxtools.models.bank import (
    STMTTRN, INCTRAN, BALLIST, INV401KSOURCES,
)
from ofxtools.models.seclist import (
    SECID,
)
from ofxtools.models.i18n import (
    CURRENCY, ORIGCURRENCY,
    Origcurrency,
    CURRENCY_CODES,
)
from ofxtools.Types import (
    Bool, String, OneOf, Integer, Decimal, DateTime,
)


__all__ = ['INVACCTFROM', 'INVBAL', 'INV401KBAL', 'INVTRAN', 'INVBUY',
           'INVSELL', 'OO', 'INVBANKTRAN', 'REINVEST', 'RETOFCAP', 'SPLIT',
           'TRANSFER', 'CLOSUREOPT', 'INCOME', 'INVEXPENSE', 'JRNLFUND',
           'JRNLSEC', 'MARGININTEREST', 'BUYDEBT', 'BUYMF', 'BUYOPT',
           'BUYOTHER', 'BUYSTOCK', 'SELLDEBT', 'SELLMF', 'SELLOPT',
           'SELLOTHER', 'SELLSTOCK', 'INVPOS', 'POSDEBT', 'POSMF', 'POSOPT',
           'POSOTHER', 'POSSTOCK', 'OOBUYDEBT', 'OOBUYMF', 'OOBUYOPT',
           'OOBUYOTHER', 'OOBUYSTOCK', 'OOSELLDEBT', 'OOSELLMF', 'OOSELLOPT',
           'OOSELLOTHER', 'OOSELLSTOCK', 'SWITCHMF', 'INVTRANLIST',
           'INVPOSLIST', 'INVOOLIST', 'INVSTMTRQ', 'INVSTMTRS',
           'INVSTMTTRNRQ', 'INVSTMTTRNRS', 'INVSTMTMSGSRQV1',
           'INVSTMTMSGSRSV1', 'INVSTMTMSGSETV1', 'INVSTMTMSGSET', ]


# Enums used in aggregate validation
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
OPTBUYTYPES = ('BUYTOOPEN', 'BUYTOCLOSE')
SELLTYPES = ('SELL', 'SELLSHORT')
OPTSELLTYPES = ('SELLTOCLOSE', 'SELLTOOPEN')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
UNITTYPES = ('SHARES', 'CURRENCY')


class INVACCTFROM(Aggregate):
    """ OFX section 13.6.1 """
    brokerid = String(22, required=True)
    acctid = String(22, required=True)


class INCPOS(Aggregate):
    """ OFX section 13.9.1.2 """
    dtasof = DateTime()
    include = Bool(required=True)


class INVSTMTRQ(Aggregate):
    """ OFX section 13.9.1.2 """
    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    incoo = Bool(required=True)
    incpos = SubAggregate(INCPOS, required=True)
    incbal = Bool(required=True)
    inc401k = Bool()
    inc401bal = Bool()
    inctranimg = Bool()


# Transactions
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
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE', required=True)
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
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
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
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


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
    tferaction = OneOf('IN', 'OUT', required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    invacctfrom = SubAggregate(INVACCTFROM)
    avgcostbasis = Decimal()
    unitprice = Decimal()
    dtpurchase = DateTime()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVTRANLIST(TranList):
    """ OFX section 13.9.2.2 """
    memberTags = ('INVBANKTRAN', 'BUYDEBT', 'BUYMF', 'BUYOPT', 'BUYOTHER',
                  'BUYSTOCK', 'CLOSUREOPT', 'INCOME', 'INVEXPENSE', 'JRNLFUND',
                  'JRNLSEC', 'MARGININTEREST', 'REINVEST', 'RETOFCAP',
                  'SELLDEBT', 'SELLMF', 'SELLOPT', 'SELLOTHER', 'SELLSTOCK',
                  'SPLIT', 'TRANSFER', )


# Positions
class INVPOS(Aggregate):
    """ OFX section 13.9.2.6.1 """
    secid = SubAggregate(SECID)
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(required=True)
    mktval = Decimal(required=True)
    avgcostbasis = Decimal()
    dtpriceasof = DateTime(required=True)
    currency = SubAggregate(CURRENCY)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(Aggregate):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)


class POSMF(Aggregate):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(Aggregate):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(Aggregate):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)


class POSSTOCK(Aggregate):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()


class INVPOSLIST(List):
    """ OFX section 13.9.2.2 """
    memberTags = ['POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK', ]


# Balances
class INVBAL(Aggregate):
    """ OFX section 13.9.2.7 """
    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()
    ballist = SubAggregate(BALLIST)


class INV401KBAL(Aggregate):
    """ OFX section 13.9.2.9 """
    cashbal = Decimal()
    pretax = Decimal()
    aftertax = Decimal()
    match = Decimal()
    profitsharing = Decimal()
    rollover = Decimal()
    othervest = Decimal()
    othernonvest = Decimal()
    total = Decimal(required=True)
    ballist = SubAggregate(BALLIST)


# Open orders
class OO(Aggregate):
    """ OFX section 13.9.2.5.1 - General open order aggregate """
    fitid = String(255, required=True)
    srvrtid = String(10)
    secid = SubAggregate(SECID, required=True)
    dtplaced = DateTime(required=True)
    units = Decimal(required=True)
    subacct = OneOf(*INVSUBACCTS, required=True)
    duration = OneOf('DAY', 'GOODTILCANCEL', 'IMMEDIATE', required=True)
    restriction = OneOf('ALLORNONE', 'MINUNITS', 'NONE', required=True)
    minunits = Decimal()
    limitprice = Decimal()
    stopprice = Decimal()
    memo = String(255)
    currency = SubAggregate(CURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class OOBUYDEBT(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    auction = Bool(required=True)
    dtauction = DateTime()


class OOBUYMF(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    buytype = OneOf(*BUYTYPES, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOBUYOPT(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    optbuytype = OneOf(*OPTBUYTYPES, required=True)


class OOBUYOTHER(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOBUYSTOCK(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    buytype = OneOf(*BUYTYPES, required=True)


class OOSELLDEBT(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)


class OOSELLMF(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    selltype = OneOf(*SELLTYPES, required=True)
    unittype = OneOf(*UNITTYPES, required=True)
    sellall = Bool(required=True)


class OOSELLOPT(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    optselltype = OneOf(*OPTSELLTYPES, required=True)


class OOSELLOTHER(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    unittype = OneOf(*UNITTYPES, required=True)


class OOSELLSTOCK(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    selltype = OneOf(*SELLTYPES, required=True)


class SWITCHMF(Aggregate):
    """ OFX section 13.9.2.5.2 """
    oo = SubAggregate(OO, required=True)
    secid = SubAggregate(SECID, required=True)
    unittype = OneOf(*UNITTYPES, required=True)
    switchall = Bool(required=True)


class INVOOLIST(TranList):
    """ OFX section 13.9.2.2 """
    memberTags = ['OOBUYDEBT', 'OOBUYMF', 'OOBUYOPT', 'OOBUYOTHER',
                  'OOBUYSTOCK', 'OOSELLDEBT', 'OOSELLMF', 'OOSELLOPT',
                  'OOSELLOTHER', 'OOSELLSTOCK', 'SWITCHMF', ]


class INVSTMTRS(Aggregate):
    """ OFX section 13.9.2.1 """
    dtasof = DateTime(required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)
    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    invtranlist = SubAggregate(INVTRANLIST)
    invposlist = SubAggregate(INVPOSLIST)
    invbal = SubAggregate(INVBAL)
    # FIXME - definiing INVOOLIST blows up Aggregate.to_etree()
    invoolist = SubAggregate(INVOOLIST)
    # invoolist = Unsupported()
    mktginfo = String(360)
    inv401k = Unsupported()
    inv401kbal = SubAggregate(INV401KBAL)

    @property
    def account(self):
        return self.invacctfrom

    @property
    def transactions(self):
        return self.invtranlist

    @property
    def positions(self):
        return self.invposlist

    @property
    def balances(self):
        return self.invbal


class INVSTMTTRNRQ(Aggregate):
    """ OFX section 13.9.1.1 """
    trnuid = String(36, required=True)
    clientcookie = String(32)
    tan = String(80)
    ofxextension = Unsupported()
    invstmtrq = SubAggregate(INVSTMTRQ)


class INVSTMTTRNRS(Aggregate):
    """ OFX section 13.9.2.1 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    clientcookie = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)
    invstmtrs = SubAggregate(INVSTMTRS)

    @property
    def statement(self):
        return self.invstmtrs


class INVSTMTMSGSRQV1(List):
    """ OFX section 13.7.1.2.1 """
    memberTags = ['INVSTMTTRNRQ', ]


class INVSTMTMSGSRSV1(List):
    """ OFX section 13.7.1.2.2 """
    memberTags = ['INVSTMTTRNRS', ]

    @property
    def statements(self):
        return [trnrs.invstmtrs for trnrs in self]


class INVSTMTMSGSETV1(Aggregate):
    """ OFX section 13.7.1.1 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    trandnld = Bool(required=True)
    oodnld = Bool(required=True)
    posdnld = Bool(required=True)
    baldnld = Bool(required=True)
    canemail = Bool(required=True)
    inv401kdnld = Bool()
    closingavail = Bool()
    imageprof = Unsupported()


class INVSTMTMSGSET(Aggregate):
    """ OFX section 13.7.1.1 """
    invstmtmsgsetv1 = SubAggregate(INVSTMTMSGSETV1, required=True)
