# coding: utf-8
"""
Data structures for bank download - OFX Section 11
"""
# local imports
from ofxtools.Types import String, NagString, Decimal, Integer, OneOf, DateTime, Bool, Time
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported, List
from ofxtools.models.common import (
    MSGSETCORE,
    SVCSTATUSES,
    TrnRq,
    TrnRs,
    TranList,
    SyncRqList,
    SyncRsList,
)
from ofxtools.models.i18n import (
    CURRENCY,
    ORIGCURRENCY,
    Origcurrency,
    CURRENCY_CODES,
    COUNTRY_CODES,
)
from ofxtools.models.email import MAIL


__all__ = [
    "INV401KSOURCES", "ACCTTYPES", "TRNTYPES", "FREQUENCIES",
    "BANKACCTFROM", "BANKACCTTO", "BANKACCTINFO",
    "CCACCTFROM", "CCACCTTO", "CCACCTINFO",
    "INCTRAN", "PAYEE", "LEDGERBAL", "AVAILBAL", "BALLIST",
    "STMTTRN", "BANKTRANLIST", "STMTRQ", "STMTRS", "STMTTRNRQ", "STMTTRNRS",
    "CLOSING", "STMTENDRQ", "STMTENDRS", "STMTENDTRNRQ", "STMTENDTRNRS",
    "CHKRANGE", "CHKDESC", "STPCHKNUM", "STPCHKRQ", "STPCHKRS",
    "STPCHKTRNRQ", "STPCHKTRNRS", "STPCHKSYNCRQ", "STPCHKSYNCRS",
    "XFERINFO", "XFERPRCSTS", "INTRARQ", "INTRARS",
    "INTRAMODRQ", "INTRACANRQ", "INTRAMODRS", "INTRACANRS",
    "INTRATRNRQ", "INTRATRNRS", "INTRASYNCRQ", "INTRASYNCRS",
    "RECURRINST", "RECINTRARQ", "RECINTRARS",
    "RECINTRAMODRQ", "RECINTRAMODRS", "RECINTRACANRQ", "RECINTRACANRS",
    "RECINTRATRNRQ", "RECINTRATRNRS", "RECINTRASYNCRQ", "RECINTRASYNCRS",
    "BANKMAILRQ", "BANKMAILRS", "DEPMAILRS", "CHKMAILRS",
    "BANKMAILTRNRQ", "BANKMAILTRNRS", "BANKMAILSYNCRQ", "BANKMAILSYNCRS",
    "XFERPROF", "STPCHKPROF", "EMAILPROF",
    "BANKMSGSRQV1", "BANKMSGSRSV1", "BANKMSGSETV1", "BANKMSGSET",
]


# Enums used in aggregate validation
INV401KSOURCES = (
    "PRETAX", "AFTERTAX", "MATCH", "PROFITSHARING", "ROLLOVER", "OTHERVEST", "OTHERNONVEST",
)
# OFX section 11.3.1.1
ACCTTYPES = ("CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD")
TRNTYPES = (
    "CREDIT", "DEBIT", "INT", "DIV", "FEE", "SRVCHG", "DEP", "ATM", "POS",
    "XFER", "CHECK", "PAYMENT", "CASH", "DIRECTDEP", "DIRECTDEBIT", "REPEATPMT",
    "OTHER",
)
FREQUENCIES = (
    "WEEKLY", "BIWEEKLY", "TWICEMONTHLY", "MONTHLY", "FOURWEEKS", "BIMONTHLY",
    "QUARTERLY", "SEMIANNUALLY", "ANNUALLY",
)


class BANKACCTFROM(Aggregate):
    """ OFX section 11.3.1 """

    bankid = String(9, required=True)
    branchid = String(22)
    acctid = String(22, required=True)
    accttype = OneOf(*ACCTTYPES, required=True)
    acctkey = String(22)


class BANKACCTTO(Aggregate):
    """ OFX section 11.3.1 """

    bankid = String(9, required=True)
    branchid = String(22)
    acctid = String(22, required=True)
    accttype = OneOf(*ACCTTYPES, required=True)
    acctkey = String(22)


class BANKACCTINFO(Aggregate):
    """ OFX section 11.3.3 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    suptxdl = Bool(required=True)
    xfersrc = Bool(required=True)
    xferdest = Bool(required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


# CCACCTFROM/CCACCTTO are defined here rather than models.creditcard
# in order to avoid recursive imports.
class CCACCTFROM(Aggregate):
    """ OFX section 11.3.2 """

    acctid = String(22, required=True)
    acctkey = String(22)


class CCACCTTO(Aggregate):
    """ OFX section 11.3.2 """

    acctid = String(22, required=True)
    acctkey = String(22)


class CCACCTINFO(Aggregate):
    """ OFX section 11.3.4 """

    ccacctfrom = SubAggregate(CCACCTFROM, required=True)
    suptxdl = Bool(required=True)
    xfersrc = Bool(required=True)
    xferdest = Bool(required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)


class INCTRAN(Aggregate):
    """ OFX section 11.4.2.1 """

    dtstart = DateTime()
    dtend = DateTime()
    include = Bool(required=True)


class STMTRQ(Aggregate):
    """ OFX section 11.4.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    includepending = Bool()
    inctranimg = Bool()


class PAYEE(Aggregate):
    """ OFX section 12.5.2.1 """

    name = NagString(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32, required=True)


class STMTTRN(Aggregate, Origcurrency):
    """ OFX section 11.4.3 """

    trntype = OneOf(*TRNTYPES, required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    fitid = String(255, required=True)
    correctfitid = String(255)
    correctaction = OneOf("REPLACE", "DELETE")
    srvrtid = String(10)
    checknum = String(12)
    refnum = String(32)
    sic = Integer()
    payeeid = String(12)
    name = String(32)
    payee = SubAggregate(PAYEE)
    extdname = String(100)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    memo = String(255)
    imagedata = Unsupported()
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)
    inv401ksource = OneOf(*INV401KSOURCES)

    optionalMutexes = [
        ("name", "payee"),
        ("ccacctto", "bankacctto"),
        ("currency", "origcurrency"),
    ]


class BANKTRANLIST(TranList):
    """ OFX section 11.4.2.2 """

    dataTags = ["STMTTRN"]


class LEDGERBAL(Aggregate):
    """ OFX section 11.4.2.2 """

    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class AVAILBAL(Aggregate):
    """ OFX section 11.4.2.2 """

    balamt = Decimal(required=True)
    dtasof = DateTime(required=True)


class BALLIST(List):
    """ OFX section 11.4.2.2 & 13.9.2.7 """

    dataTags = ["BAL"]


class STMTRS(Aggregate):
    """ OFX section 11.4.2.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    banktranlist = SubAggregate(BANKTRANLIST)
    banktranlistp = Unsupported()
    ledgerbal = SubAggregate(LEDGERBAL, required=True)
    availbal = SubAggregate(AVAILBAL)
    cashadvbalamt = Decimal()
    intrate = Decimal()
    ballist = SubAggregate(BALLIST)
    mktginfo = String(360)

    @property
    def account(self):
        return self.bankacctfrom

    @property
    def transactions(self):
        return self.banktranlist

    @property
    def balance(self):
        return self.ledgerbal


class STMTTRNRQ(TrnRq):
    """ OFX section 11.4.2.1 """

    stmtrq = SubAggregate(STMTRQ, required=True)


class STMTTRNRS(TrnRs):
    """ OFX section 11.4.2.2 """

    stmtrs = SubAggregate(STMTRS)

    @property
    def statement(self):
        return self.stmtrs


class CLOSING(Aggregate, Origcurrency):
    """ OFX section 11.5.2 """

    fitid = String(255, required=True)
    dtopen = DateTime()
    dtclose = DateTime(required=True)
    dtnext = DateTime()
    balopen = Decimal()
    balclose = Decimal(required=True)
    balmin = Decimal()
    depandcredit = Decimal()
    chkanddebit = Decimal()
    totalfees = Decimal()
    totalint = Decimal()
    dtpoststart = DateTime(required=True)
    dtpostend = DateTime(required=True)
    mktginfo = String(360)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)


class STMTENDRQ(Aggregate):
    """ OFX section 11.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    dtstart = DateTime()
    dtend = DateTime()


class STMTENDRS(List):
    """ OFX section 11.5.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["CLOSING"]


class STMTENDTRNRQ(TrnRq):
    """ OFX section 11.5.1 """

    stmtendrq = SubAggregate(STMTENDRQ, required=True)


class STMTENDTRNRS(TrnRs):
    """ OFX section 11.5.2 """

    stmtendrs = SubAggregate(STMTENDRS)


class CHKRANGE(Aggregate):
    """ OFX section 11.6.1.1.1 """

    chknumstart = String(12, required=True)
    chknumend = String(12)


class CHKDESC(Aggregate):
    """ OFX section 11.6.1.1.2 """

    name = String(32, required=True)
    chknum = String(12)
    dtuser = DateTime()
    trnamt = Decimal()


class STPCHKRQ(Aggregate):
    """ OFX section 11.6.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    chkrange = SubAggregate(CHKRANGE)
    chkdesc = SubAggregate(CHKDESC)

    requiredMutexes = [("chkrange", "chkdesc")]


class STPCHKNUM(Aggregate, Origcurrency):
    """ OFX section 11.6.1.2.1 """

    checknum = String(12, required=True)
    name = String(32)
    dtuser = DateTime()
    trnamt = Decimal()
    chkstatus = OneOf("0", "1", "100", "101", required=True)
    chkerror = String(255)
    currency = SubAggregate(CURRENCY)
    origcurrency = SubAggregate(ORIGCURRENCY)

    optionalMutexes = [("currency", "origcurrency")]


class STPCHKRS(List):
    """ OFX section 11.6.1.1 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    fee = Decimal(required=True)
    feemsg = String(80, required=True)

    dataTags = ["STPCHKNUM"]


class STPCHKTRNRQ(TrnRq):
    """ OFX section 11.6.1.1 """

    stpchkrq = SubAggregate(STPCHKRQ, required=True)


class STPCHKTRNRS(TrnRs):
    """ OFX section 11.6.1.2 """

    stpchkrs = SubAggregate(STPCHKRS)


class STPCHKSYNCRQ(SyncRqList):
    """ OFX section 11.12.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRQ"]


class STPCHKSYNCRS(SyncRsList):
    """ OFX section 11.12.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)

    dataTags = ["STPCHKTRNRS"]


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


class XFERINFO(Aggregate):
    """ OFX section 11.3.5 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    trnamt = Decimal(required=True)
    dtdue = DateTime()

    requiredMutexes = [("bankacctfrom", "ccacctfrom"), ("bankacctto", "ccacctto")]


class INTRARQ(Aggregate):
    """ OFX section 11.7.1.1 """

    xferinfo = SubAggregate(XFERINFO, required=True)


class XFERPRCSTS(Aggregate):
    """ OFX section 11.3.6 """

    xferprccode = OneOf(
        "WILLPROCESSON",
        "POSTEDON",
        "NOFUNDSON",
        "CANCELEDON",
        "FAILEDON",
        required=True,
    )
    dtxferprc = DateTime(required=True)


class INTRARS(Aggregate):
    """ OFX section 11.7.1.2 """

    curdef = OneOf(*CURRENCY_CODES, required=True)
    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    dtxferprj = DateTime()
    dtposted = DateTime()
    recsrvrtid = String(10)
    xferprcsts = SubAggregate(XFERPRCSTS)

    optionalMutexes = [("dtxferprj", "dtposted")]


class INTRAMODRQ(Aggregate):
    """ OFX section 11.7.2.1 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)


class INTRACANRQ(Aggregate):
    """ OFX section 11.7.3.1 """

    srvrtid = String(10, required=True)


class INTRAMODRS(Aggregate):
    """ OFX section 11.7.2.2 """

    srvrtid = String(10, required=True)
    xferinfo = SubAggregate(XFERINFO, required=True)
    xferprcsts = SubAggregate(XFERPRCSTS)


class INTRACANRS(Aggregate):
    """ OFX section 11.7.3.2 """

    srvrtid = String(10, required=True)


class INTRATRNRQ(TrnRq):
    """ OFX section 11.7.1.1 """

    intrarq = SubAggregate(INTRARQ)
    intramodrq = SubAggregate(INTRAMODRQ)
    intracanrq = SubAggregate(INTRACANRQ)

    requiredMutexes = [("intrarq", "intramodrq", "intracanrq")]


class INTRATRNRS(TrnRs):
    """ OFX section 11.7.1.2 """

    intrars = SubAggregate(INTRARS)
    intramodrs = SubAggregate(INTRAMODRS)
    intracanrs = SubAggregate(INTRACANRS)

    optionalMutexes = [("intrars", "intramodrs", "intracanrs")]


class INTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.2.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class INTRASYNCRS(SyncRsList):
    """ OFX section 11.12.2.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["INTRATRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class RECURRINST(Aggregate):
    """ OFX section 10.2 """

    ninsts = Integer(3)
    freq = OneOf(*FREQUENCIES, required=True)


class RECINTRARQ(Aggregate):
    """ OFX section 11.10.1.1 """

    recurrinst = SubAggregate(RECURRINST, required=True)
    intrarq = SubAggregate(INTRARQ, required=True)


class RECINTRARS(Aggregate):
    """ OFX section 11.10.1.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrars = SubAggregate(INTRARS, required=True)


class RECINTRAMODRQ(Aggregate):
    """ OFX section 11.10.2.1 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrarq = SubAggregate(INTRARQ, required=True)
    modpending = Bool(required=True)


class RECINTRAMODRS(Aggregate):
    """ OFX section 11.10.2.2 """

    recsrvrtid = String(10, required=True)
    recurrinst = SubAggregate(RECURRINST, required=True)
    intrars = SubAggregate(INTRARS, required=True)
    modpending = Bool(required=True)


class RECINTRACANRQ(Aggregate):
    """ OFX section 11.10.3.1 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTRACANRS(Aggregate):
    """ OFX section 11.10.3.2 """

    recsrvrtid = String(10, required=True)
    canpending = Bool(required=True)


class RECINTRATRNRQ(TrnRq):
    """ OFX section 11.10.1.1 """

    recintrarq = SubAggregate(RECINTRARQ)
    recintramodrq = SubAggregate(RECINTRAMODRQ)
    recintracanrq = SubAggregate(RECINTRACANRQ)

    requiredMutexes = [("recintrarq", "recintramodrq", "recintracanrq")]


class RECINTRATRNRS(TrnRs):
    """ OFX section 11.10.1.2 """

    recintrars = SubAggregate(RECINTRARS)
    recintramodrs = SubAggregate(RECINTRAMODRS)
    recintracanrs = SubAggregate(RECINTRACANRS)

    optionalMutexes = [("recintrars", "recintramodrs", "recintracanrs")]


class RECINTRASYNCRQ(SyncRqList):
    """ OFX section 11.12.5.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTRATRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class RECINTRASYNCRS(SyncRsList):
    """ OFX section 11.12.5.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["RECINTRATRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class BANKMAILRQ(Aggregate):
    """ OFX section 11.11.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    mail = SubAggregate(MAIL, required=True)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class BANKMAILRS(Aggregate):
    """ OFX section 11.11.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    mail = SubAggregate(MAIL, required=True)

    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


class CHKMAILRS(Aggregate):
    """ OFX section 11.11.3.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    mail = SubAggregate(MAIL, required=True)
    checknum = String(12, required=True)
    trnamt = Decimal()
    dtuser = DateTime()
    fee = Decimal()


class DEPMAILRS(Aggregate):
    """ OFX section 11.11.3.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM, required=True)
    mail = SubAggregate(MAIL, required=True)
    trnamt = Decimal(required=True)
    dtuser = DateTime()
    fee = Decimal()


class BANKMAILTRNRQ(TrnRq):
    """ OFX section 11.11.1.1 """

    bankmailrq = SubAggregate(BANKMAILRQ, required=True)


class BANKMAILTRNRS(TrnRs):
    """ OFX section 11.11.1.2 """

    bankmailrs = SubAggregate(BANKMAILRS)
    chkmailrs = SubAggregate(CHKMAILRS)
    depmailrs = SubAggregate(DEPMAILRS)

    optionalMutexes = [("bankmailrs", "chkmailrs", "depmailrs")]


class BANKMAILSYNCRQ(SyncRqList):
    """ OFX section 11.12.7.1 """

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRqList.metadataTags + ["INCIMAGES", "USEHTML", "BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["BANKMAILTRNRQ"]
    requiredMutexes = SyncRqList.requiredMutexes + [("bankacctfrom", "ccacctfrom")]


class BANKMAILSYNCRS(SyncRsList):
    """ OFX section 11.12.7.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)

    metadataTags = SyncRsList.metadataTags + ["BANKACCTFROM", "CCACCTFROM"]
    dataTags = ["BANKMAILTRNRS"]
    requiredMutexes = [("bankacctfrom", "ccacctfrom")]


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


class BANKMSGSET(Aggregate):
    """ OFX section 7.3 """

    bankmsgsetv1 = SubAggregate(BANKMSGSETV1, required=True)
