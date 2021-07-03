# coding: utf-8
"""
Bill pay message sets
"""


__all__ = [
    "INVSTMTMSGSRQV1",
    "INVSTMTMSGSRSV1",
    "INVSTMTMSGSETV1",
    "INVSTMTMSGSET",
    "SECLISTMSGSRQV1",
    "SECLISTMSGSRSV1",
    "SECLISTMSGSETV1",
    "SECLISTMSGSET",
]


# local imports
from ofxtools.Types import Bool, SubAggregate, ListAggregate, Unsupported
from ofxtools.models.base import Aggregate
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.invest.stmt import INVSTMTTRNRQ, INVSTMTTRNRS
from ofxtools.models.invest.mail import (
    INVMAILTRNRQ,
    INVMAILTRNRS,
    INVMAILSYNCRQ,
    INVMAILSYNCRS,
)
from ofxtools.models.invest.securities import SECLIST, SECLISTTRNRQ, SECLISTTRNRS


class INVSTMTMSGSRQV1(Aggregate):
    """OFX section 13.7.1.2.1"""

    invstmttrnrq = ListAggregate(INVSTMTTRNRQ)
    invmailtrnrq = ListAggregate(INVMAILTRNRQ)
    invmailsyncrq = ListAggregate(INVMAILSYNCRQ)

    @property
    def statements(self):
        stmts = []
        for trnrq in self:
            if isinstance(trnrq, INVSTMTTRNRQ):
                stmtrq = trnrq.invstmtrq
                if stmtrq is not None:
                    stmts.append(stmtrq)
        return stmts


class INVSTMTMSGSRSV1(Aggregate):
    """OFX section 13.7.1.2.2"""

    invstmttrnrs = ListAggregate(INVSTMTTRNRS)
    invmailtrnrs = ListAggregate(INVMAILTRNRS)
    invmailsyncrs = ListAggregate(INVMAILSYNCRS)

    @property
    def statements(self):
        stmts = []
        for trnrs in self:
            if isinstance(trnrs, INVSTMTTRNRS):
                stmtrs = trnrs.invstmtrs
                if stmtrs is not None:
                    # Staple wrapper TRNUID, CLTCOOKIE onto STMTRS for convenience
                    stmtrs.trnuid = trnrs.trnuid
                    stmtrs.cltcookie = trnrs.cltcookie
                    stmts.append(stmtrs)
        return stmts


class INVSTMTMSGSETV1(Aggregate):
    """OFX section 13.7.1.1"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    trandnld = Bool(required=True)
    oodnld = Bool(required=True)
    posdnld = Bool(required=True)
    baldnld = Bool(required=True)
    canemail = Bool(required=True)
    inv401kdnld = Bool()
    closingavail = Bool()
    imageprof = Unsupported()


class INVSTMTMSGSET(Aggregate):
    """OFX section 13.7.1.1"""

    invstmtmsgsetv1 = SubAggregate(INVSTMTMSGSETV1, required=True)


class SECLISTMSGSRQV1(Aggregate):
    """OFX section 13.7.2.2.1"""

    seclisttrnrq = ListAggregate(SECLISTTRNRQ)


class SECLISTMSGSRSV1(Aggregate):
    """OFX section 13.7.2.2.2"""

    # N.B. this part of the spec is unusual in that SECLIST is a direct
    # child of SECLISTMSGSRSV1, unwrapped.  SECLISTRS, wrapped in SECLISTTRNS,
    # is an empty aggregate; including SECLISTTRNRS/SECLISTRS under
    # SECLISTMSGSTSV1 merely indicates that the accompanying SECLIST was
    # generated in response to a client SECLISTRQ.
    seclisttrnrs = ListAggregate(SECLISTTRNRS)
    seclist = ListAggregate(SECLIST)

    @property
    def securities(self):
        securities = []
        for child in self:
            if isinstance(child, SECLIST):
                securities.extend(child)
        return securities


class SECLISTMSGSETV1(Aggregate):
    """OFX section 13.7.2.1"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    seclistrqdnld = Bool(required=True)


class SECLISTMSGSET(Aggregate):
    """OFX section 13.7.2.1"""

    seclistmsgsetv1 = SubAggregate(SECLISTMSGSETV1, required=True)
