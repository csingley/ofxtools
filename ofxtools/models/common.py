# coding: utf-8
"""
"""
# local imports
from ofxtools.Types import String, OneOf, Integer, Decimal, DateTime, Bool
from ofxtools.models.base import Aggregate, List, SubAggregate, Unsupported
from ofxtools.models.i18n import CURRENCY, LANG_CODES


__all__ = [
    "SVCSTATUSES",
    "STATUS",
    "BAL",
    "OFXELEMENT",
    "OFXEXTENSION",
    "MSGSETCORE",
    "TrnRq",
    "TrnRs",
    "SyncRqList",
    "SyncRsList",
]


SVCSTATUSES = ["AVAIL", "PEND", "ACTIVE"]


class STATUS(Aggregate):
    """ OFX section 3.1.5 """

    code = Integer(6, required=True)
    severity = OneOf("INFO", "WARN", "ERROR", required=True)
    message = String(255)


class BAL(Aggregate):
    """ OFX section 3.1.4 """

    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf("DOLLAR", "PERCENT", "NUMBER", required=True)
    value = Decimal(required=True)
    dtasof = DateTime()
    currency = SubAggregate(CURRENCY)


class OFXELEMENT(Aggregate):
    """ OFX section 2.7.2 """

    tagname = String(32, required=True)
    name = String(32)
    tagtype = String(20)
    tagvalue = String(1000, required=True)


class OFXEXTENSION(List):
    """ OFX section 2.7.2 """

    dataTags = ["OFXELEMENT"]


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
        for child in set(elem):
            if "." in child.tag:
                elem.remove(child)

        return super(MSGSETCORE, MSGSETCORE).groom(elem)


class TrnRq(Aggregate):
    """
    Base class for *TRNRQ wrappers.

    OFX section 2.4.6.1
    """

    trnuid = String(36, required=True)
    cltcookie = String(32)
    tan = String(80)
    ofxextension = SubAggregate(OFXEXTENSION)


class TrnRs(Aggregate):
    """
    Base class for *TRNRS wrappers.

    OFX section 2.4.6.1
    """

    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    cltcookie = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)


class TranList(List):
    """ Base class for OFX *TRANLIST """

    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    metadataTags = ["DTSTART", "DTEND"]

    def __repr__(self):
        return "<{} dtstart='{}' dtend='{}' len={}>".format(
            self.__class__.__name__, self.dtstart, self.dtend, len(self)
        )


class SyncRqList(List):
    """ Base class for *SYNCRQ """

    token = String(10)
    tokenonly = Bool()
    refresh = Bool()
    rejectifmissing = Bool(required=True)

    metadataTags = ["TOKEN", "TOKENONLY", "REFRESH", "REJECTIFMISSING"]
    requiredMutexes = [("token", "tokenonly", "refresh")]


class SyncRsList(List):
    """ Base class for *SYNCRS """

    token = String(10, required=True)
    lostsync = Bool()

    metadataTags = ["TOKEN", "LOSTSYNC"]
