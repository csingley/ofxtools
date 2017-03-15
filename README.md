# `ofxtools`

## Description

`ofxtools` is a Python library for working with Open Financial Exchange (OFX)
data - both OFXv1 (SGML) and OFXv2 (pure XML) - which is the standard format
for downloading financial information from banks and stockbrokers.

`ofxtools` is compatible with Python version 2.7+ and 3.1+.
It depends on [the Requests package](http://docs.python-requests.org/en/master/)

The primary facilities provided include:
- The `OFXClient` class; which dowloads OFX statements from the Internet
- The `OFXTree` class; which parses OFX data into a standard ElementTree
  structure for further processing in Python.
- The `OFXResponse` class; which validates and converts OFX data parsed by
  OFXParser into Python types and exposes them through more Pythonic
  attribute access (e.g. `OFXResponse.statements[0].ledgerbal`).

Also included is the `ofxtools.ofxalchemy` subpackage, with versions of OFXTree
and OFXResponse that can parse OFX formatted data and persist it into an SQL
database.

`ofxalchemy` depends on [the SQLAlchemy package](http://www.sqlalchemy.org).
You'll need SQLAlchemy version 1.0 or higher.


# Installation

Use the Python user installation scheme:

    python setup.py install --user

In addition to the Python package, this will also install a script `ofxget`
in `~/.local/bin`, and its sample configuration file in `~/.config/ofxtools`.

To use `ofxalchemy`, you'll need to install SQLAlchemy via:

    pip install sqlalchemy

or

    easy_install sqlalchemy

or download and install the package from [the SQLAlchemy
website](http://www.sqlalchemy.org) or from
[PyPI](https://pypi.python.org/pypi/SQLAlchemy).


# Basic Usage to Download OFX

- Copy `~/.config/ofxtools/ofxget_example.cfg` to
  `~/.config/ofxtools/ofxget.cfg` and edit:
  - Add a section for your financial institution, including URL, account
    information, login, etc.
  - See comments within.
- Execute `ofxget` with appropriate arguments, for example:

  ```
  ofxget amex stmt -s 20140101 -e 20140630 > foobar.ofx
  ```

 See the `--help` for explanation of the script options.


## Parser Usage Example

```python
>>> from ofxtools import OFXTree
>>> tree = OFXTree()
>>> tree.parse('stmtrs.ofx')
>>> response = tree.convert()
>>> response
<OFXResponse fid='1001' org='NCH' dtserver='2005-10-29 10:10:03' len(statements)=1 len(securities)=0>
>>> stmt = response.statements[0]
>>> stmt
<BankStatement account=<BANKACCTFROM acctid='999988' accttype='CHECKING' bankid='121099999'> currency=USD ledgerbal=<LEDGERBAL balamt='200.29' dtasof='2005-10-29 11:20:00'> availbal=<AVAILBAL balamt='200.29' dtasof='2005-10-29 11:20:00'> len(other_balances)=0 len(transactions)=2>
>>> stmt.transactions[-1]
<STMTTRN dtposted='2005-10-20 00:00:00' trntype='ATM' trnamt='-300.00' fitid='00003' dtuser='2005-10-20 00:00:00'>
```

## SQL Persistence Example

```python
>>> # Housekeeping to set up database connection
>>> from ofxtools.ofxalchemy.database import init_db, Session
>>> init_db('sqlite://', echo=False)

>>> # Parse and persist the OFX data
>>> parser = ofxalchemy.OFXParser() # a/k/a ofxalchemy.OFXTree
>>> parser.parse('invstmtrs.ofx')
>>> parser.instantiate(DBSession)
<OFXResponse len(statements)=1 len(securities)=3>
>>> Session.commit()
>>> # Besides the returned OFXResponse object, persisted data can now be
>>> # accessed by querying the database.  The object model follows the OFX
>>> # specification fairly closely, with data elements represented as instance
>>> # attributes, subaggregate type nesting modeled by polymorphic inheritance,
>>> # and references to other data types replaced by foreign key relationships.
>>> #
>>> # N.B. There is no database structure representing account statements
>>> # (OFX *STMT aggregates); only the transactions, balances, etc. contained
>>> # within a statement are persisted.

>>> from ofxtools.ofxalchemy.models import *
>>> acct = ACCTFROM.query.one()
>>> acct
<INVACCTFROM(brokerid='121099999', acctid='999988', id='1')>
>>> acct.invbals
[<INVBAL(availcash='200.00', marginbalance='-50.00', shortbalance='0', acctfrom_id='1', dtasof='2005-08-27 01:00:00')>]
>>> # The full range of SQLAlchemy query expressions is available.
>>> from datetime import datetime
>>> invtrans = INVTRAN.query.filter_by(acctfrom=acct).filter(INVTRAN.dttrade >= datetime(2005,1,1)).filter(INVTRAN.dttrade <= datetime(2005,12,31)).order_by(INVTRAN.dttrade).all()
>>> invtrans
[<BUYSTOCK(units='100', unitprice='50.00', commission='25.00', total='-5025.00', subacctsec='CASH', subacctfund='CASH', buytype='BUY', secinfo_id='1', id='1')>]
>>> # OFX text data has been validated and converted to Python types, so it
>>> # can be worked with directly.
>>> t = invtrans[0]
>>> assert -t.units * t.unitprice - t.commission == t.total
```

## Contributing

If you want to contribute with this project, create a virtualenv and install
all development requirements:

    virtualenv .venv
    source .venv/bin/activate
    pip install -r requirements-development.txt


Then, run the tests with `make`:

    make test

Or directly with `nosetests`:

    nosetests -dsv --with-yanc --with-coverage --cover-package ofxtools

Feel free to [create pull
requests](https://help.github.com/articles/using-pull-requests/) on [ofxtools
repository on GitHub](https://github.com/csingley/ofxtools).
