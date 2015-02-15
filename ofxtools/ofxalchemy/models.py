# vim: set fileencoding=utf-8
""" 
SQLAlchemy object model for fundamental OFX data aggregates such as transactions, 
balances, and securities.
"""
# 3rd party imports
from sqlalchemy import (
    Column,
    Boolean,
    #DateTime,
    Enum,
    Integer,
    #Numeric,
    String,
    Text,
    ForeignKey,
    ForeignKeyConstraint,
    )
import sqlalchemy.types
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )
from sqlalchemy.orm.exc import NoResultFound

# local imports
from types import Numeric, OFXDateTime
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
# We need a session for Aggregate.get() to construct queries and
# Aggregate.get_or_create() to add transient instances
DBSession = scoped_session(sessionmaker())


# Object classes
class Aggregate(object):
    """
    Declarative mixin of OFX 'aggregate', i.e. SGML parent node that contains
    no data.

    Aggregates are grouped into higher-order containers such as lists
    and statements.  Although such higher-order containers are 'aggregates'
    per the OFX specification, they are represented here by their own Python
    classes other than Aggregate.
    """
    @classmethod
    def primary_keys(cls):
        return [c.name for c in cls.__table__.c if c.primary_key]

    @classmethod
    def get(cls, **attrs):
        pks = cls.primary_keys()
        try:
            pk = {k: attrs[k] for k in pks}
        except KeyError:
            msg = "%s: Required attributes %s not satisfied by arguments %s" \
                    % (cls.__name__, pks, attrs)
            raise ValueError(msg)
        instance = DBSession.query(cls).filter_by(**pk).one()
        return instance

    @classmethod
    def get_or_create(cls, **attrs):
        try:
            instance = cls.get(**attrs)
        except NoResultFound:
            instance = cls(**attrs)
            DBSession.add(instance)
        return instance
    
    @staticmethod
    def from_etree(elem, **extra_attrs):
        """ 
        Look up the Aggregate subclass for a given ofx.Parser.Element and
        feed it the Element to instantiate the Aggregate instance.
        """
        get_or_create = extra_attrs.pop('get_or_create', False)

        SubClass = globals()[elem.tag]
        attributes = elem._flatten()
        attributes.update(extra_attrs)

        if get_or_create:
            instance = SubClass.get_or_create(**attributes)
        else:
            instance = SubClass(**attributes)
        return instance

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, ', '.join(
            ['%s=%r' % (c.name, str(getattr(self, c.name))) \
             for c in self.__class__.__table__.c \
             if getattr(self, c.name) is not None]
        ))


Aggregate = declarative_base(cls=Aggregate)


class CURRENCY(object):
    """ Declarative mixin representing OFX <CURRENCY> aggregate """
    cursym = Column(Enum(*CURRENCY_CODES, name='cursym'))
    currate = Column(Numeric())


class ORIGCURRENCY(CURRENCY):
    """ Declarative mixin representing OFX <CURRENCY> aggregate """
    curtype = Column(Enum('CURRENCY', 'ORIGCURRENCY', name='curtype'))

    @staticmethod
    def from_etree(elem):
        """ 
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        instance = Aggregate.from_etree(elem)

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
        instance.curtype = curtype

        return instance


class ACCTFROM(Aggregate):
    """ 
    Uses a synthetic primary key to implement joined-table inheritance;
    the actual unique identifiers are given as a class attribute 'pks'
    """
    __tablename__ = 'acctfroms'

    # Added for SQLAlchemy object model
    id = Column(Integer, primary_key=True)
    subclass = Column(String(length=32), nullable=False)
    __mapper_args__ = {'polymorphic_on': subclass}

    # Extra attribute definitions not from OFX spec
    name = Column(Text)

    pks = []

    @classmethod
    def primary_keys(cls):
        return cls.pks


class BANKACCTFROM(ACCTFROM):
    __tablename__ = 'bankacctfroms'
    __mapper_args__ = {'polymorphic_identity': 'bankacctfrom'}

    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)

    # Elements from OFX spec
    bankid = Column(String(length=9), nullable=False)
    branchid = Column(String(length=22))
    acctid = Column(String(length=9), nullable=False)
    accttype = Column(Enum(*ACCTTYPES, name='accttype'), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['bankid', 'acctid']


class CCACCTFROM(ACCTFROM):
    __tablename__ = 'ccacctfroms'
    __mapper_args__ = {'polymorphic_identity': 'ccacctfrom'}

    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)

    # Elements from OFX spec
    acctid = Column(String(length=22), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['acctid', ]


class INVACCTFROM(ACCTFROM):
    __tablename__ = 'invacctfroms'
    __mapper_args__ = {'polymorphic_identity': 'invacctfrom'}
    
    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)

    # Elements from OFX spec
    brokerid = Column(String(length=22), nullable=False)
    acctid = Column(String(length=9), nullable=False)

    pk = ['brokerid', 'acctid']


class ACCTTO(Aggregate):
    """ 
    Uses a synthetic primary key to implement joined-table inheritance;
    the actual unique identifiers are given as a class attribute 'pks'
    """
    __tablename__ = 'accttos'

    # Added for SQLAlchemy object model
    id = Column(Integer, primary_key=True)
    subclass = Column(String(length=32), nullable=False)
    __mapper_args__ = {'polymorphic_on': subclass}

    # Extra attribute definitions not from OFX spec
    name = Column(Text)

    pks = []

    @classmethod
    def primary_keys(cls):
        return cls.pks


class BANKACCTTO(ACCTTO):
    __tablename__ = 'bankaccttos'
    __mapper_args__ = {'polymorphic_identity': 'bankacctto'}

    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('accttos.id'), primary_key=True)

    # Elements from OFX spec
    bankid = Column(String(length=9), nullable=False)
    branchid = Column(String(length=22))
    acctid = Column(String(length=9), nullable=False)
    accttype = Column(Enum(*ACCTTYPES, name='accttype'), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['bankid', 'acctid']


class CCACCTTO(ACCTTO):
    __tablename__ = 'ccaccttos'
    __mapper_args__ = {'polymorphic_identity': 'ccacctto'}

    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('accttos.id'), primary_key=True)

    # Elements from OFX spec
    acctid = Column(String(length=22), nullable=False)
    acctkey = Column(String(length=22))

    pks = ['acctid', ]


class INVACCTTO(ACCTTO):
    __tablename__ = 'invaccttos'
    __mapper_args__ = {'polymorphic_identity': 'invacctto'}
    
    # Added for SQLAlchemy object model
    id = Column(Integer, ForeignKey('accttos.id'), primary_key=True)

    # Elements from OFX spec
    brokerid = Column(String(length=22), nullable=False)
    acctid = Column(String(length=9), nullable=False)

    pk = ['brokerid', 'acctid']


# Balances
class LEDGERBAL(Aggregate):
    __tablename__ = 'ledgerbals'

    # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)

    # Elements from OFX spec
    balamt = Column(Numeric(), nullable=False)
    dtasof = Column(OFXDateTime, primary_key=True)

    acctfrom = relationship('ACCTFROM', backref='ledgerbals')


class AVAILBAL(Aggregate):
    __tablename__ = 'availbals'

    # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)

    # Elements from OFX spec
    balamt = Column(Numeric(), nullable=False)
    dtasof = Column(OFXDateTime, primary_key=True)

    acctfrom = relationship('ACCTFROM', backref='availbals')


class INVBAL(Aggregate):
    __tablename__ = 'invbals'

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, ForeignKey('invacctfroms.id'), primary_key=True)
    invacctfrom = relationship('INVACCTFROM', backref='invbals')
    dtasof = Column(OFXDateTime, primary_key=True)

    # Elements from OFX spec
    availcash = Column(Numeric(), nullable=False)
    marginbalance = Column(Numeric(), nullable=False)
    shortbalance = Column(Numeric(), nullable=False)
    buypower = Column(Numeric())



class BAL(Aggregate, CURRENCY):
    __tablename__ = 'bals'

    # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)
    acctfrom = relationship('ACCTFROM', backref='bals')

    # Elements from OFX spec
    name = Column(String(length=32), primary_key=True)
    desc = Column(String(length=80), nullable=False)
    baltype = Column(Enum('DOLLAR', 'PERCENT', 'NUMBER', name='baltype'),
                     nullable=False)
    value = Column(Numeric(), nullable=False)
    # We deviate from the OFX spec by storing the STMT.dtasof in BAL.dtasof
    # in order to uniquely link the balance with the statement without 
    # persisting a STMT object. We make BAL.dtasof mandatory and use it
    # as part of the primary key.
    dtasof = Column(OFXDateTime, primary_key=True)  


class SECINFO(Aggregate, CURRENCY):
    __tablename__ = 'secinfos'

    # Added for SQLAlchemy object model
    subclass = Column(String(length=32), nullable=False)
    __mapper_args__ = {'polymorphic_on': subclass}

    # Elements from OFX spec
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    #secname = Column(String(length=120), nullable=False)
    # FIs *cough* IBKR *cough* abuse the secname with too much information
    # Relaxing the length constraint from the OFX spec does little harm
    secname = Column(String(length=255), nullable=False)
    ticker = Column(String(length=32))
    fiid = Column(String(length=32))
    rating = Column(String(length=10))
    unitprice = Column(Numeric())
    dtasof = Column(OFXDateTime)
    memo = Column(String(length=255))


class DEBTINFO(SECINFO):
    __tablename__ = 'debtinfos'
    __mapper_args__ = {'polymorphic_identity': 'debtinfo'}

    # Added for SQLAlchemy object model
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (ForeignKeyConstraint([uniqueid, uniqueidtype],
                                           [SECINFO.uniqueid,
                                            SECINFO.uniqueidtype],
                                          ),
                     )

    # Elements from OFX spec
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
    __tablename__ = 'mfinfos'
    __mapper_args__ = {'polymorphic_identity': 'mfinfo'}

    # Added for SQLAlchemy object model
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (ForeignKeyConstraint([uniqueid, uniqueidtype],
                                           [SECINFO.uniqueid,
                                            SECINFO.uniqueidtype],
                                          ),
                     )

    # Elements from OFX spec
    mftype = Column(Enum('OPENEND', 'CLOSEEND', 'OTHER', name='mftype'))
    yld = Column(Numeric())
    dtyieldasof = Column(OFXDateTime)

    @staticmethod
    def from_etree(elem, **extra_attrs):
        """ 
        Strip MFASSETCLASS/FIMFASSETCLASS - lists that will blow up _flatten()
        """
        mfassetclasses = []

        # Do all XPath searches before removing nodes from the tree
        #   which seems to mess up the DOM in Python3 and throw an
        #   AttributeError on subsequent searches.
        mfassetclass = elem.find('./MFASSETCLASS')
        fimfassetclass = elem.find('./FIMFASSETCLASS')

        if mfassetclass is not None:
            # Convert PORTIONs; save for later
            mfassetclasses.append(mfassetclass)
            elem.remove(mfassetclass)
        if fimfassetclass is not None:
            # Convert FIPORTIONs; save for later
            mfassetclass.append(fimfassetclass)
            elem.remove(fimfassetclass)

        instance = Aggregate.from_etree(elem, **extra_attrs)

        # Instantiate MFASSETCLASS/FIMFASSETCLASS with foreign key reference
        # to MFINFO
        for mfassetclass in mfassetclasses:
            for portion in mfassetclass:
                Aggregate.from_etree(
                    portion, mfinfo_uniqueid=instance.uniqueid,
                    mfinfo_uniqueidtype=instance.uniqueidtype,
                    get_or_create=True
                )

        return instance

class PORTION(Aggregate):
    __tablename__ = 'portions'

    # Added for SQLAlchemy object model
    mfinfo_uniqueid = Column(String(length=32), primary_key=True)
    mfinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    mfinfo = relationship('MFINFO', backref='mfassetclasses')
    __table_args__ = (
        ForeignKeyConstraint([mfinfo_uniqueid, mfinfo_uniqueidtype],
                             [MFINFO.uniqueid, MFINFO.uniqueidtype],),
    )

    # Elements from OFX spec
    assetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )
    percent = Column(Numeric(), nullable=False)


class FIPORTION(Aggregate):
    __tablename__ = 'fiportions'

    # Added for SQLAlchemy object model
    mfinfo_uniqueid = Column(String(length=32), primary_key=True)
    mfinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    mfinfo = relationship('MFINFO', backref='fimfassetclasses')
    __table_args__ = (
        ForeignKeyConstraint([mfinfo_uniqueid, mfinfo_uniqueidtype],
                             [MFINFO.uniqueid, MFINFO.uniqueidtype],),
    )

    # Elements from OFX spec
    assetclass = Column(
        Enum(*ASSETCLASSES, name='assetclass'), primary_key=True
    )


class OPTINFO(SECINFO):
    __tablename__ = 'optinfos'
    __mapper_args__ = {'polymorphic_identity': 'optinfo'}

    # Added for SQLAlchemy object model
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (ForeignKeyConstraint([uniqueid, uniqueidtype],
                                           [SECINFO.uniqueid,
                                            SECINFO.uniqueidtype],
                                          ),
                     )

    # Elements from OFX spec
    opttype = Column(Enum('CALL', 'PUT', name='opttype'), nullable=False)
    strikeprice = Column(Numeric(), nullable=False)
    dtexpire = Column(OFXDateTime, nullable=False)
    shperctrct = Column(Integer(required=True))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


class OTHERINFO(SECINFO):
    __tablename__ = 'otherinfos'
    __mapper_args__ = {'polymorphic_identity': 'otherinfo'}

    # Added for SQLAlchemy object model
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (ForeignKeyConstraint([uniqueid, uniqueidtype],
                                           [SECINFO.uniqueid,
                                            SECINFO.uniqueidtype],
                                          ),
                     )

    # Elements from OFX spec
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))
    percent = Column(Numeric())


class STOCKINFO(SECINFO):
    __tablename__ = 'stockinfos'
    __mapper_args__ = {'polymorphic_identity': 'stockinfo'}

    # Added for SQLAlchemy object model
    uniqueid = Column(String(length=32), primary_key=True)
    uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (ForeignKeyConstraint([uniqueid, uniqueidtype],
                                           [SECINFO.uniqueid, 
                                            SECINFO.uniqueidtype],
                                          ),
                     )

    # Elements from OFX spec
    typedesc = Column(String(length=32))
    stocktype = Column(Enum('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER',
                           name='stocktype')
                      )
    yld = Column(Numeric())
    dtyieldasof = Column(OFXDateTime)
    typedesc = Column(String(length=32))
    assetclass = Column(Enum(*ASSETCLASSES, name='assetclass'))
    fiassetclass = Column(String(length=32))


# Transactions
class PAYEE(Aggregate):
    __tablename__ = 'payees'

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


class TRAN(ORIGCURRENCY):
    """ Synthetic base class of STMTTRN/INVBANKTRAN - not in OFX spec """
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


class STMTTRN(Aggregate, TRAN):
    __tablename__ = 'stmttrns'
     # Added for SQLAlchemy object model
    acctfrom_id = Column(Integer, ForeignKey('acctfroms.id'), primary_key=True)
    acctfrom = relationship('ACCTFROM', foreign_keys=[acctfrom_id,], backref='stmttrns')
    payee_name = Column(String(32), ForeignKey('payees.name'))
    payee = relationship('PAYEE', backref='stmttrns')
    acctto_id = Column(Integer, ForeignKey('accttos.id'))
    acctto = relationship('ACCTTO', foreign_keys=[acctto_id,])

    @staticmethod
    def from_etree(elem, **extra_attrs):
        # BANKACCTTO/CCACCTTO
        bankacctto = elem.find('BANKACCTTO')
        if bankacctto:
            instance = Aggregate.from_etree(bankacctto)
            extra_attrs['acctto_id'] = instance.id
            elem.remove(instance)
        else:
            ccacctto = elem.find('CCACCTTO')
            if ccacctto:
                instance = Aggregate.from_etree(ccacctto)
                extra_attrs['acctto_id'] = instance.id
                elem.remove(ccacctto)
        # PAYEE
        payee= elem.find('PAYEE')
        if payee:
            instance = Aggregate.from_etree(payee)
            extra_attrs['payee_name'] = instance.name
            elem.remove(payee)

        return Aggregate.from_etree(elem, **extra_attrs)


class INVBANKTRAN(Aggregate, TRAN):
    __tablename__ = 'invbanktrans'
    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, ForeignKey('invacctfroms.id'), primary_key=True)
    invacctfrom = relationship('INVACCTFROM')
    payee_name = Column(String(32), ForeignKey('payees.name'))
    bankacctto_id = Column(Integer, ForeignKey('bankacctfroms.id'))
    ccacctto_id = Column(Integer, ForeignKey('ccacctfroms.id'))
    invacct = relationship('INVACCTFROM', foreign_keys=[invacctfrom_id,], backref='invbanktrans')
    payee = relationship('PAYEE', backref='invbanktrans')
    bankacctto = relationship('BANKACCTFROM', foreign_keys=[bankacctto_id,])
    ccacctto = relationship('CCACCTFROM', foreign_keys=[ccacctto_id,])

    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class INVTRAN(Aggregate):
    __tablename__ = 'invtrans'

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, ForeignKey('invacctfroms.id'), primary_key=True)
    invacctfrom = relationship('INVACCTFROM', backref='invtrans')
    subclass = Column(String(length=32), nullable=False)

    # Elements from OFX spec
    fitid = Column(String(length=255), primary_key=True)
    srvrtid = Column(String(length=10))
    dttrade = Column(OFXDateTime, nullable=False)
    dtsettle = Column(OFXDateTime)
    reversalfitid = Column(String(length=255))
    memo = Column(String(length=255))

    __mapper_args__ = {'polymorphic_on': subclass}

    @staticmethod
    def from_etree(elem, **extra_attrs):
        secid = elem.find('SECID')
        assert secid is not None
        secinfo = SECID.from_etree(secid)
        extra_attrs['secinfo_uniqueid'] = secinfo.uniqueid
        extra_attrs['secinfo_uniqueidtype'] = secinfo.uniqueidtype
        elem.remove(secid)

        return Aggregate.from_etree(elem, **extra_attrs)


class SECID(object):
    """
    Mixin to hold logic for securities-related investment transactions (INVTRAN)
    """
    @staticmethod
    def from_etree(elem, **extra_attrs):
        """ 
        Return the SECINFO referred to by (UNIQUEID, UNIQUEDTYPE) elements of
        a SECID aggregate
        """
        uniqueidtype = elem.find('UNIQUEIDTYPE')
        uniqueid = elem.find('UNIQUEID')
        return SECINFO.get(uniqueidtype=uniqueidtype.text,
                               uniqueid=uniqueid.text)


class INVBUYSELL(ORIGCURRENCY):
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

    @staticmethod
    def from_etree(elem, **extra_attrs):
        """ """
        # Remove SECINFO and instantiate
        invbuysell = elem[0]
        secid = invbuysell[1]
        assert secid is not None
        extra_attrs['secinfo'] = SECID.from_etree(secid)
        invbuysell.remove(secid)

        return Aggregate.from_etree(elem, **extra_attrs)


class INVBUY(INVBUYSELL):
    """ Declarative mixin for OFX INVBUY aggregate """
    # Elements from OFX spec
    markup = Column(Numeric())
    loanid = Column(String(length=32))
    loanprincipal = Column(Numeric())
    loaninterest = Column(Numeric())
    dtpayroll = Column(OFXDateTime)
    prioryearcontrib = Column(Boolean())


class INVSELL(INVBUYSELL):
    """ Declarative mixin for OFX INVSELL aggregate """
   # Elements from OFX spec
    markdown = Column(Numeric())
    withholding = Column(Numeric())
    taxexempt = Column(Boolean())
    gain = Column(Numeric())
    loanid = Column(String(length=32))
    statewithholding = Column(Numeric())
    penalty = Column(Numeric())


class BUYDEBT(INVTRAN):
    __tablename__ = 'buydebts'
    __mapper_args__ = {'polymorphic_identity': 'buydebt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='buydebts')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype]),
    )

    # Elements from OFX spec
    accrdint = Column(Numeric())

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class BUYMF(INVTRAN):
    __tablename__ = 'buymfs'
    __mapper_args__ = {'polymorphic_identity': 'buymf'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='buymfs')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype]),
    )

    # Elements from OFX spec
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)
    relfitid = Column(String(length=255))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class BUYOPT(INVTRAN, INVBUY):
    __tablename__ = 'buyopts'
    __mapper_args__ = {'polymorphic_identity': 'buyopt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='buyopts')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype]),
    )

    # Elements from OFX spec
    optbuytype = Column(Enum('BUYTOOPEN', 'BUYTOCLOSE', name='obtbuytype'),
                        nullable=False
                       )
    shperctrct = Column(Integer(required=True))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class BUYOTHER(INVTRAN, INVBUY):
    __tablename__ = 'buyothers'
    __mapper_args__ = {'polymorphic_identity': 'buyother'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='buyothers')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype]),
    )

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class BUYSTOCK(INVTRAN, INVBUY):
    __tablename__ = 'buystocks'
    __mapper_args__ = {'polymorphic_identity': 'buystock'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='buystocks')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    buytype = Column(Enum(*BUYTYPES, name='buytype'), nullable=False)

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class CLOSUREOPT(INVTRAN):
    __tablename__ = 'closureopts'
    __mapper_args__ = {'polymorphic_identity': 'closureopt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    optaction = Column(Enum('EXERCISE', 'ASSIGN', 'EXPIRE', name='optaction'))
    units = Column(Numeric(), nullable=False)
    shperctrct = Column(Integer(required=True))
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    relfitid = Column(String(length=255))
    gain = Column(Numeric())
    


class INCOME(INVTRAN, ORIGCURRENCY):
    __tablename__ = 'incomes'
    __mapper_args__ = {'polymorphic_identity': 'income'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='income')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    taxexempt = Column(Boolean())
    withholding = Column(Numeric())
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class INVEXPENSE(INVTRAN, ORIGCURRENCY):
    __tablename__ = 'invexpenses'
    __mapper_args__ = {'polymorphic_identity': 'invexpense'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    secinfo = relationship('SECINFO', backref='invexpenses')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class JRNLFUND(INVTRAN):
    __tablename__ = 'jrnlfunds'
    __mapper_args__ = {'polymorphic_identity': 'jrnlfund'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid],
                            ),
    )

    # Elements from OFX spec
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    total = Column(Numeric(), nullable=False)


class JRNLSEC(INVTRAN):
    __tablename__ = 'jrnlsecs'
    __mapper_args__ = {'polymorphic_identity': 'jrnlsec'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    subacctto = Column(Enum(*INVSUBACCTS, name='subacctto'), nullable=False)
    subacctfrom = Column(Enum(*INVSUBACCTS, name='subacctfrom'), nullable=False)
    units = Column(Numeric(), nullable=False)

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class MARGININTEREST(INVTRAN, ORIGCURRENCY):
    __tablename__ = 'marginterests'
    __mapper_args__ = {'polymorphic_identity': 'margininterest'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid],
                            ),
    )

    # Elements from OFX spec
    total = Column(Numeric(), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)


class REINVEST(INVTRAN, ORIGCURRENCY):
    __tablename__ = 'reinvests'
    __mapper_args__ = {'polymorphic_identity': 'reinvest'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    incometype = Column(Enum(*INCOMETYPES, name='incometype'), nullable=False)
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'))
    units = Column(Numeric(), nullable=False)
    unitprice = Column(Numeric(), nullable=False)
    commission = Column(Numeric())
    taxes = Column(Numeric())
    fees = Column(Numeric())
    load = Column(Numeric())
    taxexempt = Column(Boolean())
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class RETOFCAP(INVTRAN, ORIGCURRENCY):
    __tablename__ = 'retofcaps'
    __mapper_args__ = {'polymorphic_identity': 'retofcap'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    total = Column(Numeric(), nullable=False)
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'), nullable=False)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class SELLDEBT(INVTRAN, INVSELL):
    __tablename__ = 'selldebts'
    __mapper_args__ = {'polymorphic_identity': 'selldebt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='selldebts')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    sellreason = Column(Enum('CALL', 'SELL', 'MATURITY', name='sellreason'),
                        nullable=False
                       )
    accrdint = Column(Numeric())

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class SELLMF(INVTRAN, INVSELL):
    __tablename__ = 'sellmf'
    __mapper_args__ = {'polymorphic_identity': 'sellmf'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='sellmfs')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    selltype = Column(Enum(*SELLTYPES, name='selltype'), nullable=False)
    avgcostbasis = Column(Numeric())
    relfitid = Column(String(length=255))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class SELLOPT(INVTRAN, INVSELL):
    __tablename__ = 'sellopts'
    __mapper_args__ = {'polymorphic_identity': 'sellopt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='sellopts')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    optselltype = Column(Enum('SELLTOCLOSE', 'SELLTOOPEN', name='optselltype'),
                         nullable=False)
    shperctrct = Column(Integer(required=True))
    relfitid = Column(String(length=255))
    reltype = Column(Enum('SPREAD', 'STRADDLE', 'NONE', 'OTHER', name='reltype')
                    )
    secured = Column(Enum('NAKED', 'COVERED', name='secured'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class SELLOTHER(INVTRAN, INVSELL):
    __tablename__ = 'sellothers'
    __mapper_args__ = {'polymorphic_identity': 'sellother'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='sellothers')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class SELLSTOCK(INVTRAN, INVSELL):
    __tablename__ = 'sellstocks'
    __mapper_args__ = {'polymorphic_identity': 'sellstock'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)

    secinfo_uniqueid = Column(String(length=32), nullable=False)
    secinfo_uniqueidtype = Column(String(length=10), nullable=False)
    secinfo = relationship('SECINFO', foreign_keys=[secinfo_uniqueid, 
                                                    secinfo_uniqueidtype], 
                           backref='sellstocks')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,]),
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype,],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,]),
    )

    # Elements from OFX spec
    selltype = Column(Enum(*SELLTYPES, name='selltype'), nullable=False)

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVBUYSELL.from_etree(elem, **extra_attrs)


class SPLIT(INVTRAN):
    __tablename__ = 'splits'
    __mapper_args__ = {'polymorphic_identity': 'splits'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    oldunits = Column(Numeric(), nullable=False)
    newunits = Column(Numeric(), nullable=False)
    numerator = Column(Numeric(), nullable=False)
    denominator = Column(Numeric(), nullable=False)
    fraccash = Column(Numeric())
    subacctfund = Column(Enum(*INVSUBACCTS, name='subacctfund'))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)


class TRANSFER(INVTRAN):
    __tablename__ = 'transfers'
    __mapper_args__ = {'polymorphic_identity': 'transfer'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    fitid = Column(String(length=255), primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    secinfo = relationship('SECINFO', backref='transfers')
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, fitid,],
                             [INVTRAN.invacctfrom_id, INVTRAN.fitid,],
                            ),
        ForeignKeyConstraint([ secinfo_uniqueid, secinfo_uniqueidtype,], 
                             [SECINFO.uniqueid, SECINFO.uniqueidtype,],
                            ),
    )

    # Elements from OFX spec
    subacctsec = Column(Enum(*INVSUBACCTS, name='subacctsec'), nullable=False)
    units = Column(Numeric(), nullable=False)
    tferaction = Column(Enum('IN', 'OUT', name='tferaction'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    avgcostbasis = Column(Numeric())
    unitprice = Column(Numeric())
    dtpurchase = Column(OFXDateTime)
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        return INVTRAN.from_etree(elem, **extra_attrs)

# Positions
class INVPOS(Aggregate, CURRENCY):
    __tablename__ = 'invposs'

    # Added for SQLAlchemy object model
    subclass = Column(String(length=32), nullable=False)
    invacctfrom_id = Column(Integer, ForeignKey('invacctfroms.id'), primary_key=True)
    invacctfrom = relationship('INVACCTFROM', backref='invposs')
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    secinfo = relationship('SECINFO', backref='invposs')
    dtasof = Column(OFXDateTime, primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint([secinfo_uniqueid, secinfo_uniqueidtype],
                             [SECINFO.uniqueid, SECINFO.uniqueidtype],
                            ),
    )
    __mapper_args__ = {'polymorphic_on': subclass}

    # Elements from OFX spec
    heldinacct = Column(Enum(*INVSUBACCTS, name='heldinacct'), nullable=False)
    postype = Column(Enum('SHORT', 'LONG', name='postype'), nullable=False)
    units = Column(Numeric(), nullable=False)
    unitprice = Column(Numeric(), nullable=False)
    mktval = Column(Numeric(), nullable=False)
    dtpriceasof = Column(OFXDateTime, nullable=False)
    memo = Column(String(length=255))
    inv401ksource = Column(Enum(*INV401KSOURCES, name='inv401ksource'))

    @staticmethod
    def from_etree(elem, **extra_attrs):
        """ """
        # Remove SECINFO and instantiate
        invpos = elem[0]
        secid = invpos[0]
        secinfo = SECID.from_etree(secid)
        extra_attrs['secinfo_uniqueid'] = secinfo.uniqueid
        extra_attrs['secinfo_uniqueidtype'] = secinfo.uniqueidtype
        invpos.remove(secid)

        return Aggregate.from_etree(elem, **extra_attrs)




class POSDEBT(INVPOS):
    __tablename__ = 'posdebts'
    __mapper_args__ = {'polymorphic_identity': 'posdebt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    dtasof = Column(OFXDateTime, primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, secinfo_uniqueid,
                              secinfo_uniqueidtype, dtasof],
                             [INVPOS.invacctfrom_id, INVPOS.secinfo_uniqueid, 
                              INVPOS.secinfo_uniqueidtype, INVPOS.dtasof],
                            ),
    )


class POSMF(INVPOS):
    __tablename__ = 'posmfs'
    __mapper_args__ = {'polymorphic_identity': 'posmf'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    dtasof = Column(OFXDateTime, primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, secinfo_uniqueid,
                              secinfo_uniqueidtype, dtasof],
                             [INVPOS.invacctfrom_id, INVPOS.secinfo_uniqueid, 
                              INVPOS.secinfo_uniqueidtype, INVPOS.dtasof],
                            ),
    )

    # Elements from OFX spec
    unitsstreet = Column(Numeric())
    unitsuser = Column(Numeric())
    reinvdiv = Column(Boolean())
    reinvcg = Column(Boolean())


class POSOPT(INVPOS):
    __tablename__ = 'posopts'
    __mapper_args__ = {'polymorphic_identity': 'posopt'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    dtasof = Column(OFXDateTime, primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, secinfo_uniqueid,
                              secinfo_uniqueidtype, dtasof],
                             [INVPOS.invacctfrom_id, INVPOS.secinfo_uniqueid, 
                              INVPOS.secinfo_uniqueidtype, INVPOS.dtasof],
                            ),
    )

    # Elements from OFX spec
    secured = Column(Enum('NAKED', 'COVERED', name='secured'))


class POSOTHER(INVPOS):
    __tablename__ = 'posothers'
    __mapper_args__ = {'polymorphic_identity': 'posother'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    dtasof = Column(OFXDateTime, primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, secinfo_uniqueid,
                              secinfo_uniqueidtype, dtasof],
                             [INVPOS.invacctfrom_id, INVPOS.secinfo_uniqueid, 
                              INVPOS.secinfo_uniqueidtype, INVPOS.dtasof],
                            ),
    )

class POSSTOCK(INVPOS):
    __tablename__ = 'posstocks'
    __mapper_args__ = {'polymorphic_identity': 'posstock'}

    # Added for SQLAlchemy object model
    invacctfrom_id = Column(Integer, primary_key=True)
    secinfo_uniqueid = Column(String(length=32), primary_key=True)
    secinfo_uniqueidtype = Column(String(length=10), primary_key=True)
    dtasof = Column(OFXDateTime, primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint([invacctfrom_id, secinfo_uniqueid,
                              secinfo_uniqueidtype, dtasof],
                             [INVPOS.invacctfrom_id, INVPOS.secinfo_uniqueid, 
                              INVPOS.secinfo_uniqueidtype, INVPOS.dtasof],
                            ),
    )

    # Elements from OFX spec
    unitsstreet = Column(Numeric())
    unitsuser = Column(Numeric())
    reinvdiv = Column(Boolean())


