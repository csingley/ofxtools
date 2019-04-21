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
some parameters.  Quicken and Money don't expose OFX-specific parameters, so
you'll have to find these on your own.  Tech support calls to banks tend to go
like this:
    | Me: Hi, what's your OFX server URL?
    | CSR: What version of Quicken do you run?  Sorry, we don't support that.

The best resource for finding OFX configs is the `OFX Home`_ website
(thanks are due to Jesse Lietch).  Sadly, since Microsoft Money went EOL,
Microsoft no longer provides a web API containing FI configs (as utilized
in Jeremy Jongsma's pioneering `getfidata.sh`_ script) - the source data
for OFX Home.  Read through the OFX Home comments; users often post updates
with configurations that have worked for them.

You can also talk to the fine folks at `GnuCash`_, who share the struggle.

You will definitely need to configure:

- Server URL
- Bank id
- Broker id
- Account numbers

The URL is of course mandatory in order to connect.  You will need
bankid/brokerid and acount numbers in order to download statements.

For US banks, the bankid is an `ABA routing number`_.  This will be printed
on their checks.

US brokers tend to follow the recommendation of the OFX spec and use their
primary DNS domain as their brokerid (e.g. "ameritrade.com").  You could also
try using a 4-digit `DTC number`_.

You may also need to configure:

- Financial institution identifiers (``<FI><ORG>`` and ``<FI><FID>``)
- Supported OFX version
- Supported client application

It's entirely possible that you don't need to configure ``<FI>`` in order
to connect.  This aggregate is optional per the OFX spec, and if your financial
institution is running its own OFX server it is unnecessary - many major
don't need it to connect.  However, Quicken always sends ``<FI>``, so your bank
may require it.

Quicken also hasn't yet updated to OFX version 2, so your bank may require
a lower protocol version in order to connect.  Quicken only requires
compliance with OFXv1.0.3 if implementing multifactor authentication; if
a financial institution doesn't support MFA (as published in its OFX profile)
then it may reject any OFX version higher than 1.0.2.  E*Trade, for example,
does this.

Similarly, many banks configure their servers to reject any connections that
aren't from Quicken.  It's usually safest to tell them you're a recent version
of Quicken for Windows.  ``OFXClient`` does this by default, so you probably
don't need to worry about it.

Finally, some financial institutions are picky about formatting.  They may
fail to parse OFXv1 that includes closing tags - the ``unclosedelements``
argument comes in handy here.  They may require that OFX requests either
must have or can't have tags separated by newlines - try setting or
unsetting the ``prettyprint`` argument.

We've also had some problems with FIs checking the ``User-Agent`` header in
HTTP requests, so it's blanked out.  If a motivated user wants to send along
a packet capture showing what Quicken sends for ``User_Agent``, it might be
a good idea to spoof that as well.


Using the ofxget script
-----------------------
Activate the virtual environment in which you installed ``ofxtools``, e.g.

.. code-block:: bash
    source ~/.venvs/ofxtools/bin/activate

Execute ``ofxget`` with appropriate arguments, for example:

.. code-block:: bash

    ofxget https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload --org AMEX --fid 3101 --user porkypig --creditcard 99999999999 --start 20140101 --end 20140630 > 2014-04_amex.ofx

Enter your password when prompted.

See the ``--help`` for explanation of the script options.

Please note that the CLI accepts OFX-formatted dates (YYYYmmdd) rather than
ISO-8601 (YYYY-mm-dd).

Of course, typing this kind of command gets old very quickly.  You can store
these details in a config file for reuse:

-  Copy ``~/.config/ofxtools/ofxget_example.cfg`` to
   ``~/.config/ofxtools/ofxget.cfg`` and edit.
-  Add a section for your financial institution, including URL, account
   information, login, etc.  See comments within the example file.

Since ``ofxtools`` already has connection information for American Express,
our own config file would just look like this:

.. code-block:: ini

    # American Express
    [amex]
    user: porkypig
    creditcard: 99999999999

A more fully-specified configuration might look like this:

.. code-block:: ini

    # American Express
    [amex]
    url: https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload
    version: 220
    org: AMEX
    fid: 3101
    appid: QWIN
    appver:  2700
    user: porkypig
    creditcard: 88888888888,99999999999

Using such a configuration, the command invocation simplifies to this:

.. code-block:: bash

    ofxget amex -s 20140101 -e 20140630 > 2014-04_amex.ofx

Using OFXClient in another program
----------------------------------
To use within another program, first initialize an ``ofxtools.Client.OFXClient``
instance with the relevant connection parameters.

Using the configured ``OFXClient`` instance, make a request by calling the
relevant method, e.g. ``OFXClient.request_statements()``.  OFX supports
multi-part statement requests, so ``request_statements()`` accepts sequences as
arguments.  Simple data containers for each statement
(``StmtRq``, ``CcStmtRq``, etc.) are provided in ``ofxtools.Client``.

The method call therefore looks like this:

.. code-block:: python 


    >>> client = OFXClient('https://onlinebanking.capitalone.com/ofx/process.ofx',
    ...                    org='Hibernia', fid='1001', bankid='056073502',
    ...                    version=202)
    >>> dtstart = datetime.datetime(2015, 1, 1, tzinfo=ofxtools.utils.UTC)
    >>> dtend = datetime.datetime(2015, 1, 31, tzinfo=ofxtools.utils.UTC)
    >>> s0 = StmtRq(acctid='1', accttype='CHECKING', dtstart=dtstart, dtend=dtend)
    >>> s1 = StmtRq(acctid='2', accttype='SAVINGS', dtstart=dtstart, dtend=dtend)
    >>> c0 = CcStmtRq(acctid='3', dtstart=dtstart, dtend=dtend)
    >>> response = client.request_statements('jpmorgan', 't0ps3kr1t', s0, s1, c0,
    ...                                      prettyprint=True)

Other methods available:
    * ``OFXClient.request_end_statements()`` - STMTENDRQ/CCSTMTENDRQ
    * ``OFXClient.request_profile()`` - PROFRQ
    * ``OFXClient.request_accounts()``- ACCTINFORQ

.. _OFX Home: http://www.ofxhome.com/
.. _ABA routing number: http://routingnumber.aba.com/default1.aspx
.. _DTC number: http://www.dtcc.com/client-center/dtc-directories
.. _getfidata.sh: https://web.archive.org/web/20070120102800/http://www.jongsma.org/gc/bankinfo/getfidata.sh.gz
.. _GnuCash: https://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings
