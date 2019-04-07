# coding: utf-8
"""
Investment accounts - OFX Section 13.6
"""
from ofxtools.Types import Bool, String, OneOf
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.common import SVCSTATUSES


__all__ = [
    "INVACCTTYPES",
    "USPRODUCTTYPES",
    "INVSUBACCTS",
    "INVACCTFROM",
    "INVACCTTO",
    "INVACCTINFO",
]


# Section 13.6.2
INVACCTTYPES = ("INDIVIDUAL", "JOINT", "TRUST", "CORPORATE")
# Section 13.6.2.1
USPRODUCTTYPES = (
    "401K", "403B", "IRA", "KEOGH", "OTHER", "SARSEP", "SIMPLE",
    "NORMAL", "TDA", "TRUST", "UGMA",
)
INVSUBACCTS = ("CASH", "MARGIN", "SHORT", "OTHER")


class INVACCTFROM(Aggregate):
    """ OFX section 13.6.1 """

    brokerid = String(22, required=True)
    acctid = String(22, required=True)


class INVACCTTO(Aggregate):
    """ OFX section 13.6.1 """

    brokerid = String(22, required=True)
    acctid = String(22, required=True)


class INVACCTINFO(Aggregate):
    """ OFX section 13.6.2 """

    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    usproducttype = OneOf(*USPRODUCTTYPES, required=True)
    checking = Bool(required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)
    invaccttype = OneOf(*INVACCTTYPES)
    optionlevel = String(40)
