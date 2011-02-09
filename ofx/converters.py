import decimal
import datetime
import time
import re

from utilities import ISO4217, ISO3166_1a3

INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING', 'ROLLOVER',
                'OTHERVEST', 'OTHERNONVEST')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


###
class Aggregate(object):
    """ """
    @property
    def elements(self):
        d = {}
        for m in self.__class__.mro():
            d.update({k: v for k,v in m.__dict__.iteritems() \
                                    if isinstance(v, Element)})
        return d

    def __init__(self, **kwargs):
        for name, element in self.elements.viewitems():
            value = kwargs.pop(name, None)
            if element.required and value is None:
                raise ValueError("'%s' attribute is required for %s"
                                % (name, self.__class__.__name__))
            setattr(self, name, value)
        if kwargs:
            raise ValueError("Undefined element(s) for '%s': %s"
                            % (self.__class__.__name__, str(kwargs.viewkeys())))


    def __getattribute__(self, name):
        if name.startswith('__'):
            # Short-circuit private attributes to avoid infinite recursion
            attribute = object.__getattribute__(self, name)
        elif isinstance(getattr(self.__class__, name), Element):
            # Don't inherit Element attributes from class
            attribute = self.__dict__[name]
        else:
            attribute = object.__getattribute__(self, name)
        return attribute

    def __setattr__(self, name, value):
        """ If attribute references an Element, convert before setting """
        classattr = getattr(self.__class__, name)
        if isinstance(classattr, Element):
            value = classattr.convert(value)
        object.__setattr__(self, name, value)


class Element(object):
    """ """
    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', False)
        self.required = required
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Override in subclass """
        if args or kwargs:
            raise ValueError("Unknown args for '%s'- args: %s; kwargs: %s"
                            % (self.__class__.__name__, str(args), str(kwargs)))

    def convert(self, value):
        """ Override in subclass """
        raise NotImplementedError


class Boolean(Element):
    mapping = {'Y': True, 'N': False}

    def convert(self, value):
        if value is None and not self.required:
            return None
        return cls.mapping[value]


class Unicode(Element):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(Unicode, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        if self.length is not None and len(value) > self.length:
            raise ValueError # FIXME
        return unicode(value)


class OneOf(Element):
    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super(OneOf, self)._init(**kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        if (value in self.valid):
            return value
        raise ValueError("'%s' is not OneOf%s" % (str(value), str(tuple(self.valid)))) # FIXME


class Integer(Element):
    def convert(self, value):
        if value is None and not self.required:
            return None
        return int(value)


class Decimal(Element):
    def _init(self, *args, **kwargs):
        precision = 2
        if args:
            precision = args[0]
            args = args[1:]
        self.precision = precision
        super(Decimal, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        value = decimal.Decimal(value)
        precision = decimal.Decimal('0.' + '0'*(self.precision-1) + '1')
        value.quantize(precision)
        return value


class DateTime(Element):
    # Valid datetime formats given by OFX spec in section 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{0,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S', 8: '%Y%m%d'}

    @classmethod
    def convert(cls, value):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value is None:
            return value

        # Pristine copy of input for error reporting purposes
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = cls.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            # Some FIs *cough* IBKR *cough* write crap for the TZ offset
            if gmt_offset == '-':
                gmt_offset = '0'
            gmt_offset = int(decimal.Decimal(gmt_offset)*3600) # hours -> seconds
        else:
            gmt_offset = 0
        format = cls.formats[len(value)]
        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                            (orig_value, str(cls.formats.values())))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    @classmethod
    def unconvert(cls, value):
        """ Input datetime.datetime in local time; output str in GMT. """
        # Pristine copy of input for error reporting purposes
        orig_value = value

        try:
            # Transform to GMT
            value = time.gmtime(time.mktime(value.timetuple()))
            # timetuples don't have usec precision
            #value = time.strftime('%s[0:GMT]' % cls.formats[14], value)
            value = time.strftime(cls.formats[14], value)
        except:
            raise # FIXME
        return value

###
class FI(Aggregate):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = Unicode(32, required=True)
    fid = Unicode(32)


# Accounts
class ACCT(Aggregate):
    acctid = Unicode(22, required=True)


class BANKACCT(ACCT):
    bankid = Unicode(9, required=True)
    branchid = Unicode(22)
    accttype = OneOf('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE',
                    required=True)
    acctkey = Unicode(22)


class CCACCT(ACCT):
    acctkey = Unicode(22)


class INVACCT(ACCT):
    brokerid = Unicode(22, required=True)


# Balances
class BAL(Aggregate):
    dtasof = DateTime(required=True)
    cursym = OneOf(*ISO4217, required=True)
    currate = Decimal(8)


class BANKBAL(BAL):
    ledgerbal = Decimal(required=True)
    availbal = Decimal(required=True)


class CCBAL(BAL):
    ledgerbal = Decimal(required=True)
    availbal = Decimal(required=True)


class INVBAL(BAL):
    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()


class FIBAL(Aggregate):
    name = Unicode(32, required=True)
    desc = Unicode(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)


# Securities
class SECID(Aggregate):
    uniqueid = Unicode(32, required=True)
    uniqueidtype = Unicode(10, required=True)

class SECINFO(SECID):
    secname = Unicode(120, required=True)
    ticker = Unicode(32)
    fiid = Unicode(32)
    rating = Unicode(10)
    unitprice = Decimal()
    dtasof = DateTime()
    currate = Decimal(8)
    cursym = OneOf(*ISO4217)
    memo = Unicode(255)


class DEBTINFO(SECINFO):
    parvalue = Decimal(required=True)
    debttype = OneOf('COUPON', 'ZERO', required=True)
    debtclass = OneOf('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
    couponrt = Decimal(4)
    dtcoupon = DateTime()
    couponfreq = OneOf('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER')
    callprice = Decimal(4)
    yieldtocall = Decimal(4)
    dtcall = DateTime()
    calltype = OneOf('CALL', 'PUT', 'PREFUND', 'MATURITY')
    ytmat = Decimal(4)
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


class MFASSETCLASS(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = Decimal()

    # FIXME
    #mf = ManyToOne('MFINFO')


class FIMFASSETCLASS(Aggregate):
    fiassetclass = Unicode(32)
    percent = Decimal()

    # FIXME
    #mf = ManyToOne('MFINFO')


class MFINFO(SECINFO):
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()

    # FIXME
    #mfassetclasses = OneToMany('MFASSETCLASS')
    #fimfassetclass = OneToMany('FIMFASSETCLASS')


class OPTINFO(SECINFO):
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)

    # FIXME
    #sec = ManyToOne('SECINFO', required=True)


class OTHERINFO(SECINFO):
    typedesc = Unicode(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


class STOCKINFO(SECINFO):
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    typedesc = Unicode(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


# Transactions
class PAYEE(Aggregate):
    name = Unicode(32, required=True)
    addr1 = Unicode(32, required=True)
    addr2 = Unicode(32)
    addr3 = Unicode(32)
    city = Unicode(32, required=True)
    state = Unicode(5, required=True)
    postalcode = Unicode(11, required=True)
    country = OneOf(*ISO3166_1a3)
    phone = Unicode(32, required=True)


class TRAN(Aggregate):
    fitid = Unicode(255, required=True)
    srvrtid = Unicode(10)


class STMTTRN(TRAN):
    trntype = OneOf('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                    'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                    'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                    'OTHER', required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    correctfitid = Decimal()
    correctaction = OneOf('REPLACE', 'DELETE')
    checknum = Unicode(12)
    refnum = Unicode(32)
    sic = Integer()
    payeeid = Unicode(12)
    name = Unicode(32)
    memo = Unicode(255)
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    inv401ksource = OneOf(*INV401KSOURCES)

    # FIXME
    #payee = ManyToMany('PAYEE')
    #bankacctto = ManyToOne('BANKACCT')
    #ccacctto = ManyToOne('CCACCT')


class INVBANKTRAN(STMTTRN):
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(TRAN):
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = Unicode(255)
    memo = Unicode(255)


class INVBUY(INVTRAN, SECID):
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    markup = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    total = Decimal(required=True)
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    subacctsec = OneOf(*INVSUBACCTS)
    subacctfund = OneOf(*INVSUBACCTS)
    loanid = Unicode(32)
    loanprincipal = Decimal()
    loaninterest = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = DateTime()
    prioryearcontrib = Boolean()


class INVSELL(INVTRAN, SECID):
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    markdown = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    withholding = Decimal()
    taxexempt = Boolean()
    total = Decimal(required=True)
    gain = Decimal()
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = Unicode(32)
    statewithholding = Decimal()
    penalty = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class BUYDEBT(INVBUY):
    accrdint = Decimal()


class BUYMF(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = Unicode(255)


class BUYOPT(INVBUY):
    optbuytype = OneOf('BUYTOOPEN', 'BUYTOCLOSE', required=True)
    shperctrct = Integer(required=True)


class BUYOTHER(INVBUY):
    pass


class BUYSTOCK(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(INVTRAN, SECID):
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE')
    units = Decimal(required=True)
    shperctrct = Integer(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = Unicode(255)
    gain = Decimal()


class INCOME(INVTRAN, SECID):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = Boolean()
    withholding = Decimal()
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, SECID):
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(INVTRAN):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = Decimal(required=True)


class JRNLSEC(INVTRAN, SECID):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)


class MARGININTEREST(INVTRAN):
    total = Decimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)


class REINVEST(INVTRAN, SECID):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    taxexempt = Boolean()
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID):
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)
    origcursym = OneOf(*ISO4217)
    origcurrate = Decimal(8)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    sellreason = OneOf('CALL','SELL', 'MATURITY', required=True)
    accrdint = Decimal()


class SELLMF(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = Unicode(255)


class SELLOPT(INVSELL):
    optselltype = OneOf('SELLTOCLOSE', 'SELLTOOPEN', required=True)
    shperctrct = Integer(required=True)
    relfitid = Unicode(255)
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


class SELLOTHER(INVSELL):
    pass


class SELLSTOCK(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    oldunits = Decimal(required=True)
    newunits = Decimal(required=True)
    numerator = Decimal(required=True)
    denominator = Decimal(required=True)
    fraccash = Decimal()
    subacctfund = OneOf(*INVSUBACCTS)
    inv401ksource = OneOf(*INV401KSOURCES)


class TRANSFER(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)
    tferaction = OneOf('IN', 'OUT', required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    avgcostbasis = Decimal()
    unitprice = Decimal()
    dtpurchase = DateTime()
    inv401ksource = OneOf(*INV401KSOURCES)


# Positions
class INVPOS(SECID):
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    dtpriceasof = DateTime(required=True)
    cursym = OneOf(*ISO4217, required=True)
    currate = Decimal(8)
    memo = Unicode(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Boolean()
    reinvcg = Boolean()


class POSOPT(INVPOS):
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    pass


class POSSTOCK(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Boolean()
