# coding: utf-8
"""
Common Aggregates (OFX Section 3.1); message extensions (OFX Section 2.7)
"""


__all__ = [
    "SVCSTATUSES",
    "STATUS",
    "BAL",
    "OFXELEMENT",
    "OFXEXTENSION",
    "MSGSETCORE",
]


# local imports
from ofxtools.Types import (
    String,
    OneOf,
    Integer,
    Decimal,
    DateTime,
    Bool,
    ListItem,
    ListElement,
)
from ofxtools.models.base import Aggregate, SubAggregate, ElementList
from ofxtools.models.i18n import CURRENCY, LANG_CODES


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


class OFXEXTENSION(Aggregate):
    """ OFX section 2.7.2 """
    ofxelement = ListItem(OFXELEMENT)


class MSGSETCORE(ElementList):
    """ OFX section 7.2.1 """

    ver = Integer(required=True)
    url = String(255, required=True)
    ofxsec = OneOf("NONE", "TYPE1", required=True)
    transpsec = Bool(required=True)
    signonrealm = String(32, required=True)
    language = ListElement(OneOf(*LANG_CODES))
    syncmode = OneOf("FULL", "LITE", required=True)
    refreshsupt = Bool()
    respfileer = Bool(required=True)
    spname = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        if len(args) == 0:
            msg = "{} must contain at least one item"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)
