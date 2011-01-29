from decimal import Decimal

from elixir import *
from sqlalchemy import types, orm, UniqueConstraint

from utilities import ISO4217, ISO3166_1a3, OFXDtConverter

INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING', 'ROLLOVER',
                'OTHERVEST', 'OTHERNONVEST')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')

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


class Mergeable(object):
    """
    Mixin class providing get_or_create().

    Subclasses must define 'signature' attribute (sequence of column names).
    """

    @classmethod
    def get_or_create(cls, **kwargs):
        #print kwargs
        sig = {k: kwargs.get(k, None) for k in cls.signature}
        try:
            instance = cls.query.filter_by(**sig).one()
            created = False
        except orm.exc.NoResultFound:
            instance = cls(**kwargs)
            created = True
        return instance, created


class FI(Entity, Mergeable):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    We stick the OFX server URL here (there won't be one if OFX files
    are generated for download by a web server).
    """
    signature = ('org', 'fid')
    using_options(UniqueConstraint(*signature), tablename='fi')

    url = Field(Unicode)
    org = Field(Unicode(32), required=True)
    fid = Field(Unicode(32))

    accts = OneToMany('ACCT')
    signons = OneToMany('SIGNON')


class SIGNON(Entity, Mergeable):
    """ Only present in SONRQ, not in SONRS. """
    signature = ('fi', 'userid')
    using_options(UniqueConstraint(*signature), tablename='signon')

    userid = Field(Unicode(), required=True)

    fi = ManyToOne('FI', required=True)
    accts = OneToMany('ACCT')


# Accounts
class ACCT(Entity):
    using_options(tablename='acct', inheritance='multi')

    acctid = Field(Unicode(22), required=True)

    fi = ManyToOne('FI')
    signon = ManyToOne('SIGNON')
    bals = OneToMany('BAL')
    fibals = OneToMany('FIBAL')
    trans = OneToMany('TRAN')


class BANKACCT(ACCT, Mergeable):
    signature = ('bankid', 'acctid')
    using_options(UniqueConstraint(*signature), tablename='bankacct',
                    inheritance='multi')

    bankid = Field(Unicode(9), required=True)
    branchid = Field(Unicode(22))
    accttype = Field(Enum('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE'),
                    required=True)
    acctkey = Field(Unicode(22))


class CCACCT(ACCT, Mergeable):
    signature = ('acctid', )
    using_options(UniqueConstraint(*signature), tablename='ccacct',
                    inheritance='multi')

    acctkey = Field(Unicode(22))


class INVACCT(ACCT, Mergeable):
    signature = ('brokerid', 'acctid')
    using_options(UniqueConstraint(*signature), tablename='invacct',
                    inheritance='multi')

    brokerid = Field(Unicode(22), required=True)

    invposs = OneToMany('INVPOS')


# Balances
class BAL(Entity, Mergeable):
    signature = ('acct', 'dtasof')
    using_options(UniqueConstraint(*signature), tablename='bal',
                    inheritance='multi')

    dtasof = Field(OFXDateTime, required=True)
    cursym = Field(Enum(*ISO4217), required=True)
    currate = Field(OFXDecimal(8))

    acct = ManyToOne('ACCT', required=True)


class BANKBAL(BAL):
    using_options(tablename='bankbal', inheritance='multi')

    ledgerbal = Field(OFXDecimal, required=True)
    availbal = Field(OFXDecimal, required=True)


class CCBAL(BAL):
    using_options(tablename='ccbal', inheritance='multi')

    ledgerbal = Field(OFXDecimal, required=True)
    availbal = Field(OFXDecimal, required=True)


class INVBAL(BAL):
    using_options(tablename='invbal', inheritance='multi')

    availcash = Field(OFXDecimal, required=True)
    marginbalance = Field(OFXDecimal, required=True)
    shortbalance = Field(OFXDecimal, required=True)
    buypower = Field(OFXDecimal)


class FIBAL(Entity, Mergeable):
    signature = ('acct', 'dtasof','name')
    using_options(UniqueConstraint(*signature), tablename='fibal')

    name = Field(Unicode(32), required=True)
    desc = Field(Unicode(80), required=True)
    baltype = Field(Enum('DOLLAR', 'PERCENT', 'NUMBER'), required=True)
    value = Field(OFXDecimal, required=True)
    dtasof = Field(OFXDateTime)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))

    acct = ManyToOne('ACCT', required=True)


# Transactions
class PAYEE(Entity):
    using_options(tablename='payee')

    name = Field(Unicode(32), required=True)
    addr1 = Field(Unicode(32), required=True)
    addr2 = Field(Unicode(32))
    addr3 = Field(Unicode(32))
    city = Field(Unicode(32), required=True)
    state = Field(Unicode(5), required=True)
    postalcode = Field(Unicode(11), required=True)
    country = Field(Enum(*ISO3166_1a3))
    phone = Field(Unicode(32), required=True)

    stmttrns = ManyToMany('STMTTRN')


class TRAN(Entity, Mergeable):
    signature = ('acct', 'fitid')
    using_options(UniqueConstraint(*signature), tablename='tran',
                    inheritance='multi')

    fitid = Field(Unicode(255), required=True)
    srvrtid = Field(Unicode(10))

    acct = ManyToOne('ACCT', required=True)


class STMTTRN(TRAN):
    using_options(tablename='stmttrn', inheritance='multi')

    trntype = Field(Enum('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                        'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                        'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                        'OTHER'), required=True)
    dtposted = Field(OFXDateTime, required=True)
    dtuser = Field(OFXDateTime)
    dtavail = Field(OFXDateTime)
    trnamt = Field(OFXDecimal, required=True)
    correctfitid = Field(OFXDecimal)
    correctaction = Field(Enum('REPLACE', 'DELETE'))
    checknum = Field(Unicode(12))
    refnum = Field(Unicode(32))
    sic = Field(Integer)
    payeeid = Field(Unicode(12))
    name = Field(Unicode(32))
    memo = Field(Unicode(255))
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    payee = ManyToMany('PAYEE')
    bankacctto = ManyToOne('BANKACCT')
    ccacctto = ManyToOne('CCACCT')


class INVBANKTRAN(STMTTRN):
    using_options(tablename='invbanktran', inheritance='multi')

    subacctfund = Field(Enum(*INVSUBACCTS), required=True)


class INVTRAN(TRAN):
    using_options(tablename='invtran', inheritance='multi')

    dttrade = Field(OFXDateTime, required=True)
    dtsettle = Field(OFXDateTime)
    reversalfitid = Field(Unicode(255))
    memo = Field(Unicode(255))


class INVBUY(INVTRAN):
    using_options(tablename='invbuy', inheritance='multi')

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
    loanid = Field(Unicode(32))
    loanprincipal = Field(OFXDecimal)
    loaninterest = Field(OFXDecimal)
    inv401ksource = Field(Enum(*INV401KSOURCES))
    dtpayroll = Field(OFXDateTime)
    prioryearcontrib = Field(Boolean)


class INVSELL(INVTRAN):
    using_options(tablename='invsell', inheritance='multi')

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
    loanid = Field(Unicode(32))
    statewithholding = Field(OFXDecimal)
    penalty = Field(OFXDecimal)
    inv401ksource = Field(Enum(*INV401KSOURCES))


class BUYDEBT(INVBUY):
    using_options(tablename='buydebt', inheritance='multi')

    accrdint = Field(OFXDecimal)

    sec = ManyToOne('DEBTINFO', required=True)


class BUYMF(INVBUY):
    using_options(tablename='buymf', inheritance='multi')

    buytype = Field(Enum(*BUYTYPES), required=True)
    relfitid = Field(Unicode(255))

    sec = ManyToOne('MFINFO', required=True)


class BUYOPT(INVBUY):
    using_options(tablename='buyopt', inheritance='multi')

    optbuytype = Field(Enum('BUYTOOPEN', 'BUYTOCLOSE'), required=True)
    shperctrct = Field(Integer, required=True)

    sec = ManyToOne('OPTINFO', required=True)


class BUYOTHER(INVBUY):
    using_options(tablename='buyother', inheritance='multi')

    sec = ManyToOne('OTHERINFO', required=True)


class BUYSTOCK(INVBUY):
    using_options(tablename='buystock', inheritance='multi')

    buytype = Field(Enum(*BUYTYPES), required=True)

    sec = ManyToOne('STOCKINFO', required=True)


class CLOSUREOPT(INVTRAN):
    using_options(tablename='closureopt', inheritance='multi')

    optaction = Field(Enum('EXERCISE', 'ASSIGN', 'EXPIRE'))
    units = Field(OFXDecimal, required=True)
    shperctrct = Field(Integer, required=True)
    subacctsec = Field(Enum(*INVSUBACCTS), required=True)
    relfitid = Field(Unicode(255))
    gain = Field(OFXDecimal)

    sec = ManyToOne('OPTINFO', required=True)


class INCOME(INVTRAN):
    using_options(tablename='income', inheritance='multi')

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
    using_options(tablename='invexpense', inheritance='multi')

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
    using_options(tablename='jrnlfund', inheritance='multi')

    subacctto = Field(Enum(*INVSUBACCTS), required=True)
    subacctfrom = Field(Enum(*INVSUBACCTS), required=True)
    total = Field(OFXDecimal, required=True)


class JRNLSEC(INVTRAN):
    using_options(tablename='jrnlsec', inheritance='multi')

    subacctto = Field(Enum(*INVSUBACCTS), required=True)
    subacctfrom = Field(Enum(*INVSUBACCTS), required=True)
    units = Field(OFXDecimal, required=True)

    sec = ManyToOne('SECINFO', required=True)


class MARGININTEREST(INVTRAN):
    using_options(tablename='margininterest', inheritance='multi')

    total = Field(OFXDecimal, required=True)
    subacctfund = Field(Enum(*INVSUBACCTS), required=True)
    cursym = Field(Enum(*ISO4217))
    currate = Field(OFXDecimal(8))
    origcursym = Field(Enum(*ISO4217))
    origcurrate = Field(OFXDecimal(8))


class REINVEST(INVTRAN):
    using_options(tablename='reinvest', inheritance='multi')

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
    using_options(tablename='retofcap', inheritance='multi')

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
    using_options(tablename='selldebt', inheritance='multi')

    sellreason = Field(Enum('CALL','SELL', 'MATURITY', required=True))
    accrdint = Field(OFXDecimal)

    sec = ManyToOne('DEBTINFO', required=True)


class SELLMF(INVSELL):
    using_options(tablename='sellmf', inheritance='multi')

    selltype = Field(Enum(*SELLTYPES), required=True)
    avgcostbasis = Field(OFXDecimal)
    relfitid = Field(Unicode(255))

    sec = ManyToOne('MFINFO', required=True)


class SELLOPT(INVSELL):
    using_options(tablename='sellopt', inheritance='multi')

    optselltype = Field(Enum('SELLTOCLOSE', 'SELLTOOPEN'), required=True)
    shperctrct = Field(Integer, required=True)
    relfitid = Field(Unicode(255))
    reltype = Field(Enum('SPREAD', 'STRADDLE', 'NONE', 'OTHER'))
    secured = Field(Enum('NAKED', 'COVERED'))

    sec = ManyToOne('OPTINFO', required=True)


class SELLOTHER(INVSELL):
    using_options(tablename='sellother', inheritance='multi')

    sec = ManyToOne('OTHERINFO', required=True)


class SELLSTOCK(INVSELL):
    using_options(tablename='sellstock', inheritance='multi')

    selltype = Field(Enum(*SELLTYPES), required=True)

    sec = ManyToOne('STOCKINFO', required=True)


class SPLIT(INVTRAN):
    using_options(tablename='split', inheritance='multi')

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
    using_options(tablename='transfer', inheritance='multi')

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
    signature = ('uniqueidtype', 'uniqueid')
    using_options(UniqueConstraint(*signature),
                                    tablename='secinfo', inheritance='multi')

    uniqueid = Field(Unicode(32), required=True)
    uniqueidtype = Field(Unicode(10), required=True)
    secname = Field(Unicode(120), required=True)
    ticker = Field(Unicode(32))
    fiid = Field(Unicode(32))
    rating = Field(Unicode(10))
    #unitprice = Field(OFXDecimal)
    #dtasof = Field(OFXDateTime)
    memo = Field(Unicode(255))

    invposs = OneToMany('INVPOS')

    @classmethod
    def match(cls, **kwargs):
        """
        Quicken will attempt to match securities downloaded in the SECLIST
        to securities in Quicken using the following logic:

        First Quicken checks to see if the security has already been matched
        by comparing the CUSIP or UNIQUEID in the download to the unique
        identifier stored in the Quicken database. If there is a match no
        additional steps are taken.

        When Quicken does not find a match based on CUSIP, it will compare the
        downloaded security name to the security names in the file. It will
        match the security if it finds an exact match for the security name.
        Next Quicken compares the ticker downloaded to the symbol for each
        security. When a ticker in the download matches the symbol for a
        security in the Quicken database they are matched. When there is no
        symbol for the security on the security list this step is skipped.
        Quicken will proceed to showing the security matching dialog.

        When Quicken cannot find a match based on one of the 3 criteria above
        it will show the security matching dialog. Under existing securities
        Quicken will show the entire security list. If Quicken thinks it has
        found a match based on comparison of security names it will default
        to the security it believes is the match in the list of securities.
        The user can accept the match, change to a different security, or
        choose the "No" radio button to create a new security.

        http://fi.intuit.com/ofximplementation/dl/OFXDataMappingGuide.pdf
        """
        for keys in ('uniqueidtype', 'uniqueid'), ('secname',), ('ticker',):
            attrs = dict([(key, kwargs[key]) for key in keys])
            try:
                return cls.query.filter_by(**attrs).one()
            except orm.exc.NoResultFound:
                continue

class DEBTINFO(SECINFO):
    using_options(tablename='debtinfo', inheritance='multi')

    parvalue = Field(OFXDecimal, required=True)
    debttype = Field(Enum('COUPON', 'ZERO'), required=True)
    debtclass = Field(Enum('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER'))
    couponrt = Field(OFXDecimal(4))
    dtcoupon = Field(OFXDateTime)
    couponfreq = Field(Enum('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER'))
    callprice = Field(OFXDecimal(4))
    yieldtocall = Field(OFXDecimal(4))
    dtcall = Field(OFXDateTime)
    calltype = Field(Enum('CALL', 'PUT', 'PREFUND', 'MATURITY'))
    ytmat = Field(OFXDecimal(4))
    dtmat = Field(OFXDateTime)
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(Unicode(32))


class MFASSETCLASS(Entity, Mergeable):
    signature = ('assetclass',)
    using_options(tablename='mfassetclass')

    assetclass = Field(Enum(*ASSETCLASSES), unique=True)
    percent = Field(OFXDecimal)

    mf = ManyToOne('MFINFO')


class FIMFASSETCLASS(Entity, Mergeable):
    signature = ('fiassetclass',)
    using_options(tablename='fimfassetclass')

    fiassetclass = Field(Unicode(32), unique=True)
    percent = Field(OFXDecimal)

    mf = ManyToOne('MFINFO')


class MFINFO(SECINFO):
    using_options(tablename='mfinfo', inheritance='multi')

    mftype = Field(Enum('OPENEND', 'CLOSEEND', 'OTHER'))
    yld = Field(OFXDecimal(4))
    dtyieldasof = Field(OFXDateTime)
    mfassetclasses = OneToMany('MFASSETCLASS')
    fimfassetclass = OneToMany('FIMFASSETCLASS')


class OPTINFO(SECINFO):
    using_options(tablename='optinfo', inheritance='multi')

    opttype = Field(Enum('CALL', 'PUT'), required=True)
    strikeprice = Field(OFXDecimal, required=True)
    dtexpire = Field(OFXDateTime, required=True)
    shperctrct = Field(Integer, required=True)
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(Unicode(32))

    sec = ManyToOne('SECINFO', required=True)


class OTHERINFO(SECINFO):
    using_options(tablename='otherinfo', inheritance='multi')

    typedesc = Field(Unicode(32))
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(Unicode(32))


class STOCKINFO(SECINFO):
    using_options(tablename='stockinfo', inheritance='multi')

    stocktype = Field(Enum('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER'))
    yld = Field(OFXDecimal(4))
    dtyieldasof = Field(OFXDateTime)
    typedesc = Field(Unicode(32))
    assetclass = Field(Enum(*ASSETCLASSES))
    fiassetclass = Field(Unicode(32))


# Securities prices
class SECPRICE(Entity, Mergeable):
    signature = ('sec', 'dtpriceasof')
    using_options(UniqueConstraint(*signature), tablename='secprice')

    dtpriceasof = Field(OFXDateTime, required=True)
    unitprice = Field(OFXDecimal(4), required=True)
    cursym = Field(Enum(*ISO4217), required=True)
    currate = Field(OFXDecimal(8))

    sec = ManyToOne('SECINFO', required=True)
    #stmtrs = ManyToOne('INVSTMTRS', required=True)
    #invpos = ManyToOne('INVPOS')


# Positions
class INVPOS(Entity, Mergeable):
    signature = ('sec', 'acct', 'heldinacct', 'postype')
    using_options(UniqueConstraint(*signature), tablename='invpos', inheritance='multi')

    heldinacct = Field(Enum(*INVSUBACCTS), required=True)
    postype = Field(Enum('SHORT', 'LONG'), required=True)
    units = Field(OFXDecimal, required=True)
    #unitprice = Field(OFXDecimal(4), required=True)
    mktval = Field(OFXDecimal, required=True)
    #dtpriceasof = Field(OFXDateTime, required=True)
    #cursym = Field(Enum(*ISO4217), required=True)
    #currate = Field(OFXDecimal(8))
    memo = Field(Unicode(255))
    inv401ksource = Field(Enum(*INV401KSOURCES))

    acct = ManyToOne('INVACCT', required=True)
    sec = ManyToOne('SECINFO', required=True)
    #stmtrs = ManyToOne('INVSTMTRS', required=True)


class POSDEBT(INVPOS):
    using_options(tablename='posdebt', inheritance='multi')


class POSMF(INVPOS):
    using_options(tablename='posmf', inheritance='multi')

    unitsstreet = Field(OFXDecimal)
    unitsuser = Field(OFXDecimal)
    reinvdiv = Field(Boolean)
    reinvcg = Field(Boolean)


class POSOPT(INVPOS):
    using_options(tablename='posopt', inheritance='multi')

    secured = Field(Enum('NAKED', 'COVERED'))


class POSOTHER(INVPOS):
    using_options(tablename='posother', inheritance='multi')


class POSSTOCK(INVPOS):
    using_options(tablename='posstock', inheritance='multi')

    unitsstreet = Field(OFXDecimal)
    unitsuser = Field(OFXDecimal)
    reinvdiv = Field(Boolean)
