DESCRIPTION
====
ofxtools is a Python library for working with Open Financial Exchange (OFX)
data - both OFXv1 (SGML) and OFXv2 (pure XML) - which is the standard format
for downloading financial information from banks and stockbrokers.

ofxtools has no external dependencies beyond stdlib, and is compatible with
Python version 2.7+ and 3.1+.

The primary facilities provided include:
    * The OFXClient class; which dowloads OFX statements from the Internet
    * The OFXTree class; which parses OFX data into a standard ElementTree
      structure for further processing in Python.
    * The OFXResponse class; which validates and converts OFX data parsed by
      OFXParser into Python types and exposes them through more Pythonic
      attribute access (e.g. OFXResponse.statements[0].ledgerbal)

Also included is the ofxtools.ofxalchemy subpackage, with versions of
OFXTree and OFXResponse that can parse OFX formatted data and persist it
into an SQL database.
ofxalchemy depends on [the SQLAlchemy package][http://www.sqlalchemy.org].

INSTALLATION
====
Use the Python user installation scheme:
    `python setup.py install --user`

In addition to the Python package, this will also install a script 'ofxget'
in ~/.local/bin, and its sample configuration file in ~/.config/ofxtools .

To use ofxalchemy, you'll need to install SQLAlchemy via:
    `pip install sqlalchemy`
or
    `easy_install sqlalchemy`
or download and install the package from 
[the SQLAlchemy website][http://www.sqlalchemy.org]
or from [PyPI][https://pypi.python.org]


BASIC USAGE TO DOWNLOAD OFX
====
    1) Copy ~/.config/ofxtools/ofxget_example.cfg to ~/.config/ofxtools/ofxget.cfg and edit.
        Add a section for your financial institution, including URL, 
        account information, login, etc.
        See comments within.
    2) Execute ofxget with appropriate arguments, e.g.
        `# ofxget amex stmt -s 20140101 -e 20140630 > foobar.ofx`
        See the --help for explanation of the script options

PARSER USAGE EXAMPLE
====
>>> from ofxtools import OFXTree
>>> tree = OFXTree()
>>> tree.parse('foobar.ofx')
>>> response = tree.convert()
>>> response                  
<OFXResponse fid='AIS' org='Ameritrade Technology Group' dtserver='2014-12-01 16:11:44' len(statements)=1 len(securities)=5>
>>> stmt = response.statements[0] 
>>> stmt
<InvestmentStatement account=<INVACCTFROM acctid='000000000' brokerid='ameritrade.com'> currency='USD' balances=<INVBAL buypower='3466.92' marginbalance='-488.6' shortbalance='-2830.001953' availcash='1469.51'> len(other_balances)=23 len(positions)=4 len(transactions)=5>
>>> stmt.positions[2]
<POSSTOCK dtpriceasof='2014-11-28 12:00:00' mktval='2313' postype='LONG' heldinacct='MARGIN' uniqueidtype='CUSIP' uniqueid='527288104' units='100' unitprice='23.13'>
>>> stmt.transactions[3]
<SELLSTOCK selltype='SELL' uniqueid='404139107' memo='SELL TRADE' subacctfund='MARGIN' units='-2704' uniqueidtype='CUSIP' dttrade='2014-11-13 11:16:59' fees='0.41' total='18376.8' commission='9.99' fitid='12386048052' subacctsec='MARGIN' unitprice='6.8'>
>>> response.securities[1]
<STOCKINFO secname='HC 2 HOLDINGS INC (QB)' uniqueidtype='CUSIP' uniqueid='404139107' ticker='HCHC'>
