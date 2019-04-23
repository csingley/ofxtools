.. _client:

Downloading OFX Data
====================
Some financial institutions make you use their web application to generate
OFX (or QFX) files that you can download via your browser.  If they give you
a choice, prefer "OFX" or "Microsoft Money" format over "QFX" or "Quicken".

Other financial institutions are good enough to offer you a server socket,
to which ``ofxtools`` can connect and download OFX data for you.


Using the ofxget script
-----------------------
Activate the virtual environment in which you installed ``ofxtools``, e.g.

.. code-block:: bash

    $ source ~/.venvs/ofxtools/bin/activate

Execute ``ofxget`` with appropriate arguments, for example:

.. code-block:: bash

    $ ofxget https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload --org AMEX --fid 3101 --user porkypig --creditcard 99999999999 --start 20140101 --end 20140630 > 2014-04_amex.ofx

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

    $ ofxget amex -s 20140101 -e 20140630 > 2014-04_amex.ofx


Discovering OFX client configurations
-------------------------------------
Quicken and Money don't expose OFX-specific parameters, so you'll have to find
these on your own.  Tech support calls to banks tend to go like this:
    | Me: Hi, what's your OFX server URL?
    | CSR: What version of Quicken do you run?  Sorry, we don't support that.

Sadly, since Microsoft Money went EOL, Microsoft no longer provides a public
web API containing FI configs.  However, Jesse Lietch is carrying the torch
at the `OFX Home`_ website, which is the best resource for finding OFX configs.

The OFX Home database is getting a little stale in places. Read through the
comments, where users often post updated configurations that have worked
for them.  If you get something working, post it there.

You can also talk to the fine folks at `GnuCash`_, who share the struggle.

You will definitely need to configure:

- Server URL
- Bank id
- Broker id
- Account numbers

The URL is of course mandatory in order to connect at all.

You will need bankid/brokerid and acount numbers in order to download
statements.  I'm optimistic that you'll be able to discover your account
numbers.

For US banks, the bankid is an `ABA routing number`_.  This will be printed
on their checks.

US brokers tend to follow the recommendation of the OFX spec and use their
primary DNS domain as their brokerid (e.g. "ameritrade.com").  Some FIs
style the brokerid in all caps (e.g. "SCHWAB.COM").  Some apparently don't
understand the DNS system, and use the FQDN of their website
(e.g. "www.scottrade.com").  Try various permutations.  Of course, then there's
Interactive Brokers, whose brokerid is an apparently random 4-digit number
(no, it's not a `DTC number`_ )... not that it really matters, since they don't
open a port anyway.

Probably you will also need to configure financial institution identifiers
(i.e. ``<FI><ORG>`` and ``<FI><FID>`` in the signon request.)  This aggregate
is optional per the OFX spec, and if your FI is running its own OFX server it
is unnecessary - many major providers don't need it to connect.  However,
Quicken always sends ``<FI>``, so your bank may require it anyway.

If a listing exists (and is up to date), `OFX Home`_ can provide you with
all the necessary configuration data.  In fact, you don't even need to enter
all of it into your ``ofxtools`` configuration file... just get the OFX Home
database id (at the end of the webpage URL) and configure ``ofxtools`` like so:

.. code-block:: ini

    # American Express
    [amex]
    ofxhome_id: 424

With any luck this will just work.  You can test the connection parameters by
requesting their OFX profile, which doesn't require login info or acct#s.

.. code-block:: bash

    $ ofxget --profile amex                                                                                                           1 ↵
    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <?OFX OFXHEADER="200" VERSION="203" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="08c9f61f-f16a-4471-9b1c-463b31dbaae4"?>
    <OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY><MESSAGE>Login successful</MESSAGE></STATUS><DTSERVER>20190422122549.771[-7:MST]</DTSERVER><LANGUAGE>ENG</LANGUAGE><FI><ORG>AMEX</ORG><FID>3101</FID></FI><START.TIME>20190422122549</START.TIME></SONRS></SIGNONMSGSRSV1><PROFMSGSRSV1><PROFTRNRS><TRNUID>6397def1-869e-4141-9c14-8c0236f7b8a1</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><PROFRS><MSGSETLIST><SIGNONMSGSET><SIGNONMSGSETV1><MSGSETCORE><VER>1</VER><URL>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</URL><OFXSEC>NONE</OFXSEC><TRANSPSEC>Y</TRANSPSEC><SIGNONREALM>AMEXREALM</SIGNONREALM><LANGUAGE>ENG</LANGUAGE><SYNCMODE>LITE</SYNCMODE><RESPFILEER>Y</RESPFILEER><SPNAME>Aexp</SPNAME></MSGSETCORE></SIGNONMSGSETV1></SIGNONMSGSET><SIGNUPMSGSET><SIGNUPMSGSETV1><MSGSETCORE><VER>1</VER><URL>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</URL><OFXSEC>NONE</OFXSEC><TRANSPSEC>Y</TRANSPSEC><SIGNONREALM>AMEXREALM</SIGNONREALM><LANGUAGE>ENG</LANGUAGE><SYNCMODE>LITE</SYNCMODE><RESPFILEER>Y</RESPFILEER><SPNAME>Aexp</SPNAME></MSGSETCORE><WEBENROLL><URL>https://www.americanexpress.com</URL></WEBENROLL><CHGUSERINFO>N</CHGUSERINFO><AVAILACCTS>Y</AVAILACCTS><CLIENTACTREQ>Y</CLIENTACTREQ></SIGNUPMSGSETV1></SIGNUPMSGSET><BANKMSGSET><BANKMSGSETV1><MSGSETCORE><VER>1</VER><URL>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</URL><OFXSEC>NONE</OFXSEC><TRANSPSEC>Y</TRANSPSEC><SIGNONREALM>AMEXREALM</SIGNONREALM><LANGUAGE>ENG</LANGUAGE><SYNCMODE>LITE</SYNCMODE><RESPFILEER>Y</RESPFILEER><SPNAME>Aexp</SPNAME></MSGSETCORE><CLOSINGAVAIL>N</CLOSINGAVAIL><EMAILPROF><CANEMAIL>N</CANEMAIL><CANNOTIFY>N</CANNOTIFY></EMAILPROF></BANKMSGSETV1></BANKMSGSET><CREDITCARDMSGSET><CREDITCARDMSGSETV1><MSGSETCORE><VER>1</VER><URL>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</URL><OFXSEC>NONE</OFXSEC><TRANSPSEC>Y</TRANSPSEC><SIGNONREALM>AMEXREALM</SIGNONREALM><LANGUAGE>ENG</LANGUAGE><SYNCMODE>LITE</SYNCMODE><RESPFILEER>Y</RESPFILEER><SPNAME>Aexp</SPNAME></MSGSETCORE><CLOSINGAVAIL>N</CLOSINGAVAIL></CREDITCARDMSGSETV1></CREDITCARDMSGSET><PROFMSGSET><PROFMSGSETV1><MSGSETCORE><VER>1</VER><URL>https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload</URL><OFXSEC>NONE</OFXSEC><TRANSPSEC>Y</TRANSPSEC><SIGNONREALM>AMEXREALM</SIGNONREALM><LANGUAGE>ENG</LANGUAGE><SYNCMODE>LITE</SYNCMODE><RESPFILEER>Y</RESPFILEER><SPNAME>Aexp</SPNAME></MSGSETCORE></PROFMSGSETV1></PROFMSGSET></MSGSETLIST><SIGNONINFOLIST><SIGNONINFO><SIGNONREALM>AMEXREALM</SIGNONREALM><MIN>5</MIN><MAX>20</MAX><CHARTYPE>ALPHAANDNUMERIC</CHARTYPE><CASESEN>N</CASESEN><SPECIAL>Y</SPECIAL><SPACES>N</SPACES><PINCH>N</PINCH><CHGPINFIRST>N</CHGPINFIRST><CLIENTUIDREQ>N</CLIENTUIDREQ><AUTHTOKENFIRST>N</AUTHTOKENFIRST><MFACHALLENGESUPT>N</MFACHALLENGESUPT><MFACHALLENGEFIRST>N</MFACHALLENGEFIRST></SIGNONINFO></SIGNONINFOLIST><DTPROFUP>20120730200000.925[-7:MST]</DTPROFUP><FINAME>American Express</FINAME><ADDR1>777 American Expressway</ADDR1><CITY>Fort Lauderdale</CITY><STATE>Fla.</STATE><POSTALCODE>33337-0001</POSTALCODE><COUNTRY>USA</COUNTRY><CSPHONE>1-800-AXP-7500  (1-800-297-7500)</CSPHONE></PROFRS></PROFTRNRS></PROFMSGSRSV1></OFX>

Looking good!  If it doesn't work...  well, Quicken hasn't yet updated
to OFX version 2, so your bank may require a lower protocol version in order to
connect.  The ``version`` argument is used for this purpose.

As well, some financial institutions are picky about formatting.  They may
fail to parse OFXv1 that includes closing tags - the ``unclosedelements``
argument comes in handy here.  They may require that OFX requests either
must have or can't have tags separated by newlines - try setting or
unsetting the ``prettyprint`` argument.

``ofxget`` includes a ``scan`` option to help you discover these requirements.
Here's how to use it.

.. code-block:: bash

    $ ofxget --scan etrade
    {"102": [{"pretty": false, "unclosed_elements": true}, {"pretty": false, "unclosed_elements": false}]}
    $ ofxget --scan usaa    
    {"102": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}], "151": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}], "200": [{"pretty": true, "unclosed_elements": false}, {"pretty": false, "unclosed_elements": false}], "202": [{"pretty": true, "unclosed_elements": false}, {"pretty": false, "unclosed_elements": false}]}
    $ ofxget --scan vanguard
    {"102": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": false}, {"pretty": true, "unclosed_elements": true}], "103": [{"pretty": true, "unclosed_elements": false}, {"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}], "151": [{"pretty": true, "unclosed_elements": false}, {"pretty": true, "unclosed_elements": true}, {"pretty": false, "unclosed_elements": true}], "160": [{"pretty": true, "unclosed_elements": false}, {"pretty": true, "unclosed_elements": true}, {"pretty": false, "unclosed_elements": true}], "200": [{"pretty": true, "unclosed_elements": false}], "201": [{"pretty": true, "unclosed_elements": false}], "202": [{"pretty": true, "unclosed_elements": false}], "203": [{"pretty": true, "unclosed_elements": false}], "210": [{"pretty": true, "unclosed_elements": false}], "211": [{"pretty": true, "unclosed_elements": false}], "220": [{"pretty": true, "unclosed_elements": false}]}

(Try to exercise restraint with this command.  Each invocation sends several
dozen HTTP requests to the server; you can get your IP throttled or blocked.)

The output shows configurations that worked.

E*Trade will only accept OFX version 1.0.2; they don't care about newlines or
closing tags.

USAA only accepts OFX versions 1.0.2, 1.5.1, 2.0.0, and 2.0.2.  Version 1 needs
to be old-school SGML - no closing tags.  Newlines are optional.

Vanguard is a little funkier.  They accept all versions of OFX, but version
2 must have newlines.  For version 1, you must either insert newlines or
leave element tags unclosed (or both).  Closing tags will fail without newlines.

Copy these configs in your ``ofxget.cfg`` like so:

.. code-block:: ini

    [etrade]
    ofxhome_id: 446
    version: 102

    [usaa]
    ofxhome_id: 483
    version: 103
    unclosedelements: true

    [vanguard]
    ofxhome_id: 479
    version: 203
    pretty: false


In reality, though, it'd probaby be better just to use OFX 2.0.2 for USAA.

The master configs for OFX connection parameters are located in
``ofxtools/config/fi.cfg`` - if you get something working, edit it there and
submit a pull request to share it with others.

Finally, many banks configure their servers to reject any connections that
aren't from Quicken.  It's usually safest to tell them you're a recent version
of Quicken for Windows.  ``OFXClient`` does this by default, so you probably
don't need to worry about it.  If you do need to fiddle with it, use the
``appid`` and ``appver`` arguments.

We've also had some problems with FIs checking the ``User-Agent`` header in
HTTP requests, so it's been blanked out.  If some motivated user wants to send
along a packet capture showing what Quicken sends for ``User_Agent``, it might
be a good idea to spoof that as well.

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
