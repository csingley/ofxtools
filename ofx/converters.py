import decimal
import datetime
import time
import re
import sys

from utilities import ISO4217, ISO3166_1a3, ISO639_2


if sys.version_info < (2, 7):
    raise RuntimeError('ofx.parser library requires Python v2.7+')


INV401KSOURCES = (u'PRETAX', u'AFTERTAX', u'MATCH', u'PROFITSHARING',
                    u'ROLLOVER', u'OTHERVEST', u'OTHERNONVEST')
ACCTTYPES = (u'CHECKING', u'SAVINGS', u'MONEYMRKT', u'CREDITLINE')
INVSUBACCTS = (u'CASH', u'MARGIN', u'SHORT', u'OTHER')
BUYTYPES = (u'BUY', u'BUYTOCOVER')
SELLTYPES = (u'SELL', u'SELLSHORT')
INCOMETYPES = (u'CGLONG', u'CGSHORT', u'DIV', u'INTEREST', u'MISC')
ASSETCLASSES = (u'DOMESTICBOND', u'INTLBOND', u'LARGESTOCK', u'SMALLSTOCK',
                u'INTLSTOCK', u'MONEYMRKT', u'OTHER')


class Element(object):
    """
    Base class of validator/type converter for OFX 'element', i.e. SGML leaf
    node that contains text data.

    Element instances store validation parameters relevant to a particular
    Aggregate subclass (e.g. maximum string length, decimal precision,
    required vs. optional, etc.) - they don't directly store the data
    itself (which lives in the __dict__ of an Aggregate instance).
    """
    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', False)
        self.required = required
        self._init(*args, **kwargs)

    def _init(self, *args, **kwargs):
        """ Override in subclass """
        if args or kwargs:
            raise ValueError("Unknown args for '%s'- args: %r; kwargs: %r"
                            % (self.__class__.__name__, args, kwargs))

    def convert(self, value):
        """ Override in subclass """
        raise NotImplementedError


class Boolean(Element):
    mapping = {'Y': True, 'N': False}

    def convert(self, value):
        if value is None and not self.required:
            return None
        return self.mapping[value]

    def unconvert(self, value):
        if value is None and not self.required:
            return None
        return {v:k for k,v in self.mapping.viewitems()}[value]

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
            raise ValueError("'%s' is too long; max length=%s" % (value, self.length))
        return unicode(value)


class OneOf(Element):
    def _init(self, *args, **kwargs):
        self.valid = set(args)
        super(OneOf, self)._init(**kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        if (value in self.valid):
            # unicode, dammit
            if isinstance(value, basestring):
                value = unicode(value)
            return value
        raise ValueError("'%s' is not OneOf %r" % (value, self.valid))


class Integer(Element):
    def _init(self, *args, **kwargs):
        length = None
        if args:
            length = args[0]
            args = args[1:]
        self.length = length
        super(Integer, self)._init(*args, **kwargs)

    def convert(self, value):
        if value is None and not self.required:
            return None
        value = int(value)
        if self.length is not None and value >= 10**self.length:
            raise ValueError('%s has too many digits; max digits=%s' % (value, self.length))
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
                            (orig_value, cls.formats.values()))

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


class Aggregate(object):
    """
    Base class of validator/type converter for OFX 'aggregate', i.e. SGML parent
    node that contains no data.  Data-bearing Elements are represented as
    attributes of the containing Aggregate.

    The Aggregate class is implemented as a data descriptor that, before
    setting an attribute, checks whether that attribute is defined as
    an Element in the class definition.  If it is, the Element's type
    conversion method is called, and the resulting value stored in the
    Aggregate instance's __dict__.
    """
    def __init__(self, **kwargs):
        for name, element in self.elements.viewitems():
            value = kwargs.pop(name, None)
            if element.required and value is None:
                raise ValueError("'%s' attribute is required for %s"
                                % (name, self.__class__.__name__))
            setattr(self, name, value)
        if kwargs:
            raise ValueError("Undefined element(s) for '%s': %s"
                            % (self.__class__.__name__, kwargs.viewkeys()))

    @property
    def elements(self):
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k,v in m.__dict__.iteritems() \
                                    if isinstance(v, Element)})
        return d

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

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, ' '.join(['%s=%r' % (attr, getattr(self, attr)) for attr in self.elements.viewkeys() if getattr(self, attr) is not None]))


class FI(Aggregate):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = Unicode(32)
    fid = Unicode(32)


class STATUS(Aggregate):
    code = Integer(6, required=True)
    severity = OneOf(u'INFO', u'WARN', u'ERROR', required=True)
    message = Unicode(255)


class SONRS(FI, STATUS):
    dtserver = DateTime(required=True)
    userkey = Unicode(64)
    tskeyexpire = DateTime()
    language = OneOf(*ISO639_2)
    dtprofup = DateTime()
    dtacctup = DateTime()
    sesscookie = Unicode(1000)
    accesskey = Unicode(1000)


class CURRENCY(Aggregate):
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)


class ORIGCURRENCY(CURRENCY):
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')


class ACCTFROM(Aggregate):
    acctid = Unicode(22, required=True)


class BANKACCTFROM(ACCTFROM):
    bankid = Unicode(9, required=True)
    branchid = Unicode(22)
    accttype = OneOf(*ACCTTYPES,
                    required=True)
    acctkey = Unicode(22)


class BANKACCTTO(BANKACCTFROM):
    pass


class CCACCTFROM(ACCTFROM):
    acctkey = Unicode(22)


class CCACCTTO(CCACCTFROM):
    pass


class INVACCTFROM(ACCTFROM):
    brokerid = Unicode(22, required=True)


# Balances
class LEDGERBAL(Aggregate):
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class AVAILBAL(Aggregate):
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class INVBAL(Aggregate):
    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()


class BAL(CURRENCY):
    name = Unicode(32, required=True)
    desc = Unicode(80, required=True)
    baltype = OneOf(u'DOLLAR', u'PERCENT', u'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()


# Securities
class SECID(Aggregate):
    uniqueid = Unicode(32, required=True)
    uniqueidtype = Unicode(10, required=True)


class SECINFO(CURRENCY, SECID):
    secname = Unicode(120, required=True)
    ticker = Unicode(32)
    fiid = Unicode(32)
    rating = Unicode(10)
    unitprice = Decimal()
    dtasof = DateTime()
    memo = Unicode(255)

    currency_parent = 'SECINFO'


class DEBTINFO(SECINFO):
    parvalue = Decimal(required=True)
    debttype = OneOf(u'COUPON', u'ZERO', required=True)
    debtclass = OneOf(u'TREASURY', u'MUNICIPAL', u'CORPORATE', u'OTHER')
    couponrt = Decimal(4)
    dtcoupon = DateTime()
    couponfreq = OneOf(u'MONTHLY', u'QUARTERLY', u'SEMIANNUAL', u'ANNUAL',
                            u'OTHER')
    callprice = Decimal(4)
    yieldtocall = Decimal(4)
    dtcall = DateTime()
    calltype = OneOf(u'CALL', u'PUT', u'PREFUND', u'MATURITY')
    ytmat = Decimal(4)
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


class MFINFO(SECINFO):
    mftype = OneOf(u'OPENEND', u'CLOSEEND', u'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()

    mfassetclass = []
    fimfassetclass = []


class MFASSETCLASS(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = Decimal()


class FIMFASSETCLASS(Aggregate):
    fiassetclass = Unicode(32)
    percent = Decimal()


class OPTINFO(SECINFO):
    opttype = OneOf(u'CALL', u'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


class OTHERINFO(SECINFO):
    typedesc = Unicode(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = Unicode(32)


class STOCKINFO(SECINFO):
    stocktype = OneOf(u'COMMON', u'PREFERRED', u'CONVERTIBLE', u'OTHER')
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


class STMTTRN(TRAN, ORIGCURRENCY):
    trntype = OneOf(u'CREDIT', u'DEBIT', u'INT', u'DIV', u'FEE', u'SRVCHG',
                    u'DEP', u'ATM', u'POS', u'XFER', u'CHECK', u'PAYMENT',
                    u'CASH', u'DIRECTDEP', u'DIRECTDEBIT', u'REPEATPMT',
                    u'OTHER', required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    correctfitid = Decimal()
    correctaction = OneOf(u'REPLACE', u'DELETE')
    checknum = Unicode(12)
    refnum = Unicode(32)
    sic = Integer()
    payeeid = Unicode(12)
    name = Unicode(32)
    memo = Unicode(255)
    inv401ksource = OneOf(*INV401KSOURCES)

    payee = None
    bankacctto = None
    ccacctto = None


class INVBANKTRAN(STMTTRN):
    subacctfund = OneOf(*INVSUBACCTS, required=True)

    currency_parent = 'STMTTRN'


class INVTRAN(TRAN):
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = Unicode(255)
    memo = Unicode(255)


class INVBUY(INVTRAN, SECID, ORIGCURRENCY):
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    markup = Decimal()
    commission = Decimal()
    taxes = Decimal()
    fees = Decimal()
    load = Decimal()
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    subacctfund = OneOf(*INVSUBACCTS)
    loanid = Unicode(32)
    loanprincipal = Decimal()
    loaninterest = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = DateTime()
    prioryearcontrib = Boolean()

    currency_parent = 'INVBUY'


class INVSELL(INVTRAN, SECID, ORIGCURRENCY):
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
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = Unicode(32)
    statewithholding = Decimal()
    penalty = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)

    currency_parent = 'INVSELL'


class BUYDEBT(INVBUY):
    accrdint = Decimal()


class BUYMF(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = Unicode(255)


class BUYOPT(INVBUY):
    optbuytype = OneOf(u'BUYTOOPEN', u'BUYTOCLOSE', required=True)
    shperctrct = Integer(required=True)


class BUYOTHER(INVBUY):
    pass


class BUYSTOCK(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(INVTRAN, SECID):
    optaction = OneOf(u'EXERCISE', u'ASSIGN', u'EXPIRE')
    units = Decimal(required=True)
    shperctrct = Integer(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = Unicode(255)
    gain = Decimal()


class INCOME(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = Boolean()
    withholding = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, ORIGCURRENCY):
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(INVTRAN):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = Decimal(required=True)


class JRNLSEC(INVTRAN, SECID):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = Decimal(required=True)


class MARGININTEREST(INVTRAN, ORIGCURRENCY):
    total = Decimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class REINVEST(INVTRAN, SECID, ORIGCURRENCY):
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
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID, ORIGCURRENCY):
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    sellreason = OneOf(u'CALL', u'SELL', u'MATURITY', required=True)
    accrdint = Decimal()


class SELLMF(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = Unicode(255)


class SELLOPT(INVSELL):
    optselltype = OneOf(u'SELLTOCLOSE', u'SELLTOOPEN', required=True)
    shperctrct = Integer(required=True)
    relfitid = Unicode(255)
    reltype = OneOf(u'SPREAD', u'STRADDLE', u'NONE', u'OTHER')
    secured = OneOf(u'NAKED', u'COVERED')


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
    tferaction = OneOf(u'IN', u'OUT', required=True)
    postype = OneOf(u'SHORT', u'LONG', required=True)
    avgcostbasis = Decimal()
    unitprice = Decimal()
    dtpurchase = DateTime()
    inv401ksource = OneOf(*INV401KSOURCES)


# Positions
class INVPOS(SECID, CURRENCY):
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf(u'SHORT', u'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    dtpriceasof = DateTime(required=True)
    memo = Unicode(255)
    inv401ksource = OneOf(*INV401KSOURCES)

    currency_parent = 'INVPOS'


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Boolean()
    reinvcg = Boolean()


class POSOPT(INVPOS):
    secured = OneOf(u'NAKED', u'COVERED')


class POSOTHER(INVPOS):
    pass


class POSSTOCK(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Boolean()
