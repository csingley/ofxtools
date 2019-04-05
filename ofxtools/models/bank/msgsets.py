# coding: utf-8
"""
Message sets and profile - OFX Section 11.13
"""
# local imports
from ofxtools.Types import Decimal, Integer, OneOf, Bool, Time
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, List
from ofxtools.models.profile import MSGSETCORE
from ofxtools.models.bank.stmt import ACCTTYPES, STMTTRNRS


__all__ = [
    "XFERPROF", "STPCHKPROF", "EMAILPROF",
    "BANKMSGSRQV1", "BANKMSGSRSV1", "BANKMSGSETV1", "BANKMSGSET",
    "CREDITCARDMSGSRQV1", "CREDITCARDMSGSRSV1", "CREDITCARDMSGSETV1", "CREDITCARDMSGSET",
    "INTERXFERMSGSRQV1", "INTERXFERMSGSRSV1", "INTERXFERMSGSETV1", "INTERXFERMSGSET",
    "WIREXFERMSGSRQV1", "WIREXFERMSGSRSV1", "WIREXFERMSGSETV1", "WIREXFERMSGSET",
]


class XFERPROF(Aggregate):
    """ OFX section 11.13.2.2 """

    # FIXME
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PROCDAYSOFF.
    procdaysoff = Unsupported()
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    canrecur = Bool(required=True)
    canmodxfer = Bool(required=True)
    canmodmdls = Bool(required=True)
    modelwnd = Integer(3, required=True)
    dayswith = Integer(3, required=True)
    dfldaystopay = Integer(3, required=True)


class STPCHKPROF(Aggregate):
    """ OFX section 11.13.2.3 """

    # FIXME
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PROCDAYSOFF.
    procdaysoff = Unsupported()
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


class BANKMSGSRQV1(List):
    """ OFX section 11.13.1.1.1 """

    dataTags = [
        "STMTTRNRQ",
        "STMTENDTRNRQ",
        "STPCHKTRNRQ",
        "STPCHKSYNCRQ",
        "INTRATRNRQ",
        "INTRASYNCRQ",
        "RECINTRATRNRQ",
        "RECINTRASYNCRQ",
        "BANKMAILTRNRQ",
        "BANKMAILSYNCRQ",
    ]


class BANKMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """

    dataTags = [
        "STMTTRNRS",
        "STMTENDTRNRS",
        "STPCHKTRNRS",
        "STPCHKSYNCRS",
        "INTRATRNRS",
        "INTRASYNCRS",
        "RECINTRATRNRS",
        "RECINTRASYNCRS",
        "BANKMAILTRNRS",
        "BANKMAILSYNCRS",
    ]

    @property
    def statements(self):
        stmts = []
        for rs in self:
            if isinstance(rs, STMTTRNRS):
                stmtrs = rs.stmtrs
                if stmtrs is not None:
                    stmts.append(stmtrs)
        return stmts


class BANKMSGSET(Aggregate):
    """ OFX section 7.3 """

    bankmsgsetv1 = SubAggregate(BANKMSGSETV1, required=True)


class INTERXFERMSGSRQV1(List):
    """ OFX section 11.13.1.3.1 """

    dataTags = [
        "INTERTRNRQ",
        "RECINTERTRNRQ",
        "INTERSYNCRQ",
        "RECINTERSYNCRQ",
    ]


class CREDITCARDMSGSRQV1(List):
    """ OFX section 11.13.1.1.1 """

    dataTags = ["CCSTMTTRNRQ", "CCSTMTENDTRNRQ"]


class CREDITCARDMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """

    dataTags = ["CCSTMTTRNRS", "CCSTMTENDTRNRS"]

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

class INTERXFERMSGSRSV1(List):
    """ OFX section 11.13.1.3.2 """

    dataTags = [
        "INTERTRNRS",
        "RECINTERTRNRS",
        "INTERSYNCRS",
        "RECINTERSYNCRS",
    ]


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


class WIREXFERMSGSRQV1(List):
    """ OFX section 11.13.1.4.1 """

    dataTags = ["WIRETRNRQ", "WIRESYNCRQ"]


class WIREXFERMSGSRSV1(List):
    """ OFX section 11.13.1.4.2 """

    dataTags = ["WIRETRNRS", "WIRESYNCRS"]


class WIREXFERMSGSETV1(Aggregate):
    """ OFX section 11.13.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    # FIXME
    # Need to define an Aggregate subclass that support multiple repeated
    # Elements (not just SubAggregates, like List) for PROCDAYSOFF.
    procdaysoff = Unsupported()
    procendtm = Time(required=True)
    cansched = Bool(required=True)
    domxferfee = Decimal(required=True)
    intlxferfee = Decimal(required=True)


class WIREXFERMSGSET(Aggregate):
    """ OFX section 11.13.5 """

    wirexfermsgsetv1 = SubAggregate(WIREXFERMSGSETV1, required=True)
