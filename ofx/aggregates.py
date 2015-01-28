# vim: set fileencoding=utf-8
""" 
Python object model for fundamental data aggregates such as transactions, 
balances, and securities.
"""

# local imports
from elements import (Element, Bool, String, OneOf, Integer, Decimal,
                        DateTime)
from lib import ISO639_2, ISO4217, ISO3166_1a3


# Enums used in aggregate validation
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING',
                    'ROLLOVER', 'OTHERVEST', 'OTHERNONVEST')
ACCTTYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


class Aggregate(object):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.

    Initialize with an instance of ofx.Parser.Element.

    This class represents fundamental data aggregates such as transactions,
    balances, and securities.  Subaggregates have been flattened so that
    data-bearing Elements are directly accessed as attributes of the 
    containing Aggregate.

    Aggregates are grouped into higher-order containers such as lists
    and statements.  Although such higher-order containers are 'aggregates'
    per the OFX specification, they are represented here by their own Python
    classes other than Aggregate.
    """
    def __init__(self, elem, strict=True):
        assert strict in (True, False)
        self.strict = strict

        assert elem.tag == self.__class__.__name__
        attributes = elem._flatten()

        for name, element in self.elements.items():
            value = attributes.pop(name, None)
            if element.required and value is None:
                raise ValueError("'%s' attribute is required for %s"
                                % (name, self.__class__.__name__))
            setattr(self, name, value)
        if attributes:
            raise ValueError("Undefined element(s) for '%s': %s"
                            % (self.__class__.__name__, attributes.keys()))

    @property
    def elements(self):
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k,v in m.__dict__.items() \
                                    if isinstance(v, Element)})
        return d

    @staticmethod
    def from_etree(elem, strict=True):
        """ 
        Look up the Aggregate subclass for a given ofx.Parser.Element and
        feed it the Element to instantiate the Aggregate instance.
        """
        SubClass = globals()[elem.tag]
        instance = SubClass(elem, strict=strict)
        return instance

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, ' '.join(['%s=%r' % (attr, str(getattr(self, attr))) for attr in self.elements.viewkeys() if getattr(self, attr) is not None]))


class FI(Aggregate):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = String(32)
    fid = String(32)


class STATUS(Aggregate):
    code = Integer(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = String(255)


class SONRS(FI, STATUS):
    dtserver = DateTime(required=True)
    userkey = String(64)
    tskeyexpire = DateTime()
    language = OneOf(*ISO639_2)
    dtprofup = DateTime()
    dtacctup = DateTime()
    sesscookie = String(1000)
    accesskey = String(1000)


class CURRENCY(Aggregate):
    cursym = OneOf(*ISO4217)
    currate = Decimal(8)


class ORIGCURRENCY(CURRENCY):
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')

    def __init__(self, elem, strict=True):
        """ 
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        super(ORIGCURRENCY, self).__init__(elem, strict=strict)

        currency = elem.find('*/CURRENCY')
        origcurrency = elem.find('*/ORIGCURRENCY')
        if (currency is not None) and (origcurrency is not None):
            raise ValueError("<%s> may not contain both <CURRENCY> and \
                             <ORIGCURRENCY>" % elem.tag)
        curtype = currency
        if curtype is None:
            curtype = origcurrency
        if curtype is not None:
            curtype = curtype.tag
        self.curtype = curtype


class ACCTFROM(Aggregate):
    acctid = String(22, required=True)


class BANKACCTFROM(ACCTFROM):
    bankid = String(9, required=True)
    branchid = String(22)
    accttype = OneOf(*ACCTTYPES,
                    required=True)
    acctkey = String(22)


class BANKACCTTO(BANKACCTFROM):
    pass


class CCACCTFROM(ACCTFROM):
    acctkey = String(22)


class CCACCTTO(CCACCTFROM):
    pass


class INVACCTFROM(ACCTFROM):
    brokerid = String(22, required=True)


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
    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()


# Securities
class SECID(Aggregate):
    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class SECINFO(CURRENCY, SECID):
    secname = String(120, required=True)
    ticker = String(32)
    fiid = String(32)
    rating = String(10)
    unitprice = Decimal()
    dtasof = DateTime()
    memo = String(255)


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
    fiassetclass = String(32)


class MFINFO(SECINFO):
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()

    mfassetclass = []
    fimfassetclass = []

    def __init__(self, elem, strict=True):
        """ 
        Strip MFASSETCLASS/FIMFASSETCLASS - lists that will blow up _flatten()
        """
        extra_attrs = {}

        # Do all XPath searches before removing nodes from the tree
        #   which seems to mess up the DOM in Python3 and throw an
        #   AttributeError on subsequent searches.
        mfassetclass = elem.find('./MFASSETCLASS')
        fimfassetclass = elem.find('./FIMFASSETCLASS')

        if mfassetclass is not None:
            # Convert PORTIONs; save for later
            extra_attrs['mfassetclass'] = [Aggregate.from_etree(p) for p in mfassetclass]
            elem.remove(mfassetclass)
        if fimfassetclass is not None:
            # Convert FIPORTIONs; save for later
            extra_attrs['fimfassetclass'] = [Aggregate.from_etree(p) for p in fimfassetclass]
            elem.remove(fimfassetclass)

        super(MFINFO, self).__init__(elem, strict=strict)

        # Staple MFASSETCLASS/FIMFASSETCLASS onto MFINFO
        for attr,val in extra_attrs.items():
            setattr(self, attr, val)
         

class PORTION(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = Decimal()


class FIPORTION(Aggregate):
    fiassetclass = String(32)
    percent = Decimal()


class OPTINFO(SECINFO):
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class OTHERINFO(SECINFO):
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class STOCKINFO(SECINFO):
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


# Transactions
class PAYEE(Aggregate):
    name = String(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*ISO3166_1a3)
    phone = String(32, required=True)


class TRAN(Aggregate):
    fitid = String(255, required=True)
    srvrtid = String(10)


class STMTTRN(TRAN, ORIGCURRENCY):
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


class INVBANKTRAN(STMTTRN):
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(TRAN):
    dttrade = DateTime(required=True)
    dtsettle = DateTime()
    reversalfitid = String(255)
    memo = String(255)


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
    loanid = String(32)
    loanprincipal = Decimal()
    loaninterest = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = DateTime()
    prioryearcontrib = Bool()


class INVSELL(INVTRAN, SECID, ORIGCURRENCY):
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
    accrdint = Decimal()


class BUYMF(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = String(255)


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
    relfitid = String(255)
    gain = Decimal()


class INCOME(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = Bool()
    withholding = Decimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, SECID, ORIGCURRENCY):
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
    taxexempt = Bool()
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID, ORIGCURRENCY):
    total = Decimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
    accrdint = Decimal()


class SELLMF(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = Decimal()
    relfitid = String(255)


class SELLOPT(INVSELL):
    optselltype = OneOf('SELLTOCLOSE', 'SELLTOOPEN', required=True)
    shperctrct = Integer(required=True)
    relfitid = String(255)
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
class INVPOS(SECID, CURRENCY):
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    dtpriceasof = DateTime(required=True)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(INVPOS):
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    pass


class POSSTOCK(INVPOS):
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()


