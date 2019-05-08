# coding: utf-8
"""
Tax form 1099 - as of TY2018
"""


__all__ = [
    "PAYERADDR",
    "RECADDR",
    "ADDLSTTAXWHAGG",
    "STTAXWHAGG",
    "LCLTAXWHAGG",
    "PROCDET_V100",
    "PROCSUM_V100",
    "EXTDBINFO_V100",
    "STKBND",
    "FORINCOME",
    "FIDIRECTDEPOSITINFO",
    "ORIGSTATE",
    "ADDLSTATETAXWHAGG",
    "TAX1099MISC_V100",
    "TAX1099R_V100",
    "TAX1099B_V100",
    "TAX1099INT_V100",
    "TAX1099DIV_V100",
    "TAX1099OID_V100",
    "TAX1099RQ",
    "TAX1099RS",
    "TAX1099TRNRQ",
    "TAX1099TRNRS",
    "TAX1099MSGSRQV1",
    "TAX1099MSGSRSV1",
    "TAX1099MSGSETV1",
    "TAX1099MSGSET",
]


# local imports
from ofxtools.Types import (
    String,
    Bool,
    Integer,
    Decimal,
    OneOf,
    DateTime,
    ListItem,
)
from ofxtools.models.base import (
    Aggregate,
    SubAggregate,
    ElementList,
    ListElement,
)
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.common import MSGSETCORE


class PAYERADDR(Aggregate):
    """ OFX tax extensions section 2.2.7 """
    payername1 = String(32, required=True)
    payername2 = String(32)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    phone = String(32)


class RECADDR(Aggregate):
    """ OFX tax extensions section 2.2.8 """
    recname1 = String(32, required=True)
    recname2 = String(32)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    countrystring = String(32)
    phone = String(32)


class ADDLSTTAXWHAGG(Aggregate):
    """ OFX tax extensions section 2.2.9 """

    sttaxwh = Decimal(required=True)
    payerstate = String(2, required=True)
    payerstid = String(32)
    stincome = Decimal()


class STTAXWHAGG(Aggregate):
    """ OFX tax extensions section 2.2.10 """

    amount = Decimal(required=True)
    payerstate = String(2, required=True)
    payerstid = String(32)
    stdist = Decimal()


class LCLTAXWHAGG(Aggregate):
    """ OFX tax extensions section 2.2.10 """

    amount = Decimal(required=True)
    namelcl = String(32, required=True)
    lcldist = Decimal()


class PROCDET_V100(Aggregate):
    """ OFX tax extensions section 2.2.11.2 """
    form8949code = String(1)
    dtaqd = DateTime()
    dtvar = Bool()
    dtsale = DateTime(required=True)
    secname = String(120)
    saledescription = String(120)
    numshrs = Decimal()
    costbasis = Decimal()
    salespr = Decimal(required=True)
    accruedmktdiscount = Decimal()
    longshort = OneOf("LONG", "SHORT")
    ordinary = Bool()
    washsale = Bool()
    fedtaxwh = Decimal()
    washsalelossdisallowed = Decimal()
    noncoveredsecurity = Bool()
    lossnotallowed = Bool()
    basisnotshown = Bool()
    form1099bnotreceived = Bool()
    collectible = Bool()
    statecode = String(2)
    stateidnum = String(32)
    statetaxwheld = Decimal()
    statecode2 = String(2)
    stateidnum2 = String(32)
    statetaxwheld2 = Decimal()
    fatca = Bool()

    requiredMutexes = [
        ["dtaqd", "dtvar"],
    ]


class PROCSUM_V100(Aggregate):
    """ OFX tax extensions section 2.2.11.3 """
    form8949code = String(1, required=True)
    adjcode = String(9)
    sumcostbasis = Decimal()
    sumsalespr = Decimal(required=True)
    sumadjamt = Decimal()
    sumdescription = String(120)


class EXTDBINFO_V100(Aggregate):
    """ OFX tax extensions section 2.2.11.1 """
    procsum_v100 = ListItem(PROCSUM_V100)
    procdet_v100 = ListItem(PROCDET_V100)


class STKBND(Aggregate):
    """ OFX tax extensions section 2.2.11 """
    stkbndamt = Decimal(required=True)
    sbgros = Bool()
    sbgrosless = Bool()


class FORINCOME(Aggregate):
    """ OFX tax extensions section 2.2.12 """
    countrystring = String(32, required=True)
    forincomeallocamt = Decimal()


class FIDIRECTDEPOSITINFO(Aggregate):
    """ OFX tax extensions section 2.2.16 """
    finame_directdeposit = String(32, required=True)
    firoutingnum = Integer(9, required=True)
    fiacctnum = String(22, required=True)
    fiaccountnickname = String(32)


class ORIGSTATE(Aggregate):
    """ OFX tax extensions section 2.2.12 """
    origstatecode = String(2, required=True)
    origstateallocamt = Decimal()


class ADDLSTATETAXWHAGG(Aggregate):
    """ OFX tax extensions section 2.2.12 """
    statecode = String(2, required=True)
    stateidnum = String(32)
    statetaxwheld = Decimal(required=True)


class TAX1099MISC_V100(Aggregate):
    """ OFX tax extensions section 2.2.9 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    corrected = Bool()
    rents = Decimal()
    royalties = Decimal()
    otherincome = Decimal()
    federaltaxwh = Decimal()
    fishboatpro = Decimal()
    medhealthpay = Decimal()
    nonempcomp = Decimal()
    subpmts = Decimal()
    payer5ksales = Decimal()
    cropinspro = Decimal()
    sttaxwh = Decimal()
    payerstate = String(2)
    payerstid = String(32)
    stincome = Decimal()
    addlsttaxwhagg = ListItem(ADDLSTTAXWHAGG)
    grossattor = Decimal()
    excsgldn = Decimal()
    sec409adeferrals = Decimal()
    sec409aincome = Decimal()
    payeraddr = SubAggregate(PAYERADDR, required=True)
    payerid = String(32, required=True)
    recaddr = SubAggregate(RECADDR)
    recid = String(32)
    recacct = String(32)
    tinnot = Bool()
    fatca = Bool()

    optionalMutexes = [
        ["sttaxwh", "addlsttaxwhagg"],
    ]

    @classmethod
    def validate_args(cls, *args, **kwargs):
        if "STTAXWH" in kwargs and "PAYERSTATE" not in kwargs:
            msg = "{}: payerstate must also be provided if sttaxwh is provided"
            raise ValueError(msg)
        super().validate_args(*args, **kwargs)


class TAX1099R_V100(Aggregate):
    """ OFX tax extensions section 2.2.10 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    grossdist = Bool()
    taxamt = Decimal()
    taxamtnd = Decimal()
    totaldist = Bool()
    capgain = Decimal()
    fedtaxwh = Decimal()
    empcontins = Decimal()
    netunapmp = Decimal()
    nonempcomp = Decimal()
    distcode = String(1, required=True)
    irasepsimp = Bool()
    annctrctdist = Decimal()
    annctrctper = Decimal()
    pertodist = Decimal()
    totempcont = Decimal()
    amtallocableirr = Decimal()
    firstyeardesigroth = Integer(4)
    sttaxwhagg = ListItem(STTAXWHAGG)
    lcltaxwhagg = ListItem(LCLTAXWHAGG)
    payeraddr = SubAggregate(PAYERADDR, required=True)
    payerid = String(32, required=True)
    recaddr = SubAggregate(RECADDR)
    recid = String(32)
    recacct = String(32)
    fatca = Bool()
    dtbenefitpmt = DateTime()

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # "[IRASEPSIMP] is required if any of the following tags are present in
        # the 1099R aggregate: GROSSDIST, TAXAMT, FEDTAXWH, STTAXWH,
        # or LCLTAXWH"
        has_irasepsimp = "irasepsimp" in kwargs
        for tag in ("grossdist", "taxamt", "fedtaxwh", "sttaxwh", "lcltaxwh"):
            if tag in kwargs and not has_irasepsimp:
                msg = "{}.__init__(): irasepsimp must also be provided if {} is provided"
                raise ValueError(msg.format(cls.__name__, tag))

        super().validate_args(*args, **kwargs)


class TAX1099B_V100(Aggregate):
    """ OFX tax extensions section 2.2.11 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    corrected = Bool()
    dtsale = DateTime()
    cusipnum = String(32)
    stkbnd = SubAggregate(STKBND)
    bartering = Decimal()
    fedtaxwh = Decimal()
    dscr = String(80)
    profit = Decimal()
    unrelprofitprev = Decimal()
    unrelprofit = Decimal()
    aggprofit = Decimal()
    extdbinfo_v100 = SubAggregate(EXTDBINFO_V100)
    payeraddr = SubAggregate(PAYERADDR, required=True)
    payerid = String(32, required=True)
    recaddr = SubAggregate(RECADDR)
    recid = String(32, required=True)
    recacct = String(32)
    tinnot = Bool()


class TAX1099INT_V100(Aggregate):
    """ OFX tax extensions section 2.2.12 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    corrected = Bool()
    payerrtn = String(32)
    intincome = Decimal()
    intusbndtrs = Decimal()
    fedtaxwh = Decimal()
    investexp = Decimal()
    fortaxpd = Decimal()
    forincomeamt = Decimal()
    forcnt = String(32)
    forincome = ListItem(FORINCOME)
    taxexemptint = Decimal()
    origstate = ListItem(ORIGSTATE)
    specifiedpabint = Decimal()
    marketdiscount = Decimal()
    bondpremium = Decimal()
    bondpremusobligations = Decimal()
    tebondpremium = Decimal()
    cusipnum = String(32)
    statecode = String(2)
    stateidnum = String(32)
    statetaxwheld = Decimal()
    addlstatetaxwhagg = SubAggregate(ADDLSTATETAXWHAGG)
    payeraddr = SubAggregate(PAYERADDR, required=True)
    payerid = String(32, required=True)
    recaddr = SubAggregate(RECADDR)
    recid = String(32)
    recacct = String(32)
    tinnot = Bool()
    fatca = Bool()

    optionalMutexes = [
        ['forcnt', 'forincome'],
        ['statecode', 'addlstatetaxwhagg'],
        ['stateidnum', 'addlstatetaxwhagg'],
        ['statetaxwheld', 'addlstatetaxwhagg'],
    ]


class TAX1099DIV_V100(Aggregate):
    """ OFX tax extensions section 2.2.13 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    corrected = Bool()
    orddiv = Decimal()
    qualifieddiv = Decimal()
    totcapgain = Decimal()
    p28gain = Decimal()
    unrecsec1250 = Decimal()
    sec1202 = Decimal()
    nontaxdist = Decimal()
    fedtaxwh = Decimal()
    sec199a = Decimal()
    investexp = Decimal()
    fortaxpd = Decimal()
    forincomeamt = Decimal()
    forcnt = String(32)
    forincome = ListItem(FORINCOME)
    cashliq = Decimal()
    noncashliq = Decimal()
    exemptintdiv = Decimal()
    origstate = SubAggregate(ORIGSTATE)
    specifiedpabintdiv = Decimal()
    statecode = String(2)
    stateidnum = String(32)
    statetaxwheld = Decimal()
    addlstatetaxwhagg = SubAggregate(ADDLSTATETAXWHAGG)
    payeraddr = SubAggregate(PAYERADDR, required=True)
    payerid = String(32, required=True)
    recaddr = SubAggregate(RECADDR)
    recid = String(32, required=True)
    recacct = String(32)
    tinnot = Bool()
    fatca = Bool()

    optionalMutexes = [
        ['forcnt', 'forincome'],
        ['statetaxwheld', 'addlstatetaxwhagg'],
    ]


class TAX1099OID_V100(Aggregate):
    """ OFX tax extensions section 2.2.14 """
    srvrtid = String(10, required=True)
    taxyear = Integer(4, required=True)
    void = Bool()
    corrected = Bool()
    origisdisc = Decimal()
    otherperint = Decimal()
    erlwithpen = Decimal()
    fedtaxwh = Decimal()
    marketdiscount = Decimal()
    acqpremium = Decimal()
    description = String(2000)
    oidonustres = Decimal()
    investexp = Decimal()
    bondpremium = Decimal()
    taxexemptoid = Decimal()
    origstate = ListItem(ORIGSTATE)
    privactbondamt = Decimal()
    privactbondint = Decimal()
    statecode = String(2)
    stateidnum = String(32)
    statetaxwheld = Decimal()
    addlstatetaxwhagg = SubAggregate(ADDLSTATETAXWHAGG)
    payeraddr = SubAggregate(PAYERADDR)
    payerid = String(32, required=True)
    recid = String(32)
    recacct = String(32)
    tinnot = Bool()
    fatca = Bool()

    optionalMutexes = [
        ['statecode', 'addlstatetaxwhagg'],
        ['stateidnum', 'addlstatetaxwhagg'],
        ['statetaxwheld', 'addlstatetaxwhagg'],
    ]


class TAX1099RQ(ElementList):
    """ OFX tax extensions section 2.2.5 """
    acctnum = String(32)
    recid = String(32)
    taxyear = ListElement(Integer(4))


class TAX1099RS(Aggregate):
    """ OFX tax extensions section 2.2.6 """
    acctnum = String(32)
    recid = String(32)
    fidirectdepositinfo = ListItem(FIDIRECTDEPOSITINFO)
    tax1099misc_v100 = ListItem(TAX1099MISC_V100)
    tax1099r_v100 = ListItem(TAX1099R_V100)
    tax1099b_v100 = ListItem(TAX1099B_V100)
    tax1099int_v100 = ListItem(TAX1099INT_V100)
    tax1099div_v100 = ListItem(TAX1099DIV_V100)
    tax1099oid_v100 = ListItem(TAX1099OID_V100)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Must contain at least one TAX1099x_Vy
        if len([a for a in args if a.__class__.__name__.startswith("TAX1099")]) == 0:
            mandatory = list(cls.listitems.keys())
            mandatory.remove('fidirectdepositinfo')
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(cls.__name__, mandatory))

        super().validate_args(*args, **kwargs)


class TAX1099TRNRQ(TrnRq):
    """ OFX tax extensions section 2.2.3 """
    tax1099rq = SubAggregate(TAX1099RQ, required=True)


class TAX1099TRNRS(TrnRs):
    """ OFX tax extensions section 2.2.4 """
    tax1099rs = SubAggregate(TAX1099RS)


class TAX1099MSGSRQV1(Aggregate):
    """ OFX tax extensions section 2.2.1 """

    tax1099trnrq = ListItem(TAX1099TRNRQ)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Must contain at least one TAX1099TRNRQ
        if len(args) == 0:
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(cls.__name__,
                                        list(cls.listitems.keys())))

        super().validate_args(*args, **kwargs)


class TAX1099MSGSRSV1(Aggregate):
    """ OFX tax extensions section 2.2.2 """

    tax1099trnrs = ListItem(TAX1099TRNRS)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Must contain at least one TAX1099TRNRS
        if len(args) == 0:
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(cls.__name__,
                                        list(cls.listitems.keys())))

        super().validate_args(*args, **kwargs)


class TAX1099MSGSETV1(ElementList):
    """ OFX tax extensions section 2.1 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    tax1099dnld = Bool(required=True)
    extd1099b = Bool(required=True)
    taxyearsupported = ListElement(Integer(4))

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Must contain at least one TAXYEARSUPPORTED
        if len(args) == 0:
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(cls.__name__,
                                        list(cls.listitems.keys())))

        super().validate_args(*args, **kwargs)


class TAX1099MSGSET(Aggregate):
    """ OFX tax extensions section 2.1 """
    tax1099msgsetv1 = SubAggregate(TAX1099MSGSETV1, required=True)
