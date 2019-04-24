#!/usr/bin/env python
# coding: utf-8
"""
Network client that composes/transmits Open Financial Exchange (OFX) requests,
and receives OFX responses in reply.  A basic CLI utility is included.

To use, create an OFXClient instance configured with OFX connection parameters:
server URL, OFX protocol version, financial institution identifiers, client
identifiers, etc.

If you don't have these, try http://ofxhome.com/ .

Using the configured OFXClient instance, make a request by calling the
relevant method, e.g. `OFXClient.request_statements()`, passing
username/password as the first two positional arguments.  Any remaining
positional arguments are parsed as requests; simple data containers for each
statement (`StmtRq`, `CcStmtRq`, etc.) are provided for this purpose.
Options follow as keyword arguments.

For example:

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
"""
# stdlib imports
import datetime
import uuid
import xml.etree.ElementTree as ET
from collections import namedtuple, defaultdict, OrderedDict
from os import path
import getpass
from configparser import ConfigParser
import ssl
import urllib
from io import BytesIO
import itertools
from operator import attrgetter
import concurrent.futures
import json


# local imports
from ofxtools.header import make_header
from ofxtools.Types import DateTime
from ofxtools.models.ofx import OFX
from ofxtools.models import ACCTINFORQ, ACCTINFOTRNRQ
from ofxtools.models.profile import PROFRQ, PROFTRNRQ, PROFMSGSRQV1
from ofxtools.models.signon import SONRQ, FI, SIGNONMSGSRQV1
from ofxtools.models.signup import SIGNUPMSGSRQV1
from ofxtools.models.bank import (
    BANKACCTFROM,
    CCACCTFROM,
    INCTRAN,
    STMTRQ,
    STMTTRNRQ,
    CCSTMTRQ,
    CCSTMTTRNRQ,
    STMTENDRQ,
    STMTENDTRNRQ,
    CCSTMTENDRQ,
    CCSTMTENDTRNRQ,
    BANKMSGSRQV1,
    CREDITCARDMSGSRQV1,
)
from ofxtools.models.invest import (
    INVSTMTTRNRQ,
    INVSTMTRQ,
    INVACCTFROM,
    INCPOS,
    INVSTMTMSGSRQV1,
)
from ofxtools import utils
from ofxtools.utils import UTC
from ofxtools import ofxhome


# Statement request data containers
# Pass instances of these containers as args to OFXClient.request_statement()
StmtRq = namedtuple("StmtRq", ["acctid", "accttype", "dtstart", "dtend", "inctran"])
StmtRq.__new__.__defaults__ = (None, None, None, None, True)

CcStmtRq = namedtuple("CcStmtRq", ["acctid", "dtstart", "dtend", "inctran"])
CcStmtRq.__new__.__defaults__ = (None, None, None, True)

InvStmtRq = namedtuple(
    "InvStmtRq",
    ["acctid", "dtstart", "dtend", "dtasof", "inctran", "incoo", "incpos", "incbal"],
)
InvStmtRq.__new__.__defaults__ = (None, None, None, None, True, False, True, True)

# Pass instances of these containers as args to OFXClient.request_end_statement()
StmtEndRq = namedtuple("StmtEndRq", ["acctid", "accttype", "dtstart", "dtend"])
StmtEndRq.__new__.__defaults__ = (None, None, None, None, True)

CcStmtEndRq = namedtuple("CcStmtEndRq", ["acctid", "dtstart", "dtend"])
CcStmtEndRq.__new__.__defaults__ = (None, None, None, False)


class OFXClient:
    """
    Basic OFX client to download statement and profile requests.
    """

    # OFX header/signon defaults
    clientuid = None
    org = None
    fid = None
    version = 203
    appid = "QWIN"
    appver = "2700"
    language = "ENG"

    # Stmt request
    bankid = None
    brokerid = None

    def __init__(
        self,
        url,
        org=None,
        fid=None,
        version=None,
        appid=None,
        appver=None,
        language=None,
        bankid=None,
        brokerid=None):
        self.url = url
        self.org = org
        self.fid = fid
        if version is not None:
            self.version = int(version)
        self.appid = appid or self.appid
        if appver is not None:
            self.appver = str(appver)
        self.language = language or self.language
        self.bankid = bankid
        self.brokerid = brokerid

    @property
    def uuid(self):
        """ Returns a new UUID each time called """
        return str(uuid.uuid4())

    @property
    def http_headers(self):
        """ Pass to urllib.request.urlopen() """
        mimetype = "application/x-ofx"
        # Python libraries such as ``urllib.request`` and ``requests``
        # identify themselves in the ``User-Agent`` header,
        # which apparently displeases some FIs
        return {
            "User-Agent": "",
            "Content-type": mimetype,
            "Accept": "*/*, %s" % mimetype,
        }

    def dtclient(self):
        """
        Wrapper we can mock for testing purposes
        (as opposed to datetime.datetime, which is a C extension)
        """
        return datetime.datetime.now(UTC)

    def request_statements(
        self,
        user,
        password,
        *requests,
        language=None,
        clientuid=None,
        appid=None,
        appver=None,
        version=None,
        dryrun=False,
        prettyprint=False,
        close_elements=True,
        timeout=None):
        """
        Package and send OFX statement requests (STMTRQ/CCSTMTRQ/INVSTMTRQ).

        Input *requests are instances of the corresponding namedtuples
        (StmtRq, CcStmtRq, InvStmtRq)
        """
        msgs = {
            "bankmsgsrqv1": None,
            "creditcardmsgsrqv1": None,
            "invstmtmsgsrqv1": None,
        }

        sortkey = attrgetter("__class__.__name__")
        requests = sorted(requests, key=sortkey)
        for clsName, rqs in itertools.groupby(requests, key=sortkey):
            if clsName == "StmtRq":
                msgs["bankmsgsrqv1"] = BANKMSGSRQV1(
                    *[
                        self.stmttrnrq(**dict(rq._asdict(), bankid=self.bankid))
                        for rq in rqs
                    ]
                )
            elif clsName == "CcStmtRq":
                msgs["creditcardmsgsrqv1"] = CREDITCARDMSGSRQV1(
                    *[self.ccstmttrnrq(**rq._asdict()) for rq in rqs]
                )
            elif clsName == "InvStmtRq":
                msgs["invstmtmsgsrqv1"] = INVSTMTMSGSRQV1(
                    *[
                        self.invstmttrnrq(**dict(rq._asdict(), brokerid=self.brokerid))
                        for rq in rqs
                    ]
                )
            else:
                msg = "Not a *StmtRq: {}".format(clsName)
                raise ValueError(msg)

        signon = self.signon(user,
                             password,
                             language=language,
                             clientuid=clientuid,
                             appid=appid,
                             appver=appver)
        ofx = OFX(signonmsgsrqv1=signon, **msgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            timeout=timeout,
        )

    def request_end_statements(
        self,
        user,
        password,
        *requests,
        language=None,
        clientuid=None,
        appid=None,
        appver=None,
        version=None,
        dryrun=False,
        prettyprint=False,
        close_elements=True,
        timeout=None):
        """
        Package and send OFX end statement requests (STMTENDRQ, CCSTMTENDRQ).

        Input *requests are instances of the corresponding namedtuples
        (StmtEndRq, CcStmtEndRq)
        """
        msgs = {
            "bankmsgsrqv1": None,
            "creditcardmsgsrqv1": None,
            "invstmtmsgsrqv1": None,
        }

        sortkey = attrgetter("__class__.__name__")
        requests = sorted(requests, key=sortkey)
        for clsName, rqs in itertools.groupby(requests, key=sortkey):
            if clsName == "StmtEndRq":
                msgs["bankmsgsrqv1"] = BANKMSGSRQV1(
                    *[
                        self.stmtendtrnrq(**dict(rq._asdict(), bankid=self.bankid))
                        for rq in rqs
                    ]
                )
            elif clsName == "CcStmtEndRq":
                msgs["creditcardmsgsrqv1"] = CREDITCARDMSGSRQV1(
                    *[self.ccstmtendtrnrq(**rq._asdict()) for rq in rqs]
                )
            else:
                msg = "Not a *StmtEndRq: {}".format(clsName)
                raise ValueError(msg)

        signon = self.signon(user,
                             password,
                             language=language,
                             clientuid=clientuid,
                             appid=appid,
                             appver=appver)
        ofx = OFX(signonmsgsrqv1=signon, **msgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            timeout=timeout,
        )

    def request_profile(
        self,
        user=None,
        password=None,
        language=None,
        appid=None,
        appver=None,
        dryrun=False,
        version=None,
        prettyprint=False,
        close_elements=True,
        timeout=None):
        """
        Package and send OFX profile requests (PROFRQ).
        """

        dtprofup = datetime.datetime(1990, 1, 1, tzinfo=UTC)
        profrq = PROFRQ(clientrouting="NONE", dtprofup=dtprofup)
        trnuid = self.uuid
        proftrnrq = PROFTRNRQ(trnuid=trnuid, profrq=profrq)
        msgs = PROFMSGSRQV1(proftrnrq)

        user = user or "{:0<32}".format("anonymous")
        password = password or "{:0<32}".format("anonymous")
        signon = self.signon(user,
                             password,
                             language=language,
                             appid=appid,
                             appver=appver)

        ofx = OFX(signonmsgsrqv1=signon, profmsgsrqv1=msgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            timeout=timeout,
        )

    def request_accounts(
        self,
        user,
        password,
        dtacctup,
        language=None,
        clientuid=None,
        appid=None,
        appver=None,
        dryrun=False,
        version=None,
        prettyprint=False,
        close_elements=True,
        timeout=None):
        """
        Package and send OFX account info requests (ACCTINFORQ)
        """
        signon = self.signon(user,
                             password,
                             language=language,
                             clientuid=clientuid,
                             appid=appid,
                             appver=appver)

        acctinforq = ACCTINFORQ(dtacctup=dtacctup)
        acctinfotrnrq = ACCTINFOTRNRQ(trnuid=self.uuid, acctinforq=acctinforq)
        signupmsgs = SIGNUPMSGSRQV1(acctinfotrnrq)

        ofx = OFX(signonmsgsrqv1=signon, signupmsgsrqv1=signupmsgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            timeout=timeout,
        )

    def signon(self, userid, userpass, language=None, sesscookie=None,
               appid=None, appver=None, clientuid=None):
        """ Construct SONRQ; package in SIGNONMSGSRQV1 """
        if self.org:
            fi = FI(org=self.org, fid=self.fid)
        else:
            fi = None

        sonrq = SONRQ(
            dtclient=self.dtclient(),
            userid=userid,
            userpass=userpass,
            language=language or self.language,
            fi=fi,
            sesscookie=sesscookie,
            appid=appid or self.appid,
            appver=appver or self.appver,
            clientuid=clientuid,
        )
        return SIGNONMSGSRQV1(sonrq=sonrq)

    def stmttrnrq(
        self, bankid, acctid, accttype, dtstart=None, dtend=None, inctran=True
    ):
        """ Construct STMTRQ; package in STMTTRNRQ """
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran)
        trnuid = self.uuid
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def stmtendtrnrq(self, bankid, acctid, accttype, dtstart=None, dtend=None):
        """ Construct STMTENDRQ; package in STMTENDTRNRQ """
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        stmtrq = STMTENDRQ(bankacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return STMTENDTRNRQ(trnuid=trnuid, stmtendrq=stmtrq)

    def ccstmttrnrq(self, acctid, dtstart=None, dtend=None, inctran=True):
        """ Construct CCSTMTRQ; package in CCSTMTTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran)
        trnuid = self.uuid
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def ccstmtendtrnrq(self, acctid, dtstart=None, dtend=None):
        """ Construct CCSTMTENDRQ; package in CCSTMTENDTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        stmtrq = CCSTMTENDRQ(ccacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return CCSTMTENDTRNRQ(trnuid=trnuid, ccstmtendrq=stmtrq)

    def invstmttrnrq(
        self,
        acctid,
        brokerid,
        dtstart=None,
        dtend=None,
        inctran=True,
        incoo=False,
        dtasof=None,
        incpos=True,
        incbal=True,
    ):
        """ Construct INVSTMTRQ; package in INVSTMTTRNRQ """
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        if inctran:
            inctran = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        incpos = INCPOS(dtasof=dtasof, include=incpos)
        stmtrq = INVSTMTRQ(
            invacctfrom=acct, inctran=inctran, incoo=incoo, incpos=incpos, incbal=incbal
        )
        trnuid = self.uuid
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(self,
                 ofx,
                 dryrun=False,
                 version=None,
                 prettyprint=False,
                 close_elements=True,
                 verify_ssl=True,
                 timeout=None):
        """
        Package complete OFX tree and POST to server.

        Returns a file-like object that supports the file interface, and can
        therefore be passed drectly to ``OFXTree.parse()``.
        """
        request = self.serialize(ofx,
                                 version=version,
                                 prettyprint=prettyprint,
                                 close_elements=close_elements)

        if dryrun:
            return BytesIO(request)

        req = urllib.request.Request(
            self.url, method="POST", data=request, headers=self.http_headers
        )
        # By default, verify SSL certificate signatures
        # Cf. PEP 476
        # TESTME
        if verify_ssl is False:
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = ssl.create_default_context()
        response = urllib.request.urlopen(req, timeout=timeout,
                                          context=ssl_context)
        return response

    def serialize(self,
                  ofx,
                  version=None,
                  prettyprint=False,
                  close_elements=True):
        if version is None:
            version = self.version
        header = make_header(version=version, newfileuid=self.uuid)
        header = bytes(str(header), "utf_8")

        tree = ofx.to_etree()
        if prettyprint:
            utils.indent(tree)

        # Some servers choke on OFXv1 requests including ending tags for
        # elements (which are optional per the spec).
        if close_elements is False:
            if version >= 200:
                msg = "OFX version {} requires ending tags for elements"
                raise ValueError(msg.format(version))
            body = utils.tostring_unclosed_elements(tree)
        else:
            # ``method="html"`` skips the initial XML declaration
            body = ET.tostring(tree, encoding="utf_8", method="html")

        return header + body


### CLI COMMANDS
def init_client(args):
    """
    Initialize OFXClient with connection info from args
    """
    client = OFXClient(
        args.url,
        org=args.org,
        fid=args.fid,
        version=args.version,
        appid=args.appid,
        appver=args.appver,
        language=args.language,
        bankid=args.bankid,
        brokerid=args.brokerid,
    )
    return client


def do_stmt(args):
    """
    Construct OFX statement request from CLI/config args; send to server.
    """
    client = init_client(args)

    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(getattr(args, d)) for d in ("dtstart", "dtend", "dtasof")}

    # Define statement requests
    stmtrqs = []
    for accttype in ("checking", "savings", "moneymrkt", "creditline"):
        acctids = getattr(args, accttype, [])
        stmtrqs.extend(
            [
                StmtRq(
                    acctid=acctid,
                    accttype=accttype.upper(),
                    dtstart=dt["start"],
                    dtend=dt["end"],
                    inctran=args.inctran,
                )
                for acctid in acctids
            ]
        )

    for acctid in args.creditcard:
        stmtrqs.append(
            CcStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                inctran=args.inctran,
            )
        )

    for acctid in args.investment:
        stmtrqs.append(
            InvStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                dtasof=dt["asof"],
                inctran=args.inctran,
                incoo=args.incoo,
                incpos=args.incpos,
                incbal=args.incbal,
            )
        )

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    with client.request_statements(
        args.user,
        password,
        *stmtrqs,
        clientuid=args.clientuid,
        dryrun=args.dryrun,
        close_elements=not args.unclosedelements,
        prettyprint=args.pretty
    ) as f:
        response = f.read()

    print(response.decode())


def do_profile(args):
    """
    Construct OFX profile request from CLI/config args; send to server.
    """
    client = init_client(args)
    with client.request_profile(
        dryrun=args.dryrun,
        close_elements=not args.unclosedelements,
        prettyprint=args.pretty
    ) as f:
        response = f.read()

    print(response.decode())


def do_scan(args):
    """
    Report working connection parameters
    """
    results = scan_profile(args.url, args.org, args.fid)
    print(results)


def do_acctinfo(args):
    """
    Construct OFX account info request from CLI/config args; send to server.
    """
    client = init_client(args)

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(args.user,
                                 password,
                                 dtacctup,
                                 dryrun=args.dryrun,
                                 close_elements=not args.unclosedelements,
                                 prettyprint=args.pretty
                                ) as f:
        response = f.read()

    print(response.decode())


class OFXConfigParser(ConfigParser):
    """
    INI parser that loads default FI configs from oftools/config/fi.cfg and
    updates them from the user config file specified in its [global] section.

    It also provides a list of configured FIs (i.e. config sections except
    for [global]) for use by the CLI --help.
    """

    fi_config = path.join(path.dirname(__file__), "config", "fi.cfg")

    def __init__(self):
        ConfigParser.__init__(self)

    def read(self, filenames=None):
        # Load FI config
        with open(utils.fixpath(self.fi_config)) as fi_config:
            self.read_file(fi_config)
        # Then load user configs (defaults to fi.cfg [global] config: value)
        filenames = filenames or utils.fixpath(self.get("global", "config"))
        return ConfigParser.read(self, filenames)

    @property
    def fi_index(self):
        """ List of configured FIs """
        sections = self.sections()
        sections.remove("global")
        return sections


def make_argparser(fi_index):
    from argparse import ArgumentParser

    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index),
    )
    argparser.add_argument("server", help="OFX server - URL or FI name from config")
    argparser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        default=False,
        help="display OFX request and exit",
    )
    argparser.add_argument(
        "-p",
        "--profile",
        action="store_true",
        default=False,
        help="Download OFX profile instead of statement",
    )
    argparser.add_argument(
        "--scan",
        action="store_true",
        default=False,
        help="Scan for working OFX connection parameters",
    )
    argparser.add_argument(
        "--accts",
        action="store_true",
        default=False,
        help="Download account information instead of statement",
    )
    argparser.add_argument(
        "--unclosedelements",
        action="store_true",
        default=False,
        help="Omit end tags for elements (OFXv1 only)",
    )
    argparser.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Insert newlines and whitespace indentation",
    )

    signon_group = argparser.add_argument_group(title="Signon Options")
    signon_group.add_argument("-u", "--user", help="FI login username")
    signon_group.add_argument("--clientuid", help="OFX client UID")
    signon_group.add_argument("--org", help="FI.ORG")
    signon_group.add_argument("--fid", help="FI.FID")
    signon_group.add_argument("--bankid", help="ABA routing#")
    signon_group.add_argument("--brokerid", help="Broker ID string")
    signon_group.add_argument("--version", help="OFX version")
    signon_group.add_argument("--appid", help="OFX client app identifier")
    signon_group.add_argument("--appver", help="OFX client app version")
    signon_group.add_argument("--language", default="ENG", help="OFX language")

    acct_group = argparser.add_argument_group(title="Account Options")
    acct_group.add_argument(
        "-C", "--checking", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-S", "--savings", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-M", "--moneymrkt", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-L", "--creditline", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-c", "--creditcard", "--cc", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-i", "--investment", metavar="acct#", action="append", default=[]
    )

    stmt_group = argparser.add_argument_group(title="Statement Options")
    stmt_group.add_argument(
        "-s", "--start", dest="dtstart", help="(YYYYmmdd) Transactions list start date"
    )
    stmt_group.add_argument(
        "-e", "--end", dest="dtend", help="(YYYYmmdd) Transactions list end date"
    )
    stmt_group.add_argument(
        "-d",
        "--date",
        dest="dtasof",
        help="(YYYYmmdd) As-of date for investment positions",
    )
    stmt_group.add_argument(
        "--no-transactions",
        dest="inctran",
        action="store_false",
        default=True,
        help="Omit transactions list",
    )
    stmt_group.add_argument(
        "--no-positions",
        dest="incpos",
        action="store_false",
        default=True,
        help="Omit investment positions",
    )
    stmt_group.add_argument(
        "--no-balances",
        dest="incbal",
        action="store_false",
        default=True,
        help="Omit balances",
    )
    stmt_group.add_argument(
        "--open-orders",
        dest="incoo",
        action="store_true",
        default=False,
        help="Include open orders",
    )

    return argparser


def merge_config(config, args):
    """
    Merge default FI configs with user configs from oftools.cfg and CLI args
    """
    server = args.server
    if server not in config.fi_index:
        raise ValueError(
            "Unknown FI '{}' not in {}".format(server, str(config.fi_index))
        )
    # List of nonempty argparse args set from command line
    overrides = [k for k, v in vars(args).items() if v]
    for cfg, value in config.items(server, raw=True):
        # argparse settings override configparser settings
        if cfg in overrides:
            continue
        if cfg in (
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
        ):
            # Allow sequences of acct nos
            values = [v.strip() for v in value.split(",")]
            arg = getattr(args, cfg)
            assert isinstance(arg, list)
            arg.extend(values)
        else:
            # Coerce config to bool, if applicable
            arg = getattr(args, cfg, None)
            if type(arg) is bool:
                value = config.getboolean(server, cfg)
            setattr(args, cfg, value)

    # Fall back to OFX Home, if possible
    url = getattr(args, "url", None)
    if url is None and "ofxhome_id" in config[server]:
        lookup = ofxhome.lookup(config[server]["ofxhome_id"])
        args.url = lookup.url
        for cfg in "fid", "org", "brokerid":
            if getattr(args, cfg, None) is None:
                value = getattr(lookup, cfg)
                setattr(args, cfg, value)

    return args


def scan_profiles(start, stop, timeout=None):
    """
    Scan OFX Home's list of FIs for working connection configs.
    """
    results = {}

    institutions = ofxhome.list_institutions()
    for institution in institutions[start:stop]:
        ofxhome_id = int(institution.get("id"))
        lookup = ofxhome.lookup(ofxhome_id)
        if lookup is None or ofxhome.ofx_invalid(lookup) or ofxhome.ssl_invalid(lookup):
            continue
        working = scan_profile(url=lookup.url,
                               org=lookup.org,
                               fid=lookup.fid,
                               timeout=timeout)
        if working:
            results[ofxhome_id] = working

    return results


def scan_profile(url, org, fid, timeout=None):
    """
    Report permutations of OFX version/prettyprint/unclosed_elements that
    successfully download OFX profile from server.

    Returns a pair of (OFXv1 results, OFXv2 results), each type(dict).
    dict values provide ``ofxget`` configs that will work to connect.
    """
    if timeout is None:
        timeout = 5

    ofxv1 = [102, 103, 151, 160]
    ofxv2 = [200, 201, 202, 203, 210, 211, 220]

    futures = {}
    client = OFXClient(url, org, fid)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for prettyprint in (False, True):
            for close_elements in (False, True):
                futures.update({executor.submit(
                    client.request_profile,
                    version=version,
                    prettyprint=prettyprint,
                    close_elements=close_elements,
                    timeout=timeout):
                    (version, prettyprint, close_elements)
                    for version in ofxv1})

            futures.update({executor.submit(
                client.request_profile,
                version=version,
                prettyprint=prettyprint,
                close_elements=True,
                timeout=timeout):
                (version, prettyprint, True) for version in ofxv2})

    working = defaultdict(list)

    for future in concurrent.futures.as_completed(futures):
        try:
            response = future.result()
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                ConnectionError,
                OSError) as exc:
            cancelled = future.cancel()
            continue
        else:
            (version, prettyprint, close_elements) = futures[future]
            working[version].append((prettyprint, close_elements))

    def collate_results(results):
        results = list(results)
        if not results:
            return [], []
        versions, formats = zip(*results)

        # Assumption: the same formatting requirements apply to all
        # sub-versions (e.g. 1.0.2 and 1.0.3, or 2.0.3 and 2.2.0).
        # If a (pretty, close_elements) pair succeeds on most sub-versions
        # but fails on a few, we'll chalk it up to network transmission
        # errors and ignore it.
        #
        # Translation: just pick the longest sequence of successful
        # formats and assume it applies to the whole version.
        formats = max(formats, key=len)
        formats.sort()
        formats = [OrderedDict([("pretty", format[0]),
                               ("unclosed_elements", not format[1])])
                   for format in formats]
        return sorted(list(versions)), formats

    v2, v1 = utils.partition(lambda pair: pair[0] < 200, working.items())
    v1_versions, v1_formats = collate_results(v1)
    v2_versions, v2_formats = collate_results(v2)

    # V2 always has closing tags for elements; just report prettyprint
    for format in v2_formats:
        del format["unclosed_elements"]

    return json.dumps((OrderedDict([("versions", v1_versions),
                                    ("formats", v1_formats)]),
                       OrderedDict([("versions", v2_versions),
                                    ("formats", v2_formats)])))


def main():
    # Read config first, so fi_index can be used in help
    config = OFXConfigParser()
    config.read()

    argparser = make_argparser(config.fi_index)

    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urllib.parse.urlparse(server).scheme:
        args.url = server
    else:
        args = merge_config(config, args)

    # Pass the parsed args to the statement-request function
    if args.profile:
        do_profile(args)
    elif args.scan:
        do_scan(args)
    elif args.accts:
        do_acctinfo(args)
    else:
        do_stmt(args)


if __name__ == "__main__":
    main()
