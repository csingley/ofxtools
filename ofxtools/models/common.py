# coding: utf-8
"""
"""
# local imports
from ofxtools.Types import (
    String,
    OneOf,
    Integer,
    Decimal,
    DateTime,
)
from ofxtools.models.base import (
    Aggregate,
    List,
    SubAggregate,
)
from ofxtools.models.i18n import (
    CURRENCY,
)


class OFXELEMENT(Aggregate):
    """ OFX section 2.7.2 """
    tagname = String(32, required=True)
    name = String(32)
    tagtype = String(20)
    tagvalue = String(1000, required=True)


class OFXEXTENSION(List):
    """ OFX section 2.7.2 """
    memberTags = ('OFXELEMENT', )


class STATUS(Aggregate):
    """ OFX section 3.1.5 """
    code = Integer(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = String(255)


class BAL(Aggregate):
    """ OFX section 3.1.4 """
    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()
    currency = SubAggregate(CURRENCY)
