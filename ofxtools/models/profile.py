# coding: utf-8
""" FI Profile - OFX Section 7 """
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import Bool, String, OneOf, Integer, DateTime
from ofxtools.models.base import Aggregate, SubAggregate, List
from ofxtools.models.common import OFXEXTENSION
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.i18n import LANG_CODES, COUNTRY_CODES


__all__ = [
    "MSGSETLIST",
    "SIGNONINFOLIST",
    "PROFRQ",
    "PROFRS",
    "PROFTRNRQ",
    "PROFTRNRS",
    "PROFMSGSRQV1",
    "PROFMSGSRSV1",
    "MSGSETCORE",
    "PROFMSGSETV1",
    "PROFMSGSET",
]


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


class PROFMSGSRQV1(List):
    dataTags = ["PROFTRNRQ"]


class PROFMSGSRSV1(List):
    dataTags = ["PROFTRNRS"]


class MSGSETCORE(Aggregate):
    """ OFX section 7.2.1 """

    ver = Integer(required=True)
    url = String(255, required=True)
    ofxsec = OneOf("NONE", "TYPE1", required=True)
    transpsec = Bool(required=True)
    signonrealm = String(32, required=True)
    language = OneOf(*LANG_CODES, required=True)
    syncmode = OneOf("FULL", "LITE", required=True)
    refreshsupt = Bool()
    respfileer = Bool(required=True)
    spname = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)

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

        return super(MSGSETCORE, MSGSETCORE).groom(elem)


class PROFMSGSETV1(Aggregate):
    """ OFX section 7.3 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class PROFMSGSET(Aggregate):
    """ OFX section 7.3 """

    profmsgsetv1 = SubAggregate(PROFMSGSETV1, required=True)
