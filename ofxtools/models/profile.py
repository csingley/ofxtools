"""FI Profile - OFX Section 7"""

from __future__ import annotations

__all__ = [
    "SIGNONINFO",
    "SIGNONINFOLIST",
    "PROFRQ",
    "PROFRS",
    "PROFTRNRQ",
    "PROFTRNRS",
    "PROFMSGSRQV1",
    "PROFMSGSRSV1",
    "PROFMSGSETV1",
    "PROFMSGSET",
    "MSGSETLIST",
]


from typing import Any

# local imports
from ofxtools.models.bank.msgsets import (
    BANKMSGSET,
    CREDITCARDMSGSET,
    INTERXFERMSGSET,
    WIREXFERMSGSET,
)
from ofxtools.models.base import Aggregate
from ofxtools.models.billpay.msgsets import BILLPAYMSGSET
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.email import EMAILMSGSET
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.invest.msgsets import INVSTMTMSGSET, SECLISTMSGSET
from ofxtools.models.signon import SIGNONMSGSET
from ofxtools.models.signup import SIGNUPMSGSET
from ofxtools.models.tax1099 import TAX1099MSGSET
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.Types import (
    Bool,
    DateTime,
    Integer,
    ListAggregate,
    OneOf,
    String,
    SubAggregate,
    Unsupported,
)


class PROFMSGSETV1(Aggregate):
    """OFX section 7.3"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class PROFMSGSET(Aggregate):
    """OFX section 7.3"""

    profmsgsetv1 = SubAggregate(PROFMSGSETV1, required=True)


class MSGSETLIST(Aggregate):
    """OFX section 7.2"""

    signonmsgset = ListAggregate(SIGNONMSGSET)
    signupmsgset = ListAggregate(SIGNUPMSGSET)
    bankmsgset = ListAggregate(BANKMSGSET)
    creditcardmsgset = ListAggregate(CREDITCARDMSGSET)
    invstmtmsgset = ListAggregate(INVSTMTMSGSET)
    interxfermsgset = ListAggregate(INTERXFERMSGSET)
    wirexfermsgset = ListAggregate(WIREXFERMSGSET)
    billpaymsgset = ListAggregate(BILLPAYMSGSET)
    emailmsgset = ListAggregate(EMAILMSGSET)
    seclistmsgset = ListAggregate(SECLISTMSGSET)
    #  presdirmsgset = ListAggregate(PRESDIRMSGSET)
    presdirmsgset = Unsupported()
    #  presdlvmsgset = ListAggregate(PRESDLVMSGSET)
    presdlvmsgset = Unsupported()
    profmsgset = ListAggregate(PROFMSGSET)
    tax1099msgset = ListAggregate(TAX1099MSGSET)

    @classmethod
    def validate_args(cls, *args: object, **kwargs: object) -> None:
        #  "[MSGSETLIST contents] One or more message set aggregates"
        if len(args) == 0:
            raise ValueError(f"{cls.__name__} must contain at least one item")

        super().validate_args(*args, **kwargs)


class SIGNONINFO(Aggregate):
    """OFX section 7.2.2"""

    signonrealm = String(32, required=True)
    min = Integer(required=True)
    max = Integer(required=True)
    chartype = OneOf(
        "ALPHAONLY", "NUMERICONLY", "ALPHAORNUMERIC", "ALPHAANDNUMERIC", required=True
    )
    casesen = Bool(required=True)
    special = Bool(required=True)
    spaces = Bool(required=True)
    pinch = Bool(required=True)
    chgpinfirst = Bool()
    usercred1label = String(64)
    usercred2label = String(64)
    clientuidreq = Bool()
    authtokenfirst = Bool()
    authtokenlabel = String(64)
    authtokeninfourl = String(255)
    mfachallengesupt = Bool()
    mfachallengefirst = Bool()
    accesstokenreq = Bool()


class SIGNONINFOLIST(Aggregate):
    """OFX section 7.2"""

    signoninfo = ListAggregate(SIGNONINFO)


class PROFRQ(Aggregate):
    """OFX section 7.1.5"""

    clientrouting = OneOf("NONE", "SERVICE", "MSGSET", required=True)
    dtprofup = DateTime(required=True)


class PROFRS(Aggregate):
    """OFX section 7.2"""

    msgsetlist = SubAggregate(MSGSETLIST, required=True)
    signoninfolist = SubAggregate(SIGNONINFOLIST, required=True)
    dtprofup = DateTime(required=True)
    finame = String(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES, required=True)
    csphone = String(32)
    tsphone = String(32)
    faxphone = String(32)
    url = String(255)
    email = String(80)


class PROFTRNRQ(TrnRq):
    """OFX section 7.1.5"""

    profrq = SubAggregate(PROFRQ, required=True)


class PROFTRNRS(TrnRs):
    """OFX section 7.2"""

    profrs = SubAggregate(PROFRS)

    @property
    def profile(self) -> Any:
        return self.profrs


class PROFMSGSRQV1(Aggregate):
    proftrnrq = ListAggregate(PROFTRNRQ)


class PROFMSGSRSV1(Aggregate):
    proftrnrs = ListAggregate(PROFTRNRS)
