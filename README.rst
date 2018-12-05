====================
OFX tools for Python
====================

``ofxtools`` is a Python library for working with Open Financial Exchange
(OFX) data - both OFXv1 (SGML) and OFXv2 (pure XML) - which is the standard
format for downloading financial information from banks and stockbrokers.

``ofxtools`` is compatible with Python version 2.7+ and 3.1+.
It depends on `Requests`_ .

The primary facilities provided include:

-  The ``OFXClient`` class; which dowloads OFX statements from the
   Internet;
-  The ``OFXTree`` class; which parses OFX data into a standard Python
   ElementTree structure, then converts the parsed data into normal Python
   types (e.g. datetime.datetime, list) and exposes them through more Pythonic
   attribute access (e.g. ``OFX.statements[0].ledgerbal``); and
-  A (deprecated) ``ofxalchemy`` object model that persists OFX data in an
   SQL database where they can be queried.

Installation
============
``ofxtools`` is released on `PyPI`_, so it can be installed simply via:

::

    pip install ofxtools

To install the most recent prerelease (which is where the magic happens, and
also the bugs), you can download the `current master`_, unzip it, and install
via the included setup file:

::

    python setup.py install

In addition to the Python package, this will also install a script ``ofxget``
in ``~/.local/bin``, and its sample configuration file in
``~/.config/ofxtools``.

For any installation method, it's recommended to install ``ofxtools`` in a
`virtual environment`_.

OFX Client
==========

Basic usage of the CLI script:

-  Copy ``~/.config/ofxtools/ofxget_example.cfg`` to
   ``~/.config/ofxtools/ofxget.cfg`` and edit:
-  Add a section for your financial institution, including URL, account
   information, login, etc.  See comments within the example file.
-  Execute ``ofxget`` with appropriate arguments, for example:

``ofxget amex stmt -s 20140101 -e 20140630 > foobar.ofx``

See the ``--help`` for explanation of the script options.

To use within another program, initialize an ``OFXClient`` instance with the
relevant connection parameters, then pass ``*StmtRq`` namedtuples along with
a username and password to its ``request_statements`` method.  See below for
an example.

OFX Parser
==========
The ``OFXTree`` parser subclasses ``xml.etree.ElementTree``, and is used similarly --
get an ``OFXTree`` instance, and pass a file-like object (or a reference to one)
to its ``parse`` method.  Thereafter, calling its ``convert`` method returns
a tree of nested ``ofxtools.models.Aggregate`` containers that preserve the
original OFX structure.  Following the `OFX spec`_ , you can get a node in the
parse tree with Python dotted attribute access, using standard slice notation
for lists.  E.g.:

.. code:: python

    ofx.invstmtmsgsrsv1[0].invstmttrnrs.invstmtrs.invtranlist[-1].invsell.invtran.dttrade

Data-bearing leaf nodes (such as ``DTTRADE`` above) are subclasses of
``ofxtools.Types.Element``, which validate the OFX character data and convert
it to standard Python types (``datetime.datetime`` in this case,
``decimal.Decimal``, ``bool``, etc.)

For quick access, ``Aggregates`` also provide shortcuts via read-only properties.
``ofx.statements`` yields all {``STMTRS``, ``CCSTMTRS``, ``INVSTMTRS``} found in the response.
``ofx.statements[0].transactions`` goes to the relevant ``*TRANLIST``
``ofx.statements[0].account`` goes to the relevant ``*ACCTFROM``
Use ``ofx.statements[0].balance`` for bank statement ``LEDGERBAL``, or
``ofx.statements[0].balances`` for investment statement ``INVBAL``.

Investment transactions provide lookthrough access to attributes of their
``SubAggregates``, so you can use ``STOCKBUY.uniqueid`` or ``INCOME.dttrade``.

For handling multicurrency transactions per OFX section 5.2, ``Aggregates`` that
can contain ``ORIGCURRENCY`` have an additional ``curtype`` attribute which
yields ``'CURRENCY'`` if the money amounts have not been converted to the
home currency, or yields ``'ORIGCURRENCY'`` if they have been converted.

``YIELD`` elements are renamed ``yld`` to avoid name collision with the Python
built-in.

Proprietary OFX tags (e.g. ``<INTU.BROKERID>``) are stripped and dropped.

Usage Example
=============

.. code:: python

    In [1]: from ofxtools.Client import OFXClient, InvStmtRq

    In [2]: client = OFXClient('https://ofxs.ameritrade.com/cgi-bin/apps/OFX',
       ...:      org='Ameritrade Technology Group', fid='AIS', brokerid='ameritrade.com')

    In [3]: stmtrq = InvStmtRq(acctid='999999999')

    In [4]: response = client.request_statements(user='elmerfudd', password='T0PS3CR3T',
       ...:      invstmtrqs=[stmtrq])

    In [5]: response.read()[:512]  # It's a StringIO
    Out[5]: '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\r\n<?OFX OFXHEADER="200" VERSION="200" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>\r\n<OFX>\r\n<SIGNONMSGSRSV1>\r\n<SONRS>\r\n<STATUS>\r\n<CODE>0</CODE>\r\n<SEVERITY>INFO</SEVERITY>\r\n<MESSAGE>Success</MESSAGE>\r\n</STATUS>\r\n<DTSERVER>20170421120513</DTSERVER>\r\n<LANGUAGE>ENG</LANGUAGE>\r\n<FI>\r\n<ORG>Ameritrade Technology Group</ORG>\r\n<FID>AIS</FID>\r\n</FI>\r\n</SONRS>\r\n</SIGNONMSGSRSV1>\r\n<INVSTMTMSGSRSV1>\r\n<INVSTMTTRNRS>\r\n<TRNUID>2a656f1c-5f86-4265-84f1-6c7f0dc8c37'

    In [6]: response.seek(0)  # Rewind so parser read()s from beginning of file
    Out[6]: 0

    In [7]: from ofxtools.Parser import OFXTree

    In [8]: parser = OFXTree()

    In [9]: parser.parse(response)  # parser.parse('/path/to/file.ofx') works too

    In [10]: parser.find('.//STATUS')[:]  # It's an ElementTree subclass
    Out[10]: 
    [<Element 'CODE' at 0x7f27dd4a2048>,
     <Element 'SEVERITY' at 0x7f27dd4a2ea8>,
     <Element 'MESSAGE' at 0x7f27dd4a2318>]

    In [11]: ofx = parser.convert()

    In [12]: ofx.statements  # It's a tree of ofxtools.models.Aggregate
    Out[12]: [<INVSTMTRS dtasof='2017-03-31 22:06:09' curdef='USD'>]

    In [13]: ofx.statements[0].transactions
    Out[13]: <INVTRANLIST dtstart=2015-04-21 12:05:13 dtend=2017-04-20 00:00:00 len=47>

    In [14]: t = ofx.statements[0].transactions[9]

    In [15]: t
    Out[15]: <BUYSTOCK buytype='BUY'>

    In [16]: t.dttrade
    Out[16]: datetime.datetime(2016, 9, 7, 13, 10, 4)

    In [17]: t.uniqueid
    Out[17]: '233242106'

    In [18]: t.units
    Out[18]: Decimal('18000.00')

    In [19]: t.total
    Out[19]: Decimal('-4509.99')

    In [20]: tree = ofx.to_etree()  # ElementTree(ofx.to_etree()) is a little nicer

    In [21]: tree.find('.//STATUS')[:]  # Back to ElementTree
    Out[21]: 
    [<Element 'CODE' at 0x7f27dc9870e8>,
     <Element 'SEVERITY' at 0x7f27dc987a98>,
     <Element 'MESSAGE' at 0x7f27dc987098>]

    In [22]: import xml.etree.ElementTree as ET

    In [23]: ET.tostring(tree)[:512]  # Back to str
    Out[23]: b'<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY><MESSAGE>Success</MESSAGE></STATUS><DTSERVER>20170421170513</DTSERVER><LANGUAGE>ENG</LANGUAGE><FI><ORG>Ameritrade Technology Group</ORG><FID>AIS</FID></FI></SONRS></SIGNONMSGSRSV1><INVSTMTMSGSRSV1><INVSTMTTRNRS><TRNUID>2a656f1c-5f86-4265-84f1-6c7f0dc8c370</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY><MESSAGE>pr-ctlvofx-pp03-clientsys Success</MESSAGE></STATUS><INVSTMTRS><DTASOF>20170401030609</DTASOF><CURDEF>USD</CURDEF><IN'

ofxtools and SQL
================

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

Contributing
============

If you want to contribute to this project, it's recommended to use `Git`_ to
clone the repository:

::

    git clone https://github.com/csingley/ofxtools.git

Set up a `virtual environment`_, and install the package in development mode
so you're working on live code:

::

    python setup.py develop

Install all development requirements:

::

    pip install -r requirements-development.txt

Run the tests, either with ``make``:

::

    make test

or directly with ``nosetests``:

::

    nosetests -dsv  --with-coverage --cover-package ofxtools

Feel free to `create pull requests`_ on `ofxtools repository on GitHub`_.


Resources
=========

* The `OFX spec`_ is canonical...
* ... but since Quicken dominates the industry, also see the
  `Quicken data mapping guide`_
* `OFX Home`_ is a great free resource to look up OFX connection information
  for various financial institutions


.. _Requests: http://docs.python-requests.org/en/master/
.. _PyPI: https://pypi.python.org/pypi/ofxtools
.. _current master: https://github.com/csingley/ofxtools/archive/master.zip
.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
.. _OFX spec: http://www.ofx.net/downloads.html
.. _Git: https://git-scm.com/
.. _create pull requests: https://help.github.com/articles/using-pull-requests/
.. _ofxtools repository on GitHub: https://github.com/csingley/ofxtools
.. _Quicken data mapping guide: https://fi.intuit.com/downloads/QW_DataMappingGuide.pdf
.. _OFX Home: http://www.ofxhome.com/

