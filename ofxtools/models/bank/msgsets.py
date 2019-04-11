# coding: utf-8
"""
Banking message sets
"""
# local imports
from ofxtools.Types import Bool, OneOf, Integer, Decimal, Time, ListItem, ListElement
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, ElementList
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.bank.stmt import (
    ACCTTYPES, STMTTRNRQ, STMTTRNRS, CCSTMTTRNRQ, CCSTMTTRNRS,
)
from ofxtools.models.bank.stmtend import STMTENDTRNRQ, STMTENDTRNRS
from ofxtools.models.bank.stpchk import STPCHKTRNRQ, STPCHKTRNRS
from ofxtools.models.bank.xfer import INTRATRNRQ, INTRATRNRS
from ofxtools.models.bank.interxfer import INTERTRNRQ, INTERTRNRS
from ofxtools.models.bank.wire import WIRETRNRQ, WIRETRNRS
from ofxtools.models.bank.recur import (
    RECINTRATRNRQ, RECINTRATRNRS, RECINTERTRNRQ, RECINTERTRNRS,
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


DAYS = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")


class BANKMSGSRQV1(Aggregate):
    """ OFX section 11.13.1.1.1 """

    stmttrnrq = ListItem(STMTTRNRQ)
    stmtendtrnrq = ListItem(STMTENDTRNRQ)
    stpchktrnrq = ListItem(STPCHKTRNRQ)
    intratrnrq = ListItem(INTRATRNRQ)
    recintratrnrq = ListItem(RECINTRATRNRQ)
    bankmailtrnrq = ListItem(BANKMAILTRNRQ)
    stpchksyncrq = ListItem(STPCHKSYNCRQ)
    intrasyncrq = ListItem(INTRASYNCRQ)
    recintrasyncrq = ListItem(RECINTRASYNCRQ)
    bankmailsyncrq = ListItem(BANKMAILSYNCRQ)


class BANKMSGSRSV1(Aggregate):
    """ OFX section 11.13.1.1.2 """

    stmttrnrs = ListItem(STMTTRNRS)
    stmtendtrnrs = ListItem(STMTENDTRNRS)
    stpchktrnrs = ListItem(STPCHKTRNRS)
    intratrnrs = ListItem(INTRATRNRS)
    recintratrnrs = ListItem(RECINTRATRNRS)
    bankmailtrnrs = ListItem(BANKMAILTRNRS)
    stpchksyncrs = ListItem(STPCHKSYNCRS)
    intrasyncrs = ListItem(INTRASYNCRS)
    recintrasyncrs = ListItem(RECINTRASYNCRS)
    bankmailsyncrs = ListItem(BANKMAILSYNCRS)

    @property
    def statements(self):
        stmts = []
        for rs in self:
            if isinstance(rs, STMTTRNRS):
                stmtrs = rs.stmtrs
                if stmtrs is not None:
                    stmts.append(stmtrs)
        return stmts


class XFERPROF(ElementList):
    """ OFX section 11.13.2.2 """

    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    canrecur = Bool(required=True)
    canmodxfer = Bool(required=True)
    canmodmdls = Bool(required=True)
    modelwnd = Integer(3, required=True)
    dayswith = Integer(3, required=True)
    dfltdaystopay = Integer(3, required=True)


class STPCHKPROF(ElementList):
    """ OFX section 11.13.2.3 """

    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    canuserange = Bool(required=True)
    canusedesc = Bool(required=True)
    stpchkfee = Decimal(required=True)


class EMAILPROF(Aggregate):
    """ OFX section 11.13.2.4 """

    canemail = Bool(required=True)
    cannotify = Bool(required=True)


class BANKMSGSETV1(Aggregate):
    """ OFX section 11.13.2.1 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    invalidaccttype = OneOf(*ACCTTYPES)
    closingavail = Bool(required=True)
    pendingavail = Bool()
    xferprof = SubAggregate(XFERPROF)
    stpchkprof = SubAggregate(STPCHKPROF)
    emailprof = SubAggregate(EMAILPROF, required=True)
    imageprof = Unsupported()


class BANKMSGSET(Aggregate):
    """ OFX section 7.3 """

    bankmsgsetv1 = SubAggregate(BANKMSGSETV1, required=True)


class CREDITCARDMSGSRQV1(Aggregate):
    """ OFX section 11.13.1.1.1 """

    ccstmttrnrq = ListItem(CCSTMTTRNRQ)
    ccstmtendtrnrq = ListItem(CCSTMTTRNRQ)


class CREDITCARDMSGSRSV1(Aggregate):
    """ OFX section 11.13.1.1.2 """

    ccstmttrnrs = ListItem(CCSTMTTRNRS)
    ccstmtendtrnrs = ListItem(CCSTMTTRNRS)

    @property
    def statements(self):
        return [trnrs.statement for trnrs in self]


class CREDITCARDMSGSETV1(Aggregate):
    """ OFX section 11.13.3 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    closingavail = Bool(required=True)
    pendingavail = Bool()
    imageprof = Unsupported()


class CREDITCARDMSGSET(Aggregate):
    """ OFX section 11.13.3 """

    creditcardmsgsetv1 = SubAggregate(CREDITCARDMSGSETV1, required=True)


class INTERXFERMSGSRQV1(Aggregate):
    """ OFX section 11.13.1.3.1 """
    intertrnrq = ListItem(INTERTRNRQ)
    recintertrnrq = ListItem(RECINTERTRNRQ)
    intersyncrq = ListItem(INTERSYNCRQ)
    recintersyncrq = ListItem(RECINTERSYNCRQ)


class INTERXFERMSGSRSV1(Aggregate):
    """ OFX section 11.13.1.3.2 """

    intertrnrs = ListItem(INTERTRNRS)
    recintertrnrs = ListItem(RECINTERTRNRS)
    intersyncrs = ListItem(INTERSYNCRS)
    recintersyncrs = ListItem(RECINTERSYNCRS)


class INTERXFERMSGSETV1(Aggregate):
    """ OFX section 11.13.4 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    xferprof = SubAggregate(XFERPROF, required=True)
    canbillpay = Bool(required=True)
    cancwnd = Integer(3, required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class INTERXFERMSGSET(Aggregate):
    """ OFX section 11.13.4 """

    interxfermsgsetv1 = SubAggregate(INTERXFERMSGSETV1, required=True)


class WIREXFERMSGSRQV1(Aggregate):
    """ OFX section 11.13.1.4.1 """

    wiretrnrq = ListItem(WIRETRNRQ)
    wiresyncrq = ListItem(WIRESYNCRQ)


class WIREXFERMSGSRSV1(Aggregate):
    """ OFX section 11.13.1.4.2 """

    wiretrnrs = ListItem(WIRETRNRS)
    wiresyncrs = ListItem(WIRESYNCRS)


class WIREXFERMSGSETV1(ElementList):
    """ OFX section 11.13.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    procdaysoff = ListElement(OneOf(*DAYS))
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class WIREXFERMSGSET(Aggregate):
    """ OFX section 11.13.5 """

    wirexfermsgsetv1 = SubAggregate(WIREXFERMSGSETV1, required=True)
