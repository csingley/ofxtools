# vim: set fileencoding=utf-8
"""
Python object model for transactions,
"""
# local imports
from ofxtools.models.base import (
    Aggregate, List, TranList, SubAggregate, Unsupported,
)
from ofxtools.models.common import (
    STATUS, OFXEXTENSION,
)
from ofxtools.models.bank import (
    STMTTRN, BALLIST, INV401KSOURCES
)
from ofxtools.models.seclist import (
    SECID,
    Secid,
)
from ofxtools.models.i18n import (
    CURRENCY, ORIGCURRENCY,
    Origcurrency,
    CURRENCY_CODES,
)
from ofxtools.Types import (
    Bool, String, OneOf, Integer, Decimal, DateTime,
)


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
    acctid = String(22, required=True)
    brokerid = String(22, required=True)


# Transactions
class INVBANKTRAN(Aggregate):
    """ OFX section 13.9.2.3 """
    stmttrn = SubAggregate(STMTTRN, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)

    @property
    def trntype(self):
        return self.stmttrn.trntype

    @property
    def dtposted(self):
        return self.stmttrn.dtposted

    @property
    def trnamt(self):
        return self.stmttrn.trnamt

    @property
    def fitid(self):
        return self.stmttrn.fitid

    @property
    def memo(self):
        return self.stmttrn.memo

    @property
    def curtype(self):
        return (self.stmttrn.currency
                or self.stmttrn.origcurrency).__class__.__name__

    @property
    def cursym(self):
        ctype = getattr(self.stmttrn, self.curtype.lower())
        return ctype.cursym

    @property
    def currate(self):
        ctype = getattr(self.stmttrn, self.curtype.lower())
        return ctype.currate


class INVTRAN(Aggregate):
    """ OFX section 13.9.2.4.2 """
    fitid = String(255, required=True)
    srvrtid = String(10)
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = String(255)
    memo = String(255)


class Invtran(object):
    """ Mixin providing property aliases """

    @property
    def fitid(self):
        return self.invtran.fitid

    @property
    def dttrade(self):
        return self.invtran.dttrade

    @property
    def memo(self):
        return self.invtran.memo


class INVBUY(Aggregate, Invtran, Origcurrency, Secid):
    """ OFX section 13.9.2.4.3 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
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


class Invbuy(object):
    """ Mixin providing property aliases """

    @property
    def uniqueid(self):
        return self.invbuy.secid.uniqueid

    @property
    def uniqueidtype(self):
        return self.invbuy.secid.uniqueidtype

    @property
    def units(self):
        return self.invbuy.units

    @property
    def unitprice(self):
        return self.invbuy.unitprice

    @property
    def total(self):
        return self.invbuy.total

    @property
    def curtype(self):
        return self.invbuy.curtype

    @property
    def cursym(self):
        return self.invbuy.cursym

    @property
    def currate(self):
        return self.invbuy.currate

    @property
    def subacctsec(self):
        return self.invbuy.subacctsec

    @property
    def subacctfund(self):
        return self.invbuy.subacctfund

    @property
    def fitid(self):
        return self.invbuy.invtran.fitid

    @property
    def dttrade(self):
        return self.invbuy.invtran.dttrade

    @property
    def memo(self):
        return self.invbuy.invtran.memo


class INVSELL(Aggregate, Invtran, Origcurrency, Secid):
    """ OFX section 13.9.2.4.3 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
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
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = String(32)
    statewithholding = Decimal()
    penalty = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class Invsell(object):
    """ Mixin providing property aliases """

    @property
    def uniqueid(self):
        return self.invsell.secid.uniqueid

    @property
    def uniqueidtype(self):
        return self.invsell.secid.uniqueidtype

    @property
    def units(self):
        return self.invsell.units

    @property
    def unitprice(self):
        return self.invsell.unitprice

    @property
    def total(self):
        return self.invsell.total

    @property
    def curtype(self):
        return self.invsell.curtype

    @property
    def cursym(self):
        return self.invsell.cursym

    @property
    def currate(self):
        return self.invsell.currate

    @property
    def subacctsec(self):
        return self.invsell.subacctsec

    @property
    def subacctfund(self):
        return self.invsell.subacctfund

    @property
    def fitid(self):
        return self.invsell.invtran.fitid

    @property
    def dttrade(self):
        return self.invsell.invtran.dttrade

    @property
    def memo(self):
        return self.invsell.invtran.memo


class BUYDEBT(Aggregate, Invbuy):
    """ OFX section 13.9.2.4.4 """
    invbuy = SubAggregate(INVBUY, required=True)
    accrdint = Decimal()


class BUYMF(Aggregate, Invbuy):
    """ OFX section 13.9.2.4.4 """
    invbuy = SubAggregate(INVBUY, required=True)
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = String(255)


class BUYOPT(Aggregate, Invbuy):
    """ OFX section 13.9.2.4.4 """
    invbuy = SubAggregate(INVBUY, required=True)
    optbuytype = OneOf(*OPTBUYTYPES, required=True)
    shperctrct = Integer(required=True)


class BUYOTHER(Aggregate, Invbuy):
    """ OFX section 13.9.2.4.4 """
    invbuy = SubAggregate(INVBUY, required=True)
    pass


class BUYSTOCK(Aggregate, Invbuy):
    """ OFX section 13.9.2.4.4 """
    invbuy = SubAggregate(INVBUY, required=True)
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(Aggregate, Invtran, Secid):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE', required=True)
    units = Decimal(required=True)
    shperctrct = Integer(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = String(255)
    gain = Decimal()


class INCOME(Aggregate, Invtran, Origcurrency, Secid):
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


class INVEXPENSE(Aggregate, Invtran, Origcurrency, Secid):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(Aggregate, Invtran):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = Decimal(required=True)


class JRNLSEC(Aggregate, Invtran, Secid):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)


class MARGININTEREST(Aggregate, Invtran, Origcurrency):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    total = Decimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)


class REINVEST(Aggregate, Invtran, Origcurrency, Secid):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
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
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(Aggregate, Invtran, Origcurrency, Secid):
    """ OFX section 13.9.2.4.4 """
    invtran = SubAggregate(INVTRAN, required=True)
    secid = SubAggregate(SECID, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(Aggregate, Invsell):
    """ OFX section 13.9.2.4.4 """
    invsell = SubAggregate(INVSELL, required=True)
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
    accrdint = Decimal()


class SELLMF(Aggregate, Invsell):
    """ OFX section 13.9.2.4.4 """
    invsell = SubAggregate(INVSELL, required=True)
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = String(255)


class SELLOPT(Aggregate, Invsell):
    """ OFX section 13.9.2.4.4 """
    invsell = SubAggregate(INVSELL, required=True)
    optselltype = OneOf(*OPTSELLTYPES, required=True)
    shperctrct = Integer(required=True)
    relfitid = String(255)
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


class SELLOTHER(Aggregate, Invsell):
    """ OFX section 13.9.2.4.4 """
    invsell = SubAggregate(INVSELL, required=True)


class SELLSTOCK(Aggregate, Invsell):
    """ OFX section 13.9.2.4.4 """
    invsell = SubAggregate(INVSELL, required=True)
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(Aggregate, Invtran, Origcurrency, Secid):
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


class TRANSFER(Aggregate, Invtran, Secid):
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
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    memberTags = ('INVBANKTRAN', 'BUYDEBT', 'BUYMF', 'BUYOPT', 'BUYOTHER',
                  'BUYSTOCK', 'CLOSUREOPT', 'INCOME', 'INVEXPENSE', 'JRNLFUND',
                  'JRNLSEC', 'MARGININTEREST', 'REINVEST', 'RETOFCAP',
                  'SELLDEBT', 'SELLMF', 'SELLOPT', 'SELLOTHER', 'SELLSTOCK',
                  'SPLIT', 'TRANSFER', )


# Positions
class INVPOS(Aggregate, Secid):
    """ OFX section 13.9.2.6.1 """
    secid = SubAggregate(SECID)
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    avgcostbasis = Decimal()
    dtpriceasof = DateTime(required=True)
    currency = SubAggregate(CURRENCY)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class Invpos(object):
    """ Mixin providing property aliases """
    @property
    def uniqueid(self):
        return self.invpos.secid.uniqueid

    @property
    def uniqueidtype(self):
        return self.invpos.secid.uniqueidtype

    @property
    def heldinacct(self):
        return self.invpos.heldinacct

    @property
    def postype(self):
        return self.invpos.postype

    @property
    def units(self):
        return self.invpos.units

    @property
    def unitprice(self):
        return self.invpos.unitprice

    @property
    def mktval(self):
        return self.invpos.mktval

    @property
    def dtpriceasof(self):
        return self.invpos.dtpriceasof

    @property
    def cursym(self):
        currency = self.invpos.currency
        if currency:
            return self.invpos.currency.cursym

    @property
    def currate(self):
        currency = self.invpos.currency
        if currency:
            return self.invpos.currency.currate

    @property
    def memo(self):
        return self.invpos.memo


class POSDEBT(Aggregate, Invpos):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)


class POSMF(Aggregate, Invpos):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(Aggregate, Invpos):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(Aggregate, Invpos):
    """ OFX section 13.9.2.6.1 """
    invpos = SubAggregate(INVPOS, required=True)


class POSSTOCK(Aggregate, Invpos):
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


class INVOOLIST(List):
    """ OFX section 13.9.2.2 """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

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
    # invoolist = SubAggregate(INVOOLIST)
    invoolist = Unsupported()
    mktginfo = String(360)
    inv401k = Unsupported()
    inv401kbal = SubAggregate(INV401KBAL)

    # Human-friendly attribute aliases
    @property
    def currency(self):
        return self.curdef

    @property
    def account(self):
        return self.invacctfrom

    @property
    def datetime(self):
        return self.dtasof

    @property
    def balances(self):
        return self.invbal

    @property
    def transactions(self):
        return self.invtranlist

    @property
    def positions(self):
        return self.invposlist


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


class INVSTMTMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    memberTags = ['INVSTMTTRNRS', ]

    @property
    def statements(self):
        return [trnrs.invstmtrs for trnrs in self]
