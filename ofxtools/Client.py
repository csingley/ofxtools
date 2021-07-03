# coding: utf-8
"""
Network client that composes/transmits Open Financial Exchange (OFX) requests,
and receives OFX responses in reply.  A basic CLI utility is included.

To use, create an OFXClient instance configured with OFX connection parameters:
server URL, OFX protocol version, financial institution identifiers, client
identifiers, etc.

``config/fi.cfg`` contains a database of these parameters, most conveniently
accessed via ``scripts/ofx.py``.

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
import logging
import datetime
import http.cookiejar
import uuid
import xml.etree.ElementTree as ET
import urllib.request as urllib_request
import socket
from io import BytesIO
import itertools
from operator import attrgetter, itemgetter
from functools import singledispatch
from typing import (
    Dict,
    Union,
    Optional,
    Tuple,
    Iterator,
    NamedTuple,
    BinaryIO,
    Type,
    Callable,
)


# local imports
from ofxtools.header import make_header
from ofxtools.models.ofx import OFX
from ofxtools.models import ACCTINFORQ, ACCTINFOTRNRQ
from ofxtools.models.profile import PROFRQ, PROFTRNRQ, PROFMSGSRQV1, PROFMSGSET
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
    BANKMSGSET,
    CREDITCARDMSGSET,
    INTERXFERMSGSET,
    WIREXFERMSGSET,
)
from ofxtools.models.invest import (
    INVSTMTTRNRQ,
    INVSTMTRQ,
    INVACCTFROM,
    INCPOS,
    INVSTMTMSGSRQV1,
    INVSTMTMSGSET,
    SECLISTMSGSET,
)
from ofxtools.models.signon import SIGNONMSGSET
from ofxtools.models.signup import SIGNUPMSGSET
from ofxtools.models.billpay.msgsets import BILLPAYMSGSET
from ofxtools.models.email import EMAILMSGSET
from ofxtools.models.tax1099 import TAX1099MSGSET
from ofxtools.models.tax1099 import TAX1099RQ, TAX1099TRNRQ, TAX1099MSGSRQV1
from ofxtools.utils import classproperty, UTC
from ofxtools import utils, config
from ofxtools.Parser import OFXTree


AUTH_PLACEHOLDER = "{:0<32}".format("anonymous")


logger = logging.getLogger(__name__)


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


# TYPE ALIASES
RequestParam = Union[StmtRq, CcStmtRq, InvStmtRq, StmtEndRq, CcStmtEndRq]
Request = Union[STMTRQ, CCSTMTRQ, INVSTMTRQ, STMTENDRQ, CCSTMTENDRQ]
Message = Union[BANKMSGSRQV1, CREDITCARDMSGSRQV1, INVSTMTMSGSRQV1]
MsgsetClass = Union[
    Type[SIGNONMSGSET],
    Type[SIGNUPMSGSET],
    Type[BANKMSGSET],
    Type[CREDITCARDMSGSET],
    Type[INVSTMTMSGSET],
    Type[INTERXFERMSGSET],
    Type[WIREXFERMSGSET],
    Type[BILLPAYMSGSET],
    Type[EMAILMSGSET],
    Type[SECLISTMSGSET],
    Type[PROFMSGSET],
    Type[TAX1099MSGSET],
]


class OFXClient:
    """
    Basic OFX client to download statement and profile requests.
    """

    # OFX header/signon defaults
    userid: str = AUTH_PLACEHOLDER
    clientuid: Optional[str] = None
    org: Optional[str] = None
    fid: Optional[str] = None
    version: int = 203
    appid: str = "QWIN"
    appver: str = "2700"
    language: str = "ENG"
    useragent: str = "InetClntApp/3.0"

    # Formatting defaults
    prettyprint: bool = False
    close_elements: bool = True

    # Stmt request
    bankid: Optional[str] = None
    brokerid: Optional[str] = None

    # URL opener
    url_opener: Optional[Callable] = None

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
        useragent: Optional[str] = None,
        persist_cookies: bool = True,
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
        ]:
            value = locals()[attr]
            if value is not None:
                setattr(self, attr, value)

        if (not self.close_elements) and self.version >= 200:
            raise ValueError(f"OFX version {self.version} must close all tags")

        if persist_cookies:
            cj = http.cookiejar.CookieJar()
            opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(cj))
            self.url_opener = opener.open

    @classproperty
    @classmethod
    def uuid(cls) -> str:
        """
        Return a new UUID each time called.

        Wrapper we can mock for testing.
        """
        return str(uuid.uuid4()).upper()

    @property
    def http_headers(self) -> Dict[str, str]:
        """Pass to urllib.request.urlopen()"""
        mimetype = "application/x-ofx"
        # Python libraries such as ``urllib.request`` and ``requests``
        # identify themselves in the ``User-Agent`` header,
        # which apparently displeases some FIs
        return {
            "User-Agent": self.useragent,
            "Content-type": mimetype,
            # Apparently Amex is unhappy unless it sees a MIME type of application/xml
            # with some quality rating - ANY quality rating, it seems.
            "Accept": "*/*, {}, application/xml;q=0.9".format(mimetype),
        }

    def dtclient(self) -> datetime.datetime:
        """
        Wrapper we can mock for testing.
        (as opposed to datetime.datetime, which is a C extension)
        """
        return datetime.datetime.now(UTC)

    def request_statements(
        self,
        password: str,
        *requests: RequestParam,
        gen_newfileuid: bool = True,
        dryrun: bool = False,
        timeout: Optional[float] = None,
    ) -> BinaryIO:
        """
        Package and send OFX statement requests
        (STMTRQ/CCSTMTRQ/INVSTMTRQ/STMTENDRQ/CCSTMTENDRQ).
        """
        if dryrun:
            url = ""
        else:
            RqCls2url = self._get_service_urls(
                timeout=timeout,
                gen_newfileuid=gen_newfileuid,
            )

            # HACK FIXME
            # As a simplification, we assume that FIs handle all classes
            # of statement request from a single URL.
            urls = set(RqCls2url.values())
            assert len(urls) == 1
            url = urls.pop()

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
        def trnSortKey(pair):
            return pair[0].__name__

        trnGroupKey = itemgetter(0)
        trnrqs.sort(key=trnSortKey)

        # N.B. we need to annotate first arg as typing.Type here to indicate that
        # we're passing in a class not an instance.
        def msg_args(
            msgcls: Union[
                Type[BANKMSGSRQV1], Type[CREDITCARDMSGSRQV1], Type[INVSTMTMSGSRQV1]
            ],
            trnrqs: Iterator[Request],
        ) -> Tuple[str, Message]:
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

        if gen_newfileuid:
            newfileuid = self.uuid
        else:
            newfileuid = None

        return self.download(
            ofx,
            newfileuid=newfileuid,
            dryrun=dryrun,
            timeout=timeout,
            url=url,
        )

    def _get_service_urls(
        self,
        timeout: Optional[float] = None,
        gen_newfileuid: bool = True,
    ) -> dict:
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
            stmtendrqCls: Union[Type[StmtEndRq], Type[CcStmtEndRq]],
        ):
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
        version: Optional[int] = None,
        gen_newfileuid: bool = True,
        prettyprint: Optional[bool] = None,
        close_elements: Optional[bool] = None,
        dryrun: bool = False,
        timeout: Optional[float] = None,
        url: Optional[str] = None,
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
                profrs: Optional[BytesIO] = BytesIO(f.read())

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
            assert profrs is not None
            response = profrs
        else:
            assert proftrnrs.status.code == 0
            dtprofup_server = proftrnrs.profrs.dtprofup
            assert dtprofup is None or dtprofup <= dtprofup_server

            # Cache the updated PROFRS sent by the server
            response.seek(0)
            with open(persistpath, "wb") as f:
                f.write(response.read())

        # Rewind PROFRS so it can be returned cleanly after having been parsed.
        response.seek(0)

        return response

    def _request_profile(
        self,
        dtprofup: Optional[datetime.datetime] = None,
        version: Optional[int] = None,
        gen_newfileuid: bool = True,
        prettyprint: Optional[bool] = None,
        close_elements: Optional[bool] = None,
        dryrun: bool = False,
        timeout: Optional[float] = None,
        url: Optional[str] = None,
    ) -> BytesIO:
        """Package and send OFX profile requests (PROFRQ)."""
        logger.info("Creating profile request")

        if dtprofup is None:
            dtprofup = datetime.datetime(1990, 1, 1, tzinfo=UTC)
        profrq = PROFRQ(clientrouting="NONE", dtprofup=dtprofup)
        proftrnrq = PROFTRNRQ(trnuid=self.uuid, profrq=profrq)

        logger.debug(f"Wrapped profile request: {proftrnrq}")

        user = password = AUTH_PLACEHOLDER
        signon = self.signon(password, userid=user)

        ofx = OFX(signonmsgsrqv1=signon, profmsgsrqv1=PROFMSGSRQV1(proftrnrq))

        if gen_newfileuid:
            newfileuid = self.uuid
        else:
            newfileuid = None

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
        version: Optional[int] = None,
        gen_newfileuid: bool = True,
        timeout: Optional[float] = None,
    ) -> BinaryIO:
        """
        Package and send OFX account info requests (ACCTINFORQ)
        """
        if dryrun:
            url = ""
        else:
            RqCls2url = self._get_service_urls(
                timeout=timeout,
                gen_newfileuid=gen_newfileuid,
            )

            # HACK FIXME
            # As a simplification, we assume that FIs handle all classes
            # of statement request from a single URL.
            urls = set(RqCls2url.values())
            assert len(urls) == 1
            url = urls.pop()

        logger.info("Creating account info request")
        signon = self.signon(password)

        acctinforq = ACCTINFORQ(dtacctup=dtacctup)
        acctinfotrnrq = ACCTINFOTRNRQ(trnuid=self.uuid, acctinforq=acctinforq)
        msgs = SIGNUPMSGSRQV1(acctinfotrnrq)

        logger.debug(f"Wrapped account info request messages: {msgs}")

        ofx = OFX(signonmsgsrqv1=signon, signupmsgsrqv1=msgs)

        if gen_newfileuid:
            newfileuid = self.uuid
        else:
            newfileuid = None

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
        acctnum: str = None,
        recid: str = None,
        gen_newfileuid: bool = True,
        dryrun: bool = False,
        timeout: Optional[float] = None,
    ) -> BinaryIO:
        """
        Request US federal income tax form 1099 (TAX1099RQ)
        """
        if dryrun:
            url = ""
        else:
            RqCls2url = self._get_service_urls(
                timeout=timeout,
                gen_newfileuid=gen_newfileuid,
            )

            # HACK FIXME
            # As a simplification, we assume that FIs handle all classes
            # of statement request from a single URL.
            urls = set(RqCls2url.values())
            assert len(urls) == 1
            url = urls.pop()

        logger.info("Creating tax 1099 request")
        signon = self.signon(password)

        rq = TAX1099RQ(*taxyears, recid=recid or None)
        msgs = TAX1099MSGSRQV1(TAX1099TRNRQ(trnuid=self.uuid, tax1099rq=rq))

        logger.debug(f"Wrapped tax 1099 request messages: {msgs}")

        ofx = OFX(signonmsgsrqv1=signon, tax1099msgsrqv1=msgs)

        if gen_newfileuid:
            newfileuid = self.uuid
        else:
            newfileuid = None

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
        userid: Optional[str] = None,
        sesscookie: Optional[str] = None,
    ) -> SIGNONMSGSRQV1:
        """Construct SONRQ; package in SIGNONMSGSRQV1"""
        if self.org:
            fi: Optional[FI] = FI(org=self.org, fid=self.fid)
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
        dtstart: Optional[datetime.datetime] = None,
        dtend: Optional[datetime.datetime] = None,
        inctran: bool = True,
    ) -> STMTTRNRQ:
        """Construct STMTRQ; package in STMTTRNRQ"""
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = STMTRQ(bankacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid
        return STMTTRNRQ(trnuid=trnuid, stmtrq=stmtrq)

    def stmtendtrnrq(
        self,
        bankid: str,
        acctid: str,
        accttype: str,
        dtstart: Optional[datetime.datetime] = None,
        dtend: Optional[datetime.datetime] = None,
    ) -> STMTENDTRNRQ:
        """Construct STMTENDRQ; package in STMTENDTRNRQ"""
        acct = BANKACCTFROM(bankid=bankid, acctid=acctid, accttype=accttype)
        stmtrq = STMTENDRQ(bankacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return STMTENDTRNRQ(trnuid=trnuid, stmtendrq=stmtrq)

    def ccstmttrnrq(
        self,
        acctid: str,
        dtstart: Optional[datetime.datetime] = None,
        dtend: Optional[datetime.datetime] = None,
        inctran: bool = True,
    ) -> CCSTMTTRNRQ:
        """Construct CCSTMTRQ; package in CCSTMTTRNRQ"""
        acct = CCACCTFROM(acctid=acctid)
        inctran_ = INCTRAN(dtstart=dtstart, dtend=dtend, include=inctran)
        stmtrq = CCSTMTRQ(ccacctfrom=acct, inctran=inctran_)
        trnuid = self.uuid
        return CCSTMTTRNRQ(trnuid=trnuid, ccstmtrq=stmtrq)

    def ccstmtendtrnrq(
        self,
        acctid: str,
        dtstart: Optional[datetime.datetime] = None,
        dtend: Optional[datetime.datetime] = None,
    ) -> CCSTMTENDTRNRQ:
        """Construct CCSTMTENDRQ; package in CCSTMTENDTRNRQ"""
        acct = CCACCTFROM(acctid=acctid)
        stmtrq = CCSTMTENDRQ(ccacctfrom=acct, dtstart=dtstart, dtend=dtend)
        trnuid = self.uuid
        return CCSTMTENDTRNRQ(trnuid=trnuid, ccstmtendrq=stmtrq)

    def invstmttrnrq(
        self,
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
        """Construct INVSTMTRQ; package in INVSTMTTRNRQ"""
        acct = INVACCTFROM(acctid=acctid, brokerid=brokerid)
        if inctran:
            inctran_: Optional[INCTRAN] = INCTRAN(
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
        trnuid = self.uuid
        return INVSTMTTRNRQ(trnuid=trnuid, invstmtrq=stmtrq)

    def download(
        self,
        ofx: OFX,
        version: Optional[int] = None,
        oldfileuid: Optional[str] = None,
        newfileuid: Optional[str] = None,
        prettyprint: Optional[bool] = None,
        close_elements: Optional[bool] = None,
        dryrun: bool = False,
        timeout: Optional[float] = None,
        url: Optional[str] = None,
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

        req = urllib_request.Request(
            url, method="POST", data=request, headers=self.http_headers
        )

        if timeout in (None, False):
            #  timeout = socket._GLOBAL_DEFAULT_TIMEOUT  # type: ignore
            timeout = 10.0

        kwargs = dict(timeout=timeout)

        url_opener = self.url_opener
        if url_opener is None:
            # NB: we resolve the default url opener here instead
            #     instead of in __init__ because the tests
            #     mock urlopen after instantiating the OFXClient object
            url_opener = urllib_request.urlopen

        response = url_opener(req, **kwargs)
        return BytesIO(response.read())

    def serialize(
        self,
        ofx: OFX,
        version: Optional[int] = None,
        oldfileuid: Optional[str] = None,
        newfileuid: Optional[str] = None,
        prettyprint: Optional[bool] = None,
        close_elements: Optional[bool] = None,
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
            utils.indent(tree)

        # Some servers choke on OFXv1 requests including ending tags for
        # elements (which are optional per the spec).
        if close_elements is False:
            if version >= 200:
                raise ValueError(
                    f"OFX version {version} requires ending tags for elements"
                )
            body = utils.tostring_unclosed_elements(tree)
        else:
            # ``method="html"`` skips the initial XML declaration
            body = ET.tostring(tree, encoding="utf_8", method="html")

        return header + body


@singledispatch
def wrap_stmtrq(nt, rqs, client):
    raise ValueError(f"Not a *StmtRq/*StmtEndRq: {nt.__class__.__name__}")


@wrap_stmtrq.register(StmtRq)
def wrap_stmtrq_stmtrq(nt, rqs, client):
    return (
        BANKMSGSRQV1,
        [client.stmttrnrq(**dict(rq._asdict(), bankid=client.bankid)) for rq in rqs],
    )


@wrap_stmtrq.register(CcStmtRq)
def wrap_stmtrq_ccstmtrq(nt, rqs, client):
    return (CREDITCARDMSGSRQV1, [client.ccstmttrnrq(**rq._asdict()) for rq in rqs])


@wrap_stmtrq.register(InvStmtRq)
def wrap_stmtrq_invstmtrq(nt, rqs, client):
    return (
        INVSTMTMSGSRQV1,
        [
            client.invstmttrnrq(**dict(r._asdict(), brokerid=client.brokerid))
            for r in rqs
        ],
    )


@wrap_stmtrq.register(StmtEndRq)
def wrap_stmtrq_stmtendrq(nt, rqs, client):
    return (
        BANKMSGSRQV1,
        [client.stmtendtrnrq(**dict(rq._asdict(), bankid=client.bankid)) for rq in rqs],
    )


@wrap_stmtrq.register(CcStmtEndRq)
def wrap_stmtrq_ccstmtendrq(nt, rqs, client):
    return (CREDITCARDMSGSRQV1, [client.ccstmtendtrnrq(**rq._asdict()) for rq in rqs])
