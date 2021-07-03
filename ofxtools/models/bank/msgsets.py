# coding: utf-8
"""
Banking message sets
"""


__all__ = [
    "BANKMSGSRQV1",
    "BANKMSGSRSV1",
    "XFERPROF",
    "STPCHKPROF",
    "EMAILPROF",
    "BANKMSGSETV1",
    "BANKMSGSET",
    "CREDITCARDMSGSRQV1",
    "CREDITCARDMSGSRSV1",
    "CREDITCARDMSGSETV1",
    "CREDITCARDMSGSET",
    "INTERXFERMSGSRQV1",
    "INTERXFERMSGSRSV1",
    "INTERXFERMSGSETV1",
    "INTERXFERMSGSET",
    "WIREXFERMSGSRQV1",
    "WIREXFERMSGSRSV1",
    "WIREXFERMSGSETV1",
    "WIREXFERMSGSET",
]


# local imports
from ofxtools.Types import (
    Bool,
    OneOf,
    Integer,
    Decimal,
    Time,
    SubAggregate,
    ListAggregate,
    ListElement,
    Unsupported,
)
from ofxtools.models.base import Aggregate, ElementList
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.bank.stmt import (
    ACCTTYPES,
    STMTTRNRQ,
    STMTTRNRS,
    CCSTMTTRNRQ,
    CCSTMTTRNRS,
)
from ofxtools.models.bank.stmtend import (
    STMTENDTRNRQ,
    STMTENDTRNRS,
    CCSTMTENDTRNRQ,
    CCSTMTENDTRNRS,
)
from ofxtools.models.bank.stpchk import STPCHKTRNRQ, STPCHKTRNRS
from ofxtools.models.bank.xfer import INTRATRNRQ, INTRATRNRS
from ofxtools.models.bank.interxfer import INTERTRNRQ, INTERTRNRS
from ofxtools.models.bank.wire import WIRETRNRQ, WIRETRNRS
from ofxtools.models.bank.recur import (
    RECINTRATRNRQ,
    RECINTRATRNRS,
    RECINTERTRNRQ,
    RECINTERTRNRS,
)
from ofxtools.models.bank.sync import (
    INTRASYNCRQ,
    INTRASYNCRS,
    INTERSYNCRQ,
    INTERSYNCRS,
    WIRESYNCRQ,
    WIRESYNCRS,
    STPCHKSYNCRQ,
    STPCHKSYNCRS,
    RECINTRASYNCRQ,
    RECINTRASYNCRS,
    RECINTERSYNCRQ,
    RECINTERSYNCRS,
    BANKMAILSYNCRQ,
    BANKMAILSYNCRS,
)
from ofxtools.models.bank.mail import BANKMAILTRNRQ, BANKMAILTRNRS


DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


class BANKMSGSRQV1(Aggregate):
    """OFX section 11.13.1.1.1"""

    stmttrnrq = ListAggregate(STMTTRNRQ)
    stmtendtrnrq = ListAggregate(STMTENDTRNRQ)
    stpchktrnrq = ListAggregate(STPCHKTRNRQ)
    intratrnrq = ListAggregate(INTRATRNRQ)
    recintratrnrq = ListAggregate(RECINTRATRNRQ)
    bankmailtrnrq = ListAggregate(BANKMAILTRNRQ)
    stpchksyncrq = ListAggregate(STPCHKSYNCRQ)
    intrasyncrq = ListAggregate(INTRASYNCRQ)
    recintrasyncrq = ListAggregate(RECINTRASYNCRQ)
    bankmailsyncrq = ListAggregate(BANKMAILSYNCRQ)

    @property
    def statements(self):
        stmts = []
        for trnrq in self:
            stmtrq = None
            if isinstance(trnrq, STMTTRNRQ):
                stmtrq = trnrq.stmtrq
            elif isinstance(trnrq, STMTTRNRQ):
                stmtrq = trnrq.stmtendrq

            if stmtrq is not None:
                stmts.append(stmtrq)
        return stmts


class BANKMSGSRSV1(Aggregate):
    """OFX section 11.13.1.1.2"""

    stmttrnrs = ListAggregate(STMTTRNRS)
    stmtendtrnrs = ListAggregate(STMTENDTRNRS)
    stpchktrnrs = ListAggregate(STPCHKTRNRS)
    intratrnrs = ListAggregate(INTRATRNRS)
    recintratrnrs = ListAggregate(RECINTRATRNRS)
    bankmailtrnrs = ListAggregate(BANKMAILTRNRS)
    stpchksyncrs = ListAggregate(STPCHKSYNCRS)
    intrasyncrs = ListAggregate(INTRASYNCRS)
    recintrasyncrs = ListAggregate(RECINTRASYNCRS)
    bankmailsyncrs = ListAggregate(BANKMAILSYNCRS)

    @property
    def statements(self):
        stmts = []
        for trnrs in self:
            stmtrs = None
            if isinstance(trnrs, STMTTRNRS):
                stmtrs = trnrs.stmtrs
            elif isinstance(trnrs, STMTENDTRNRS):
                stmtrs = trnrs.stmtendrs

            if stmtrs is not None:
                # Staple wrapper TRNUID, CLTCOOKIE onto STMTRS for convenience
                stmtrs.trnuid = trnrs.trnuid
                stmtrs.cltcookie = trnrs.cltcookie
                stmts.append(stmtrs)
        return stmts


class XFERPROF(ElementList):
    """OFX section 11.13.2.2"""

    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    canrecur = Bool(required=True)
    canloan = Bool()
    canschedloan = Bool()
    canrecurloan = Bool()
    canmodxfers = Bool(required=True)
    canmodmdls = Bool(required=True)
    modelwnd = Integer(3, required=True)
    dayswith = Integer(3, required=True)
    dfltdaystopay = Integer(3, required=True)


class STPCHKPROF(ElementList):
    """OFX section 11.13.2.3"""

    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    canuserange = Bool(required=True)
    canusedesc = Bool(required=True)
    stpchkfee = Decimal(required=True)


class EMAILPROF(Aggregate):
    """OFX section 11.13.2.4"""

    canemail = Bool(required=True)
    cannotify = Bool(required=True)


class BANKMSGSETV1(ElementList):
    """OFX section 11.13.2.1"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    invalidaccttype = ListElement(OneOf(*ACCTTYPES))
    closingavail = Bool(required=True)
    pendingavail = Bool()
    xferprof = SubAggregate(XFERPROF)
    stpchkprof = SubAggregate(STPCHKPROF)
    emailprof = SubAggregate(EMAILPROF, required=True)
    imageprof = Unsupported()


class BANKMSGSET(Aggregate):
    """OFX section 7.3"""

    bankmsgsetv1 = SubAggregate(BANKMSGSETV1, required=True)


class CREDITCARDMSGSRQV1(Aggregate):
    """OFX section 11.13.1.1.1"""

    ccstmttrnrq = ListAggregate(CCSTMTTRNRQ)
    ccstmtendtrnrq = ListAggregate(CCSTMTENDTRNRQ)

    @property
    def statements(self):
        stmts = []
        for trnrq in self:
            stmtrq = None
            if isinstance(trnrq, CCSTMTTRNRQ):
                stmtrq = trnrq.ccstmtrq
            elif isinstance(trnrq, CCSTMTENDTRNRQ):
                stmtrq = trnrq.ccstmtendrq

            if stmtrq is not None:
                stmts.append(stmtrq)
        return stmts


class CREDITCARDMSGSRSV1(Aggregate):
    """OFX section 11.13.1.1.2"""

    ccstmttrnrs = ListAggregate(CCSTMTTRNRS)
    ccstmtendtrnrs = ListAggregate(CCSTMTENDTRNRS)

    @property
    def statements(self):
        stmts = []
        for trnrs in self:
            stmtrs = None
            if isinstance(trnrs, CCSTMTTRNRS):
                stmtrs = trnrs.ccstmtrs
            else:
                assert isinstance(trnrs, CCSTMTENDTRNRS)
                stmtrs = trnrs.ccstmtendrs

            if stmtrs is not None:
                # Staple wrapper TRNUID, CLTCOOKIE onto STMTRS for convenience
                stmtrs.trnuid = trnrs.trnuid
                stmtrs.cltcookie = trnrs.cltcookie
                stmts.append(stmtrs)
        return stmts


class CREDITCARDMSGSETV1(Aggregate):
    """OFX section 11.13.3"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    closingavail = Bool(required=True)
    pendingavail = Bool()
    imageprof = Unsupported()


class CREDITCARDMSGSET(Aggregate):
    """OFX section 11.13.3"""

    creditcardmsgsetv1 = SubAggregate(CREDITCARDMSGSETV1, required=True)


class INTERXFERMSGSRQV1(Aggregate):
    """OFX section 11.13.1.3.1"""

    intertrnrq = ListAggregate(INTERTRNRQ)
    recintertrnrq = ListAggregate(RECINTERTRNRQ)
    intersyncrq = ListAggregate(INTERSYNCRQ)
    recintersyncrq = ListAggregate(RECINTERSYNCRQ)


class INTERXFERMSGSRSV1(Aggregate):
    """OFX section 11.13.1.3.2"""

    intertrnrs = ListAggregate(INTERTRNRS)
    recintertrnrs = ListAggregate(RECINTERTRNRS)
    intersyncrs = ListAggregate(INTERSYNCRS)
    recintersyncrs = ListAggregate(RECINTERSYNCRS)


class INTERXFERMSGSETV1(Aggregate):
    """OFX section 11.13.4"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    xferprof = SubAggregate(XFERPROF, required=True)
    canbillpay = Bool(required=True)
    cancwnd = Integer(3, required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class INTERXFERMSGSET(Aggregate):
    """OFX section 11.13.4"""

    interxfermsgsetv1 = SubAggregate(INTERXFERMSGSETV1, required=True)


class WIREXFERMSGSRQV1(Aggregate):
    """OFX section 11.13.1.4.1"""

    wiretrnrq = ListAggregate(WIRETRNRQ)
    wiresyncrq = ListAggregate(WIRESYNCRQ)


class WIREXFERMSGSRSV1(Aggregate):
    """OFX section 11.13.1.4.2"""

    wiretrnrs = ListAggregate(WIRETRNRS)
    wiresyncrs = ListAggregate(WIRESYNCRS)


class WIREXFERMSGSETV1(ElementList):
    """OFX section 11.13.5"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class WIREXFERMSGSET(Aggregate):
    """OFX section 11.13.5"""

    wirexfermsgsetv1 = SubAggregate(WIREXFERMSGSETV1, required=True)
