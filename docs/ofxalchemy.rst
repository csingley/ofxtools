.. ofxalchemy:

``ofxtools`` and SQL
====================

``ofxtools`` does include the ``ofxalchemy`` subpackage, but you probably don't
want to use it.  The implementation is pretty nasty, and the SQL tables it
generates are cumbersome and inefficient.

Frankly, OFX is a poor data format for serious use, as is obvious to anyone
who's tried to work with its handling of online bill payees or securities
reorganizations.  A better approach is to decouple your SQL data model from
OFX, which will also allow you to better handle other financial data formats.

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
                                         password='T0PS3CR3T', invstmtrqs=[stmtrq])
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


