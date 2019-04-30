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
from collections import namedtuple
import ssl
import urllib
from io import BytesIO
import itertools
from operator import attrgetter


# local imports
from ofxtools.header import make_header
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
from ofxtools.models.tax1099 import (
    TAX1099RQ,
    TAX1099TRNRQ,
    TAX1099MSGSRQV1,
)
from ofxtools.utils import UTC
from ofxtools import utils


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
        verify_ssl=True,
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
            verify_ssl=verify_ssl,
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
        verify_ssl=True,
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
            verify_ssl=verify_ssl,
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
        verify_ssl=True,
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
            verify_ssl=verify_ssl,
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
        verify_ssl=True,
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
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

    def request_tax1099(
        self,
        user,
        password,
        *taxyears,
        acctnum=None,
        recid=None,
        language=None,
        clientuid=None,
        appid=None,
        appver=None,
        dryrun=False,
        version=None,
        prettyprint=False,
        close_elements=True,
        verify_ssl=True,
        timeout=None):
        """
        Request US federal income tax form 1099 (TAX1099RQ)
        """
        signon = self.signon(user,
                             password,
                             language=language,
                             clientuid=clientuid,
                             appid=appid,
                             appver=appver)

        rq = TAX1099RQ(*taxyears, recid=recid or None)
        msgs = TAX1099MSGSRQV1(
            TAX1099TRNRQ(trnuid=self.uuid, tax1099rq=rq))

        ofx = OFX(signonmsgsrqv1=signon, tax1099msgsrqv1=msgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            verify_ssl=verify_ssl,
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
