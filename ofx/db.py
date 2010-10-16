from decimal import Decimal

from elixir import *
from sqlalchemy import types

from utilities import ISO4217, ISO3166_1a3, OFXDtConverter

INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING', 'ROLLOVER',
'OTHERVEST', 'OTHERNONVEST')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK', 'INTLSTOCK', 'MONEYMRKT', 'OTHER')

# Custom SQLAlchemy types
class OFXDecimal(types.TypeDecorator):
    impl = types.Integer

    def __init__(self, scale=2, **kwargs):
        self.scale = scale
        super(OFXDecimal, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return int(Decimal(value) * 10**self.scale)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(value) / 10**self.scale


class OFXDateTime(types.TypeDecorator):
    impl = types.DateTime

    def process_bind_param(self, value, dialect):
        return OFXDtConverter.to_python(value)


# Accounts
class ACCT(Entity):
    using_options(inheritance='multi')

    acctid = Field(String(22), required=True)
    curdef = Field(Enum(*ISO4217), required=True)

    fibals = OneToMany('FIBAL')
    stmttrns = OneToMany('STMTTRN')


class BANKACCT(ACCT):
    using_options(inheritance='multi')

    bankid = Field(String(9), required=True)
    branchid = Field(String(22))
    accttype = Field(Enum('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE'), required=True)
    acctkey = Field(String(22))

    bals = OneToMany('BANKBAL')


class CCACCT(ACCT):
    using_options(inheritance='multi')

    acctkey = Field(String(22))

    bals = OneToMany('CCBAL')


class INVACCT(ACCT):
    using_options(inheritance='multi')

    brokerid = Field(String(22), required=True)

    bals = OneToMany('INVBAL')
    invposs = OneToMany('INVPOS')
    invtrans = OneToMany('INVTRAN')


# Balances
class BANKBAL(Entity):
    dtasof = Field(OFXDateTime, required=True)
    ledgerbal = Field(OFXDecimal, required=True)
    availbal = Field(OFXDecimal, required=True)

    acct = ManyToOne('BANKACCT', required=True)


class CCBAL(Entity):
    dtasof = Field(OFXDateTime, required=True)
    ledgerbal = Field(OFXDecimal, required=True)
    availbal = Field(OFXDecimal, required=True)

    acct = ManyToOne('CCACCT', required=True)


class INVBAL(Entity):
    dtasof = Field(OFXDateTime, required=True)
    availcash = Field(OFXDecimal, required=True)
    marginbalance = Field(OFXDecimal, required=True)
    shortbalance = Field(OFXDecimal, required=True)
    buypower = Field(OFXDecimal)

    acct = ManyToOne('INVACCT', required=True)


class FIBAL(Entity):
    name = Field(String(32), required=True)
    desc = Field(String(80), required=True)
    baltype = Field(Enum('DOLLAR', 'PERCENT', 'NUMBER'), required=True)
    value = Field(OFXDecimal, required=True)
    dtasof = Field(OFXDateTime)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))

    acct = ManyToOne('ACCT', required=True)


# Transactions
class PAYEE(Entity):
    name = Field(String(32), required=True)
    addr1 = Field(String(32), required=True)
    addr2 = Field(String(32))
    addr3 = Field(String(32))
    city = Field(String(32), required=True)
    state = Field(String(5), required=True)
    postalcode = Field(String(11), required=True)
    country = Field(Enum(*ISO3166_1a3))
    phone = Field(String(32), required=True)

    stmttrns = OneToMany('STMTTRN')


class STMTTRN(Entity):
    using_options(inheritance='multi')

    trntype = Field(Enum('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG', 'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT', 'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT', 'OTHER'), required=True)
    dtposted = Field(OFXDateTime, required=True)
    dtuser = Field(OFXDateTime)
    dtavail = Field(OFXDateTime)
    trnamt = Field(OFXDecimal, required=True)
    fitid = Field(String(255), required=True)
    correctfitid = Field(OFXDecimal)
    correctaction = Field(Enum('REPLACE', 'DELETE'))
    srvrtid = Field(String(10))
    checknum = Field(String(12))
    refnum = Field(String(32))
    sic = Field(Integer)
    payeeid = Field(String(12))
    name = Field(String(32))
    payee = ManyToOne('PAYEE')
    bankacctto = ManyToOne('BANKACCT')
    ccacctto = ManyToOne('CCACCT')
    memo = Field(String(255))
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    acct = ManyToOne('ACCT', required=True)


class INVBANKTRAN(STMTTRN):
    using_options(inheritance='multi')

    subacctfund = Field(Enum(*INVSUBACCTS), required=True)


class INVTRAN(Entity):
    fitid = Field(String(255), required=True)
    srvrtid = Field(String(10))
    dttrade = Field(OFXDateTime, required=True)
    dtsettle = Field(OFXDateTime)
    reversalfitid = Field(String(255))
    memo = Field(String(255))

    acct = ManyToOne('INVACCT', required=True)


class INVBUY(INVTRAN):
    using_options(inheritance='multi')

    units = Field(OFXDecimal, required=True)
    unitprice = Field(OFXDecimal(4), required=True)
    markup = Field(OFXDecimal)
    commission = Field(OFXDecimal)
    taxes = Field(OFXDecimal)
    fees = Field(OFXDecimal)
    load = Field(OFXDecimal)
    total = Field(OFXDecimal, required=True)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    subacctsec = Field(Enum(*INVSUBACCTS))
    subacctfund = Field(Enum(*INVSUBACCTS))
    loanid = Field(String(32))
    loanprincipal = Field(OFXDecimal)
    loaninterest = Field(OFXDecimal)
    inv401ksource = Field(Enum(*INV401KSOURCES))
    dtpayroll = Field(OFXDateTime)
    prioryearcontrib = Field(Boolean)


class INVSELL(INVTRAN):
    using_options(inheritance='multi')

    units = Field(OFXDecimal, required=True)
    unitprice = Field(OFXDecimal(4), required=True)
    markdown = Field(OFXDecimal)
    commission = Field(OFXDecimal)
    taxes = Field(OFXDecimal)
    fees = Field(OFXDecimal)
    load = Field(OFXDecimal)
    withholding = Field(OFXDecimal)
    taxexempt = Field(Boolean)
    total = Field(OFXDecimal, required=True)
    gain = Field(OFXDecimal)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    loanid = Field(String(32))
    statewithholding = Field(OFXDecimal)
    penalty = Field(OFXDecimal)
    inv401ksource = Field(Enum(*INV401KSOURCES))


class BUYDEBT(INVBUY):
    using_options(inheritance='multi')

    accrdint = Field(OFXDecimal)

    sec = ManyToOne('DEBTINFO', required=True)


class BUYMF(INVBUY):
    using_options(inheritance='multi')

    buytype = Field(Enum(*BUYTYPES), required=True)
    relfitid = Field(String(255))

    sec = ManyToOne('MFINFO', required=True)


class BUYOPT(INVBUY):
    using_options(inheritance='multi')

    optbuytype = Field(Enum('BUYTOOPEN', 'BUYTOCLOSE'), required=True)
    shperctrct = Field(Integer, required=True)

    sec = ManyToOne('OPTINFO', required=True)


class BUYOTHER(INVBUY):
    using_options(inheritance='multi')

    sec = ManyToOne('OTHERINFO', required=True)


class BUYSTOCK(INVBUY):
    using_options(inheritance='multi')

    buytype = Field(Enum(*BUYTYPES), required=True)

    sec = ManyToOne('STOCKINFO', required=True)


class CLOSUREOPT(INVTRAN):
    using_options(inheritance='multi')

    optaction = Field(Enum('EXERCISE', 'ASSIGN', 'EXPIRE'))
    units = Field(OFXDecimal, required=True)
    shperctrct = Field(Integer, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    relfitid = Field(String(255))
    gain = Field(OFXDecimal)

    sec = ManyToOne('OPTINFO', required=True)


class INCOME(INVTRAN):
    using_options(inheritance='multi')

    incometype = Field(Enum(*INCOMETYPES), required=True)
    total = Field(OFXDecimal, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    taxexempt = Field(Boolean)
    withholding = Field(OFXDecimal)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


class INVEXPENSE(INVTRAN):
    using_options(inheritance='multi')

    total = Field(OFXDecimal, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


class JRNLFUND(INVTRAN):
    using_options(inheritance='multi')

    subacctto = Field(Enum(*INVSUBACCTS), required=True)
    subacctfrom = Field(Enum(*INVSUBACCTS), required=True)
    total = Field(OFXDecimal, required=True)


class JRNLSEC(INVTRAN):
    using_options(inheritance='multi')

    subacctto = Field(Enum(*INVSUBACCTS), required=True)
    subacctfrom = Field(Enum(*INVSUBACCTS), required=True)
    units = Field(OFXDecimal, required=True)

    sec = ManyToOne('SECINFO', required=True)


class MARGININTEREST(INVTRAN):
    using_options(inheritance='multi')

    total = Field(OFXDecimal, required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))


class REINVEST(INVTRAN):
    using_options(inheritance='multi')

    incometype = Field(Enum(*INCOMETYPES), required=True)
    total = Field(OFXDecimal, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS))
    units = Field(OFXDecimal, required=True)
    unitprice = Field(OFXDecimal(4), required=True)
    commission = Field(OFXDecimal)
    taxes = Field(OFXDecimal)
    fees = Field(OFXDecimal)
    load = Field(OFXDecimal)
    taxexempt = Field(Boolean)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


class RETOFCAP(INVTRAN):
    using_options(inheritance='multi')

    total = Field(OFXDecimal, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


class SELLDEBT(INVSELL):
    using_options(inheritance='multi')

    sellreason = Field(Enum('CALL','SELL', 'MATURITY', required=True))
    accrdint = Field(OFXDecimal)

    sec = ManyToOne('DEBTINFO', required=True)


class SELLMF(INVSELL):
    using_options(inheritance='multi')

    selltype = Field(Enum(*SELLTYPES), required=True)
    avgcostbasis = Field(OFXDecimal)
    relfitid = Field(String(255))

    sec = ManyToOne('MFINFO', required=True)


class SELLOPT(INVSELL):
    using_options(inheritance='multi')

    optselltype = Field(Enum('SELLTOCLOSE', 'SELLTOOPEN'), required=True)
    shperctrct = Field(Integer, required=True)
    relfitid = Field(String(255))
    reltype = Field(Enum('SPREAD', 'STRADDLE', 'NONE', 'OTHER'))
    secured = Field(Enum('NAKED', 'COVERED'))

    sec = ManyToOne('OPTINFO', required=True)


class SELLOTHER(INVSELL):
    using_options(inheritance='multi')

    sec = ManyToOne('OTHERINFO', required=True)


class SELLSTOCK(INVSELL):
    using_options(inheritance='multi')

    selltype = Field(Enum(*SELLTYPES), required=True)

    sec = ManyToOne('STOCKINFO', required=True)


class SPLIT(INVTRAN):
    using_options(inheritance='multi')

    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    oldunits = Field(OFXDecimal, required=True)
    newunits = Field(OFXDecimal, required=True)
    numerator = Field(OFXDecimal, required=True)
    denominator = Field(OFXDecimal, required=True)
    fraccash = Field(OFXDecimal)
    subacctfund = Field(Enum(*INVSUBACCTS))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


class TRANSFER(INVTRAN):
    using_options(inheritance='multi')

    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    units = Field(OFXDecimal, required=True)
    tferaction = Field(Enum('IN', 'OUT'), required=True)
    postype = Field(Enum('SHORT', 'LONG'), required=True)
    avgcostbasis = Field(OFXDecimal)
    unitprice = Field(OFXDecimal)
    dtpurchase = Field(OFXDateTime)
    inv401ksource = Field(Enum(*INV401KSOURCES))

    sec = ManyToOne('SECINFO', required=True)


# Securities
class SECINFO(Entity):
    using_options(inheritance='multi')

    uniqueid = Field(String(32), required=True)
    uniqueidtype = Field(String(10), required=True)
    secname = Field(String(50), required=True)
    ticker = Field(String(120))
    fiid = Field(String(32))
    rating = Field(String(10))
    #unitprice = Field(OFXDecimal)
    #dtasof = Field(OFXDateTime)
    memo = Field(String(255))


class DEBTINFO(SECINFO):
    using_options(inheritance='multi')

    parvalue = Field(OFXDecimal, required=True)
    debttype = Field(Enum('COUPON', 'ZERO'), required=True)
    debtclass = Field(Enum('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER'))
    couponrt = Field(OFXDecimal(4))
    dtcoupon = Field(OFXDateTime)
    couponfreq = Field(Enum('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL', 'OTHER'))
    callprice = Field(OFXDecimal(4))
    yieldtocall = Field(OFXDecimal(4))
    dtcall = Field(OFXDateTime)
    calltype = Field(Enum('CALL', 'PUT', 'PREFUND', 'MATURITY'))
    ytmat = Field(OFXDecimal(4))
    dtmat = Field(OFXDateTime)
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(String(32))


class MFASSETCLASS(Entity):
    assetclass = Field(Enum(*ASSETCLASSES))
    percent = Field(OFXDecimal)

    mf = ManyToOne('MFINFO')


class FIMFASSETCLASS(Entity):
    fiassetclass = Field(String(32))
    percent = Field(OFXDecimal)

    mf = ManyToOne('MFINFO')


class MFINFO(SECINFO):
    using_options(inheritance='multi')

    mftype = Field(Enum('OPENEND', 'CLOSEEND', 'OTHER'))
    yld = Field(OFXDecimal(4))
    dtyieldasof = Field(OFXDateTime)
    mfassetclasses = OneToMany('MFASSETCLASS')
    fimfassetclass = OneToMany('FIMFASSETCLASS')


class OPTINFO(SECINFO):
    using_options(inheritance='multi')

    opttype = Field(Enum('CALL', 'PUT'), required=True)
    strikeprice = Field(OFXDecimal, required=True)
    dtexpire = Field(OFXDateTime, required=True)
    shperctrct = Field(Integer, required=True)
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(String(32))

    sec = ManyToOne('SECINFO', required=True)


class OTHERINFO(SECINFO):
    using_options(inheritance='multi')

    typedesc = Field(String(32))
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(String(32))


class STOCKINFO(SECINFO):
    using_options(inheritance='multi')

    stocktype = Field(Enum('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER'))
    yld = Field(OFXDecimal(4))
    dtyieldasof = Field(OFXDateTime)
    typedesc = Field(String(32))
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(String(32))


# Securities prices
class SECPRICE(Entity):
    dtpriceasof = Field(OFXDateTime, required=True)
    unitprice = Field(OFXDecimal(4), required=True)
    cursym = Field(Enum(*ISO4217), required=True)
    currate = Field(OFXDecimal(8))

    sec = ManyToOne('SECINFO', required=True)
    #invpos = OneToOne('INVPOS')


# Positions
class INVPOS(Entity):
    using_options(inheritance='multi')

    heldinacct = Field(Enum(*INVSUBACCTS), required=True)
    postype = Field(Enum('SHORT', 'LONG'), required=True)
    units = Field(OFXDecimal, required=True)
    #unitprice = Field(OFXDecimal(4), required=True)
    mktval = Field(OFXDecimal, required=True)
    #dtpriceasof = Field(OFXDateTime, required=True)
    #cursym = Field(Enum(*ISO4217), required=True)
    #currate = Field(OFXDecimal(8))
    memo = Field(String(255))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    acct = ManyToOne('INVACCT', required=True)
    #secprice = OneToOne('SECPRICE')


class POSDEBT(INVPOS):
    using_options(inheritance='multi')

    sec = ManyToOne('DEBTINFO', required=True)


class POSMF(INVPOS):
    using_options(inheritance='multi')

    unitsstreet = Field(OFXDecimal)
    unitsuser = Field(OFXDecimal)
    reinvdiv = Field(Boolean)
    reinvcg = Field(Boolean)

    sec = ManyToOne('MFINFO', required=True)


class POSOPT(INVPOS):
    using_options(inheritance='multi')

    secured = Field(Enum('NAKED', 'COVERED'))

    sec = ManyToOne('OPTINFO', required=True)


class POSOTHER(INVPOS):
    using_options(inheritance='multi')

    sec = ManyToOne('OTHERINFO', required=True)


class POSSTOCK(INVPOS):
    using_options(inheritance='multi')

    unitsstreet = Field(OFXDecimal)
    unitsuser = Field(OFXDecimal)
    reinvdiv = Field(Boolean)

    sec = ManyToOne('STOCKINFO', required=True)
