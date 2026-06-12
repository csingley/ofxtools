"""
Common Aggregates (OFX Section 3.1); message extensions (OFX Section 2.7)
"""

from __future__ import annotations

__all__ = ["SVCSTATUSES", "STATUS", "BAL", "OFXELEMENT", "OFXEXTENSION", "MSGSETCORE"]


# local imports
from ofxtools.models.base import Aggregate, ElementList
from ofxtools.models.i18n import CURRENCY, LANG_CODES
from ofxtools.Types import (
    Bool,
    DateTime,
    Decimal,
    Integer,
    ListAggregate,
    ListElement,
    OneOf,
    String,
    SubAggregate,
)

SVCSTATUSES = ["AVAIL", "PEND", "ACTIVE"]


class STATUS(Aggregate):
    """OFX section 3.1.5"""

    code = Integer(6, required=True)
    severity = OneOf("INFO", "WARN", "ERROR", required=True)
    message = String(255)


class BAL(Aggregate):
    """OFX section 3.1.4"""

    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf("DOLLAR", "PERCENT", "NUMBER", required=True)
    value = Decimal(required=True)
    dtasof = DateTime()
    currency = SubAggregate(CURRENCY)


class OFXELEMENT(Aggregate):
    """OFX section 2.7.2"""

    tagname = String(32, required=True)
    name = String(32)
    tagtype = String(20)
    tagvalue = String(1000, required=True)


class OFXEXTENSION(Aggregate):
    """OFX section 2.7.2"""

    ofxelement = ListAggregate(OFXELEMENT)


class MSGSETCORE(ElementList):
    """OFX section 7.2.1"""

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
    def validate_args(cls, *args: object, **kwargs: object) -> None:
        if len(args) == 0:
            raise ValueError(f"{cls.__name__} must contain at least one item")

        super().validate_args(*args, **kwargs)
