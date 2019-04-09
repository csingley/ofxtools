# coding: utf-8
"""
Tax form 1099 - work in progress
"""
# local imports
from ofxtools.Types import Bool, Integer
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.common import MSGSETCORE


__all__ = ["TAX1099MSGSETV1", "TAX1099MSGSET"]


class TAX1099MSGSETV1(Aggregate):
    """ OFX tax extensions section 2.1 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    tax1099dnld = Bool(required=True)
    extd1099b = Bool(required=True)
    taxyearsupported = Integer(required=True)


class TAX1099MSGSET(Aggregate):
    """ OFX tax extensions section 2.1 """

    tax1099msgsetv1 = SubAggregate(TAX1099MSGSETV1, required=True)
