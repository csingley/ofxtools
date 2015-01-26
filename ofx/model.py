# vim: set fileencoding=utf-8

# local imports
from lib import ISO639_2, ISO4217, ISO3166_1a3
from validators import (OFXElement, OFXbool, OFXstr, OneOf, OFXint, OFXdecimal,
                        OFXdatetime)


class OFXResponse(object):
    """ 
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements,
    SECLIST (description of referenced securities), and SONRS (server response
    to signon request).

    After conversion, each of these convenience attributes holds instances
    of various Aggregate subclasses.
    """
    sonrs = None
    statements = []
    seclist = []

    def __init__(self, tree, strict=True):
        """ 
        Initialize with ElementTree instance containing parsed OFX.

        The strict argument determines whether to throw an error for certain
        OFX data validation violations.
        """
        self.tree = tree
        self._processSONRS()
        self._processTRNRS()
        self._processSECLIST(strict=strict)

    def _processSONRS(self):
        """ Validate/convert server response to signon request """
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.sonrs = sonrs.convert()

    def _processTRNRS(self):
        """
        Validate/convert transaction response, which is the main section
        containing account statements
        """
        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (STMT, CCSTMT, INVSTMT):
            classname = stmtClass.__name__
            for trnrs in self.tree.findall('*/%sTRNRS' % classname):
                stmtrs = trnrs.find('%sRS' % classname)
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                if stmtrs is not None:
                    stmt = stmtClass(stmtrs)
                    # Staple the TRNRS wrapper data onto the STMT
                    stmt.trnuid = OFXstr(36).convert(trnrs.find('TRNUID').text)
                    stmt.status = trnrs.find('STATUS').convert()
                    cltcookie = trnrs.find('CLTCOOKIE')
                    if cltcookie is not None:
                        stmt.cltcookie = OFXstr(36).convert(cltcookie.text)
                    self.statements.append(stmt)

    def _processSECLIST(self, strict=True):
        """ 
        Validate/convert the list of description of securities referenced by
        INVSTMT (investment account statement)
        """
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is None:
            return
        for sec in seclist:
            if sec.tag == 'MFINFO':
                # Strip MFASSETCLASS/FIMFASSETCLASS 
                # - lists that will blow up _flatten()

                # Do all XPath searches before removing nodes from the tree
                #   which seems to mess up the DOM in Python3 and throw an
                #   AttributeError on subsequent searches.
                mfassetclass = sec.find('./MFASSETCLASS')
                fimfassetclass = sec.find('./FIMFASSETCLASS')

                if mfassetclass is not None:
                    # Convert PORTIONs; add to list on MFINFO
                    sec.mfassetclass = [p.convert() for p in mfassetclass]
                    sec.remove(mfassetclass)
                if fimfassetclass is not None:
                    # Convert FIPORTIONs; add to list on MFINFO
                    sec.fimfassetclass = [p.convert() for p in fimfassetclass]
                    sec.remove(fimfassetclass)

            self.seclist.append(sec.convert(strict=strict))


    def __repr__(self):
        return '<%s at at 0x%x>' % (self.__class__.__name__, id(self))

### STATEMENTS
class BaseSTMT(object):
    """ Base class for Python representation of OFX *STMT aggregate """
    # From TRNRS wrapper
    trnuid = None
    status = None
    cltcookie = None

    curdef = None
    acctfrom = None

    tranlist = None
    ballist = None

    def __init__(self, stmtrs):
        """ Initialize with *STMTRS Element """
        self.curdef = stmtrs.find('CURDEF').text
        self.acctfrom = stmtrs.find(self._acctTag).convert()
        self.process(stmtrs)

    def process(self, stmtrs):
        # Define in subclass
        raise NotImplementedError

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class STMT(BaseSTMT):
    """ Python representation of OFX STMT (bank statement) aggregate """
    ledgerbal = None
    availbal = None

    _acctTag = 'BANKACCTFROM'

    @property
    def bankacctfrom(self):
        return self.acctfrom

    @bankacctfrom.setter
    def bankacctfrom(self, value):
        self.acctfrom = value

    @property
    def banktranlist(self):
        return self.tranlist

    @banktranlist.setter
    def banktranlist(self, value):
        self.tranlist = value

    def process(self, stmtrs):
        # BANKTRANLIST
        tranlist = stmtrs.find('BANKTRANLIST')
        if tranlist is not None:
            self.tranlist = BANKTRANLIST(tranlist)

        # LEDGERBAL - mandatory
        self.ledgerbal = stmtrs.find('LEDGERBAL').convert()

        # AVAILBAL
        availbal = stmtrs.find('AVAILBAL')
        if availbal is not None:
            self.availbal = availbal.convert()

        # BALLIST
        ballist = stmtrs.find('BALLIST')
        if ballist:
            self.ballist = [bal.convert() for bal in ballist]

        # Unsupported subaggregates
        for tag in ('MKTGINFO', ):
            child = stmtrs.find(tag)
            if child:
                stmtrs.remove


class CCSTMT(STMT):
    """ 
    Python representation of OFX CCSTMT (credit card statement) 
    aggregate 
    """
    _acctTag = 'CCACCTFROM'

    @property
    def ccacctfrom(self):
        return self.acctfrom

    @ccacctfrom.setter
    def ccacctfrom(self, value):
        self.acctfrom = value


class INVSTMT(BaseSTMT):
    """ 
    Python representation of OFX INVSTMT (investment account statement) 
    aggregate 
    """
    dtasof = None

    invposlist = None
    invbal = None

    _acctTag = 'INVACCTFROM'

    @property
    def invacctfrom(self):
        return self.acctfrom

    @invacctfrom.setter
    def invacctfrom(self, value):
        self.acctfrom = value

    @property
    def invtranlist(self):
        return self.tranlist

    @invtranlist.setter
    def invtranlist(self, value):
        self.tranlist = value

    def process(self, invstmtrs):
        dtasof = invstmtrs.find('DTASOF').text
        self.dtasof = OFXdatetime.convert(dtasof)

        # INVTRANLIST
        tranlist = invstmtrs.find('INVTRANLIST')
        if tranlist is not None:
            self.tranlist = INVTRANLIST(tranlist)

        # INVPOSLIST
        poslist = invstmtrs.find('INVPOSLIST')
        if poslist is not None:
            self.invposlist = [pos.convert() for pos in poslist]

        # INVBAL
        invbal = invstmtrs.find('INVBAL')
        if invbal is not None:
            # First strip off BALLIST & process it
            ballist = invbal.find('BALLIST')
            if ballist is not None:
                invbal.remove(ballist)
                self.ballist = [bal.convert() for bal in ballist]
            # Now we can flatten the rest of INVBAL
            self.invbal = invbal.convert()

        # Unsupported subaggregates
        for tag in ('INVOOLIST', 'INV401K', 'INV401KBAL', 'MKTGINFO'):
            child = invstmtrs.find(tag)
            if child is not None:
                invstmtrs.remove


### TRANSACTION LISTS
class TRANLIST(list):
    """ 
    Base class for Python representation of OFX *TRANLIST (transaction list) 
    aggregate 
    """
    def __init__(self, tranlist):
        # Initialize with *TRANLIST Element
        dtstart, dtend = tranlist[0:2]
        tranlist = tranlist[2:]
        self.dtstart = OFXdatetime.convert(dtstart.text)
        self.dtend = OFXdatetime.convert(dtend.text)
        self.extend([tran.convert() for tran in tranlist])

    def __repr__(self):
        return "<%s dtstart='%s' dtend='%s' #transactions=%s>" % \
                (self.__class__.__name__, self.dtstart, self.dtend, len(self))


class BANKTRANLIST(TRANLIST):
    """
    Python representation of OFX BANKTRANLIST (bank transaction list) 
    aggregate
    """
    pass


class INVTRANLIST(TRANLIST):
    """
    Python representation of OFX INVTRANLIST (investment transaction list)
    aggregate 
    """
    pass


### AGGREGATES
class Aggregate(object):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.  Data-bearing OFXElements are represented as
    attributes of the containing Aggregate.

    The Aggregate class is implemented as a data descriptor that, before
    setting an attribute, checks whether that attribute is defined as
    an OFXElement in the class definition.  If it is, the OFXElement's type
    conversion method is called, and the resulting value stored in the
    Aggregate instance's __dict__.
    """
    def __init__(self, strict=True, **kwargs):
        assert strict in (True, False)
        # Use superclass __setattr__ to avoid AttributeError because
        # overridden __setattr__ below won't find strict in self.__dict__
        object.__setattr__(self, 'strict', strict)

        for name, element in self.elements.items():
            value = kwargs.pop(name, None)
            if element.required and value is None:
                raise ValueError("'%s' attribute is required for %s"
                                % (name, self.__class__.__name__))
            setattr(self, name, value)
        if kwargs:
            raise ValueError("Undefined element(s) for '%s': %s"
                            % (self.__class__.__name__, kwargs.keys()))

    @property
    def elements(self):
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k,v in m.__dict__.items() \
                                    if isinstance(v, OFXElement)})
        return d

    def __getattribute__(self, name):
        if name.startswith('__'):
            # Short-circuit private attributes to avoid infinite recursion
            attribute = object.__getattribute__(self, name)
        elif hasattr(self.__class__, name) and \
                isinstance(getattr(self.__class__, name), OFXElement):
            # Don't inherit OFXElement attributes from class
            attribute = self.__dict__[name]
        else:
            attribute = object.__getattribute__(self, name)
        return attribute

    def __setattr__(self, name, value):
        """ If attribute references an OFXElement, convert before setting """
        classattr = getattr(self.__class__, name)
        if isinstance(classattr, OFXElement):
            strict = self.strict
            value = classattr.convert(value, strict)
        object.__setattr__(self, name, value)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, ' '.join(['%s=%r' % (attr, getattr(self, attr)) for attr in self.elements.viewkeys() if getattr(self, attr) is not None]))


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


class FI(Aggregate):
    """
    FI aggregates are optional in SONRQ/SONRS; not all firms use them.
    """
    org = OFXstr(32)
    fid = OFXstr(32)


class STATUS(Aggregate):
    code = OFXint(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = OFXstr(255)


class SONRS(FI, STATUS):
    dtserver = OFXdatetime(required=True)
    userkey = OFXstr(64)
    tskeyexpire = OFXdatetime()
    language = OneOf(*ISO639_2)
    dtprofup = OFXdatetime()
    dtacctup = OFXdatetime()
    sesscookie = OFXstr(1000)
    accesskey = OFXstr(1000)


class CURRENCY(Aggregate):
    cursym = OneOf(*ISO4217)
    currate = OFXdecimal(8)


class ORIGCURRENCY(CURRENCY):
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')


class ACCTFROM(Aggregate):
    acctid = OFXstr(22, required=True)


class BANKACCTFROM(ACCTFROM):
    bankid = OFXstr(9, required=True)
    branchid = OFXstr(22)
    accttype = OneOf(*ACCTTYPES,
                    required=True)
    acctkey = OFXstr(22)


class BANKACCTTO(BANKACCTFROM):
    pass


class CCACCTFROM(ACCTFROM):
    acctkey = OFXstr(22)


class CCACCTTO(CCACCTFROM):
    pass


class INVACCTFROM(ACCTFROM):
    brokerid = OFXstr(22, required=True)


# Balances
class LEDGERBAL(Aggregate):
    balamt = OFXdecimal(required=True)
    dtasof = OFXdatetime(required=True)


class AVAILBAL(Aggregate):
    balamt = OFXdecimal(required=True)
    dtasof = OFXdatetime(required=True)


class INVBAL(Aggregate):
    availcash = OFXdecimal(required=True)
    marginbalance = OFXdecimal(required=True)
    shortbalance = OFXdecimal(required=True)
    buypower = OFXdecimal()


class BAL(CURRENCY):
    name = OFXstr(32, required=True)
    desc = OFXstr(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = OFXdecimal(required=True)
    dtasof = OFXdatetime()


# Securities
class SECID(Aggregate):
    uniqueid = OFXstr(32, required=True)
    uniqueidtype = OFXstr(10, required=True)


class SECINFO(CURRENCY, SECID):
    secname = OFXstr(120, required=True)
    ticker = OFXstr(32)
    fiid = OFXstr(32)
    rating = OFXstr(10)
    unitprice = OFXdecimal()
    dtasof = OFXdatetime()
    memo = OFXstr(255)


class DEBTINFO(SECINFO):
    parvalue = OFXdecimal(required=True)
    debttype = OneOf('COUPON', 'ZERO', required=True)
    debtclass = OneOf('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
    couponrt = OFXdecimal(4)
    dtcoupon = OFXdatetime()
    couponfreq = OneOf('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER')
    callprice = OFXdecimal(4)
    yieldtocall = OFXdecimal(4)
    dtcall = OFXdatetime()
    calltype = OneOf('CALL', 'PUT', 'PREFUND', 'MATURITY')
    ytmat = OFXdecimal(4)
    dtmat = OFXdatetime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class MFINFO(SECINFO):
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = OFXdecimal(4)
    dtyieldasof = OFXdatetime()


class PORTION(Aggregate):
    assetclass = OneOf(*ASSETCLASSES)
    percent = OFXdecimal()


class FIPORTION(Aggregate):
    fiassetclass = OFXstr(32)
    percent = OFXdecimal()


class OPTINFO(SECINFO):
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = OFXdecimal(required=True)
    dtexpire = OFXdatetime(required=True)
    shperctrct = OFXint(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class OTHERINFO(SECINFO):
    typedesc = OFXstr(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


class STOCKINFO(SECINFO):
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = OFXdecimal(4)
    dtyieldasof = OFXdatetime()
    typedesc = OFXstr(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = OFXstr(32)


# Transactions
class PAYEE(Aggregate):
    name = OFXstr(32, required=True)
    addr1 = OFXstr(32, required=True)
    addr2 = OFXstr(32)
    addr3 = OFXstr(32)
    city = OFXstr(32, required=True)
    state = OFXstr(5, required=True)
    postalcode = OFXstr(11, required=True)
    country = OneOf(*ISO3166_1a3)
    phone = OFXstr(32, required=True)


class TRAN(Aggregate):
    fitid = OFXstr(255, required=True)
    srvrtid = OFXstr(10)


class STMTTRN(TRAN, ORIGCURRENCY):
    trntype = OneOf('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                    'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                    'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                    'OTHER', required=True)
    dtposted = OFXdatetime(required=True)
    dtuser = OFXdatetime()
    dtavail = OFXdatetime()
    trnamt = OFXdecimal(required=True)
    correctfitid = OFXdecimal()
    correctaction = OneOf('REPLACE', 'DELETE')
    checknum = OFXstr(12)
    refnum = OFXstr(32)
    sic = OFXint()
    payeeid = OFXstr(12)
    name = OFXstr(32)
    memo = OFXstr(255)
    inv401ksource = OneOf(*INV401KSOURCES)

    payee = None
    bankacctto = None
    ccacctto = None


class INVBANKTRAN(STMTTRN):
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class INVTRAN(TRAN):
    dttrade = OFXdatetime(required=True)
    dtsettle = OFXdatetime()
    reversalfitid = OFXstr(255)
    memo = OFXstr(255)


class INVBUY(INVTRAN, SECID, ORIGCURRENCY):
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    markup = OFXdecimal()
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    subacctfund = OneOf(*INVSUBACCTS)
    loanid = OFXstr(32)
    loanprincipal = OFXdecimal()
    loaninterest = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)
    dtpayroll = OFXdatetime()
    prioryearcontrib = OFXbool()


class INVSELL(INVTRAN, SECID, ORIGCURRENCY):
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    markdown = OFXdecimal()
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    withholding = OFXdecimal()
    taxexempt = OFXbool()
    total = OFXdecimal(required=True)
    gain = OFXdecimal()
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    loanid = OFXstr(32)
    statewithholding = OFXdecimal()
    penalty = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class BUYDEBT(INVBUY):
    accrdint = OFXdecimal()


class BUYMF(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)
    relfitid = OFXstr(255)


class BUYOPT(INVBUY):
    optbuytype = OneOf('BUYTOOPEN', 'BUYTOCLOSE', required=True)
    shperctrct = OFXint(required=True)


class BUYOTHER(INVBUY):
    pass


class BUYSTOCK(INVBUY):
    buytype = OneOf(*BUYTYPES, required=True)


class CLOSUREOPT(INVTRAN, SECID):
    optaction = OneOf('EXERCISE', 'ASSIGN', 'EXPIRE')
    units = OFXdecimal(required=True)
    shperctrct = OFXint(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    relfitid = OFXstr(255)
    gain = OFXdecimal()


class INCOME(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    taxexempt = OFXbool()
    withholding = OFXdecimal()
    inv401ksource = OneOf(*INV401KSOURCES)


class INVEXPENSE(INVTRAN, SECID, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class JRNLFUND(INVTRAN):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    total = OFXdecimal(required=True)


class JRNLSEC(INVTRAN, SECID):
    subacctto = OneOf(*INVSUBACCTS, required=True)
    subacctfrom = OneOf(*INVSUBACCTS, required=True)
    units = OFXdecimal(required=True)


class MARGININTEREST(INVTRAN, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)


class REINVEST(INVTRAN, SECID, ORIGCURRENCY):
    incometype = OneOf(*INCOMETYPES, required=True)
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS)
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    commission = OFXdecimal()
    taxes = OFXdecimal()
    fees = OFXdecimal()
    load = OFXdecimal()
    taxexempt = OFXbool()
    inv401ksource = OneOf(*INV401KSOURCES)


class RETOFCAP(INVTRAN, SECID, ORIGCURRENCY):
    total = OFXdecimal(required=True)
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    subacctfund = OneOf(*INVSUBACCTS, required=True)
    inv401ksource = OneOf(*INV401KSOURCES)


class SELLDEBT(INVSELL):
    sellreason = OneOf('CALL', 'SELL', 'MATURITY', required=True)
    accrdint = OFXdecimal()


class SELLMF(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)
    avgcostbasis = OFXdecimal()
    relfitid = OFXstr(255)


class SELLOPT(INVSELL):
    optselltype = OneOf('SELLTOCLOSE', 'SELLTOOPEN', required=True)
    shperctrct = OFXint(required=True)
    relfitid = OFXstr(255)
    reltype = OneOf('SPREAD', 'STRADDLE', 'NONE', 'OTHER')
    secured = OneOf('NAKED', 'COVERED')


class SELLOTHER(INVSELL):
    pass


class SELLSTOCK(INVSELL):
    selltype = OneOf(*SELLTYPES, required=True)


class SPLIT(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    oldunits = OFXdecimal(required=True)
    newunits = OFXdecimal(required=True)
    numerator = OFXdecimal(required=True)
    denominator = OFXdecimal(required=True)
    fraccash = OFXdecimal()
    subacctfund = OneOf(*INVSUBACCTS)
    inv401ksource = OneOf(*INV401KSOURCES)


class TRANSFER(INVTRAN, SECID):
    subacctsec = OneOf(*INVSUBACCTS, required=True)
    units = OFXdecimal(required=True)
    tferaction = OneOf('IN', 'OUT', required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    avgcostbasis = OFXdecimal()
    unitprice = OFXdecimal()
    dtpurchase = OFXdatetime()
    inv401ksource = OneOf(*INV401KSOURCES)


# Positions
class INVPOS(SECID, CURRENCY):
    heldinacct = OneOf(*INVSUBACCTS, required=True)
    postype = OneOf('SHORT', 'LONG', required=True)
    units = OFXdecimal(required=True)
    unitprice = OFXdecimal(4, required=True)
    mktval = OFXdecimal(required=True)
    dtpriceasof = OFXdatetime(required=True)
    memo = OFXstr(255)
    inv401ksource = OneOf(*INV401KSOURCES)


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = OFXdecimal()
    unitsuser = OFXdecimal()
    reinvdiv = OFXbool()
    reinvcg = OFXbool()


class POSOPT(INVPOS):
    secured = OneOf('NAKED', 'COVERED')


class POSOTHER(INVPOS):
    pass


class POSSTOCK(INVPOS):
    unitsstreet = OFXdecimal()
    unitsuser = OFXdecimal()
    reinvdiv = OFXbool()

