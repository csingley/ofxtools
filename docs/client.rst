.. _client:

Some financial institutions make you use their web application to generate
OFX (or QFX) files that you can download via your browser.  If they give you
a choice, prefer "OFX" or "Microsoft Money" format over "QFX" or "Quicken".

Other financial institutions are good enough to offer you a server socket,
to which ``ofxtools`` can connect and download OFX data for you.


Downloading OFX Data With ofxget
================================

Locating ofxget
---------------
The ``ofxget`` shell script should have been installed by ``pip`` along with
the ``ofxtools`` library.  If the install location isn't already in your
``$PATH``, you'll likely want to add it.

    **User installation**

    * Mac: ``~/Library/PythonX.Y/bin/ofxget``
    * Windows: ``AppData\Roaming\Python\PythonXY\Scripts\ofxget``
    * Linux/BSD/etc.: ``~/.local/bin/ofxget``

    **Site installation**

    * Mac: ``/Library/Frameworks/Python.framework/Versions/X.Y/bin/ofxget``
    * Windows: Good question; anybody know?
    * Linux/BSD/etc.: ``/usr/local/bin/ofxget``

    **Virtual environment installation**

    * ``</path/to/venv/root>/bin/ofxget``

If all else fails, you can execute ``python -m ofxtools.scripts.ofxget``, or
directly run ``python </path/to/ofxtools>/scripts/ofxget.py``.  You can
check where exactly that is by opening a Python interpreter and saying:

.. code-block:: python 

    >>> from ofxtools.scripts import ofxget
    >>> print(ofxget.__file__)

Using ofxget  - TL;DR
---------------------
Find your financial institution's nickname:

.. code-block:: bash

    $ ofxget list

If your financial institution is listed, then the quickest way to get your
hands on some OFX data is to say:

.. code-block:: bash

    $ ofxget stmt <server_nickname> -u <your_username> --all

Enter your password when prompted.

However, you really won't want to set the ``--all`` option every time you
download a statement; it's very inefficient.  Slightly more verbosely, you
might say :

.. code-block:: bash

    $ ofxget acctinfo <server_nickname> -u <your_username> --write
    $ ofxget stmt <server_nickname>

The first command requests a list of accounts and saves it to your config file
along with your user name.  This is in the nature of a first-time setup chore.

The second command is the kind of thing you'd run on a regular basis.  It
requests statements for each account listed in your config file for a given
server nickname.

Storing ofxget passwords in the system keyring
----------------------------------------------
**Note: this feature is experimental.  Expect bugs; kindly report them.**

Rather than typing them in each time, you can securely store your passwords
in the system keyring (if one is available) and have ``ofxget`` retrieve them
for you.  Examples of such keyring software include:

    * Windows Credential Locker
    * Mac Keychain
    * Freedesktop Secret Service (used by GNOME et al.)
    * KWallet (used by KDE)

To use these services, you will need to clutter up your nice clean ``ofxtools``
by installing the `python-keyring`_ package.

.. code-block:: bash

    $ pip install --user keyring

Additionally, KDE users will need to install `dbus-python`_.  Note the
recommendation in the ``python-keyring`` docs to install it systemwide via
your package manager.

Once these dependencies have been satisfied, you can pass the ``--savepass``
option to ``ofxget`` anywhere it wants a password, e.g.

.. code-block:: bash

    $ ofxget acctinfo <server_nickname> -u <your_username> --write --savepass

That should set you up to download statements easily.

To overwrite an existing password, simply add the  ``--savepass`` option
again and you will be prompted for a new password.

To delete a password entirely, you'll need to use your OS facilities for
managing these passwords (they are stored under "ofxtools", with an entry
for each server nickname).


Using ofxget - in depth 
-----------------------
``ofxget`` takes two positional arguments - request type (mandatory) and server
nickname (optional) - along with a bunch of optional keyword arguments.

See the ``--help`` for explanation of the script options.

Available request types (as indicated in the ``--help``) are ``list``, ``scan``,
``prof``, ``acctinfo``, ``stmt``, ``stmtend`` and ``tax1099``.  We'll work
through most of these in an example of bootstrapping a full configuration for
American Express.

Basic connectivity: requesting an OFX profile
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We must know the OFX server URL in order to connect at all.  ``ofxtools``
contains a database of all US financial institutions listed on the
`OFX Home`_ website that I could get to speak OFX with me.  If you can't find
your bank in ``ofxget`` (or if you're having a hard time configuring a
connection), `OFX Home`_ should be your first stop.  If you prefer, the
`OFX Blog` also makes the same data available in a different format.  Be sure
to review user-posted comments on either site.  You can also try the fine
folks at `GnuCash`_, who share the struggle.

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

    $ ofxget prof --org AMEX --fid 3101 --url https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload

This hairy beast of a command can be used for any arbitrary OFX server.
If the server is already known to ``ofxget``, then you can just use
its nickname instead:

.. code-block:: bash

    $ ofxget prof amex

Or, if the server is known to OFX Home, then you can just use its database
ID (the end part of its `institution page on OFX Home`_):

.. code-block:: bash

    $ ofxget prof --ofxhome 424

Any of these work just fine, dumping a load of markup on the screen telling us
what OFX services are available and some parameters for accessing them.

If it doesn't work, see below for a discussion of scanning version and format
parameters.

Creating a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We probably don't want to keep typing out multiline commands every time,
so we'll create a configuration file to store these parameters for reuse.

The simplest way to accomplish this is just to tell ``ofxget`` to save the
arguments you've passed on the command line to the config file.  To do that,
append the "--write" option to your CLI invocation.  You'll also need to
provide a server nickname.

.. code-block:: bash

    $ ofxget prof myfi --write --org AMEX --fid 3101 --url https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload

If your server is up on OFX Home, this works as well:

.. code-block:: bash

    ofxget prof myfi --ofxhome 424 --write

It's also easy to write a configuration file manually in a text editor - it's
just the command line options in simple INI format, with a server nicknames as
section headers.  You can find a sample at 
``</path/to/ofxtools>/config/ofxget_example.cfg``, including some hints in the
comments.

The location of the the config file depends on the platform.

    * Windows: ``<userhome>\AppData\Roaming\ofxtools\ofxget.cfg``
    * Mac: ``<userhome>/Library/Preferences/ofxtools/ofxget.cfg``
    * Linux/BSD/etc.: ``<userhome>/.config/ofxtools/ofxget.cfg``

(Of course, these locations may differ if you have exported nondefault
environment variables for ``APPDATA`` or ``XDG_CONFIG_HOME``)

You can verify where precisely ``ofxget`` is looking for its configuration
file by opening a Python interpreter and saying:

.. code-block:: python 

    >>> from ofxtools.scripts import ofxget
    >>> print(ofxget.USERCONFIGPATH)


Our configuration file will look like this:

.. code-block:: ini

    # American Express
    [amex]
    url: https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload
    org: AMEX
    fid: 3101

Alternatively, since AmEx has working parameters listed on OFX Home, you could
just use the OFX Home API to look them up for each request.  Using the OFX Home
database id (at the end of the webpage URL), the config looks like this:

.. code-block:: ini

    # American Express
    [amex]
    ofxhome: 424

With either configuration, we can now use the provider nickname to make our
connection more conveniently:

.. code-block:: bash

    $ ofxget prof amex

Logging in and requesting account information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The next step is to log into the OFX server with our username & password,
and get a list of accounts for which we can download statements.

.. code-block:: bash

    $ ofxget acctinfo amex --user <username>

After passing authentication, a successful result looks like this:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <?OFX OFXHEADER="200" VERSION="203" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="e1259eaf-b54e-46de-be22-fe07a9172b79"?>
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                    <MESSAGE>Login successful</MESSAGE>
                </STATUS>
                <DTSERVER>20190430093324.000[-7:MST]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>AMEX</ORG>
                    <FID>3101</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
        <SIGNUPMSGSRSV1>
            <ACCTINFOTRNRS>
                <TRNUID>2a3cbf11-23da-4e77-9a55-2359caf82afe</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <ACCTINFORS>
                    <DTACCTUP>20190430093324.150[-7:MST]</DTACCTUP>
                    <ACCTINFO>
                        <CCACCTINFO>
                            <CCACCTFROM>
                                <ACCTID>888888888888888</ACCTID>
                            </CCACCTFROM>
                            <SUPTXDL>Y</SUPTXDL>
                            <XFERSRC>N</XFERSRC>
                            <XFERDEST>N</XFERDEST>
                            <SVCSTATUS>ACTIVE</SVCSTATUS>
                        </CCACCTINFO>
                    </ACCTINFO>
                    <ACCTINFO>
                        <CCACCTINFO>
                            <CCACCTFROM>
                                <ACCTID>999999999999999</ACCTID>
                            </CCACCTFROM>
                            <SUPTXDL>Y</SUPTXDL>
                            <XFERSRC>N</XFERSRC>
                            <XFERDEST>N</XFERDEST>
                            <SVCSTATUS>ACTIVE</SVCSTATUS>
                        </CCACCTINFO>
                    </ACCTINFO>
                </ACCTINFORS>
            </ACCTINFOTRNRS>
        </SIGNUPMSGSRSV1>
    </OFX>

(Indentation applied and Intuit proprietary extension tags removed to improve
readability)

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

Note that multiple accounts are specified as a comma-separated sequence.

To spare your eyes from looking through all that tag soup, you can just tell
``ofxget`` to download the ACCTINFO response and update your config
file automatically:

.. code-block:: bash

    $ ofxget acctinfo amex --user <username> --write

Alternatively, as touched on in the TL;DR - if you're in a hurry, you can skip 
configuring which accounts you want, and instead just pass the ``--all``
argument:

.. code-block:: bash

    $ ofxget stmt amex --user <username> --all

This tells ``ofxget`` to generate an ACCTINFO request as above, parse the
response, and generate a STMT request for each account listed therein.  You
might as well tack on a ``--write`` to save these parameters to your config
file, so you don't have to do all that again next time.

Requesting statements
^^^^^^^^^^^^^^^^^^^^^

To rehash, a full statement request constructed entirely through the CLI looks
like this:

.. code-block:: bash

    $ export URL="https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do\?request_type\=nl_ofxdownload"
    $ ofxget stmt --url $URL --org AMEX --fid 3101 -u <username> -c 888888888888888 -c 999999999999999
    $ unset URL

This is for a credit card statement; for a bank statement you will also need
to pass in ``--bankid`` (usually the bank's `ABA routing number`_), and for a
brokerage statement you will need to pass in ``--brokerid`` (usually the
broker's DNS domain).

Presumably you will have migrated most/all of these parameters to your config
file as described above, so you can instead just say this:

.. code-block:: bash

    $ ofxget stmt amex

By default, a statement request asks for all transaction activity available
from the server.  To restrict the statement to a certain time period, we
use the ``--start`` and ``--end`` arguments:

.. code-block:: bash

    $ ofxget stmt amex --start 20140101 --end 20140630 > 2014-04_amex.ofx

Please note that the CLI accepts OFX-formatted dates (YYYYmmdd) rather than
ISO-8601 (YYYY-mm-dd).

You can also pass``--asof`` to set the reporting date for balances and/or
investment positions, although it tends to be ignored for the latter.

There are additional statement options for omitting transactions, balances,
and/or investment positions if you so desire, or including open securities
orders as of the statement end date.  See the ``--help`` for more details.


Scanning for OFX connection formats
-----------------------------------
What if you can't make an OFX connection?  Your bank isn't in ``ofxtools``; it
isn't at `OFX Home`_; it is in OFX Home but you can't request a profile; or
you're trying to connect to a non-US institution and all you have is the URL.

Quicken hasn't yet updated to OFX version 2, so your bank may require a lower
protocol version in order to connect.  The ``--version`` argument is used for
this purpose.

As well, some financial institutions are picky about formatting.  They may
fail to parse OFXv1 that includes closing tags - the ``--unclosedelements``
argument comes in handy here.  They may require that OFX requests either
must have or can't have tags separated by newlines - try setting or
unsetting the ``--prettyprint`` argument.

``ofxget`` includes a ``scan`` command to help you discover these requirements.
Here's how to use it.

.. code-block:: bash

    $ # E*Trade
    $ ofxget scan https://ofx.etrade.com/cgi-ofx/etradeofx
    [{"versions": [102], "formats": [{"pretty": false, "unclosedelements": true}, {"pretty": false, "unclosedelements": false}]}, {"versions": [], "formats": []}, {"chgpinfirst": false, "clientuidreq": false, "authtokenfirst": false, "mfachallengefirst": false}]
    $ ofxget scan usaa
    [{"versions": [102, 151], "formats": [{"pretty": false, "unclosedelements": true}, {"pretty": true, "unclosedelements": true}]}, {"versions": [200, 202], "formats": [{"pretty": false}, {"pretty": true}]}, {"chgpinfirst": false, "clientuidreq": false, "authtokenfirst": false, "mfachallengefirst": false}]
    $ ofxget scan vanguard
    [{"versions": [102, 103, 151, 160], "formats": [{"pretty": false, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": true}, {"pretty": true, "unclosed_elements": false}]}, {"versions": [200, 201, 202, 203, 210, 211, 220], "formats": [{"pretty": true}]}, {}]

(Try to exercise restraint with this command.  Each invocation sends several
dozen HTTP requests to the server; you can get your IP throttled or blocked.)

The output shows configurations that worked.

E*Trade will only accept OFX version 1.0.2; they don't care about newlines or
closing tags.

USAA only accepts OFX versions 1.0.2, 1.5.1, 2.0.0, and 2.0.2.  Version 1 needs
to be old-school SGML - no closing tags.  Newlines are optional. [Nota bene:
in actual fact, while USAA accepts profile requests in OFX versions 2.0.0 and
2.0.2, it only accepts statement requests in OFX versions 1.0.2 and 1.5.1...
without closing tags, as indicated above].

Vanguard is a little funkier.  They accept all versions of OFX, but version
2 must have newlines.  For version 1, you must either insert newlines or
leave element tags unclosed (or both).  Closing tags will fail without newlines.

Copyng these configs into your ``ofxget.cfg`` manually, they would look like
this:

.. code-block:: ini

    [etrade]
    version = 102

    [usaa]
    version = 151
    unclosedelements = true

    [vanguard]
    version = 203
    pretty = true

The config for USAA is just an example to show the syntax; in reality you'd be
better off just setting ``version = 202``.

As before, instead of manually editing the config file, you can also just ask
``ofxget`` to do it for you:

.. code-block:: bash

    $ ofxget scan myfi --write --url https://ofx.mybank.com/download

Setting CLIENTUID
^^^^^^^^^^^^^^^^^

Returning to the JSON screen dump from the ``scan`` output - the last set of
configs, after OFXv1 and OFXv2, contains information extracted from the
SIGNONINFO in the profile.  For the above institutions, this has contained
nothing interesting - all fields are false, except in the case of Vanguard,
which is blank because they deviate from the OFX spec and require an
authenticated login in order to return a profile.  However, in some cases
there's some important information in the SIGNONINFO.

.. code-block:: bash

    $ ofxget scan bofa
    [{"versions": [102], "formats": [{"pretty": false, "unclosedelements": true}, {"pretty": false, "unclosedelements": false}, {"pretty": true, "unclosedelements": true}, {"pretty": true, "unclosedelements": false}]}, {"versions": [], "formats": []}, {"chgpinfirst": false, "clientuidreq": true, "authtokenfirst": false, "mfachallengefirst": false}]
    $ ofxget scan chase
    [{"versions": [], "formats": []}, {"versions": [200, 201, 202, 203, 210, 211, 220], "formats": [{"pretty": false}, {"pretty": true}]}, {"chgpinfirst": false, "clientuidreq": true, "authtokenfirst": false, "mfachallengefirst": false}]

Of the 3 JSON objects included in the output, here we are focused on the last
(reformatted for readability):

.. code-block:: json

    {
        "chgpinfirst": false,
        "clientuidreq": true,
        "authtokenfirst": false,
        "mfachallengefirst": false
    }

Both Chase and BofA have the CLIENTUIDREQ flag set, which means you'll need to
set ``clientuid`` (a valid `UUID v4`_ value) either from the command line or in
your ``ofxget.cfg``.

Not to worry!  ``ofxget`` will automatically set a global default CLIENTUID for
you if you ask it to ``--write`` a configuration.  You can override this global 
default by setting a ``clientuid`` value under a server section in your config
file (in UUID4 format).  More conveniently, you can just pass ``ofxget``
the ``--clientuid`` option, e.g.:

.. code-block:: bash

    # The following generates a global default CLIENTUID
    $ ofxget scan chase --write
    # So does this
    $ ofxget prof chase --write
    # The following additionally generates a Chase-specific CLIENTUID
    $ ofxget acctinfo chase -u <username> --savepass --clientuid --write

Note: if you choose to use an FI-specific CLIENTUID, as in that last command,
then you really want to be sure to pass the ``--write`` option in order to save
it to your config file.  It is important that the CLIENTUID be consistent
across sessions.

After setting CLIENTUID, heed the ``<SONRS><STATUS>`` in the ACCTINFO response
returned by Chase.  It has a nonzero ``<CODE>`` (indicating a problem), and the
``<MESSAGE>`` instructs you to verify your identity within 7 days.  To do this,
you need to log into the bank's website and perform some sort of verification
process.

In Chase's case, they want you to click a link in their secure messaging
facility and enter a code sent via SMS/email.  Other banks make you jump
through slightly different hoops, but they usually involve logging into the
bank's website and performing some sort of high-hassle/low-security MFA
routine for first-time access.

The master configs for OFX connection parameters are located in
``ofxtools/config/fi.cfg``.  If you get a new server working, edit it there and
submit a pull request to share it with others.

Many banks configure their servers to reject any connections that aren't from
Quicken.  It's usually safest to tell them you're a recent version of Quicken
for Windows.  ``ofxget`` does this by default, so you probably don't need to
worry about it.  If you do need to fiddle with it, use the ``appid`` and
``appver`` arguments, either from the command line or in your ``ofxget.cfg``.

We've also had some problems with FIs checking the ``User-Agent`` header in
HTTP requests, so it's been blanked out.  If we can figure out what Quicken
sends for ``User_Agent``, it might be a good idea to spoof that as well.

What I'd really like to do is set up a packet sniffer on a PC running
Quicken and pull down a current list of working URLs.  If that sounds like
your idea of a fun time, drop me a line.

Using OFXClient in Another Program
==================================

To use within another program, first initialize an ``ofxtools.Client.OFXClient``
instance with the relevant connection parameters.

Using the configured ``OFXClient`` instance, make a request by calling the
relevant method, e.g. ``OFXClient.request_statements()``.  Provide the password
as the first positional argument; any remaining positional arguments are parsed
as requests.  Simple data containers for each statement type (``StmtRq``,
``CcStmtRq``, ``InvStmtRq``, ``StmtEndRq``, ``CcStmtEndRq`` are provided for 
this purpose.  Options follow as keyword arguments.

The method call therefore looks like this:

.. code-block:: python 

    >>> import datetime; import ofxtools
    >>> from ofxtools.Client import OFXClient, StmtRq, CcStmtEndRq
    >>> client = OFXClient("https://ofx.chase.com", userid="MoMoney",
    ...                    org="B1", fid="10898",
    ...                    version=220, prettyprint=True,
    ...                    bankid="111000614")
    >>> dtstart = datetime.datetime(2015, 1, 1, tzinfo=ofxtools.utils.UTC)
    >>> dtend = datetime.datetime(2015, 1, 31, tzinfo=ofxtools.utils.UTC)
    >>> s0 = StmtRq(acctid="1", accttype="CHECKING", dtstart=dtstart, dtend=dtend)
    >>> s1 = StmtRq(acctid="2", accttype="SAVINGS", dtstart=dtstart, dtend=dtend)
    >>> c0 = CcStmtEndRq(acctid="3", dtstart=dtstart, dtend=dtend)
    >>> response = client.request_statements("t0ps3kr1t", s0, s1, c0)


Other methods available:
    * ``OFXClient.request_profile()`` - PROFRQ
    * ``OFXClient.request_accounts()``- ACCTINFORQ
    * ``OFXClient.request_tax1099()``- TAX1099RQ (still a WIP)

.. _OFX Home: http://www.ofxhome.com/
.. _institution page on OFX Home: http://www.ofxhome.com/index.php/institution/view/424
.. _OFX Blog: https://ofxblog.wordpress.com/
.. _ABA routing number: http://routingnumber.aba.com/default1.aspx
.. _getfidata.sh: https://web.archive.org/web/20070120102800/http://www.jongsma.org/gc/bankinfo/getfidata.sh.gz
.. _GnuCash: https://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings
.. _python-keyring: https://pypi.org/project/keyring/
.. _dbus-python: https://pypi.org/project/dbus-python/
.. _UUID v4: https://en.wikipedia.org/wiki/Universally_unique_identifier#Version_4_(random)
