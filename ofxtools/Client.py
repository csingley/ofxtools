"""
Network client that composes/transmits Open Financial Exchange (OFX) requests,
and receives OFX responses in reply.  A basic CLI utility is included.

To use, create an OFXClient instance configured with OFX connection parameters:
server URL, OFX protocol version, financial institution identifiers, client
identifiers, etc.

``config/fi.cfg`` contains a database of these parameters, most conveniently
accessed via ``scripts/ofxget.py``.

Using the configured ``OFXClient`` instance, make a request by calling the
relevant method, e.g. ``OFXClient.request_statements()``.  Provide the password
as the first positional argument; any remaining positional arguments are parsed
as requests.  Simple data containers for each statement (``StmtRq``,
``CcStmtRq``, etc.) are provided for this purpose.  Options follow as keyword
arguments.

For example:

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
"""

from __future__ import annotations

__all__ = [
    "AUTH_PLACEHOLDER",
    "StmtRq",
    "CcStmtRq",
    "InvStmtRq",
    "StmtEndRq",
    "CcStmtEndRq",
    "OFXClient",
    "wrap_stmtrq",
]


# stdlib imports
import datetime
import http.cookiejar
import itertools
import logging
import urllib.request as urllib_request
import uuid
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from io import BytesIO
from operator import attrgetter, itemgetter
from typing import (
    Any,
    BinaryIO,
    NamedTuple,
)

# 3rd party libs
try:
    import requests

    USE_REQUESTS = True
except ImportError:
    USE_REQUESTS = False


# local imports
from ofxtools import config, utils
from ofxtools.header import make_header
from ofxtools.models import ACCTINFORQ, ACCTINFOTRNRQ
from ofxtools.models.bank import (
    BANKACCTFROM,
    BANKMSGSET,
    BANKMSGSRQV1,
    CCACCTFROM,
    CCSTMTENDRQ,
    CCSTMTENDTRNRQ,
    CCSTMTRQ,
    CCSTMTTRNRQ,
    CREDITCARDMSGSET,
    CREDITCARDMSGSRQV1,
    INCTRAN,
    INTERXFERMSGSET,
    STMTENDRQ,
    STMTENDTRNRQ,
    STMTRQ,
    STMTTRNRQ,
    WIREXFERMSGSET,
)
from ofxtools.models.billpay.msgsets import BILLPAYMSGSET
from ofxtools.models.email import EMAILMSGSET
from ofxtools.models.invest import (
    INCPOS,
    INVACCTFROM,
    INVSTMTMSGSET,
    INVSTMTMSGSRQV1,
    INVSTMTRQ,
    INVSTMTTRNRQ,
    SECLISTMSGSET,
)
from ofxtools.models.ofx import OFX
from ofxtools.models.profile import PROFMSGSET, PROFMSGSRQV1, PROFRQ, PROFTRNRQ
from ofxtools.models.signon import FI, SIGNONMSGSET, SIGNONMSGSRQV1, SONRQ
from ofxtools.models.signup import SIGNUPMSGSET, SIGNUPMSGSRQV1
from ofxtools.models.tax1099 import (
    TAX1099MSGSET,
    TAX1099MSGSRQV1,
    TAX1099RQ,
    TAX1099TRNRQ,
)
from ofxtools.Parser import OFXTree
from ofxtools.utils import UTC

AUTH_PLACEHOLDER = f"{'anonymous':0<32}"


logger = logging.getLogger(__name__)


# Statement request data containers
# Pass instances of these containers as args to OFXClient.request_statement()
class StmtRq(NamedTuple):
    """
    Parameters of a bank statement request
    """

    acctid: str | None = None
    accttype: str | None = None
    dtstart: datetime.datetime | None = None
    dtend: datetime.datetime | None = None
    inctran: bool | None = True


class CcStmtRq(NamedTuple):
    """
    Parameters of a credit card statement request
    """

    acctid: str | None = None
    dtstart: datetime.datetime | None = None
    dtend: datetime.datetime | None = None
    inctran: bool | None = True


class InvStmtRq(NamedTuple):
    """
    Parameters of an investment account statement request
    """

    acctid: str | None = None
    dtstart: datetime.datetime | None = None
    dtend: datetime.datetime | None = None
    dtasof: datetime.datetime | None = None
    inctran: bool | None = True
    incoo: bool | None = False
    incpos: bool | None = True
    incbal: bool | None = True


class StmtEndRq(NamedTuple):
    """
    Parameters of a bank statement ending balance request
    """

    acctid: str | None = None
    accttype: str | None = None
    dtstart: datetime.datetime | None = None
    dtend: datetime.datetime | None = None


class CcStmtEndRq(NamedTuple):
    """
    Parameters of a credit card statement ending balance request
    """

    acctid: str | None = None
    dtstart: datetime.datetime | None = None
    dtend: datetime.datetime | None = None


# TYPE ALIASES
RequestParam = StmtRq | CcStmtRq | InvStmtRq | StmtEndRq | CcStmtEndRq
Request = STMTRQ | CCSTMTRQ | INVSTMTRQ | STMTENDRQ | CCSTMTENDRQ
TrnRequest = STMTTRNRQ | CCSTMTTRNRQ | INVSTMTTRNRQ | STMTENDTRNRQ | CCSTMTENDTRNRQ
Message = BANKMSGSRQV1 | CREDITCARDMSGSRQV1 | INVSTMTMSGSRQV1
MsgsetClass = (
    type[SIGNONMSGSET]
    | type[SIGNUPMSGSET]
    | type[BANKMSGSET]
    | type[CREDITCARDMSGSET]
    | type[INVSTMTMSGSET]
    | type[INTERXFERMSGSET]
    | type[WIREXFERMSGSET]
    | type[BILLPAYMSGSET]
    | type[EMAILMSGSET]
    | type[SECLISTMSGSET]
    | type[PROFMSGSET]
    | type[TAX1099MSGSET]
)


class OFXClient:
    """
    OFX client that composes, transmits, and receives OFX messages.

    Configure an instance with the server URL and financial-institution
    parameters (``org``, ``fid``, ``version``, etc.), then call request
    methods such as ``request_statements()`` or ``request_profile()`` to
    retrieve data.  Each request method returns a file-like object containing
    the raw OFX response, which can be passed directly to ``OFXTree.parse()``.

    Statement requests are described by lightweight named-tuple containers:
    ``StmtRq``, ``CcStmtRq``, ``InvStmtRq``, ``StmtEndRq``, ``CcStmtEndRq``.

    Example::

        from ofxtools.Client import OFXClient, StmtRq
        import ofxtools.utils

        client = OFXClient(
            "https://ofx.example.com",
            userid="jsmith",
            org="MYBANK",
            fid="12345",
            version=220,
            bankid="111000614",
        )
        import datetime
        dtstart = datetime.datetime(2024, 1, 1, tzinfo=ofxtools.utils.UTC)
        rq = StmtRq(acctid="123456789", accttype="CHECKING", dtstart=dtstart)
        response = client.request_statements("s3cr3t", rq)
    """

    # OFX header/signon defaults
    userid: str = AUTH_PLACEHOLDER
    clientuid: str | None = None
    org: str | None = None
    fid: str | None = None
    version: int = 203
    appid: str = "QWIN"
    appver: str = "2700"
    language: str = "ENG"
    useragent: str = "InetClntApp/3.0"

    # Formatting defaults
    prettyprint: bool = False
    close_elements: bool = True

    # Stmt request
    bankid: str | None = None
    brokerid: str | None = None
    persist_cookies: bool = True

    def __repr__(self) -> str:
        r = (
            "{cls}(url={url!r}, userid={userid!r}, clientuid={clientuid!r}, "
            "org={org!r}, fid={fid!r}, version={version}, appid={appid!r}, "
            "appver={appver!r}, language={language!r}, prettyprint={prettyprint}, "
            "close_elements={close_elements}, bankid={bankid!r}, brokerid={brokerid!r})"
        )
        attrs = dict(vars(self.__class__))
        attrs.update(vars(self))
        attrs["cls"] = self.__class__.__name__
        return r.format(**attrs)

    def __init__(
        self,
        url: str,
        userid: str | None = None,
        clientuid: str | None = None,
        org: str | None = None,
        fid: str | None = None,
        version: int | None = None,
        appid: str | None = None,
        appver: str | None = None,
        language: str | None = None,
        prettyprint: bool | None = None,
        close_elements: bool | None = None,
        bankid: str | None = None,
        brokerid: str | None = None,
        useragent: str | None = None,
        persist_cookies: bool | None = None,
    ):
        self.url = url

        for attr in [
            "userid",
            "clientuid",
            "org",
            "fid",
            "version",
            "appid",
            "appver",
            "language",
            "prettyprint",
            "close_elements",
            "bankid",
            "brokerid",
            "useragent",
            "persist_cookies",
        ]:
            value = locals()[attr]
            if value is not None:
                setattr(self, attr, value)

        if (not self.close_elements) and self.version >= 200:
            raise ValueError(f"OFX version {self.version} must close all tags")

        # Allow persistent cookies in case PROFRS sets cookies that are needed by
        # subsequent STMTRQ or what have you.
        self.cookiejar = http.cookiejar.CookieJar()

    @classmethod
    def uuid(cls) -> str:
        """Return a new UUID each time called. Wrapper we can mock for testing."""
        return str(uuid.uuid4()).upper()

    @property
    def http_headers(self) -> dict[str, str]:
        """Pass to urllib.request.urlopen()"""
        mimetype = "application/x-ofx"
        # Python libraries such as ``urllib.request`` and ``requests``
        # identify themselves in the ``User-Agent`` header,
        # which apparently displeases some FIs
        return {
            "User-Agent": self.useragent,
            "Content-Type": mimetype,
            # Apparently Amex is unhappy unless it sees a MIME type of application/xml
            # with some quality rating - ANY quality rating, it seems.
            "Accept": f"*/*, {mimetype}, application/xml;q=0.9",
        }

    def dtclient(self) -> datetime.datetime:
        """
        Wrapper we can mock for testing.
        (as opposed to datetime.datetime, which is a C extension)
        """
        return datetime.datetime.now(UTC)

    def _url_from_profile(
        self,
        dryrun: bool,
        skip_profile: bool,
        timeout: float | None,
        gen_newfileuid: bool,
    ) -> str:
        if dryrun:
            return ""
        if skip_profile:
            return self.url
        RqCls2url = self._get_service_urls(
            timeout=timeout, gen_newfileuid=gen_newfileuid
        )
        urls = set(RqCls2url.values())
        if len(urls) != 1:
            raise ValueError(f"Expected 1 service URL, got {len(urls)}: {urls}")
        return str(urls.pop())

    def request_statements(
        self,
        password: str,
        *requests: RequestParam,
        gen_newfileuid: bool = True,
        dryrun: bool = False,
        timeout: float | None = None,
        skip_profile: bool = False,
    ) -> BinaryIO:
        """
        Package and send OFX statement requests
        (STMTRQ/CCSTMTRQ/INVSTMTRQ/STMTENDRQ/CCSTMTENDRQ).
        """
        url = self._url_from_profile(dryrun, skip_profile, timeout, gen_newfileuid)
        if url:
            logger.info(f"Service url={url}")

        logger.info(f"Creating statement requests for {requests}")
        # Group requests by type and pass to the appropriate *TRNRQ handler
        # function (see singledispatch setup below).
        #
        # Classes don't have rich comparison methods, so we can't sort by class.
        # As a proxy, we sort by class name, even though we actually group by class
        # so we can use it when iterating over groupby().
        sortKey = attrgetter("__class__.__name__")
        groupKey = attrgetter("__class__")
        trnrqs = [
            wrap_stmtrq(cls(), rqs, self)
            for cls, rqs in itertools.groupby(
                sorted(requests, key=sortKey), key=groupKey
            )
        ]

        # trnrqs is a pair of (models.*MSGSRQV1, [*TRNRQ])
        # Can't sort *MSGSRQV1 by class, either, so we use the same trick
        # of sorting by class name and grouping by class.
        def trnSortKey(pair: Any) -> Any:
            return pair[0].__name__

        trnGroupKey = itemgetter(0)
        trnrqs.sort(key=trnSortKey)

        # N.B. we need to annotate first arg as typing.Type here to indicate that
        # we're passing in a class not an instance.
        def msg_args(
            msgcls: type[BANKMSGSRQV1]
            | type[CREDITCARDMSGSRQV1]
            | type[INVSTMTMSGSRQV1],
            trnrqs: Iterator[tuple[type[Message], list[TrnRequest]]],
        ) -> tuple[str, Message]:
            trnrqs_ = list(itertools.chain.from_iterable(t[1] for t in trnrqs))
            attr_name = msgcls.__name__.lower()
            return (attr_name, msgcls(*trnrqs_))

        msgs = dict(
            msg_args(msgcls, _trnrqs)
            for msgcls, _trnrqs in itertools.groupby(trnrqs, key=trnGroupKey)
        )
        logger.debug(f"Wrapped statement request messages: {msgs}")

        signon = self.signon(password)
        ofx = OFX(signonmsgsrqv1=signon, **msgs)

        newfileuid = self.uuid() if gen_newfileuid else None

        return self.download(
            ofx,
            newfileuid=newfileuid,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

    def _get_service_urls(
        self,
        timeout: float | None = None,
        gen_newfileuid: bool = True,
    ) -> dict[Any, Any]:
        """Query OFX profile endpoint to construct mapping of statement request
        data container to URL providing that service.
        """
        profile = self.request_profile(
            gen_newfileuid=gen_newfileuid,
            timeout=timeout,
        )
        parser = OFXTree()
        parser.parse(profile)
        ofx = parser.convert()
        proftrnrs = ofx.profmsgsrsv1[0]
        msgsetlist = proftrnrs.msgsetlist  # proxy access to SubAggregate attributes
        classmap = {
            BANKMSGSET: StmtRq,
            CREDITCARDMSGSET: CcStmtRq,
            INVSTMTMSGSET: InvStmtRq,
        }
        urls = {
            RqCls: msgset.url  # proxy access to SubAggregate attributes
            for msgset in msgsetlist
            if (RqCls := classmap.get(type(msgset), None)) is not None
        }

        # Also map *STMTENDRQ
        def map_stmtendrq_urls(
            msgsetCls: MsgsetClass,
            stmtendrqCls: type[StmtEndRq] | type[CcStmtEndRq],
        ) -> None:
            try:
                index = [type(msgset) for msgset in msgsetlist].index(msgsetCls)
            except ValueError:
                pass
            else:
                msgset = msgsetlist[index]
                if msgset.closingavail:  # proxy access to SubAggregate attributes
                    urls[stmtendrqCls] = msgset.url  # proxy access to SubAgg attributes

        map_stmtendrq_urls(BANKMSGSET, StmtEndRq)
        map_stmtendrq_urls(CREDITCARDMSGSET, CcStmtEndRq)

        return urls

    def request_profile(
        self,
        version: int | None = None,
        gen_newfileuid: bool = True,
        prettyprint: bool | None = None,
        close_elements: bool | None = None,
        dryrun: bool = False,
        timeout: float | None = None,
        url: str | None = None,
        persist: bool = True,
    ) -> BinaryIO:
        """Request/cache OFX profiles (PROFRS).

        ofxget.scan_profile() overrides version/prettyprint/close_elements.
        """
        filename = f"{self.org}-{self.fid}.profrs"
        persistdir = config.DATADIR / "fiprofiles"
        persistpath = persistdir / filename

        if persistpath.exists():
            with open(persistpath, "rb") as f:
                profrs: BytesIO | None = BytesIO(f.read())

            parser = OFXTree()
            parser.parse(profrs)
            ofx = parser.convert()
            proftrnrs = ofx.profmsgsrsv1[0]
            dtprofup = proftrnrs.profrs.dtprofup
        else:
            persistdir.mkdir(parents=True, exist_ok=True)
            profrs = None
            dtprofup = None

        response = self._request_profile(
            dtprofup=dtprofup,
            version=version,
            gen_newfileuid=gen_newfileuid,
            prettyprint=prettyprint,
            close_elements=close_elements,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

        if dryrun:
            return response

        parser = OFXTree()
        parser.parse(response)
        ofx = parser.convert()

        #  If the client has the latest version of the FIs profile, the server returns
        #  status code 1 in the <STATUS> aggregate of the profile-transaction aggregate
        #  <PROFTRNRS>. The server does not return a profile- response aggregate <PROFRS>.

        #  If the client does not have the latest version of the FI profile, the server
        #  responds with the profile-response aggregate <PROFRS> in the profile-transaction
        #  aggregate <PROFTRNRS>.
        proftrnrs = ofx.profmsgsrsv1[0]
        if proftrnrs.status.code == 1:
            if profrs is None:
                raise ValueError("Profile response required but not provided")
            response = profrs
        else:
            if proftrnrs.status.code != 0:
                raise ValueError(
                    f"Profile response status code {proftrnrs.status.code}"
                )
            dtprofup_server = proftrnrs.profrs.dtprofup
            if dtprofup is not None and dtprofup > dtprofup_server:
                raise ValueError(
                    f"Profile update date {dtprofup} is newer than server's {dtprofup_server}"
                )

            # Cache the updated PROFRS sent by the server
            response.seek(0)
            with open(persistpath, "wb") as f:
                f.write(response.read())

        # Rewind PROFRS so it can be returned cleanly after having been parsed.
        response.seek(0)

        return response

    def _request_profile(
        self,
        dtprofup: datetime.datetime | None = None,
        version: int | None = None,
        gen_newfileuid: bool = True,
        prettyprint: bool | None = None,
        close_elements: bool | None = None,
        dryrun: bool = False,
        timeout: float | None = None,
        url: str | None = None,
    ) -> BytesIO:
        """Package and send OFX profile requests (PROFRQ)."""
        logger.info("Creating profile request")

        if dtprofup is None:
            dtprofup = datetime.datetime(1990, 1, 1, tzinfo=UTC)
        profrq = PROFRQ(clientrouting="NONE", dtprofup=dtprofup)
        proftrnrq = PROFTRNRQ(trnuid=self.uuid(), profrq=profrq)

        logger.debug(f"Wrapped profile request: {proftrnrq}")

        user = password = AUTH_PLACEHOLDER
        signon = self.signon(password, userid=user)

        ofx = OFX(signonmsgsrqv1=signon, profmsgsrqv1=PROFMSGSRQV1(proftrnrq))

        newfileuid = self.uuid() if gen_newfileuid else None

        return self.download(
            ofx,
            version=version,
            newfileuid=newfileuid,
            prettyprint=prettyprint,
            close_elements=close_elements,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

    def request_accounts(
        self,
        password: str,
        dtacctup: datetime.datetime,
        dryrun: bool = False,
        version: int | None = None,
        gen_newfileuid: bool = True,
        timeout: float | None = None,
        skip_profile: bool = False,
    ) -> BinaryIO:
        """
        Package and send OFX account info requests (ACCTINFORQ)
        """
        url = self._url_from_profile(dryrun, skip_profile, timeout, gen_newfileuid)
        logger.info("Creating account info request")
        signon = self.signon(password)

        acctinforq = ACCTINFORQ(dtacctup=dtacctup)
        acctinfotrnrq = ACCTINFOTRNRQ(trnuid=self.uuid(), acctinforq=acctinforq)
        msgs = SIGNUPMSGSRQV1(acctinfotrnrq)

        logger.debug(f"Wrapped account info request messages: {msgs}")

        ofx = OFX(signonmsgsrqv1=signon, signupmsgsrqv1=msgs)

        newfileuid = self.uuid() if gen_newfileuid else None

        return self.download(
            ofx,
            newfileuid=newfileuid,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

    def request_tax1099(
        self,
        password: str,
        *taxyears: str,
        acctnum: str | None = None,
        recid: str | None = None,
        gen_newfileuid: bool = True,
        dryrun: bool = False,
        timeout: float | None = None,
        skip_profile: bool = False,
    ) -> BinaryIO:
        """
        Request US federal income tax form 1099 (TAX1099RQ)
        """
        url = self._url_from_profile(dryrun, skip_profile, timeout, gen_newfileuid)
        logger.info("Creating tax 1099 request")
        signon = self.signon(password)

        rq = TAX1099RQ(*taxyears, recid=recid or None)
        msgs = TAX1099MSGSRQV1(TAX1099TRNRQ(trnuid=self.uuid(), tax1099rq=rq))

        logger.debug(f"Wrapped tax 1099 request messages: {msgs}")

        ofx = OFX(signonmsgsrqv1=signon, tax1099msgsrqv1=msgs)

        newfileuid = self.uuid() if gen_newfileuid else None

        return self.download(
            ofx,
            newfileuid=newfileuid,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

    def signon(
        self,
        userpass: str,
        userid: str | None = None,
        sesscookie: str | None = None,
    ) -> SIGNONMSGSRQV1:
        """Construct SONRQ; package in SIGNONMSGSRQV1"""
        if self.org:
            fi: FI | None = FI(org=self.org, fid=self.fid)
        else:
            fi = None

        if userid is None:
            userid = self.userid

        # CLIENTUID was introduced to the spec in OFXv1.0.3
        if self.version < 103:
            clientuid = None
        else:
            clientuid = self.clientuid

        sonrq = SONRQ(
            dtclient=self.dtclient(),
            userid=userid,
            userpass=userpass,
            language=self.language,
            fi=fi,
            sesscookie=sesscookie,
            appid=self.appid,
            appver=self.appver,
            clientuid=clientuid,
        )
        return SIGNONMSGSRQV1(sonrq=sonrq)

    def stmttrnrq(
        self,
        bankid: str,
        acctid: str,
        accttype: str,
        dtstart: datetime.datetime | None = None,
        dtend: datetime.datetime | None = None,
        inctran: bool = True,
    ) -> STMTTRNRQ:
        """Construct STMTRQ; package in STMTTRNRQ"""
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid()
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def stmtendtrnrq(
        self,
        bankid: str,
        acctid: str,
        accttype: str,
        dtstart: datetime.datetime | None = None,
        dtend: datetime.datetime | None = None,
    ) -> STMTENDTRNRQ:
        """Construct STMTENDRQ; package in STMTENDTRNRQ"""
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        stmtrq = STMTENDRQ(bankacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid()
        return STMTENDTRNRQ(trnuid=trnuid, stmtendrq=stmtrq)

    def ccstmttrnrq(
        self,
        acctid: str,
        dtstart: datetime.datetime | None = None,
        dtend: datetime.datetime | None = None,
        inctran: bool = True,
    ) -> CCSTMTTRNRQ:
        """Construct CCSTMTRQ; package in CCSTMTTRNRQ"""
        acct = CCACCTFROM(acctid=acctid)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid()
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def ccstmtendtrnrq(
        self,
        acctid: str,
        dtstart: datetime.datetime | None = None,
        dtend: datetime.datetime | None = None,
    ) -> CCSTMTENDTRNRQ:
        """Construct CCSTMTENDRQ; package in CCSTMTENDTRNRQ"""
        acct = CCACCTFROM(acctid=acctid)
        stmtrq = CCSTMTENDRQ(ccacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid()
        return CCSTMTENDTRNRQ(trnuid=trnuid, ccstmtendrq=stmtrq)

    def invstmttrnrq(
        self,
        acctid: str,
        brokerid: str,
        dtstart: datetime.datetime | None = None,
        dtend: datetime.datetime | None = None,
        inctran: bool = True,
        incoo: bool = False,
        dtasof: datetime.datetime | None = None,
        incpos: bool = True,
        incbal: bool = True,
    ) -> INVSTMTTRNRQ:
        """Construct INVSTMTRQ; package in INVSTMTTRNRQ"""
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        if inctran:
            inctran_: INCTRAN | None = INCTRAN(
                dtstart=dtstart, dtend=dtend, include=inctran
            )
        else:
            inctran_ = None
        incpos_ = INCPOS(dtasof=dtasof, include=incpos)
        stmtrq = INVSTMTRQ(
            invacctfrom=acct,
            inctran=inctran_,
            incoo=incoo,
            incpos=incpos_,
            incbal=incbal,
        )
        trnuid = self.uuid()
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(
        self,
        ofx: OFX,
        version: int | None = None,
        oldfileuid: str | None = None,
        newfileuid: str | None = None,
        prettyprint: bool | None = None,
        close_elements: bool | None = None,
        dryrun: bool = False,
        timeout: float | None = None,
        url: str | None = None,
    ) -> BytesIO:
        """
        Package complete OFX tree and POST to server.

        N.B. ``version`` / ``prettyprint`` / ``close_elements`` kwargs are
        basically hacks for ``scripts.ofxget.scan_profile()``; ordinarily you
        should initialize the ``OFXClient`` with the proper version# and
        formatting parameters, rather than overriding the client config here.

        Optional kwargs:
            ``version`` - OFX version to report in header
            ``oldfileuid`` - OLDFILEUID to report in header
            ``newfileuid`` - NEWFILEUID to report in header
            ``prettyprint`` - add newlines between tags and indentation
            ``close_elements`` - add markup closing tags to leaf elements
            ``dryrun`` - dump serialized request to stdout instead of POSTing
            ``timeout`` - HTTP connection timeout (in seconds)
        """
        request = self.serialize(
            ofx,
            version=version,
            oldfileuid=oldfileuid,
            newfileuid=newfileuid,
            prettyprint=prettyprint,
            close_elements=close_elements,
        )
        logger.debug(f"Finished request: {request.decode()}")

        if dryrun:
            return BytesIO(request)

        if url is None:
            url = self.url

        # NB: we resolve the url opener here instead of in __init__ because the tests
        #     mock urlopen after instantiating the OFXClient object
        response = self.post_request(url, request, timeout)
        return BytesIO(response)

    def post_request(
        self, url: str, serialized_request: bytes, timeout: float | None
    ) -> bytes:
        """Separated out to facilitate mocking in unit tests."""
        if timeout in (None, False):
            timeout = 10.0

        if USE_REQUESTS:
            logger.info("Using requests lib to post request")
            with requests.Session() as sess:
                if self.persist_cookies:
                    sess.cookies = self.cookiejar  # type: ignore[assignment]

                # Replace session default headers entirely rather than merging
                # via the headers= kwarg. Some FIs (e.g. Amex) validate HTTP
                # header ordering and reject requests where User-Agent is not
                # the first header — which happens when requests prepends its
                # own defaults before ours.
                sess.headers = self.http_headers  # type: ignore[assignment]

                response = sess.request(
                    method="POST",
                    url=url,
                    data=serialized_request,
                    timeout=timeout,
                )
            return response.content

        else:
            logger.info("Using urllib to post request")
            handlers = []
            if self.persist_cookies:
                handlers.append(urllib_request.HTTPCookieProcessor(self.cookiejar))
            opener = urllib_request.build_opener(*handlers)

            req = urllib_request.Request(
                url, method="POST", data=serialized_request, headers=self.http_headers
            )

            response = opener.open(req, timeout=timeout)
            return bytes(response.read())

    def serialize(
        self,
        ofx: OFX,
        version: int | None = None,
        oldfileuid: str | None = None,
        newfileuid: str | None = None,
        prettyprint: bool | None = None,
        close_elements: bool | None = None,
    ) -> bytes:
        """
        Transform a ``models.OFX`` instance into bytestring representation
        with OFX header prepended.

        N.B. ``version`` / ``prettyprint`` / ``close_elements`` kwargs are
        basically hacks for ``scripts.ofxget.scan_profile()``; ordinarily you
        should initialize the ``OFXClient`` with the proper version# and
        formatting parameters, rather than overriding the client config here.

        Optional kwargs:
            ``version`` - OFX version to report in header
            ``oldfileuid`` - OLDFILEUID to report in header
            ``newfileuid`` - NEWFILEUID to report in header
            ``prettyprint`` - add newlines between tags and indentation
            ``close_elements`` - add markup closing tags to leaf elements
        """
        if version is None:
            version = self.version
        if prettyprint is None:
            prettyprint = self.prettyprint
        if close_elements is None:
            close_elements = self.close_elements

        header = bytes(
            str(
                make_header(
                    version=version, oldfileuid=oldfileuid, newfileuid=newfileuid
                )
            ),
            "utf_8",
        )

        tree = ofx.to_etree()
        if prettyprint:
            ET.indent(tree)

        # Some servers choke on OFXv1 requests including ending tags for
        # elements (which are optional per the spec).
        if not close_elements:
            if version >= 200:
                raise ValueError(
                    f"OFX version {version} requires ending tags for elements"
                )
            body = utils.tostring_unclosed_elements(tree)
        else:
            # ``method="html"`` skips the initial XML declaration
            body = ET.tostring(tree, encoding="utf_8", method="html")

        return header + body


def wrap_stmtrq(
    nt: RequestParam, rqs: Iterable[RequestParam], client: OFXClient
) -> tuple[type[Message], list[TrnRequest]]:
    match nt:
        case StmtRq():
            return (
                BANKMSGSRQV1,
                [
                    client.stmttrnrq(**dict(rq._asdict(), bankid=client.bankid))
                    for rq in rqs
                ],
            )
        case CcStmtRq():
            return (
                CREDITCARDMSGSRQV1,
                [client.ccstmttrnrq(**rq._asdict()) for rq in rqs],
            )
        case InvStmtRq():
            return (
                INVSTMTMSGSRQV1,
                [
                    client.invstmttrnrq(**dict(r._asdict(), brokerid=client.brokerid))
                    for r in rqs
                ],
            )
        case StmtEndRq():
            return (
                BANKMSGSRQV1,
                [
                    client.stmtendtrnrq(**dict(rq._asdict(), bankid=client.bankid))
                    for rq in rqs
                ],
            )
        case CcStmtEndRq():
            return (
                CREDITCARDMSGSRQV1,
                [client.ccstmtendtrnrq(**rq._asdict()) for rq in rqs],
            )
        case _:
            raise ValueError(f"Not a *StmtRq/*StmtEndRq: {nt.__class__.__name__}")
