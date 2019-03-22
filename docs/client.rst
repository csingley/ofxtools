.. _client:

Downloading OFX Data
====================
Some financial institutions make you use their web application to generate
OFX (or QFX) files that you can download via your browser.  If they give you
a choice, prefer "OFX" or "Microsoft Money" format over "QFX" or "Quicken".

Other financial institutions are good enough to offer you a server socket,
to which ``ofxtools`` can connect and download OFX data for you.


Configuring an OFX client
-------------------------
Setting up a client to connect with an OFX servers requires configuring
some parameters, most importantly:

- Server URL
- Financial institution identifiers (``<FI><ORG>`` and ``<FI><ID>``)
- Bank id
- Broker id

Quicken and Money don't expose OFX-specific parameters, so you'll have to find
these on your own.  Tech support calls to banks tend to go like this:
    | Me: Hi, what's your OFX server URL?
    | CSR: What version of Quicken do you run?  Sorry, we don't support that.

The best resource for finding OFX configs is the `OFX Home`_ website
(thanks are due to Jesse Lietch).  Sadly, since Microsoft Money went EOL,
Microsoft no longer provides a web API containing FI configs (as utilized
in Jeremy Jongsma's pioneering `getfidata.sh`_ script) - the source data
for OFX Home.  Read through the OFX Home comments; users often post updates
with configurations that have worked for them.

You can also talk to the fine folks at `GnuCash`_, who share the struggle.

For US banks, the bank id is an `ABA routing number`_.  This will be printed
on their checks.

US brokers tend to use their primary DNS domain.  You could also try using
a 4-digit `DTC number`_.

Depending on your financial institution, you may also need to fiddle with
configuring the OFX protocol version (many credit unions and discount
brokers still haven't upgraded their servers to OFXv2) and/or the
client application identifiers (it's usually safest to tell them you're a
recent version of Quicken for Windows).


Using the ``ofxget`` script
---------------------------
-  Copy ``~/.config/ofxtools/ofxget_example.cfg`` to
   ``~/.config/ofxtools/ofxget.cfg`` and edit:
-  Add a section for your financial institution, including URL, account
   information, login, etc.  See comments within the example file.
-  Execute ``ofxget`` with appropriate arguments, for example:

``ofxget amex stmt -s 20140101 -e 20140630 > 2014-04_amex.ofx``

Please note that the CLI accepts OFX-formatted dates (YYYYmmdd) not
ISO-8601 (YYYY-mm-dd).

See the ``--help`` for explanation of the script options.


Using ``OFXClient`` in another program
--------------------------------------
To use within another program, first initialize an ``ofxtools.Client.OFXClient``
instance with the relevant connection parameters.

Using the configured OFXClient instance, make a request by calling the
relevant method, e.g. ``OFXClient.request_statements()``.  OFX supports
multi-part statement requests, so ``request_statements()`` accepts sequences as
arguments.  Simple data containers for each statement
(``StmtRq``, ``CcStmtRq``, etc.) are provided in ``ofxtools.Client``.

The method call therefore looks like this:

.. code-block:: python 

    >>> client = OFXClient('https://onlinebanking.capitalone.com/ofx/process.ofx',
    ...                    org='Hibernia', fid='1001', bankid='056073502',
    ...                    appver=202)
    >>> s0 = StmtRq(acctid='1', accttype='CHECKING',
    ...             dtstart=datetime.date(2015, 1, 1),
    ...             dtend=datetime.date(2015, 1, 31))
    >>> s1 = StmtRq(acctid='2', accttype='SAVINGS',
    ...             dtstart=datetime.date(2015, 1, 1),
    ...             dtend=datetime.date(2015, 1, 31))
    >>> c0 = CcStmtRq(acctid='3',
    ...               dtstart=datetime.date(2015, 1, 1),
    ...               dtend=datetime.date(2015, 1, 31))
    >>> response = client.request_statements(user='jpmorgan', password='t0ps3kr1t',
    ...                                      stmtrqs=[s0, s1], ccstmtrqs=[c0])


.. _OFX Home: http://www.ofxhome.com/
.. _ABA routing number: http://routingnumber.aba.com/default1.aspx
.. _DTC number: http://www.dtcc.com/client-center/dtc-directories
.. _getfidata.sh: https://web.archive.org/web/20070120102800/http://www.jongsma.org/gc/bankinfo/getfidata.sh.gz
.. _GnuCash: https://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings
