# coding: utf-8
""" FI Profile - OFX Section 7 """


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


# local imports
from ofxtools.Types import Bool, String, OneOf, Integer, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.signon import SIGNONMSGSET
from ofxtools.models.signup import SIGNUPMSGSET
from ofxtools.models.bank.msgsets import (
    BANKMSGSET, CREDITCARDMSGSET, INTERXFERMSGSET, WIREXFERMSGSET,
)
from ofxtools.models.billpay.msgsets import BILLPAYMSGSET
from ofxtools.models.invest.msgsets import INVSTMTMSGSET, SECLISTMSGSET
from ofxtools.models.email import EMAILMSGSET
from ofxtools.models.tax1099 import TAX1099MSGSET


class PROFMSGSETV1(Aggregate):
    """ OFX section 7.3 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class PROFMSGSET(Aggregate):
    """ OFX section 7.3 """

    profmsgsetv1 = SubAggregate(PROFMSGSETV1, required=True)


class MSGSETLIST(Aggregate):
    """ OFX section 7.2 """

    signonmsgset = ListItem(SIGNONMSGSET)
    signupmsgset = ListItem(SIGNUPMSGSET)
    bankmsgset = ListItem(BANKMSGSET)
    creditcardmsgset = ListItem(CREDITCARDMSGSET)
    invstmtmsgset = ListItem(INVSTMTMSGSET)
    interxfermsgset = ListItem(INTERXFERMSGSET)
    wirexfermsgset = ListItem(WIREXFERMSGSET)
    billpaymsgset = ListItem(BILLPAYMSGSET)
    emailmsgset = ListItem(EMAILMSGSET)
    seclistmsgset = ListItem(SECLISTMSGSET)
    #  presdirmsgset = ListItem(PRESDIRMSGSET)
    presdirmsgset = Unsupported()
    #  presdlvmsgset = ListItem(PRESDLVMSGSET)
    presdlvmsgset = Unsupported()
    profmsgset = ListItem(PROFMSGSET)
    tax1099msgset = ListItem(TAX1099MSGSET)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        #  "[MSGSETLIST contents] One or more message set aggregates"
        if len(args) == 0:
            msg = "{} must contain at least one item"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class SIGNONINFO(Aggregate):
    """ OFX section 7.2.2 """

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
    """ OFX section 7.2 """

    signoninfo = ListItem(SIGNONINFO)


class PROFRQ(Aggregate):
    """ OFX section 7.1.5 """

    clientrouting = OneOf("NONE", "SERVICE", "MSGSET", required=True)
    dtprofup = DateTime(required=True)


class PROFRS(Aggregate):
    """ OFX section 7.2 """

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
    """ OFX section 7.1.5 """

    profrq = SubAggregate(PROFRQ, required=True)


class PROFTRNRS(TrnRs):
    """ OFX section 7.2 """

    profrs = SubAggregate(PROFRS)

    @property
    def profile(self):
        return self.profrs


class PROFMSGSRQV1(Aggregate):
    proftrnrq = ListItem(PROFTRNRQ)


class PROFMSGSRSV1(Aggregate):
    proftrnrs = ListItem(PROFTRNRS)
