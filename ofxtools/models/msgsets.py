# coding: utf-8
"""
OFX message sets
"""
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import Bool, String, OneOf, Integer, Decimal, DateTime, Time
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, List
from ofxtools.models.common import OFXEXTENSION
from ofxtools.models.i18n import LANG_CODES
from ofxtools.models.signon import SONRQ, SONRS
from ofxtools.models.bank.stmt import ACCTTYPES, STMTTRNRS
from ofxtools.models.invest.stmt import INVSTMTTRNRS
from ofxtools.models.invest.securities import SECLIST


__all__ = [
    "MSGSETCORE",
    "SIGNONMSGSRQV1",
    "SIGNONMSGSRSV1",
    "SIGNONMSGSETV1",
    "SIGNONMSGSET",
    "PROFMSGSRQV1",
    "PROFMSGSRSV1",
    "PROFMSGSETV1",
    "PROFMSGSET",
    "SIGNUPMSGSRQV1",
    "SIGNUPMSGSRSV1",
    "CLIENTENROLL",
    "WEBENROLL",
    "OTHERENROLL",
    "SIGNUPMSGSETV1",
    "SIGNUPMSGSET",
    "EMAILMSGSRQV1",
    "EMAILMSGSRSV1",
    "EMAILMSGSETV1",
    "EMAILMSGSET",
    "XFERPROF",
    "STPCHKPROF",
    "EMAILPROF",
    "BANKMSGSRQV1",
    "BANKMSGSRSV1",
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
    "INVSTMTMSGSRQV1",
    "INVSTMTMSGSRSV1",
    "INVSTMTMSGSETV1",
    "INVSTMTMSGSET",
    "SECLISTMSGSRQV1",
    "SECLISTMSGSRSV1",
    "SECLISTMSGSETV1",
    "SECLISTMSGSET",
    "TAX1099MSGSETV1", "TAX1099MSGSET",
]


class MSGSETCORE(Aggregate):
    """ OFX section 7.2.1 """

    ver = Integer(required=True)
    url = String(255, required=True)
    ofxsec = OneOf("NONE", "TYPE1", required=True)
    transpsec = Bool(required=True)
    signonrealm = String(32, required=True)
    language = OneOf(*LANG_CODES, required=True)
    syncmode = OneOf("FULL", "LITE", required=True)
    refreshsupt = Bool()
    respfileer = Bool(required=True)
    spname = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)

    @staticmethod
    def groom(elem):
        """
        Remove proprietary tags e.g. INTU.XXX
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        for child in set(elem):
            if "." in child.tag:
                elem.remove(child)

        return super(MSGSETCORE, MSGSETCORE).groom(elem)


class SIGNONMSGSRQV1(Aggregate):
    """ """

    sonrq = SubAggregate(SONRQ)


class SIGNONMSGSRSV1(Aggregate):
    """ """

    sonrs = SubAggregate(SONRS)


class SIGNONMSGSETV1(Aggregate):
    """ OFX section 2.5.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class SIGNONMSGSET(Aggregate):
    """ OFX section 2.5.5 """

    signonmsgsetv1 = SubAggregate(SIGNONMSGSETV1, required=True)


class PROFMSGSRQV1(List):
    dataTags = ["PROFTRNRQ"]


class PROFMSGSRSV1(List):
    dataTags = ["PROFTRNRS"]


class PROFMSGSETV1(Aggregate):
    """ OFX section 7.3 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class PROFMSGSET(Aggregate):
    """ OFX section 7.3 """

    profmsgsetv1 = SubAggregate(PROFMSGSETV1, required=True)


class SIGNUPMSGSRQV1(List):
    """ OFX section 8.1 """

    dataTags = ["ENROLLTRNRQ", "ACCTINFOTRNRQ", "ACCTTRNRQ", "CHGUSERINFOTRNRQ"]


class SIGNUPMSGSRSV1(List):
    """ OFX section 8.1 """

    dataTags = ["ENROLLTRNRS", "ACCTINFOTRNRS", "ACCTTRNRS", "CHGUSERINFOTRNRS"]


class CLIENTENROLL(Aggregate):
    """ OFX section 8.8 """

    acctrequired = Bool(required=True)


class WEBENROLL(Aggregate):
    """ OFX section 8.8 """

    url = String(255, required=True)


class OTHERENROLL(Aggregate):
    """ OFX section 8.8 """

    message = String(80, required=True)


class SIGNUPMSGSETV1(Aggregate):
    """ OFX section 8.8 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    clientenroll = SubAggregate(CLIENTENROLL)
    webenroll = SubAggregate(WEBENROLL)
    otherenroll = SubAggregate(OTHERENROLL)
    chguserinfo = Bool(required=True)
    availaccts = Bool(required=True)
    clientactreq = Bool(required=True)

    optionalMutexes = [
        ("clientenroll", "webenroll"),
        ("clientenroll", "otherenroll"),
        ("webenroll", "otherenroll"),
    ]


class SIGNUPMSGSET(Aggregate):
    """ OFX section 8.8 """

    signupmsgsetv1 = SubAggregate(SIGNUPMSGSETV1, required=True)


class EMAILMSGSRQV1(List):
    """ OFX section 9.4.1.1 """

    dataTags = ["MAILTRNRQ", "GETMIMETRNRQ", "MAILSYNCRQ"]


class EMAILMSGSRSV1(List):
    """ OFX section 9.4.1.2 """

    dataTags = ["MAILTRNRS", "GETMIMETRNRS", "MAILSYNCRS"]


class EMAILMSGSETV1(Aggregate):
    """ OFX section 9.4.2 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    mailsup = Bool(required=True)
    getmimesup = Bool(required=True)


class EMAILMSGSET(Aggregate):
    """ OFX section 9.4.2 """

    emailmsgsetv1 = SubAggregate(EMAILMSGSETV1, required=True)

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


class INTERXFERMSGSRQV1(List):
    """ OFX section 11.13.1.3.1 """

    dataTags = ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]


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

    dataTags = ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]


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


class INVSTMTMSGSRQV1(List):
    """ OFX section 13.7.1.2.1 """

    dataTags = ["INVSTMTTRNRQ", "INVMAILTRNRQ", "INVMAILSYNCRQ"]


class INVSTMTMSGSRSV1(List):
    """ OFX section 13.7.1.2.2 """

    dataTags = ["INVSTMTTRNRS", "INVMAILTRNRS", "INVMAILSYNCRS"]

    @property
    def statements(self):
        stmts = []
        for rs in self:
            if isinstance(rs, INVSTMTTRNRS):
                stmtrs = rs.invstmtrs
                if stmtrs is not None:
                    stmts.append(stmtrs)
        return stmts


class INVSTMTMSGSETV1(Aggregate):
    """ OFX section 13.7.1.1 """

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
    """ OFX section 13.7.1.1 """

    invstmtmsgsetv1 = SubAggregate(INVSTMTMSGSETV1, required=True)


class SECLISTMSGSRQV1(List):
    """ OFX section 13.7.2.2.1 """

    dataTags = ["SECLISTTRNRQ"]


class SECLISTMSGSRSV1(List):
    """ OFX section 13.7.2.2.2 """

    # N.B. this part of the spec is unusual in that SECLIST is a direct
    # child of SECLISTMSGSRSV1, unwrapped.  SECLISTRS, wrapped in SECLISTTRNS,
    # is an empty aggregate; including SECLISTTRNRS/SECLISTRS under
    # SECLISTMSGSTSV1 merely indicates that the accompanying SECLIST was
    # generated in response to a client SECLISTRQ.
    dataTags = ["SECLISTTRNRS", "SECLIST"]

    @property
    def securities(self):
        securities = []
        for child in self:
            if isinstance(child, SECLIST):
                securities.extend(child)
        return securities


class SECLISTMSGSETV1(Aggregate):
    """ OFX section 13.7.2.1 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    seclistrqdnld = Bool(required=True)


class SECLISTMSGSET(Aggregate):
    """ OFX section 13.7.2.1 """

    seclistmsgsetv1 = SubAggregate(SECLISTMSGSETV1, required=True)


class TAX1099MSGSETV1(Aggregate):
    """ OFX tax extensions section 2.1 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    tax1099dnld = Bool(required=True)
    extd1099b = Bool(required=True)
    taxyearsupported = Integer(required=True)


class TAX1099MSGSET(Aggregate):
    """ OFX tax extensions section 2.1 """

    tax1099msgsetv1 = SubAggregate(TAX1099MSGSETV1, required=True)
