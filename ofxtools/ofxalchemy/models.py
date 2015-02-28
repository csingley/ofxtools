# vim: set fileencoding=utf-8
""" 
SQLAlchemy object model for fundamental OFX data aggregates such as transactions, 
balances, and securities.
"""
# 3rd party imports
from sqlalchemy import (
    Column,
    Enum,
    Integer,
    String,
    Text,
    ForeignKey,
    ForeignKeyConstraint,
    )
import sqlalchemy.types
from sqlalchemy.schema import (
    UniqueConstraint,
    CheckConstraint,
    )
from sqlalchemy.ext.declarative import (
    declarative_base,
    as_declarative,
    declared_attr,
    has_inherited_table,
    )
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )

# local imports
from types import Numeric, OFXDateTime, OFXBoolean
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


# DB setup
DBSession = scoped_session(sessionmaker())


# Object classes
@as_declarative()
class Base(object):
    """
    Base class representing the main OFX 'aggregates', i.e. SGML parent nodes
    that contain no data.

    These aggregates are grouped into higher-order containers such as lists
    and statements.  Although such higher-order containers are 'aggregates'
    per the OFX specification, they are not persisted by our model; their
    transitory representations are modelled in ofxalchemy.Parser.
    """
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def primary_keys(cls):
        return [c.name for c in cls.__table__.c if c.primary_key]

    @classmethod
    def _fingerprint(cls, **attrs):
        """ Extract an instance's primary key dict from a dict of attributes """
        def bindkey(key):
            """ 
            Look up a primary key's value in the given dict of attributes
            """
            k = key
            try: 
                v = attrs[k]
            except KeyError:
                # Allow relationship, not just FK id integer
                if k.endswith('_id'):
                    k = k[:-3]
                    v = attrs[k]
                else:
                    raise
            return k, v

        try:
            return dict([bindkey(pk) for pk in cls.primary_keys()])
        except KeyError:
            msg = "%s: Required attributes %s not satisfied by arguments %s" % (
                cls.__name__, cls.primary_keys(), attrs)
            raise ValueError(msg)

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, ', '.join(
            ['%s=%r' % (c.name, str(getattr(self, c.name))) \
             for c in self.__class__.__table__.c \
             if getattr(self, c.name) is not None]
        ))


def Inheritor(parent_table):
    class InheritanceMixin(object):
        """
        Uses a surrogate primary key to implement joined-table inheritance;
        the natural keys are given as a class attribute 'pks'
        """
        @declared_attr.cascading
        def id(cls): 
            if has_inherited_table(cls):
                return Column(Integer, ForeignKey('%s.id' % parent_table),
                              primary_key=True)
            else:
                return Column(Integer, primary_key=True)

        subclass = Column(String(length=32), nullable=False)

        @declared_attr
        def __mapper_args__(cls):
            if has_inherited_table(cls):
                return {'polymorphic_identity': cls.__name__.lower()}
            else:
                return {'polymorphic_on': cls.subclass}

        @classmethod
        def primary_keys(cls):
            return cls.pks

        # Be careful about multiple inheritance.  Subclasses of INV{BUY,SELL}
        # also use __table_args__ to define constraints checking that the
        # dollar amounts total correctly.  This is OK because the polymorphic 
        # inheritance scheme for INVTRAN subclasses only requires the uniqueness 
        # constraint on the base table (i.e. INVTRAN) which holds these PKs, 
        # so INVTRAN subclasses are free to clobber __table_args__ by inheriting 
        # it from INV{BUY,SELL}...
        # ...but be careful.
        @declared_attr.cascading
        def __table_args__(cls):
            if has_inherited_table(cls):
                return None
            else:
                return (UniqueConstraint(*cls.pks),)

    return InheritanceMixin


### CURRENCIES
class CURRENCY(object):
    """ Declarative mixin representing OFX <CURRENCY> aggregate """
    cursym = Column(Enum(*CURRENCY_CODES, name='cursym'))
    currate = Column(Numeric())


class ORIGCURRENCY(CURRENCY):
    """ Declarative mixin representing OFX <ORIGCURRENCY> aggregate """
    curtype = Column(Enum('CURRENCY', 'ORIGCURRENCY', name='curtype'))


### ACCOUNTS
class AcctMixin(object):
    """ """
    # This version of __table_args__ overrides that provided by
    # InheritanceMixin to move definition of UniqueConstraint from the base
    # table to the child table, as required for *ACCT{FROM,TO}
    @declared_attr.cascading
    def __table_args__(cls):
        if has_inherited_table(cls):
            return (UniqueConstraint(*cls.pks),)
        else:
            return None


class ACCTFROM(AcctMixin, Inheritor('acctfrom'), Base):
    """ 
    Synthetic base class of {BANK,CC,INV}ACCTFROM - not in OFX spec. 
    """
    # Extra attribute definitions not from OFX spec
    name = Column(Text)


class BANKACCTFROM(ACCTFROM):
    bankid = Column(String(length=9), nullable=False)
    branchid = Column(String(length=22))
    acctid = Column(String(length=22), nullable=False)
    accttype = Column(Enum(*ACCTTYPES, name='accttype'), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['bankid', 'acctid', ]


class CCACCTFROM(ACCTFROM):
    acctid = Column(String(length=22), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['acctid', ]


class INVACCTFROM(ACCTFROM):
    brokerid = Column(String(length=22), nullable=False)
    acctid = Column(String(length=22), nullable=False)

    pks = ['brokerid', 'acctid']


class ACCTTO(AcctMixin, Inheritor('acctto'), Base):
    """ 
    Synthetic base class of {BANK,CC,INV}ACCTTO - not in OFX spec. 
    """
    # Extra attribute definitions not from OFX spec
    name = Column(Text)


class BANKACCTTO(ACCTTO):
    # Elements from OFX spec
    bankid = Column(String(length=9), nullable=False)
    branchid = Column(String(length=22))
    acctid = Column(String(length=9), nullable=False)
    accttype = Column(Enum(*ACCTTYPES, name='accttype'), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['bankid', 'acctid', ]


class CCACCTTO(ACCTTO):
    # Elements from OFX spec
    acctid = Column(String(length=22), nullable=False, unique=True)
    acctkey = Column(String(length=22))

    pks = ['acctid', ]


### BALANCES
class Balance(object):
    """
    Declarative mixin holding object model common to OFX *BAL aggregates.

    We deviate from the OFX spec by storing the STMT.dtasof in *BAL.dtasof
    in order to uniquely link the balance with the statement without 
    persisting a STMT object. We make *BAL.dtasof mandatory and use it
    as part of the primary key.
    """
    @declared_attr
    def acctfrom_id(cls):
        return Column(Integer, ForeignKey('acctfrom.id'), primary_key=True)

    @declared_attr
    def acctfrom(cls):
        return relationship('ACCTFROM', backref='%ss' % cls.__name__.lower())

    @declared_attr
    def dtasof(cls):
        return Column(OFXDateTime, primary_key=True)


class LEDGERBAL(Balance, Base):
    balamt = Column(Numeric(), nullable=False)


class AVAILBAL(Balance, Base):
    balamt = Column(Numeric(), nullable=False)


class INVBAL(Balance, Base):
    availcash = Column(Numeric(), nullable=False)
    marginbalance = Column(Numeric(), nullable=False)
    shortbalance = Column(Numeric(), nullable=False)
    buypower = Column(Numeric())


class BAL(Balance, CURRENCY, Base):
    name = Column(String(length=32), primary_key=True)
    desc = Column(String(length=80), nullable=False)
    baltype = Column(Enum('DOLLAR', 'PERCENT', 'NUMBER', name='baltype'),
                     nullable=False)
    value = Column(Numeric(), nullable=False)


### SECURITIES
class SECID(object):
    """
    Mixin to hold logic for securities-related investment transactions (INVTRAN)
    and also OPTINFO
    """
    @declared_attr
    def secinfo_id(cls):
        return Column(Integer, ForeignKey('secinfo.id'))

    @declared_attr
    def secinfo(cls):
        return relationship('SECINFO')


class SECINFO(Inheritor('secinfo'), CURRENCY, Base):
    uniqueidtype = Column(String(length=10), nullable=False)
    uniqueid = Column(String(length=32), nullable=False)
    # FIs *cough* IBKR *cough* abuse SECNAME/TICKER with too much information
    # Relaxing the length constraints from the OFX spec does little harm
    #secname = Column(String(length=120), nullable=False)
    secname = Column(String(length=255), nullable=False)
    #ticker = Column(String(length=32))
    ticker = Column(String(length=255))
    fiid = Column(String(length=32))
    rating = Column(String(length=10))
    unitprice = Column(Numeric())
    dtasof = Column(OFXDateTime)
    memo = Column(String(length=255))

    pks = ['uniqueid', 'uniqueidtype']
   

class DEBTINFO(SECINFO):
    parvalue = Column(Numeric(), nullable=False)
    debttype = Column(Enum('COUPON', 'ZERO', name='debttype'), nullable=False)
    debtclass = Column(Enum('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER',
                           name='debtclass')
                      )
    couponrt = Column(Numeric())
    dtcoupon = Column(OFXDateTime)
    couponfreq = Column(Enum('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER', name='couponfreq')
                       )
    callprice = Column(Numeric())
    yieldtocall = Column(Numeric())
    dtcall = Column(OFXDateTime)
    calltype = Column(Enum('CALL', 'PUT', 'PREFUND', 'MATURITY', 
                           name='calltype')
                     )
    ytmat = Column(Numeric())
    dtmat = Column(OFXDateTime)
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


class MFINFO(SECINFO):
    mftype = Column(Enum('OPENEND', 'CLOSEEND', 'OTHER', name='mftype'))
    yld = Column(Numeric())
    dtyieldasof = Column(OFXDateTime)


class PORTION(Base):
    # Added for SQLAlchemy object model
    mfinfo_id = Column(Integer, ForeignKey('mfinfo.id'), primary_key=True)
    mfinfo = relationship('MFINFO', backref='mfassetclasses')

    # Elements from OFX spec
    assetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )
    percent = Column(Numeric(), nullable=False)


class FIPORTION(Base):
    # Added for SQLAlchemy object model
    mfinfo_id = Column(Integer, ForeignKey('mfinfo.id'), primary_key=True)
    mfinfo = relationship('MFINFO', backref='fimfassetclasses')

    # Elements from OFX spec
    fiassetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )
    percent = Column(Numeric(), nullable=False)


class OPTINFO(SECINFO):
    opttype = Column(Enum('CALL', 'PUT', name='opttype'), nullable=False)
    strikeprice = Column(Numeric(), nullable=False)
    dtexpire = Column(OFXDateTime, nullable=False)
    shperctrct = Column(Integer, nullable=False)
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


class OTHERINFO(SECINFO):
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))
    percent = Column(Numeric())


class STOCKINFO(SECINFO):
    typedesc = Column(String(length=32))
    stocktype = Column(Enum('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER',
                           name='stocktype')
                      )
    yld = Column(Numeric()) # 'yield' is a reserved word in Python
    dtyieldasof = Column(OFXDateTime)
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


### TRANSACTIONS
class PAYEE(Base):
    # Elements from OFX spec
    name = Column(String(length=32), primary_key=True)
    addr1 = Column(String(length=32), nullable=False)
    addr2 = Column(String(length=32))
    addr3 = Column(String(length=32))
    city = Column(String(length=32), nullable=False)
    state = Column(String(length=5), nullable=False)
    postalcode = Column(String(length=11), nullable=False)
    country = Column(Enum(*COUNTRY_CODES, name='country'))
    phone = Column(String(length=32), nullable=False)


class BANKTRAN(ORIGCURRENCY):
    """ 
    Synthetic mixin for common elements of STMTTRN/INVBANKTRAN - not in OFX spec
    """
    # Added for SQLAlchemy object model
    @declared_attr
    def acctto_id(cls):
        return Column(Integer, ForeignKey('acctto.id'))

    @declared_attr
    def acctto(cls):
        return relationship('ACCTTO')

    @declared_attr
    def payee_name(cls):
        return Column(String(32), ForeignKey('payee.name'))

    @declared_attr
    def payee(cls):
        return relationship('PAYEE')

    # Elements from OFX spec
    fitid = Column(String(length=255), primary_key=True)
    srvrtid = Column(String(length=10))
    trntype = Column(Enum('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
                    'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
                    'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
                    'OTHER', name='trntype'), nullable=False)
    dtposted = Column(OFXDateTime, nullable=False)
    dtuser = Column(OFXDateTime)
    dtavail = Column(OFXDateTime)
    trnamt = Column(Numeric(), nullable=False)
    correctfitid = Column(Numeric())
    correctaction = Column(Enum('REPLACE', 'DELETE', name='correctaction'))
    checknum = Column(String(length=12))
    refnum = Column(String(length=32))
    sic = Column(Integer())
    payeeid = Column(String(length=12))
    name = Column(String(length=32))
    memo = Column(String(length=255))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class STMTTRN(BANKTRAN, Base):
     # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('acctfrom.id'), primary_key=True)
    acctfrom = relationship('ACCTFROM', foreign_keys=[acctfrom_id,], backref='stmttrns')


class INVBANKTRAN(BANKTRAN, Base):
    # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('invacctfrom.id'), primary_key=True)
    acctfrom = relationship('INVACCTFROM')

    # Elements from OFX spec
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class INVTRAN(Inheritor('invtran'), Base):
    # Added for SQLAlchemy object model
    @declared_attr
    def acctfrom_id(cls):
        return Column(Integer, ForeignKey('invacctfrom.id'))
    
    @declared_attr
    def acctfrom(cls):
        return relationship('INVACCTFROM', backref='invtrans')

    subclass = Column(String(length=32), nullable=False)

    # Elements from OFX spec
    fitid = Column(String(length=255))
    srvrtid = Column(String(length=10))
    dttrade = Column(OFXDateTime, nullable=False)
    dtsettle = Column(OFXDateTime)
    reversalfitid = Column(String(length=255))
    memo = Column(String(length=255))


    pks = ['acctfrom_id', 'fitid']


class INVBUYSELL(SECID, ORIGCURRENCY):
    """ Synthetic base class of INVBUY/INVSELL - not in OFX spec """
    units = Column(Numeric(), nullable=False)
    unitprice = Column(Numeric(), nullable=False)
    commission = Column(Numeric())
    taxes = Column(Numeric())
    fees = Column(Numeric())
    load = Column(Numeric())
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'))
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class INVBUY(INVBUYSELL):
    """ Declarative mixin for OFX INVBUY aggregate """
    markup = Column(Numeric())
    loanid = Column(String(length=32))
    loanprincipal = Column(Numeric())
    loaninterest = Column(Numeric())
    dtpayroll = Column(OFXDateTime)
    prioryearcontrib = Column(OFXBoolean())

    # Be careful about multiple inheritance.  Subclasses of INV{BUY,SELL}
    # also inherit from INVTRAN, which also uses __table_args__ to define
    # define uniqueness constraint for the natural PKs (acctfrom_id, fitid).
    # This is OK because the polymorphic inheritance scheme for INVTRAN
    # subclasses only requires the uniqueness constraint on the base table
    # (i.e. INVTRAN) which holds these PKs, so INVTRAN subclasses are free
    # to clobber __table_args__ by inheriting it from INV{BUY,SELL}...
    # ...but be careful.
    __table_args__ = (
        CheckConstraint(
            """ 
            total = units * (unitprice + markup) 
                    + (commission + fees + load + taxes)
            """
        ),
    ) 


class INVSELL(INVBUYSELL):
    """ Declarative mixin for OFX INVSELL aggregate """
    markdown = Column(Numeric())
    withholding = Column(Numeric())
    taxexempt = Column(OFXBoolean())
    gain = Column(Numeric())
    loanid = Column(String(length=32))
    statewithholding = Column(Numeric())
    penalty = Column(Numeric())

    # Be careful about multiple inheritance.  Subclasses of INV{BUY,SELL}
    # also inherit from INVTRAN, which also uses __table_args__ to define
    # define uniqueness constraint for the natural PKs (acctfrom_id, fitid).
    # This is OK because the polymorphic inheritance scheme for INVTRAN
    # subclasses only requires the uniqueness constraint on the base table
    # (i.e. INVTRAN) which holds these PKs, so INVTRAN subclasses are free
    # to clobber __table_args__ by inheriting it from INV{BUY,SELL}...
    # ...but be careful.
    __table_args__ = (
        CheckConstraint(
            """ 
            total = units * (unitprice - markdown) 
                    - (commission + fees + load + taxes + penalty 
                        + withholding + statewithholding)
            """
        ),
    ) 


class BUYDEBT(INVBUY, INVTRAN):
    accrdint = Column(Numeric())


class BUYMF(INVBUY, INVTRAN):
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)
    relfitid = Column(String(length=255))


class BUYOPT(INVBUY, INVTRAN):
    optbuytype = Column(Enum('BUYTOOPEN', 'BUYTOCLOSE', name='obtbuytype'),
                        nullable=False
                       )
    shperctrct = Column(Integer, nullable=False)


class BUYOTHER(INVBUY, INVTRAN):
    pass


class BUYSTOCK(INVBUY, INVTRAN):
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)


class CLOSUREOPT(SECID, INVTRAN):
    optaction = Column(Enum('EXERCISE', 'ASSIGN', 'EXPIRE', name='optaction'))
    units = Column(Numeric(), nullable=False)
    shperctrct = Column(Integer, nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    relfitid = Column(String(length=255))
    gain = Column(Numeric())
    

class INCOME(SECID, ORIGCURRENCY, INVTRAN):
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    taxexempt = Column(OFXBoolean())
    withholding = Column(Numeric())
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class INVEXPENSE(SECID, ORIGCURRENCY, INVTRAN):
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class JRNLFUND(INVTRAN):
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    total = Column(Numeric(), nullable=False)


class JRNLSEC(SECID, INVTRAN):
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    units = Column(Numeric(), nullable=False)


class MARGININTEREST(ORIGCURRENCY, INVTRAN):
    total = Column(Numeric(), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class REINVEST(SECID, ORIGCURRENCY, INVTRAN):
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'))
    units = Column(Numeric(), nullable=False)
    unitprice = Column(Numeric(), nullable=False)
    commission = Column(Numeric())
    taxes = Column(Numeric())
    fees = Column(Numeric())
    load = Column(Numeric())
    taxexempt = Column(OFXBoolean())
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    
    # Be careful about multiple inheritance.  REINVEST  also inherits from 
    # INVTRAN, which also uses __table_args__ to define uniqueness constraint
    # for the natural PKs (acctfrom_id, fitid).   This is OK because the 
    # polymorphic inheritance scheme for INVTRAN subclasses only requires the 
    # uniqueness constraint on the base table (i.e. INVTRAN) 
    # which holds these PKs, so REINVEST is free to clobber __table_args__ ...
    # ...but be careful.
    __table_args__ = (
        CheckConstraint(
            """ 
            total = units * (unitprice) + (commission + fees + load + taxes)
            """
        ),
    ) 


class RETOFCAP(SECID, ORIGCURRENCY, INVTRAN):
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class SELLDEBT(INVSELL, INVTRAN):
    sellreason = Column(Enum('CALL', 'SELL', 'MATURITY', name='sellreason'),
                        nullable=False
                       )
    accrdint = Column(Numeric())


class SELLMF(INVSELL, INVTRAN):
    selltype = Column(Enum(*SELLTYPES, name='selltype'), nullable=False)
    avgcostbasis = Column(Numeric())
    relfitid = Column(String(length=255))


class SELLOPT(INVSELL, INVTRAN):
    optselltype = Column(Enum('SELLTOCLOSE', 'SELLTOOPEN', name='optselltype'),
                         nullable=False)
    shperctrct = Column(Integer, nullable=False)
    relfitid = Column(String(length=255))
    reltype = Column(Enum('SPREAD', 'STRADDLE', 'NONE', 'OTHER', name='reltype')
                    )
    secured = Column(Enum('NAKED', 'COVERED', name='secured'))


class SELLOTHER(INVSELL, INVTRAN):
    pass


class SELLSTOCK(INVSELL, INVTRAN):
    selltype = Column(Enum(*SELLTYPES, name='selltype'), nullable=False)


class SPLIT(SECID, INVTRAN):
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    oldunits = Column(Numeric(), nullable=False)
    newunits = Column(Numeric(), nullable=False)
    numerator = Column(Numeric(), nullable=False)
    denominator = Column(Numeric(), nullable=False)
    fraccash = Column(Numeric())
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class TRANSFER(SECID, INVTRAN):
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    units = Column(Numeric(), nullable=False)
    tferaction = Column(Enum('IN', 'OUT', name='tferaction'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    avgcostbasis = Column(Numeric())
    unitprice = Column(Numeric())
    dtpurchase = Column(OFXDateTime)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


### POSITIONS
class INVPOS(Inheritor('invpos'), SECID, CURRENCY, Base):
    # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('invacctfrom.id'))
    acctfrom = relationship('INVACCTFROM', backref='invposs')
    dtasof = Column(OFXDateTime)

    # Elements from OFX spec
    heldinacct = Column(Enum(*INVSUBACCTS, name='heldinacct'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    units = Column(Numeric(), nullable=False)
    unitprice = Column(Numeric(), nullable=False)
    mktval = Column(Numeric(), nullable=False)
    dtpriceasof = Column(OFXDateTime, nullable=False)
    memo = Column(String(length=255))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))
  
    pks = ['acctfrom_id', 'secinfo_id', 'dtasof']


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = Column(Numeric())
    unitsuser = Column(Numeric())
    reinvdiv = Column(OFXBoolean())
    reinvcg = Column(OFXBoolean())


class POSOPT(INVPOS):
    secured = Column(Enum('NAKED', 'COVERED', name='secured'))


class POSOTHER(INVPOS):
    pass

class POSSTOCK(INVPOS):
    unitsstreet = Column(Numeric())
    unitsuser = Column(Numeric())
    reinvdiv = Column(OFXBoolean())

