# coding: utf-8
""" FI Profile - OFX Section 7 """
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import Bool, String, OneOf, Integer, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, List
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.i18n import COUNTRY_CODES


__all__ = [
    "MSGSETLIST",
    "SIGNONINFO",
    "SIGNONINFOLIST",
    "PROFRQ",
    "PROFRS",
    "PROFTRNRQ",
    "PROFTRNRS",
]


# FIXME
# Per OFX spec, MSGSETLIST must contain one or more message set aggregates
class MSGSETLIST(List):
    """ OFX section 7.2 """

    dataTags = [
        "SIGNONMSGSET",
        "SIGNUPMSGSET",
        "PROFMSGSET",
        "BANKMSGSET",
        "CREDITCARDMSGSET",
        "INTERXFERMSGSET",
        "WIREXFERMSGSET",
        "INVSTMTMSGSET",
        "SECLISTMSGSET",
        "BILLPAYMSGSET",
        "PRESDIRMSGSET",
        "PRESDLVMSGSET",
        "TAX1099MSGSET",
    ]


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


class SIGNONINFOLIST(List):
    """ OFX section 7.2 """

    dataTags = ["SIGNONINFO"]


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

    @staticmethod
    def groom(elem):
        """
        Remove proprietary tags e.g. INTU.XXX
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        for child in set(elem):
            if "." in child.tag:
                elem.remove(child)

        return super(PROFRS, PROFRS).groom(elem)


class PROFTRNRQ(TrnRq):
    """ OFX section 7.1.5 """

    profrq = SubAggregate(PROFRQ, required=True)


class PROFTRNRS(TrnRs):
    """ OFX section 7.2 """

    profrs = SubAggregate(PROFRS)

    @property
    def profile(self):
        return self.profrs
