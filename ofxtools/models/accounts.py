# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import Aggregate, ACCTTYPES
from ofxtools.Types import (
    String,
    OneOf,
)


class ACCTFROM(Aggregate):
    """ Base class (not in OFX spec) for *ACCTFROM/*ACCTTO """
    acctid = String(22, required=True)


class BANKACCTFROM(ACCTFROM):
    """ OFX section 11.3.1 """
    bankid = String(9, required=True)
    branchid = String(22)
    accttype = OneOf(*ACCTTYPES,
                     required=True)
    acctkey = String(22)


class BANKACCTTO(BANKACCTFROM):
    """ OFX section 11.3.1 """
    pass


class CCACCTFROM(ACCTFROM):
    """ OFX section 11.3.2 """
    acctkey = String(22)


class CCACCTTO(CCACCTFROM):
    """ OFX section 11.3.2 """
    pass


class INVACCTFROM(ACCTFROM):
    """ """
    brokerid = String(22, required=True)
