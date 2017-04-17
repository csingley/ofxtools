# vim: set fileencoding=utf-8
"""
SQLAlchemy object model for fundamental OFX data aggregates such as transactions,
balances, and securities.
"""
# stdlib imports
#import sqlite3


# 3rd party imports
from sqlalchemy import (
    Column,
    Enum,
    Integer,
    String,
    Text,
    ForeignKey,
    event,
    and_,
    )
from sqlalchemy.engine import Engine
from sqlalchemy.schema import (
    UniqueConstraint,
    CheckConstraint,
    )
from sqlalchemy.ext.declarative import (
    as_declarative,
    declared_attr,
    has_inherited_table,
    )
from sqlalchemy.orm import (
    relationship,
    backref,
    )


# local imports
from ofxtools.ofxalchemy.Types import (
    OFXNumeric,
    OFXDateTime,
    OFXBoolean,
    NagString,
)
from ofxtools.ofxalchemy.database import Base
from ofxtools.models.i18n import CURRENCY_CODES, COUNTRY_CODES


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


### OBJECT CLASSES
def Inheritor(parent_table):
    """
    Mixin factory implementing joined-table inheritance.

    Uses a surrogate primary key; the natural keys are given as a class
    attribute 'pks'.
    """
    class InheritanceMixin(object):
        @declared_attr.cascading
        def id(cls):
            if has_inherited_table(cls):
                return Column(
                    Integer, ForeignKey('%s.id' % parent_table,
                                        onupdate='CASCADE', ondelete='CASCADE'),
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
    currate = Column(OFXNumeric())


class ORIGCURRENCY(CURRENCY):
    """ Declarative mixin representing OFX <ORIGCURRENCY> aggregate """
    curtype = Column(Enum('CURRENCY', 'ORIGCURRENCY', name='curtype'))


### ACCOUNTS
class AcctMixin(object):
    """
    Declarative mixin holding object model common to all OFX <*ACCT{FROM,TO}>
    aggregates
    """
    # Extra attribute definitions not from OFX spec
    name = Column(Text)

    # This version of __table_args__ overrides that provided by
    # Inheritor.InheritanceMixin to move definition of UniqueConstraint from
    # the base table to the child table, as required for *ACCT{FROM,TO}
    @declared_attr.cascading
    def __table_args__(cls):
        if has_inherited_table(cls):
            return (UniqueConstraint(*cls.pks),)
        else:
            return None


class BankAcctMixin(object):
    """ Declarative mixin representing OFX <BANKACCT{FROM,TO}> aggregate """
    bankid = Column(String(length=9), nullable=False)
    branchid = Column(String(length=22))
    acctid = Column(String(length=22), nullable=False)
    accttype = Column(Enum(*ACCTTYPES, name='accttype'), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['bankid', 'acctid', ]


class CcAcctMixin(object):
    """ Declarative mixin representing OFX <CCACCT{FROM,TO}> aggregate """
    acctid = Column(String(length=22), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['acctid', ]


class ACCTFROM(AcctMixin, Inheritor('acctfrom'), Base):
    """
    Synthetic base class of {BANK,CC,INV}ACCTFROM - not in OFX spec.

    We need a parent DB table mostly for the benefit of <BAL> which can be
    related to either <BANKACCTFROM>/<CCACCTFROM> or <INVACCTFROM>.

    @@TODO - it would be nice to define a child table of ACCTFROM that's the
    parent for {BANK,CC}ACCTFROM but not INVACCTFROM, to ensure that *ACCTFROM
    foreign key references inserted into STMTTRN, LEDGERBAL, etc. cannot
    refer to INVACCTFROM.  However, that will require some reworking of
    AcctMixin and InheritanceMixin.
    """
    pass


class BANKACCTFROM(BankAcctMixin, ACCTFROM):
    pass


class CCACCTFROM(CcAcctMixin, ACCTFROM):
    pass


class INVACCTFROM(ACCTFROM):
    brokerid = Column(String(length=22), nullable=False)
    acctid = Column(String(length=22), nullable=False)

    pks = ['brokerid', 'acctid']


class ACCTTO(AcctMixin, Inheritor('acctto'), Base):
    """
    Synthetic base class of {BANK,CC,INV}ACCTTO - not in OFX spec.
    """
    pass


class BANKACCTTO(BankAcctMixin, ACCTTO):
    pass


class CCACCTTO(CcAcctMixin, ACCTTO):
    pass


### BALANCES
class Balance(object):
    """
    Declarative mixin holding object model common to OFX <*BAL> aggregates.

    We deviate from the OFX spec by storing the STMT.dtasof in *BAL.dtasof
    in order to uniquely link the balance with the statement without
    persisting a STMT object. We make *BAL.dtasof mandatory and use it
    as part of the primary key.
    """
    # Added for SQLAlchemy object model
    @declared_attr
    def acctfrom_id(cls):
        return Column(
            Integer, ForeignKey(
                'acctfrom.id', onupdate='CASCADE', ondelete='CASCADE'
            ), primary_key=True
        )

    @declared_attr
    def acctfrom(cls):
        return relationship(
            'ACCTFROM', backref=backref('%ss' % cls.__name__.lower(),
                                        cascade='all, delete-orphan',
                                        passive_deletes=True,
                                       )
        )

    # Extra attribute definitions not from OFX spec
    @declared_attr
    def dtasof(cls):
        return Column(OFXDateTime, primary_key=True)


class LEDGERBAL(Balance, Base):
    balamt = Column(OFXNumeric(), nullable=False)


class AVAILBAL(Balance, Base):
    balamt = Column(OFXNumeric(), nullable=False)


class INVBAL(Base):
    """
    We deviate from the OFX spec by storing the STMT.dtasof in INVBAL.dtasof
    in order to uniquely link the balance with the statement without persisting
    an INVSTMT object. We make INVBAL.dtasof mandatory and use it as part of
    the primary key.
    """
    # Added for SQLAlchemy object model
    acctfrom_id = Column(
        Integer, ForeignKey('invacctfrom.id',
                            onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    acctfrom = relationship(
        'INVACCTFROM', backref=backref('invbals',
                                       cascade='all, delete-orphan',
                                       passive_deletes=True,
                                      )
    )

    # Extra attribute definitions not from OFX spec
    dtasof = Column(OFXDateTime, primary_key=True)

    # Elements from OFX spec
    availcash = Column(OFXNumeric(), nullable=False)
    marginbalance = Column(OFXNumeric(), nullable=False)
    shortbalance = Column(OFXNumeric(), nullable=False)
    buypower = Column(OFXNumeric())


class BAL(Balance, CURRENCY, Base):
    name = Column(String(length=32), primary_key=True)
    desc = Column(String(length=80), nullable=False)
    baltype = Column(Enum('DOLLAR', 'PERCENT', 'NUMBER', name='baltype'),
                     nullable=False)
    value = Column(OFXNumeric(), nullable=False)


### SECURITIES
class SECID(object):
    """
    Mixin to hold logic for securities-related investment transactions (INVTRAN)
    and also INVPOS and OPTINFO
    """
    @declared_attr
    def secinfo_id(cls):
        return Column(Integer,
                      ForeignKey('secinfo.id',
                                 onupdate='CASCADE', ondelete='CASCADE'),
                      nullable=False,
                     )

    @declared_attr
    def secinfo(cls):
        # @@FIXME backrefs don't work b/c used by INVTRAN/INVPOS/OPTINFO
        return relationship('SECINFO')


class SECINFO(Inheritor('secinfo'), CURRENCY, Base):
    uniqueidtype = Column(String(length=10), nullable=False)
    uniqueid = Column(String(length=32), nullable=False)
    # FIs *cough* IBKR *cough* abuse SECNAME/TICKER with too much information
    # Relaxing the length constraints from the OFX spec does little harm
    #secname = Column(String(length=120), nullable=False)
    secname = Column(NagString(length=120), nullable=False)
    #ticker = Column(String(length=32))
    ticker = Column(NagString(length=32))
    fiid = Column(String(length=32))
    rating = Column(String(length=10))
    unitprice = Column(OFXNumeric())
    dtasof = Column(OFXDateTime)
    memo = Column(String(length=255))

    pks = ['uniqueid', 'uniqueidtype']


class DEBTINFO(SECINFO):
    parvalue = Column(OFXNumeric(), nullable=False)
    debttype = Column(Enum('COUPON', 'ZERO', name='debttype'), nullable=False)
    debtclass = Column(Enum('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER',
                           name='debtclass')
                      )
    couponrt = Column(OFXNumeric())
    dtcoupon = Column(OFXDateTime)
    couponfreq = Column(Enum('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                            'OTHER', name='couponfreq')
                       )
    callprice = Column(OFXNumeric())
    yieldtocall = Column(OFXNumeric())
    dtcall = Column(OFXDateTime)
    calltype = Column(Enum('CALL', 'PUT', 'PREFUND', 'MATURITY',
                           name='calltype')
                     )
    ytmat = Column(OFXNumeric())
    dtmat = Column(OFXDateTime)
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


class MFINFO(SECINFO):
    mftype = Column(Enum('OPENEND', 'CLOSEEND', 'OTHER', name='mftype'))
    yld = Column(OFXNumeric())
    dtyieldasof = Column(OFXDateTime)


class PORTION(Base):
    # Added for SQLAlchemy object model
    mfinfo_id = Column(
        Integer, ForeignKey(
            'mfinfo.id', onupdate='CASCADE', ondelete='CASCADE'
        ), primary_key=True
    )
    mfinfo = relationship(
        'MFINFO', backref=backref('mfassetclasses',
                                  cascade='all, delete-orphan',
                                  passive_deletes=True,
                                 )
    )

    # Elements from OFX spec
    assetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )
    percent = Column(OFXNumeric(), nullable=False)


class FIPORTION(Base):
    # Added for SQLAlchemy object model
    mfinfo_id = Column(
        Integer, ForeignKey(
            'mfinfo.id', onupdate='CASCADE', ondelete='CASCADE'
        ), primary_key=True
    )
    mfinfo = relationship(
        'MFINFO', backref=backref('fimfassetclasses',
                                  cascade='all, delete-orphan',
                                  passive_deletes=True,
                                 )
    )

    # Elements from OFX spec
    fiassetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )
    percent = Column(OFXNumeric(), nullable=False)


class OPTINFO(SECINFO):
    opttype = Column(Enum('CALL', 'PUT', name='opttype'), nullable=False)
    strikeprice = Column(OFXNumeric(), nullable=False)
    dtexpire = Column(OFXDateTime, nullable=False)
    shperctrct = Column(Integer, nullable=False)
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


class OTHERINFO(SECINFO):
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))
    percent = Column(OFXNumeric())


class STOCKINFO(SECINFO):
    typedesc = Column(String(length=32))
    stocktype = Column(Enum('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER',
                           name='stocktype')
                      )
    yld = Column(OFXNumeric()) # 'yield' is a reserved word in Python
    dtyieldasof = Column(OFXDateTime)
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


### TRANSACTIONS
class PAYEE(Base):
    # Elements from OFX spec
    # Relaxing the length restriction from OFX spec does little harm
    #name = Column(String(length=32), primary_key=True)
    name = Column(NagString(length=32), primary_key=True)
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
        return Column(
            Integer, ForeignKey('acctto.id',
                                onupdate='CASCADE', ondelete='CASCADE'))

    @declared_attr
    def payee_name(cls):
        return Column(
            String(32), ForeignKey('payee.name',
                                   onupdate='CASCADE', ondelete='CASCADE'))

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
    trnamt = Column(OFXNumeric(), nullable=False)
    correctfitid = Column(OFXNumeric())
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
    acctfrom_id = Column(
        Integer, ForeignKey(
            'acctfrom.id', onupdate='CASCADE', ondelete='CASCADE'
        ), primary_key=True
    )

    acctfrom = relationship(
        'ACCTFROM', backref=backref('stmttrns',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                   )
    )

    @declared_attr
    def acctto(cls):
        return relationship(
            'ACCTTO', backref=backref('stmttrns',
                                      cascade='all, delete-orphan',
                                      passive_deletes=True,
                                     )
        )

    @declared_attr
    def payee(cls):
        return relationship(
            'PAYEE', backref=backref('stmttrns',
                                     cascade='all, delete-orphan',
                                     passive_deletes=True,
                                    )
        )



class INVBANKTRAN(BANKTRAN, Base):
    # Added for SQLAlchemy object model
    acctfrom_id = Column(
        Integer, ForeignKey(
            'invacctfrom.id', onupdate='CASCADE', ondelete='CASCADE'
        ), primary_key=True
    )
    acctfrom = relationship(
        'INVACCTFROM', backref=backref('invbanktrans',
                                       cascade='all, delete-orphan',
                                       passive_deletes=True,
                                      )
        )

    @declared_attr
    def acctto(cls):
        return relationship(
            'ACCTTO', backref=backref('invbanktrans',
                                      cascade='all, delete-orphan',
                                      passive_deletes=True,
                                     )
        )

    @declared_attr
    def payee(cls):
        return relationship(
            'PAYEE', backref=backref('invbanktrans',
                                     cascade='all, delete-orphan',
                                     passive_deletes=True,
                                    )
        )

    # Elements from OFX spec
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class INVTRAN(Inheritor('invtran'), Base):
    # Added for SQLAlchemy object model
    @declared_attr
    def acctfrom_id(cls):
        return Column(
            Integer, ForeignKey(
                'invacctfrom.id', onupdate='CASCADE', ondelete='CASCADE'
            ), nullable=False,
        )

    @declared_attr
    def acctfrom(cls):
        return relationship(
        'INVACCTFROM', backref=backref('invtrans',
                                       cascade='all, delete-orphan',
                                       passive_deletes=True,
                                      )
        )

    # Elements from OFX spec
    fitid = Column(String(length=255), nullable=False)
    srvrtid = Column(String(length=10))
    dttrade = Column(OFXDateTime, nullable=False)
    dtsettle = Column(OFXDateTime)
    reversalfitid = Column(String(length=255))
    memo = Column(String(length=255))

    pks = ['acctfrom_id', 'fitid']


class INVBUYSELL(SECID, ORIGCURRENCY):
    """ Synthetic base class of INVBUY/INVSELL - not in OFX spec """
    units = Column(OFXNumeric(), nullable=False)
    unitprice = Column(OFXNumeric(), CheckConstraint('unitprice >= 0'),
                       nullable=False)
    # Alas, some FIs (*cough* IBKR) violate the OFX spec by booking trade
    # reversals that include negative commissions
    #commission = Column(OFXNumeric(), CheckConstraint('commission >= 0'))
    commission = Column(OFXNumeric(),)
    taxes = Column(OFXNumeric(), CheckConstraint('taxes >= 0'))
    fees = Column(OFXNumeric(), CheckConstraint('fees >= 0'))
    load = Column(OFXNumeric(), CheckConstraint('load >= 0'))
    total = Column(OFXNumeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class INVBUY(INVBUYSELL):
    """ Declarative mixin for OFX INVBUY aggregate """
    markup = Column(OFXNumeric(), CheckConstraint('markup >= 0'))
    loanid = Column(String(length=32))
    loanprincipal = Column(OFXNumeric())
    loaninterest = Column(OFXNumeric())
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
            total = -1 * units * (unitprice + markup)
                    - (commission + fees + load + taxes)
            """
        ),
    )


class INVSELL(INVBUYSELL):
    """ Declarative mixin for OFX INVSELL aggregate """
    markdown = Column(OFXNumeric(), CheckConstraint('markdown >= 0'))
    withholding = Column(OFXNumeric(), CheckConstraint('withholding >= 0'))
    taxexempt = Column(OFXBoolean())
    gain = Column(OFXNumeric())
    loanid = Column(String(length=32))
    statewithholding = Column(OFXNumeric(), 
                              CheckConstraint('statewithholding >= 0'))
    penalty = Column(OFXNumeric())

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
            total = -1 * units * (unitprice - markdown)
                    - (commission + fees + load + taxes + penalty
                        + withholding + statewithholding)
            """
        ),
    )


class BUYDEBT(INVBUY, INVTRAN):
    accrdint = Column(OFXNumeric())


class BUYMF(INVBUY, INVTRAN):
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)
    relfitid = Column(String(length=255))


class BUYOPT(INVBUY, INVTRAN):
    optbuytype = Column(Enum('BUYTOOPEN', 'BUYTOCLOSE', name='obtbuytype'),
                        nullable=False,
                       )
    shperctrct = Column(Integer, nullable=False)


class BUYOTHER(INVBUY, INVTRAN):
    pass


class BUYSTOCK(INVBUY, INVTRAN):
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)


class CLOSUREOPT(SECID, INVTRAN):
    optaction = Column(Enum('EXERCISE', 'ASSIGN', 'EXPIRE', name='optaction'),
                      nullable=False,
                      )
    units = Column(OFXNumeric(), nullable=False)
    shperctrct = Column(Integer, nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    relfitid = Column(String(length=255))
    gain = Column(OFXNumeric())


class INCOME(SECID, ORIGCURRENCY, INVTRAN):
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(OFXNumeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    taxexempt = Column(OFXBoolean())
    withholding = Column(OFXNumeric(), CheckConstraint('withholding >= 0'))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class INVEXPENSE(SECID, ORIGCURRENCY, INVTRAN):
    total = Column(OFXNumeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class JRNLFUND(INVTRAN):
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    total = Column(OFXNumeric(), nullable=False)


class JRNLSEC(SECID, INVTRAN):
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    units = Column(OFXNumeric(), nullable=False)


class MARGININTEREST(ORIGCURRENCY, INVTRAN):
    total = Column(OFXNumeric(), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class REINVEST(SECID, ORIGCURRENCY, INVTRAN):
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(OFXNumeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    units = Column(OFXNumeric(), nullable=False)
    unitprice = Column(OFXNumeric(), nullable=False)
    commission = Column(OFXNumeric(), CheckConstraint('commission >= 0'))
    taxes = Column(OFXNumeric(), CheckConstraint('taxes >= 0'))
    fees = Column(OFXNumeric(), CheckConstraint('fees >= 0'))
    load = Column(OFXNumeric(), CheckConstraint('load >= 0'))
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
    total = Column(OFXNumeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class SELLDEBT(INVSELL, INVTRAN):
    sellreason = Column(Enum('CALL', 'SELL', 'MATURITY', name='sellreason'),
                        nullable=False
                       )
    accrdint = Column(OFXNumeric())


class SELLMF(INVSELL, INVTRAN):
    selltype = Column(Enum(*SELLTYPES, name='selltype'), nullable=False)
    avgcostbasis = Column(OFXNumeric())
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
    oldunits = Column(OFXNumeric(), nullable=False)
    newunits = Column(OFXNumeric(), nullable=False)
    numerator = Column(OFXNumeric(), nullable=False)
    denominator = Column(OFXNumeric(), nullable=False)
    fraccash = Column(OFXNumeric())
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


class TRANSFER(SECID, INVTRAN):
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    units = Column(OFXNumeric(), nullable=False)
    tferaction = Column(Enum('IN', 'OUT', name='tferaction'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    avgcostbasis = Column(OFXNumeric())
    unitprice = Column(OFXNumeric())
    dtpurchase = Column(OFXDateTime)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))


### POSITIONS
class INVPOS(Inheritor('invpos'), SECID, CURRENCY, Base):
    # Added for SQLAlchemy object model
    acctfrom_id = Column(
        Integer, ForeignKey(
            'invacctfrom.id', onupdate='CASCADE', ondelete='CASCADE'
        ), nullable=False
    )
    acctfrom = relationship(
        'INVACCTFROM', backref=backref('invposs',
                                       cascade='all, delete-orphan',
                                       passive_deletes=True,
                                      )
    )
    dtasof = Column(OFXDateTime)

    # Elements from OFX spec
    heldinacct = Column(Enum(*INVSUBACCTS, name='heldinacct'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    units = Column(OFXNumeric(), nullable=False)
    unitprice = Column(OFXNumeric(), nullable=False)
    mktval = Column(OFXNumeric(), nullable=False)
    dtpriceasof = Column(OFXDateTime, nullable=False)
    memo = Column(String(length=255))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    pks = ['acctfrom_id', 'secinfo_id', 'dtasof']


class POSDEBT(INVPOS):
    pass


class POSMF(INVPOS):
    unitsstreet = Column(OFXNumeric())
    unitsuser = Column(OFXNumeric())
    reinvdiv = Column(OFXBoolean())
    reinvcg = Column(OFXBoolean())


class POSOPT(INVPOS):
    secured = Column(Enum('NAKED', 'COVERED', name='secured'))


class POSOTHER(INVPOS):
    pass

class POSSTOCK(INVPOS):
    unitsstreet = Column(OFXNumeric())
    unitsuser = Column(OFXNumeric())
    reinvdiv = Column(OFXBoolean())
