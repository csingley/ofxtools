.. _generating:

Generating OFX
==============
Creating your own OFX requests or responses - as would be neeeded for, say,
a Python-powered OFX server - is fairly straightforward.  However, you will
need to be pretty familiar with the OFX spec.  ``ofxtools`` validates
individual nodes in the hierarchy, but doesn't really do anything to verify
compliant sequence order, for example.  It doesn't validate against a DTD.
That is on you, friend.

Don't forget to make datetimes timezone-aware.

As an example, we'll create a trivial bank statement response.  You can follow
along in section 11.4.2.2 of the OFX spec.

.. code:: python

    In [1]: from ofxtools.models import *
    In [2]: from ofxtools.utils import UTC
    In [3]: from decimal import Decimal
    In [4]: from datetime import datetime
    In [5]: ledgerbal = LEDGERBAL(balamt=Decimal('150.65'),
       ...:                       dtasof=datetime(2015, 1, 1, tzinfo=UTC))
    In [6]: acctfrom = BANKACCTFROM(bankid='123456789',
       ...:                         acctid='23456', accttype='CHECKING')  # OFX Section 11.3.1
    In [7]: stmtrs = STMTRS(curdef='USD', bankacctfrom=acctfrom,
       ...:                 ledgerbal=ledgerbal) 

So far so good.  Now to slather it in wrapper cruft and garnish with metadata.

.. code:: python

    In [8]: status = STATUS(code=0, severity='INFO')
    In [9]: stmttrnrs = STMTTRNRS(trnuid='5678', status=status, stmtrs=stmtrs)
    In [10]: bankmsgsrs = BANKMSGSRSV1(stmttrnrs)
    In [11]: fi = FI(org='Illuminati', fid='666')  # Required for Quicken compatibility
    In [12]: sonrs = SONRS(status=status,
        ...:               dtserver=datetime(2015, 1, 2, 17, tzinfo=UTC),
        ...:               language='ENG', fi=fi)
    In [13]: signonmsgs = SIGNONMSGSRSV1(sonrs=sonrs)
    In [14]: ofx = OFX(signonmsgsrsv1=signonmsgs, bankmsgsrsv1=bankmsgsrs)

OK, that's the complete OFX message body.  To serialize it, we transform the
``ofxtools.models`` structure back into an instance of
``xml.etree.ElementTree.ElementTree``.

.. code:: python

    In [15]: import xml.etree.ElementTree as ET
    In [16]: root = ofx.to_etree()
    In [17]: message = ET.tostring(root).decode()
    In [18]: message
    Out[18]: '<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><DTSERVER>20150102170000</DTSERVER><LANGUAGE>ENG</LANGUAGE><FI><ORG>Illuminati</ORG><FID>666</FID></FI></SONRS></SIGNONMSGSRSV1><BANKMSGSRSV1><STMTTRNRS><TRNUID>5678</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><STMTRS><CURDEF>USD</CURDEF><BANKACCTFROM><BANKID>123456789</BANKID><ACCTID>23456</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM><LEDGERBAL><BALAMT>150.65</BALAMT><DTASOF>20150101000000</DTASOF></LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>'

One last step - we need to prepend an OFX header.

.. code:: python

    In [19]: from ofxtools.header import make_header
    In [20]: header = str(make_header(version=220))
    In [21]: header
    Out[21]: '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\r\n<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>\r\n'
    In [22]: response = header + message
    In [23]: response
    Out[23]: '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\r\n<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>\r\n<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><DTSERVER>20150102170000</DTSERVER><LANGUAGE>ENG</LANGUAGE><FI><ORG>Illuminati</ORG><FID>666</FID></FI></SONRS></SIGNONMSGSRSV1><BANKMSGSRSV1><STMTTRNRS><TRNUID>5678</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><STMTRS><CURDEF>USD</CURDEF><BANKACCTFROM><BANKID>123456789</BANKID><ACCTID>23456</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM><LEDGERBAL><BALAMT>150.65</BALAMT><DTASOF>20150101000000</DTASOF></LEDGERBAL></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>'

Hand that to your HTTP server, and off you go.
