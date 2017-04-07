# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# stdlib imports
import xml.etree.ElementTree as ET
from collections import UserList

# local imports
from ofxtools.Types import (
    Element,
    Bool,
    String,
    OneOf,
    Integer,
    Decimal,
    DateTime,
    NagString,
)
from ofxtools.lib import LANG_CODES, CURRENCY_CODES, COUNTRY_CODES


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

    Most subaggregates have been flattened so that data-bearing Elements are
    directly accessed as attributes of the containing Aggregate.

    The constructor takes an instance of ofx.Parser.Element, but this only
    works for simple Aggregates that don't contain structure that needs to
    be maintained (e.g. lists or subaggregates).  In general, we need to call
    Aggregate.from_etree() as a constructor to do pre- and post-processing.
    """
    # Sequence of subaggregates to strip before _flatten()ing and staple
    # on afterward intact
    _subaggregates = ()

    def __init__(self, **kwargs):
        # Set instance attributes for all input kwargs that are defined by
        # the class
        for attr in self.elements:
            value = kwargs.pop(attr, None)
            try:
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that no kwargs (not part of the class definition) are left over
        if kwargs:
            msg = "Parsed Element {} is undefined for {}".format(
                            self.__class__.__name__, str(list(kwargs.keys()))
            )
            raise ValueError(msg)

    @property
    def elements(self):
        """ dict of all Aggregate attributes that are Elements """
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k, v in m.__dict__.items()
                      if isinstance(v, Element)})
        return d

    @staticmethod
    def from_etree(elem):
        """
        Look up the Aggregate subclass for a given ofx.Parser.Element and
        feed it the Element to instantiate an Aggregate corresponding to the
        Element.tag.

        Main entry point for type conversion from ElementTree to Aggregate;
        invoked by Parser.OFXResponse which is in turn invoked by
        Parser.OFXTree.convert()
        """
        SubClass = globals()[elem.tag]
        SubClass._verify(elem)
        SubClass._groom(elem)
        subaggs = SubClass._preflatten(elem)
        attributes = SubClass._flatten(elem)
        instance = SubClass(**attributes)
        SubClass._postflatten(instance, subaggs)
        return instance

    @staticmethod
    def _verify(elem):
        """
        Enforce Aggregate-level structural constraints of the OFX spec.

        Extend in subclass.
        """
        pass

    @staticmethod
    def _groom(elem):
        """
        Modify incoming XML data to play nice with our Python scheme.

        Extend in subclass.
        """
        pass

    @staticmethod
    def _mutex(elem, mutexes):
        """
        Throw an error for Elements containing sub-Elements that are
        mutually exclusive per the OFX spec, and which will cause
        problems for _flatten().

        Used in subclass _verify() methods.
        """
        for mutex in mutexes:
            if (elem.find(mutex[0]) is not None and
                    elem.find(mutex[1]) is not None):
                msg = "{} may not contain both {} and {}".format(
                    elem.tag, mutex[0], mutex[1])
                raise ValueError(msg)

    @classmethod
    def _preflatten(cls, elem):
        """
        Strip any elements that will blow up _flatten(), and store them for
        postprocessing as stapled-on subaggregates.

        Returns a 'subaggregates' dict of {name: value}, where:
            * name is a string (the attribute name)
            * value is either:
                - an Aggregate instance, or
                - a list of Aggregate instances

        Extend in subclass.
        """
        subaggs = {}

        for tag in cls._subaggregates:
            subagg = elem.find(tag)
            if subagg is not None:
                elem.remove(subagg)
                subaggs[tag] = subagg

        return subaggs

    @classmethod
    def _flatten(cls, element):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggs = {}
        leaves = {}
        for child in element:
            tag = child.tag
            data = child.text or ''
            data = data.strip()
            if data:
                # it's a data-bearing leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>)
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # it's an aggregate.
                assert tag not in aggs
                aggs.update(cls._flatten(child))
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggs:
            assert key not in leaves
        leaves.update(aggs)

        return leaves

    @staticmethod
    def _postflatten(instance, subaggs):
        """
        Staple on attributes and subaggregates stripped during preprocessing.
        """
        for tag, elem in subaggs.items():
            if isinstance(elem, ET.Element):
                setattr(instance, tag.lower(), Aggregate.from_etree(elem))
            elif isinstance(elem, (list, UserList)):
                lst = [Aggregate.from_etree(e) for e in elem]
                setattr(instance, tag.lower(), lst)
            else:
                msg = "'{}' must be type {} or {}, not {}".format(
                    tag, 'ElementTree.Element', 'list', type(elem) 
                )
                raise ValueError(msg)

    def __repr__(self):
        attrs = ['%s=%r' % (attr, str(getattr(self, attr)))
                 for attr in self.elements
                 if getattr(self, attr) is not None]
        return '<%s %s>' % (self.__class__.__name__, ' '.join(attrs))


class FI(Aggregate):
    """
    OFX section 2.5.1.8

    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = String(32)
    fid = String(32)


class STATUS(Aggregate):
    """ OFX section 3.1.5 """
    code = Integer(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = String(255)


class SONRS(FI, STATUS):
    """ OFX section 2.5.1.6 """
    dtserver = DateTime(required=True)
    userkey = String(64)
    tskeyexpire = DateTime()
    language = OneOf(*LANG_CODES)
    dtprofup = DateTime()
    dtacctup = DateTime()
    sesscookie = String(1000)
    accesskey = String(1000)


class CURRENCY(Aggregate):
    """ OFX section 5.2 """
    cursym = OneOf(*CURRENCY_CODES)
    currate = Decimal(8)


class ORIGCURRENCY(CURRENCY):
    """ OFX section 5.2 """
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')

    @staticmethod
    def _verify(elem):
        """
        Aggregates may not contain both CURRENCY and ORIGCURRENCY per OFX spec.
        """
        super(ORIGCURRENCY, ORIGCURRENCY)._verify(elem)

        mutexes = [("CURRENCY", "ORIGCURRENCY")]
        ORIGCURRENCY._mutex(elem, mutexes)

    @classmethod
    def _preflatten(cls, elem):
        """
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        subaggs = super(ORIGCURRENCY, cls)._preflatten(elem)

        curtype = elem.find('CURRENCY') or elem.find('ORIGCURRENCY')
        if curtype is not None:
            ET.SubElement(elem, 'CURTYPE').text = curtype.tag

        return subaggs


class ACCTFROM(Aggregate):
    """ Base class (not in OFX spec) for *ACCTFROM/*ACCTTO """
    acctid = String(22, required=True)


class BANKACCTFROM(ACCTFROM):
    """ OFX section 11.3.1 """
    bankid = String(9, required=True)
    branchid = String(22)
    accttype = OneOf(*ACCTTYPES,
                     required=True)
    acctkey = String(22)


class BANKACCTTO(BANKACCTFROM):
    """ OFX section 11.3.1 """
    pass


class CCACCTFROM(ACCTFROM):
    """ OFX section 11.3.2 """
    acctkey = String(22)


class CCACCTTO(CCACCTFROM):
    """ OFX section 11.3.2 """
    pass


class INVACCTFROM(ACCTFROM):
    """ """
    brokerid = String(22, required=True)


# Balances
class LEDGERBAL(Aggregate):
    """ """
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class AVAILBAL(Aggregate):
    """ """
    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class INVBAL(Aggregate):
    """ OFX section 13.9.2.7 """
    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()

    _subaggregates = ('BALLIST',)


class BAL(CURRENCY):
    """ OFX section 3.1.4 """
    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()


# Securities
class SECID(Aggregate):
    """ """
    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class SECINFO(CURRENCY, SECID):
    """ """
    # FIs abuse SECNAME/TICKER
    # Relaxing the length constraints from the OFX spec does little harm
    # secname = String(120, required=True)
    secname = NagString(120, required=True)
    # ticker = String(32)
    ticker = NagString(32)
    fiid = String(32)
    rating = String(10)
    unitprice = Decimal()
    dtasof = DateTime()
    memo = String(255)


class DEBTINFO(SECINFO):
    """ """
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
    yieldtomat = Decimal(4)
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class MFINFO(SECINFO):
    """ OFX section 13.8.5.3 """
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()

    mfassetclass = []
    fimfassetclass = []

    _subaggregates = ('MFASSETCLASS', 'FIMFASSETCLASS')

    @staticmethod
    def _groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(MFINFO, MFINFO)._groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'


class PORTION(Aggregate):
    """ """
    assetclass = OneOf(*ASSETCLASSES, required=True)
    percent = Decimal(required=True)


class FIPORTION(Aggregate):
    """ """
    fiassetclass = String(32, required=True)
    percent = Decimal(required=True)


class OPTINFO(SECINFO):
    """ """
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    _subaggregates = ('SECID',)


class OTHERINFO(SECINFO):
    """ """
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class STOCKINFO(SECINFO):
    """ """
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    @staticmethod
    def _groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(STOCKINFO, STOCKINFO)._groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'


# Transactions
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


# Positions
class INVPOS(SECID, CURRENCY):
    """ """
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = Decimal(required=True)
    unitprice = Decimal(4, required=True)
    mktval = Decimal(required=True)
    dtpriceasof = DateTime(required=True)
    memo = String(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    """ """
    pass


class POSMF(INVPOS):
    """ """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()
    reinvcg = Bool()


class POSOPT(INVPOS):
    """ """
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    """ """
    pass


class POSSTOCK(INVPOS):
    """ """
    unitsstreet = Decimal()
    unitsuser = Decimal()
    reinvdiv = Bool()


# Lists
class List(Aggregate, UserList):
    """
    Base class for OFX *LIST
    """
    def __init__(self, **kwargs):
        UserList.__init__(self)
        Aggregate.__init__(self, **kwargs)

    def __hash__(self):
        """
        HACK - as a subclass of UserList, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    @classmethod
    def _preflatten(cls, elem):
        """
        UserList is a wrapper around a standard list, accessible through its
        'data' attribute.  If we create a synthetic subaggregate
        named 'data', whose value is a list of Etree.Elements, then
        Aggregate._postflatten() will set List.data to a list of converted
        Aggregates, and the Userlist interface will work normally.
        """
        subaggs = super(List, cls)._preflatten(elem)

        lst = []
        for tran in elem[:]:
            lst.append(tran)
            elem.remove(tran)
        subaggs['data'] = lst

        return subaggs


class BANKTRANLIST(List):
    """ OFX section 11.4.2.2 """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    @classmethod
    def _preflatten(cls, elem):
        """
        The first two children of the list are DTSTART/DTEND; don't remove.
        """
        subaggs = super(List, cls)._preflatten(elem)

        lst = []
        for tran in elem[2:]:
            lst.append(tran)
            elem.remove(tran)
        subaggs['data'] = lst

        return subaggs


class INVTRANLIST(BANKTRANLIST):
    """ OFX section 13.9.2.2 """
    pass


class SECLIST(List):
    """ OFX section 13.8.4.4 """
    pass


class BALLIST(List):
    """ OFX section 11.4.2.2 & 13.9.2.7 """
    pass


class MFASSETCLASS(List):
    """ OFX section 13.8.5.3 """
    pass


class FIMFASSETCLASS(List):
    """ OFX section 13.8.5.3 """
    pass


class INVPOSLIST(List):
    """ OFX section 13.9.2.2 """
    pass


# Statements
class TRNRS(Aggregate):
    """ Base class for *TRNRS (not in OFX spec) """
    trnuid = String(36, required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)

    _subaggregates = ()

    _rsTag = None
    _acctTag = None
    _tranList = None
    _unsupported = ()

    @classmethod
    def _preflatten(cls, elem):
        """ """
        # Don't call super() - start with a clean sheet
        # For statements we want to interpret cls._subaggregates
        # differently than Aggregate._preflatten()
        subaggs = {}
                               
        status = elem.find('STATUS')
        subaggs['STATUS'] = status
        elem.remove(status)

        stmtrs = elem.find(cls._rsTag)

        acctfrom = stmtrs.find(cls._acctTag)
        subaggs[cls._acctTag] = acctfrom
        stmtrs.remove(acctfrom)

        tranlist = stmtrs.find(cls._tranList)
        if tranlist is not None:
            subaggs[cls._tranList] = tranlist
            stmtrs.remove(tranlist)

        # N.B. as opposed to Aggregate._preflatten(), TRNRS._preflatten()
        # searches for _subaggregates in the *RS child, not the *TRNRS itself.
        for tag in cls._subaggregates:
            subagg = stmtrs.find(tag)
            if subagg is not None:
                stmtrs.remove(subagg)
                subaggs[tag] = subagg

        # Unsupported subaggregates
        for tag in cls._unsupported:
            child = stmtrs.find(tag)
            if child is not None:
                stmtrs.remove(child)

        return subaggs

    # Human-friendly attribute aliases
    @property
    def currency(self):
        return self.curdef

    @property
    def account(self):
        attr = getattr(self, self._acctTag.lower())
        return attr

    @property
    def transactions(self):
        attr = getattr(self, self._tranList.lower())
        return attr


class STMTTRNRS(TRNRS):
    """ OFX section 11.4.2.2 """
    _subaggregates = ('LEDGERBAL', 'AVAILBAL', 'BALLIST')

    _rsTag = 'STMTRS'
    _acctTag = 'BANKACCTFROM'
    _tranList = 'BANKTRANLIST'
    _unsupported = ('BANKTRANLISTP', 'CASHADVBALAMT', 'INTRATE', 'MKTGINFO')


class CCSTMTTRNRS(STMTTRNRS):
    """ OFX section 11.4.3.2 """
    _rsTag = 'CCSTMTRS'
    _acctTag = 'CCACCTFROM'
    _unsupported = ('BANKTRANLISTP', 'CASHADVBALAMT', 'INTRATEPURCH',
                    'INTRATECASH', 'INTRATEXFER', 'REWARDINFO', 'MKTGINFO')


class INVSTMTTRNRS(TRNRS):
    """ OFX section 13.9.2.1 """
    dtasof = DateTime(required=True)

    _subaggregates = ('INVPOSLIST', 'INVBAL')

    _rsTag = 'INVSTMTRS'
    _acctTag = 'INVACCTFROM'
    _tranList = 'INVTRANLIST'
    _unsupported = ('INVOOLIST', 'MKTGINFO', 'INV401K', 'INV401KBAL')

    # Human-friendly attribute aliases
    @property
    def datetime(self):
        return self.dtasof

    @property
    def positions(self):
        return self.invposlist
