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


__all__ = ["AUTH_PLACEHOLDER", "StmtRq", "CcStmtRq", "InvStmtRq", "StmtEndRq",
           "CcStmtEndRq", "OFXClient", "wrap_stmtrq"]


# stdlib imports
import datetime
import uuid
import xml.etree.ElementTree as ET
import ssl
import urllib.request as urllib_request
from http.client import HTTPResponse
import socket
from io import BytesIO
import itertools
from operator import attrgetter, itemgetter
from functools import singledispatch
from typing import Dict, Union, Optional, Tuple, Iterator, NamedTuple


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
from ofxtools.utils import classproperty, UTC
from ofxtools import utils


AUTH_PLACEHOLDER = "{:0<32}".format("anonymous")


# Statement request data containers
# Pass instances of these containers as args to OFXClient.request_statement()
class StmtRq(NamedTuple):
    """
    Parameters of a bank statement request
    """
    acctid: Optional[str] = None
    accttype: Optional[str] = None
    dtstart: Optional[datetime.datetime] = None
    dtend: Optional[datetime.datetime] = None
    inctran: Optional[bool] = True


class CcStmtRq(NamedTuple):
    """
    Parameters of a credit card statement request
    """
    acctid: Optional[str] = None
    dtstart: Optional[datetime.datetime] = None
    dtend: Optional[datetime.datetime] = None
    inctran: Optional[bool] = True


class InvStmtRq(NamedTuple):
    """
    Parameters of an investment account statement request
    """
    acctid: Optional[str] = None
    dtstart: Optional[datetime.datetime] = None
    dtend: Optional[datetime.datetime] = None
    dtasof: Optional[datetime.datetime] = None
    inctran: Optional[bool] = True
    incoo: Optional[bool] = False
    incpos: Optional[bool] = True
    incbal: Optional[bool] = True


class StmtEndRq(NamedTuple):
    """
    Parameters of a bank statement ending balance request
    """
    acctid: Optional[str] = None
    accttype: Optional[str] = None
    dtstart: Optional[datetime.datetime] = None
    dtend: Optional[datetime.datetime] = None


class CcStmtEndRq(NamedTuple):
    """
    Parameters of a credit card statement ending balance request
    """
    acctid: Optional[str] = None
    dtstart: Optional[datetime.datetime] = None
    dtend: Optional[datetime.datetime] = None


class OFXClient:
    """
    Basic OFX client to download statement and profile requests.
    """

    # OFX header/signon defaults
    userid: str = "{:0<32}".format("anonymous")
    clientuid: Optional[str] = None
    org: Optional[str] = None
    fid: Optional[str] = None
    version: int = 203
    appid: str = "QWIN"
    appver: str = "2700"
    language: str = "ENG"

    # Formatting defaults
    prettyprint: bool = False
    close_elements: bool = True

    # Stmt request
    bankid: Optional[str] = None
    brokerid: Optional[str] = None

    def __repr__(self) -> str:
        r = ("{cls}(url='{url}', userid='{userid}', clientuid='{clientuid}', "
             "org='{org}', fid='{fid}', version={version}, appid='{appid}', "
             "appver='{appver}', language='{language}', "
             "prettyprint='{prettyprint}', close_elements='{close_elements}', "
             "bankid='{bankid}', brokerid='{brokerid}')")
        attrs = dict(vars(self.__class__))
        attrs.update(vars(self))
        attrs["cls"] = self.__class__.__name__
        return r.format(**attrs)

    def __init__(self,
                 url: str,
                 userid: Optional[str] = None,
                 clientuid: Optional[str] = None,
                 org: Optional[str] = None,
                 fid: Optional[str] = None,
                 version: Optional[int] = None,
                 appid: Optional[str] = None,
                 appver: Optional[str] = None,
                 language: Optional[str] = None,
                 prettyprint: Optional[bool] = None,
                 close_elements: Optional[bool] = None,
                 bankid: Optional[str] = None,
                 brokerid: Optional[str] = None,
                 ):

        self.url = url

        for attr in ["userid", "clientuid", "org", "fid", "version", "appid",
                     "appver", "language", "prettyprint", "close_elements",
                     "bankid", "brokerid"]:
            value = locals()[attr]
            if value is not None:
                setattr(self, attr, value)

        if (not self.close_elements) and self.version >= 200:
            msg = "OFX version {} must close all tags"
            raise ValueError(msg.format(self.version))

    @classproperty
    @classmethod
    def uuid(cls) -> str:
        """ Returns a new UUID each time called """
        return str(uuid.uuid4())

    @property
    def http_headers(self) -> Dict[str, str]:
        """ Pass to urllib.request.urlopen() """
        mimetype = "application/x-ofx"
        # Python libraries such as ``urllib.request`` and ``requests``
        # identify themselves in the ``User-Agent`` header,
        # which apparently displeases some FIs
        return {
            "User-Agent": "",
            "Content-type": mimetype,
            "Accept": "*/*, {}".format(mimetype),
        }

    def dtclient(self) -> datetime.datetime:
        """
        Wrapper we can mock for testing purposes
        (as opposed to datetime.datetime, which is a C extension)
        """
        return datetime.datetime.now(UTC)

    def request_statements(self,
                           password: str,
                           *requests: Union[StmtRq, CcStmtRq, InvStmtRq,
                                            StmtEndRq, CcStmtEndRq],
                           dryrun: bool = False,
                           verify_ssl: bool = True,
                           timeout: Optional[float] = None,
                           ) -> Union[HTTPResponse, BytesIO]:
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
        requests_ = sorted(requests, key=attrgetter("__class__.__name__"))

        trnrqs = [wrap_stmtrq(cls(), rqs, self)
                  for cls, rqs in itertools.groupby(
                      requests_, key=attrgetter("__class__"))]

        # trnrqs is a pair of (models.*MSGSRQV1, [*TRNRQ])
        # Can't sort *MSGSRQV1 by class, either
        trnrqs.sort(key=lambda p: p[0].__name__)

        def _mkmsgs(msgcls: Union[BANKMSGSRQV1, CREDITCARDMSGSRQV1,
                                  INVSTMTMSGSRQV1],
                    trnrqs: Iterator[
                        Union[STMTTRNRQ, CCSTMTTRNRQ, INVSTMTTRNRQ,
                              STMTENDTRNRQ, CCSTMTENDTRNRQ]]
                    ) -> Tuple[str, Union[BANKMSGSRQV1, CREDITCARDMSGSRQV1,
                                          INVSTMTMSGSRQV1]]:
            """
            msgcls - one of (BANKMSGSRQV1, CREDITCARDMSGSRQV1, INVSTMTMSGSRQV1)
            trnrqs - sequence of sequences of (*STMTTRNRQ, *STMTENDTRNRQ)
            """
            trnrqs_ = list(itertools.chain.from_iterable(t[1] for t in trnrqs))
            attr_name = msgcls.__name__.lower()
            return (attr_name, msgcls(*trnrqs_))

        msgs = dict(_mkmsgs(msgcls, _trnrqs) for msgcls, _trnrqs
                    in itertools.groupby(trnrqs, key=itemgetter(0)))

        signon = self.signon(password)
        ofx = OFX(signonmsgsrqv1=signon, **msgs)
        return self.download(ofx, dryrun=dryrun, verify_ssl=verify_ssl,
                             timeout=timeout)

    def request_profile(self,
                        version: Optional[int] = None,
                        prettyprint: Optional[bool] = None,
                        close_elements: Optional[bool] = None,
                        dryrun: bool = False,
                        verify_ssl: bool = True,
                        timeout: Optional[float] = None,
                        ) -> Union[HTTPResponse, BytesIO]:
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

    def request_accounts(self,
                         password: str,
                         dtacctup: datetime.datetime,
                         dryrun: bool = False,
                         version: Optional[int] = None,
                         verify_ssl: bool = True,
                         timeout: Optional[float] = None,
                         ) -> Union[HTTPResponse, BytesIO]:
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

    def request_tax1099(self,
                        password: str,
                        *taxyears: str,
                        acctnum: str = None,
                        recid: str = None,
                        dryrun: bool = False,
                        verify_ssl: bool = True,
                        timeout: Optional[float] = None,
                        ) -> Union[HTTPResponse, BytesIO]:
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

    def signon(self,
               userpass: str,
               userid: Optional[str] = None,
               sesscookie: Optional[str] = None) -> SIGNONMSGSRQV1:
        """ Construct SONRQ; package in SIGNONMSGSRQV1 """
        if self.org:
            fi: Optional[FI] = FI(org=self.org, fid=self.fid)
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

    def stmttrnrq(self,
                  bankid: str,
                  acctid: str,
                  accttype: str,
                  dtstart: Optional[datetime.datetime] = None,
                  dtend: Optional[datetime.datetime] = None,
                  inctran: bool = True,
                  ) -> STMTTRNRQ:
        """ Construct STMTRQ; package in STMTTRNRQ """
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def stmtendtrnrq(self,
                     bankid: str,
                     acctid: str,
                     accttype: str,
                     dtstart: Optional[datetime.datetime] = None,
                     dtend: Optional[datetime.datetime] = None,
                     ) -> STMTENDTRNRQ:
        """ Construct STMTENDRQ; package in STMTENDTRNRQ """
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        stmtrq = STMTENDRQ(bankacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return STMTENDTRNRQ(trnuid=trnuid, stmtendrq=stmtrq)

    def ccstmttrnrq(self,
                    acctid: str,
                    dtstart: Optional[datetime.datetime] = None,
                    dtend: Optional[datetime.datetime] = None,
                    inctran: bool = True,
                    ) -> CCSTMTTRNRQ:
        """ Construct CCSTMTRQ; package in CCSTMTTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def ccstmtendtrnrq(self,
                       acctid: str,
                       dtstart: Optional[datetime.datetime] = None,
                       dtend: Optional[datetime.datetime] = None,
                       ) -> CCSTMTENDTRNRQ:
        """ Construct CCSTMTENDRQ; package in CCSTMTENDTRNRQ """
        acct = CCACCTFROM(acctid=acctid)
        stmtrq = CCSTMTENDRQ(ccacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return CCSTMTENDTRNRQ(trnuid=trnuid, ccstmtendrq=stmtrq)

    def invstmttrnrq(self,
                     acctid: str,
                     brokerid: str,
                     dtstart: Optional[datetime.datetime] = None,
                     dtend: Optional[datetime.datetime] = None,
                     inctran: bool = True,
                     incoo: bool = False,
                     dtasof: Optional[datetime.datetime] = None,
                     incpos: bool = True,
                     incbal: bool = True,
                     ) -> INVSTMTTRNRQ:
        """ Construct INVSTMTRQ; package in INVSTMTTRNRQ """
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        if inctran:
            inctran_: Optional[INCTRAN] = INCTRAN(dtstart=dtstart, dtend=dtend,
                                                  include=inctran)
        else:
            inctran_ = None
        incpos_ = INCPOS(dtasof=dtasof, include=incpos)
        stmtrq = INVSTMTRQ(invacctfrom=acct, inctran=inctran_,
                           incoo=incoo, incpos=incpos_, incbal=incbal)
        trnuid = self.uuid
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(self,
                 ofx: OFX,
                 version: Optional[int] = None,
                 prettyprint: Optional[bool] = None,
                 close_elements: Optional[bool] = None,
                 dryrun: bool = False,
                 verify_ssl: bool = True,
                 timeout: Optional[float] = None,
                 ) -> Union[HTTPResponse, BytesIO]:
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

        req = urllib_request.Request(
            self.url, method="POST", data=request, headers=self.http_headers
        )
        # By default, verify SSL certificate signatures
        # Cf. PEP 476
        # TESTME
        if verify_ssl is False:
            ssl_context = ssl._create_unverified_context()
        else:
            ssl_context = ssl.create_default_context()

        timeout = timeout or socket._GLOBAL_DEFAULT_TIMEOUT
        response = urllib_request.urlopen(req, timeout=timeout,
                                          context=ssl_context)
        return response  # type: ignore

    def serialize(self,
                  ofx: OFX,
                  version: Optional[int] = None,
                  prettyprint: Optional[bool] = None,
                  close_elements: Optional[bool] = None,
                  ) -> bytes:
        if version is None:
            version = self.version
        if prettyprint is None:
            prettyprint = self.prettyprint
        if close_elements is None:
            close_elements = self.close_elements
        header = bytes(str(make_header(version=version, newfileuid=self.uuid)),
                       "utf_8")

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
def wrap_stmtrq_stmtrq(nt, rqs, client):
    return (BANKMSGSRQV1,
            [client.stmttrnrq(**dict(rq._asdict(), bankid=client.bankid))
             for rq in rqs])


@wrap_stmtrq.register(CcStmtRq)
def wrap_stmtrq_ccstmtrq(nt, rqs, client):
    return (CREDITCARDMSGSRQV1,
            [client.ccstmttrnrq(**rq._asdict()) for rq in rqs])


@wrap_stmtrq.register(InvStmtRq)
def wrap_stmtrq_invstmtrq(nt, rqs, client):
    return (INVSTMTMSGSRQV1,
            [client.invstmttrnrq(**dict(r._asdict(), brokerid=client.brokerid))
             for r in rqs])


@wrap_stmtrq.register(StmtEndRq)
def wrap_stmtrq_stmtendrq(nt, rqs, client):
    return (BANKMSGSRQV1,
            [client.stmtendtrnrq(**dict(rq._asdict(), bankid=client.bankid))
             for rq in rqs])


@wrap_stmtrq.register(CcStmtEndRq)
def wrap_stmtrq_ccstmtendrq(nt, rqs, client):
    return (CREDITCARDMSGSRQV1,
            [client.ccstmtendtrnrq(**rq._asdict()) for rq in rqs])
