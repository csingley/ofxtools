# coding: utf-8
"""
Message set response aggregates (i.e. *MSGSRSV1) - OFX section 2.4.5
"""
# local imports
from ofxtools.models import (
    Aggregate,
    List,
)


class SIGNONMSGSRSV1(Aggregate):
    """ """
    _subaggregates = ('SONRS',)


class SECLISTMSGSRSV1(Aggregate):
    """ """
    _subaggregates = ('SECLIST',)


class BANKMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    _unsupported = ('STMTENDTRNRS', 'SPCHKTRNRS', 'INTRATRNRS',
                    'RECINTRATRNRS', 'BANKMAILTRNRS', 'STPCHKSYNCRS',
                    'INTRASYNCRS', 'RECINTRASYNCRS', 'BANKMAILSYNCRS',)


class CREDITCARDMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    _unsupported = ('CCSTMTENDTRNRS',)


class INVSTMTMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    _unsupported = ('INVMAILTRNRS', 'INVMAILSYNCRS', 'INVSTMTENDTRNRS',)
