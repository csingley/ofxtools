# coding: utf-8
"""
Network client that composes/transmits Open Financial Exchange (OFX) requests,
and receives OFX responses in reply.  A basic CLI utility is included.

To use, create an OFXClient instance configured with OFX connection parameters:
server URL, OFX protocol version, financial institution identifiers, client
identifiers, etc.

If you don't have these, try http://ofxhome.com/ .


Using the configured ``OFXClient`` instance, make a request by calling the
relevant method, e.g. ``OFXClient.request_statements()``.  Provide the password
as the first positional argument; any remaining positional arguments are parsed
as requests.  Simple data containers for each statement (``StmtRq``,
``CcStmtRq``, etc.) are provided for this purpose.  Options follow as keyword
arguments.

For example:

>>> import datetime; import ofxtools
>>> from ofxtools import OFXClient, StmtRq, CcStmtEndRq
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
from operator import attrgetter, itemgetter
from functools import singledispatch


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
StmtRq = namedtuple("StmtRq", "acctid accttype dtstart dtend inctran")
StmtRq.__new__.__defaults__ = (None, None, None, None, True)

CcStmtRq = namedtuple("CcStmtRq", ["acctid", "dtstart", "dtend", "inctran"])
CcStmtRq.__new__.__defaults__ = (None, None, None, True)

InvStmtRq = namedtuple("InvStmtRq", ["acctid", "dtstart", "dtend", "dtasof",
                                     "inctran", "incoo", "incpos", "incbal"])
InvStmtRq.__new__.__defaults__ = (None, None, None, None, True, False, True, True)

StmtEndRq = namedtuple("StmtEndRq", ["acctid", "accttype", "dtstart", "dtend"])
StmtEndRq.__new__.__defaults__ = (None, None, None, None)

CcStmtEndRq = namedtuple("CcStmtEndRq", ["acctid", "dtstart", "dtend"])
CcStmtEndRq.__new__.__defaults__ =  (None, None, None, )


class OFXClient:
    """
    Basic OFX client to download statement and profile requests.
    """

    # OFX header/signon defaults
    userid = "{:0<32}".format("anonymous")
    clientuid = None
    org = None
    fid = None
    version = 203
    appid = "QWIN"
    appver = "2700"
    language = "ENG"

    # Formatting defaults
    prettyprint = False
    close_elements = True

    # Stmt request
    bankid = None
    brokerid = None

    def __repr__(self):
        r = ("{cls}(url='{url}', userid='{userid}', clientuid='{clientuid}', "
             "org='{org}', fid='{fid}', version={version}, appid='{appid}', "
             "appver='{appver}', language='{language}', "
             "prettyprint='{prettyprint}', close_elements='{close_elements}', "
             "bankid='{bankid}', brokerid='{brokerid}')")
        attrs = dict(vars(self.__class__))
        attrs.update(vars(self))
        attrs["cls"] = self.__class__.__name__
        return r.format(**attrs)

    def __init__(
        self,
        url,
        userid=None,
        clientuid=None,
        org=None,
        fid=None,
        version=None,
        appid=None,
        appver=None,
        language=None,
        prettyprint=None,
        close_elements=None,
        bankid=None,
        brokerid=None):

        self.url = url

        # Signon
        if userid is not None:
            self.userid = userid
        self.clientuid = clientuid
        self.org = org
        self.fid = fid
        if version is not None:
            self.version = int(version)
        if appid is not None:
            self.appid = appid
        if appver is not None:
            self.appver = str(appver)
        if language is not None:
            self.language = language

        # Formatting
        if prettyprint is not None:
            if type(prettyprint) is not bool:
                msg = "'prettyprint' must be type(bool), not '{}'"
                raise ValueError(msg.format(prettyprint))
            self.prettyprint = prettyprint
        if close_elements is not None:
            if type(close_elements) is not bool:
                msg = "'close_elements' must be type(bool), not '{}'"
                raise ValueError(msg.format(close_elements))
            if (not close_elements) and self.version >= 200:
                msg = "OFX version {} must close all tags"
                raise ValueError(msg.format(self.version))
            self.close_elements = close_elements

        # Statements
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

    def request_statements(self, password, *requests,
                           dryrun=False, verify_ssl=True, timeout=None):
        """
        Package and send OFX statement requests
        (STMTRQ/CCSTMTRQ/INVSTMTRQ/STMTENDRQ/CCSTMTENDRQ).

        Input *requests are instances of the corresponding namedtuples
        (StmtRq, CcStmtRq, InvStmtRq, StmtEndRq, CcStmtEndRq)
        """
        # Our input requests are (potentially mixed) *STMTRQ/*STMTENDRQ
        # namedtuples.  They must be grouped by type and passed to the
        # appropriate *TRNRQ hander function (see singledispatch setup below).

        # *StmtRq/*StmtEndRqs (namedtuples) don't have rich comparison methods;
        # can't sort by class
        requests = sorted(requests, key=attrgetter("__class__.__name__"))

        trnrqs = [wrap_stmtrq(cls(), rqs, self)
                  for cls, rqs in itertools.groupby(
                      requests, key=attrgetter("__class__"))]

        # trnrqs is a pair of (models.*MSGSRQV1, [*TRNRQ])
        # Can't sort *MSGSRQV1 by class, either
        trnrqs.sort(key=lambda p: p[0].__name__)

        def _mkmsgs(msgcls, trnrqs):
            """
            msgcls - one of (BANKMSGSRQV1, CREDITCARDMSGSRQV1, INVSTMTMSGSRQV1)
            trnrqs - sequence of sequences of (*STMTTRNRQ, *STMTENDTRNRQ)
            """
            trnrqs = list(itertools.chain.from_iterable(t[1] for t in trnrqs))
            attr_name = msgcls.__name__.lower()
            return (attr_name, msgcls(*trnrqs))

        msgs = dict(_mkmsgs(msgcls, _trnrqs) for msgcls, _trnrqs
                    in itertools.groupby(trnrqs, key=itemgetter(0)))

        signon = self.signon(password)
        ofx = OFX(signonmsgsrqv1=signon, **msgs)
        return self.download(ofx, dryrun=dryrun, verify_ssl=verify_ssl,
                             timeout=timeout)

    def request_profile(
        self,
        version=None,
        prettyprint=None,
        close_elements=None,
        dryrun=False,
        verify_ssl=True,
        timeout=None):
        """
        Package and send OFX profile requests (PROFRQ).

        ofxget.scan_profile() overrides version/prettyprint/close_elements.
        """

        dtprofup = datetime.datetime(1990, 1, 1, tzinfo=UTC)
        profrq = PROFRQ(clientrouting="NONE", dtprofup=dtprofup)
        proftrnrq = PROFTRNRQ(trnuid=self.uuid, profrq=profrq)

        user = password = "{:0<32}".format("anonymous")
        signon = self.signon(password, userid=user)

        ofx = OFX(signonmsgsrqv1=signon, profmsgsrqv1=PROFMSGSRQV1(proftrnrq))

        return self.download(
            ofx,
            version=version,
            prettyprint=prettyprint,
            close_elements=close_elements,
            dryrun=dryrun,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

    def request_accounts(
        self,
        password,
        dtacctup,
        dryrun=False,
        version=None,
        verify_ssl=True,
        timeout=None):
        """
        Package and send OFX account info requests (ACCTINFORQ)
        """
        signon = self.signon(password)

        acctinforq = ACCTINFORQ(dtacctup=dtacctup)
        acctinfotrnrq = ACCTINFOTRNRQ(trnuid=self.uuid, acctinforq=acctinforq)
        signupmsgs = SIGNUPMSGSRQV1(acctinfotrnrq)

        ofx = OFX(signonmsgsrqv1=signon, signupmsgsrqv1=signupmsgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

    def request_tax1099(
        self,
        password,
        *taxyears,
        acctnum=None,
        recid=None,
        dryrun=False,
        verify_ssl=True,
        timeout=None):
        """
        Request US federal income tax form 1099 (TAX1099RQ)
        """
        signon = self.signon(password)

        rq = TAX1099RQ(*taxyears, recid=recid or None)
        msgs = TAX1099MSGSRQV1(
            TAX1099TRNRQ(trnuid=self.uuid, tax1099rq=rq))

        ofx = OFX(signonmsgsrqv1=signon, tax1099msgsrqv1=msgs)
        return self.download(
            ofx,
            dryrun=dryrun,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

    def signon(self, userpass, userid=None, sesscookie=None):
        """ Construct SONRQ; package in SIGNONMSGSRQV1 """
        if self.org:
            fi = FI(org=self.org, fid=self.fid)
        else:
            fi = None

        if userid is None:
            userid = self.userid

        sonrq = SONRQ(
            dtclient=self.dtclient(),
            userid=userid,
            userpass=userpass,
            language=self.language,
            fi=fi,
            sesscookie=sesscookie,
            appid=self.appid,
            appver=self.appver,
            clientuid=self.clientuid,
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
                 version=None,
                 prettyprint=None,
                 close_elements=None,
                 dryrun=False,
                 verify_ssl=True,
                 timeout=None):
        """
        Package complete OFX tree and POST to server.

        Returns a file-like object that supports the file interface, and can
        therefore be passed drectly to ``OFXTree.parse()``.

        ofxget.scan_profile() overrides version/prettyprint/close_elements.
        """
        request = self.serialize(ofx, version=version, prettyprint=prettyprint,
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

    def serialize(self, ofx, version=None, prettyprint=None,
                  close_elements=None):
        if version is None:
            version = self.version
        if prettyprint is None:
            prettyprint = self.prettyprint
        if close_elements is None:
            close_elements = self.close_elements
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


@singledispatch
def wrap_stmtrq(nt, rqs, client):
    msg = "Not a *StmtRq/*StmtEndRq: {}".format(nt.__class__.__name__)
    raise ValueError(msg)


@wrap_stmtrq.register(StmtRq)
def _(nt, rqs, client):
    return (BANKMSGSRQV1,
            [client.stmttrnrq(**dict(rq._asdict(), bankid=client.bankid))
             for rq in rqs])


@wrap_stmtrq.register(CcStmtRq)
def _(nt, rqs, client):
    return (CREDITCARDMSGSRQV1,
            [client.ccstmttrnrq(**rq._asdict()) for rq in rqs])


@wrap_stmtrq.register(InvStmtRq)
def _(nt, rqs, client):
    return (INVSTMTMSGSRQV1,
            [client.invstmttrnrq(**dict(r._asdict(), brokerid=client.brokerid))
             for r in rqs])


@wrap_stmtrq.register(StmtEndRq)
def _(nt, rqs, client):
    return (BANKMSGSRQV1,
            [client.stmtendtrnrq(**dict(rq._asdict(), bankid=client.bankid))
             for rq in rqs])


@wrap_stmtrq.register(CcStmtEndRq)
def _(nt, rqs, client):
    return (CREDITCARDMSGSRQV1,
            [client.ccstmtendtrnrq(**rq._asdict()) for rq in rqs])
