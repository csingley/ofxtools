.. _client:

Some financial institutions make you use their web application to generate
OFX (or QFX) files that you can download via your browser.  If they give you
a choice, prefer "OFX" or "Microsoft Money" format over "QFX" or "Quicken".

Other financial institutions are good enough to offer you a server socket,
to which ``ofxtools`` can connect and download OFX data for you.


Downloading OFX Data With ofxget
================================

Locating ofxget
--------------------------
The ``ofxget`` shell script should have been installed by ``pip`` along with
the ``ofxtools`` library.  If the install location isn't already in your
``$PATH``, you'll likely want to add it.

A user installation drops ``ofxget`` under ``~/.local/bin`` on Linux or Mac,
and ``AppData\Roaming\Python\PythonXY\Scripts`` for Windows.

If all else fails, you can execute
``</path/to/ofxtools>/ofxtools/scripts/ofxget.py``.

Using ofxget  - TL;DR
---------------------
If your financial institution is known to ``ofxtools/config/fi.cfg``, then
the quickest way to get your data is to say (e.g. for American Express):

.. code-block:: bash

    $ ofxget stmt amex --user <your_username> --all

Enter your password when prompted.

Using ofxget - in depth 
-----------------------
``ofxget`` takes two mandatory positional arguments - the request type and
the server URL or nickname - along with a bunch of optional keyword arguments.

See the ``--help`` for explanation of the script options.

Available request types (as indicated in the ``--help``) are ``scan``,
``prof``, ``acctinfo``, ``stmt``, and ``tax1099``.  We'll work through most of
these in an example of bootstrapping a full configuration for American Express.

We must know the OFX server URL in order to connect at all.  The best place
to find this (along with other useful connection information) is the
`OFX Home`_ website.  You can also try the fine folks at `GnuCash`_, who share
the struggle.

OFX Home has a listing for AmEx, giving a URL plus the ``ORG``/``FID`` pair
(i.e. ``<FI><ORG>`` and ``<FI><FID>`` in the signon request.)  This aggregate
is optional per the OFX spec, and if your FI is running its own OFX server it
is optional - many major providers don't need it to connect.  However,
Quicken always sends ``<FI>``, so your bank may require it anyway.  AmEx
appears to be one of these; its OFX server throws HTTP error 503 if you omit
``ORG``/``FID``.

Using the connection information from OFX Home, first we will try to establish
basic connectivity by requesting an OFX profile, which does not require
authenticating a login.

.. code-block:: bash

    $ ofxget --org AMEX --fid 3101 prof https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload

This works just fine, dumping a load of markup on the screen telling us
what OFX services are available and some parameters for using them.

If it doesn't work, see below for on scanning version and format parameters.

We probably don't want to keep typing all that out every time we want to
connect, so we'll create a configuration file to store it for reuse.  Inside
our user home directory, the config file needs to be located at
``.config/ofxtools/ofxget.cfg`` (for Linux and Mac), or
``AppData\Roaming\ofxtools\ofxget.cfg`` (for Windows).  It's easy to create
one from scratch (in simple INI format), or you can find a sample at
``</path/to/ofxtools>/config/ofxget_example.cfg`` (including some hints in the
comments).  Our config just copies the script args above, tagging them with a
nickname for reference:

.. code-block:: ini

    # American Express
    [amex]
    url: https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload
    org: AMEX
    fid: 3101

Alternatively, since AmEx has working parameters listed on OFX Home, you can
just use the OFX Home API to look them up for each request.  Using the OFX Home
database id (at the end of the webpage URL), the config looks like this:

.. code-block:: ini

    # American Express
    [amex]
    ofxhome_id: 424

With either configuration, we can now use the provider nickname to make our
connection more conveniently:

.. code-block:: bash

    $ ofxget prof amex

The next step is to log into the OFX server with our username & password,
and get a list of accounts for which we can download statements.

.. code-block:: bash

    $ ofxget acctinfo amex --user <username>

After passing authentication, a successful result looks like this:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <?OFX OFXHEADER="200" VERSION="203" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="e1259eaf-b54e-46de-be22-fe07a9172b79"?>
    <OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY><MESSAGE>Login successful</MESSAGE></STATUS><DTSERVER>20190430093324.000[-7:MST]</DTSERVER><LANGUAGE>ENG</LANGUAGE><FI><ORG>AMEX</ORG><FID>3101</FID></FI><ORIGIN.ID>FMPWeb</ORIGIN.ID><CUSTOMER.TYPE>BCM</CUSTOMER.TYPE><START.TIME>20190430093324</START.TIME></SONRS></SIGNONMSGSRSV1><SIGNUPMSGSRSV1><ACCTINFOTRNRS><TRNUID>2a3cbf11-23da-4e77-9a55-2359caf82afe</TRNUID><STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS><ACCTINFORS><DTACCTUP>20190430093324.150[-7:MST]</DTACCTUP><ACCTINFO><CCACCTINFO><CCACCTFROM><ACCTID>888888888888888</ACCTID><CYCLECUT.INDICATOR>false</CYCLECUT.INDICATOR><PURGE.INDICATOR>false</PURGE.INDICATOR><INTL.INDICATOR>false</INTL.INDICATOR></CCACCTFROM><SUPTXDL>Y</SUPTXDL><XFERSRC>N</XFERSRC><XFERDEST>N</XFERDEST><SVCSTATUS>ACTIVE</SVCSTATUS></CCACCTINFO></ACCTINFO><ACCTINFO><CCACCTINFO><CCACCTFROM><ACCTID>999999999999999</ACCTID><CYCLECUT.INDICATOR>false</CYCLECUT.INDICATOR><PURGE.INDICATOR>false</PURGE.INDICATOR><INTL.INDICATOR>false</INTL.INDICATOR></CCACCTFROM><SUPTXDL>Y</SUPTXDL><XFERSRC>N</XFERSRC><XFERDEST>N</XFERDEST><SVCSTATUS>ACTIVE</SVCSTATUS></CCACCTINFO></ACCTINFO></ACCTINFORS></ACCTINFOTRNRS></SIGNUPMSGSRSV1></OFX>

Within all that markup, the part we're looking for is this:

.. code-block:: xml

    <CCACCTFROM><ACCTID>888888888888888</ACCTID></CCACCTFROM>
    <CCACCTFROM><ACCTID>999999999999999</ACCTID></CCACCTFROM>

We have two credit card accounts, 888888888888888 and 999999999999999.  We
can request activity statements for them like so:

.. code-block:: bash

    $ ofxget stmt amex --user <username> --creditcard 888888888888888 --creditcard 999999999999999

Note that multiple accounts are specified by repeating the ``creditcard`` argument.

Of course, nobody wants to memorize and type out their account numbers, so
we'll go ahead and include this information in our ``ofxget.cfg``:

.. code-block:: ini

    # American Express
    [amex]
    url: https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload
    org: AMEX
    fid: 3101
    user: <username>
    creditcard: 888888888888888,999999999999999

Note that multiple accounts are specified as a comma-separated list.

By default, a statement request asks for all transaction activity available
from the server.  To restrict the statement to a certain time period, we
use the ``--start`` and ``--end`` arguments:

.. code-block:: bash

    $ ofxget stmt amex --start 20140101 --end 20140630 > 2014-04_amex.ofx

Please note that the CLI accepts OFX-formatted dates (YYYYmmdd) rather than
ISO-8601 (YYYY-mm-dd).


Scanning for OFX connection formats
-----------------------------------
If you can't make an OFX connection...  well, Quicken hasn't yet updated
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

    $ ofxget scan etrade  
    [{"versions": [102], "formats": [{"pretty": false, "unclosed_elements": true}, {"pretty": false, "unclosed_elements": false}]}, {"versions": [], "formats": []}]
    $ ofxget scan usaa
    [{"versions": [102, 151], "formats": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}]}, {"versions": [200, 202], "formats": [{"pretty": false}, {"pretty": true}]}]
    $ ofxget scan vanguard
    [{"versions": [102, 103, 151, 160], "formats": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": false}]}, {"versions": [200, 201, 202, 203, 210, 211, 220], "formats": [{"pretty": true}]}]

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
    version: 151
    unclosedelements: true

    [vanguard]
    ofxhome_id: 479
    version: 203
    pretty: true


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


Using OFXClient in Another Program
==================================

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
