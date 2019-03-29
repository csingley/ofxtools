.. sqlalchemy:

Using ``ofxtools`` with SQL
===========================
As of version 0.7, ``ofxtools`` no longer includes the ``ofxalchemy``
subpackage.  The nature of its fundamental architectural flaw is well expressed
by this quote from a `moderately reputable source`_:

    SQLAlchemy supports class inheritance mapped to databases but it's not
    really something that scales well to deep hierarchies.  You can actually
    stretch this a lot by emphasizing single-table inheritance so that you
    aren't hobbled with dozens of joins, but this seems like it is still a very
    deep hierarchy even for that approach.

    What you need to do here is forget about your whole class hierarchy, and
    first design the database schema.   You want to persist this data in a
    relational database.  How?  What do the tables look like?  For any
    non-trivial application, this is where you need to design things from.  

OFX is a poor fit for a relational data model, as is obvious to anyone
who's tried to work with its handling of online bill payees or securities
reorganizations.  You don't really want to map that mess directly onto your
database tables... the heart of any ORM-based application.  A better approach
is to decouple your SQL data model from OFX, which will also allow you better
to handle other financial data formats.

It's recommended to define your own ORM models based on your needs.  Import
OFX into Python using the main ``ofxtools.Parser.OFXTree`` parser, extract
the relevant data, and feed it to your model classes.  Something like this:

.. code:: python

    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import (
        Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Enum,
    )
    from sqlalchemy.orm import (relationship, sessionmaker, )
    from sqlalchemy import create_engine

    from ofxtools.models.i18n import CURRENCY_CODES
    from ofxtools.Client import (OFXClient, InvStmtRq, )
    from ofxtools.Parser import OFXTree
    from ofxtools.models.investment import (BUYSTOCK, SELLSTOCK)


    # Data model
    Base = declarative_base()


    class Account(Base):
        id = Column(Integer, primary_key=True)
        brokerid = Column(String, nullable=False, unique=True)
        number = Column(String, nullable=False)
        name = Column(String)


    class Security(Base):
        id = Column(Integer, primary_key=True)
        name = Column(String)
        ticker = Column(String)
        uniqueidtype = Column(String, nullable=False)
        uniqueid = Column(String, nullable=False)


    class Transaction(Base):
        id = Column(Integer, primary_key=True)
        uniqueid = Column(String, nullable=False, unique=True)
        datetime = Column(DateTime, nullable=False)
        dtsettle = Column(DateTime)
        type = Column(Enum('returnofcapital', 'split', 'spinoff', 'transfer',
                           'trade', 'exercise', name='transaction_type'),
                      nullable=False)
        memo = Column(Text)
        currency = Column(Enum(*CURRENCY_CODES, name='transaction_currency'))
        cash = Column(Numeric)
        account_id = Column(Integer,
                            ForeignKey('account.id', onupdate='CASCADE'),
                            nullable=False)
        account = relationship('Account', foreign_keys=[account_id],
                               backref='transactions')
        security_id = Column(Integer,
                             ForeignKey('security.id', onupdate='CASCADE'),
                             nullable=False)
        security = relationship('Security', foreign_keys=[security_id],
                                backref='transactions')
        units = Column(Numeric)


    # Import
    client = OFXClient('https://ofxs.ameritrade.com/cgi-bin/apps/OFX',
                       org='Ameritrade Technology Group', fid='AIS',
                       brokerid='ameritrade.com')
    stmtrq = InvStmtRq(acctid='999999999')
    response = client.request_statements(user='elmerfudd',
                                         password='T0PS3CR3T',
                                         invstmtrqs=[stmtrq])
    parser = OFXTree()
    parser.parse(response)
    ofx = parser.convert()


    # Extract
    def make_security(secinfo):
        return Security(
            name=secinfo.secname, ticker=secinfo.ticker,
            uniqueidtype=secinfo.uniqueidtype, uniqueid=secinfo.uniqueid)


    securities = {(sec.uniqueidtype, sec.uniqueid): make_security(sec)
                  for sec in ofx.securities}


    stmt = ofx.statements[0]
    account = Account(brokerid=stmt.brokerid, number=stmt.acctid)


    def make_trade(invtran):
        security = securities[(invtran.uniqueidtype, invtran.uniqueid)]
        return Transaction(
            uniqueid=invtran.fitid, datetime=invtran.dttrade,
            dtsettle=invtran.dtsettle, type='trade', memo=invtran.memo,
            currency=invtran.currency, cash=invtran.total, account=account,
            security=security, units=invtran.units)


    trades = [make_trade(tx) for tx in stmt.transactions
              if isinstance(tx, (BUYSTOCK, SELLSTOCK))]  # dispatch by model class


    # Persist
    engine = create_engine('')
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(account)
    session.add_all(securities.values())
    session.add_all(trades)
    session.commit()


.. _moderately reputable source: https://groups.google.com/d/msg/sqlalchemy/a7xeKebSgTE/6m-qdR4BBgAJ
