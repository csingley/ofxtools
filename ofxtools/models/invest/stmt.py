# coding: utf-8
"""
Investments - OFX Section 13
"""


__all__ = [
    "LOANPMTFREQUENCIES",
    "INCPOS",
    "INVSTMTRQ",
    "INVBAL",
    "INV401KBAL",
    "MATCHINFO",
    "CONTRIBSECURITY",
    "CONTRIBINFO",
    "VESTINFO",
    "LOANINFO",
    "CONTRIBUTIONS",
    "WITHDRAWALS",
    "EARNINGS",
    "YEARTODATE",
    "INCEPTODATE",
    "PERIODTODATE",
    "INV401KSUMMARY",
    "INV401K",
    "INVSTMTRS",
    "INVSTMTTRNRQ",
    "INVSTMTTRNRS",
]


from ofxtools.Types import (
    Bool,
    String,
    Integer,
    OneOf,
    Decimal,
    DateTime,
    ListItem,
)
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.invest.acct import INVACCTFROM
from ofxtools.models.invest.transactions import INVTRANLIST
from ofxtools.models.invest.positions import INVPOSLIST
from ofxtools.models.invest.securities import SECID
from ofxtools.models.invest.openorders import INVOOLIST
from ofxtools.models.bank.stmt import INCTRAN, BALLIST
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import all_equal


#  OFX section 13.9.3
LOANPMTFREQUENCIES = (
    "WEEKLY",
    "BIWEEKLY",
    "TWICEMONTHLY",
    "MONTHLY",
    "FOURWEEKS",
    "BIMONTHLY",
    "QUARTERLY",
    "SEMIANNUALLY",
    "ANNUALLY",
    "OTHER"
)


class INCPOS(Aggregate):
    """ OFX section 13.9.1.2 """

    dtasof = DateTime()
    include = Bool(required=True)


class INVSTMTRQ(Aggregate):
    """ OFX section 13.9.1.2 """

    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    inctran = SubAggregate(INCTRAN)
    incoo = Bool(required=True)
    incpos = SubAggregate(INCPOS, required=True)
    incbal = Bool(required=True)
    inc401k = Bool()
    inc401kbal = Bool()
    inctranimg = Bool()


class INVBAL(Aggregate):
    """ OFX section 13.9.2.7 """

    availcash = Decimal(required=True)
    marginbalance = Decimal(required=True)
    shortbalance = Decimal(required=True)
    buypower = Decimal()
    ballist = SubAggregate(BALLIST)


class INV401KBAL(Aggregate):
    """ OFX section 13.9.2.9 """

    cashbal = Decimal()
    pretax = Decimal()
    aftertax = Decimal()
    match = Decimal()
    profitsharing = Decimal()
    rollover = Decimal()
    othervest = Decimal()
    othernonvest = Decimal()
    total = Decimal(required=True)
    ballist = SubAggregate(BALLIST)


class MATCHINFO(Aggregate):
    """ OFX section 13.9.3 """

    matchpct = Decimal(required=True)
    maxmatchamt = Decimal()
    maxmatchpct = Decimal()
    startofyear = DateTime()
    basematchamt = Decimal()
    basematchpct = Decimal()


class CONTRIBSECURITY(Aggregate):
    """ OFX section 13.9.3 """

    secid = SubAggregate(SECID, required=True)
    pretaxcontribpct = Decimal()
    pretaxcontribamt = Decimal()
    aftertaxcontribpct = Decimal()
    aftertaxcontribamt = Decimal()
    matchcontribpct = Decimal()
    matchcontribamt = Decimal()
    profitsharingcontribpct = Decimal()
    profitsharingcontribamt = Decimal()
    rollovercontribpct = Decimal()
    rollovercontribamt = Decimal()
    othervestpct = Decimal()
    othervestamt = Decimal()
    othernonvestpct = Decimal()
    othernonvestamt = Decimal()

    @classmethod
    def validate_args(cls, *args, **kwargs):
        """
        Specify either <xxxPCT> or <xxxAMT>.  The new contributions to each
        security are either all specified by a percentage of contributions or
        by a fixed dollar amount, but not both.
        At least one source must be provided.
        """
        if not all_equal(key[-3:] for key in kwargs if key != "secid"):
            msg = "{}: mixed *PCT and *AMT are invalid"
            raise ValueError(msg.format(cls.__name__))

        if len(kwargs) < 2:
            msg = "{}: at least one source must be provided"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class CONTRIBINFO(Aggregate):
    """ OFX section 13.9.3 """

    contribsecurity = ListItem(CONTRIBSECURITY)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        #  "current contribution allocation for a security (1 or more)"
        if len(args) == 0:
            msg = "{} must contain at least one item"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class VESTINFO(Aggregate):
    """ OFX section 13.9.3 """

    vestdate = DateTime()
    vestpct = Decimal(required=True)


class LOANINFO(Aggregate):
    """ OFX section 13.9.3 """

    loanid = String(32, required=True)
    loandesc = String(32)
    initialloanbal = Decimal()
    loanstartdate = DateTime()
    currentloanbal = Decimal(required=True)
    dtasof = DateTime(required=True)
    loanrate = Decimal()
    loanpmtamt = Decimal()
    loanpmtfreq = OneOf(*LOANPMTFREQUENCIES)
    loanpmtsinitial = Integer(5)
    loanpmtsremaining = Integer(5)
    loanmaturitydate = DateTime()
    loantotalprojinterest = Decimal()
    loaninteresttodate = Decimal()
    loannextpmtdate = DateTime()


class Inv401kSubaccountMixin:
    pretax = Decimal()
    aftertax = Decimal()
    match = Decimal()
    profitsharing = Decimal()
    rollover = Decimal()
    othervest = Decimal()
    othernonvest = Decimal()
    total = Decimal(required=True)


class CONTRIBUTIONS(Aggregate, Inv401kSubaccountMixin):
    """ OFX section 13.9.3.1 """


class WITHDRAWALS(Aggregate, Inv401kSubaccountMixin):
    """ OFX section 13.9.3.2 """


class EARNINGS(Aggregate, Inv401kSubaccountMixin):
    """ OFX section 13.9.3.3 """


class ToDateMixin:
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)
    contributions = SubAggregate(CONTRIBUTIONS)
    withdrawals = SubAggregate(WITHDRAWALS)
    earnings = SubAggregate(EARNINGS)


class YEARTODATE(Aggregate, ToDateMixin):
    """ OFX section 13.9.3 """


class INCEPTODATE(Aggregate, ToDateMixin):
    """ OFX section 13.9.3 """


class PERIODTODATE(Aggregate, ToDateMixin):
    """ OFX section 13.9.3 """


class INV401KSUMMARY(Aggregate):
    """ OFX section 13.9.3 """

    yeartodate = SubAggregate(YEARTODATE, required=True)
    inceptodate = SubAggregate(INCEPTODATE)
    periodtodate = SubAggregate(PERIODTODATE)


class INV401K(Aggregate):
    """ OFX section 13.9.3 """

    employername = String(32, required=True)
    planid = String(32)
    planjoindate = DateTime()
    employercontactinfo = String(255)
    brokercontactinfo = String(255)
    deferpctpretax = Decimal()
    deferpctaftertax = Decimal()
    matchinfo = SubAggregate(MATCHINFO)
    contribinfo = SubAggregate(CONTRIBINFO)
    currentvestpct = Decimal()
    vestinfo = ListItem(VESTINFO)
    loaninfo = ListItem(LOANINFO)
    inv401ksummary = SubAggregate(INV401KSUMMARY)


class INVSTMTRS(Aggregate):
    """ OFX section 13.9.2.1 """

    dtasof = DateTime(required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)
    invacctfrom = SubAggregate(INVACCTFROM, required=True)
    invtranlist = SubAggregate(INVTRANLIST)
    invposlist = SubAggregate(INVPOSLIST)
    invbal = SubAggregate(INVBAL)
    invoolist = SubAggregate(INVOOLIST)
    mktginfo = String(360)
    inv401kbal = SubAggregate(INV401KBAL)
    inv401k = SubAggregate(INV401K)

    @property
    def account(self):
        return self.invacctfrom

    @property
    def transactions(self):
        return self.invtranlist

    @property
    def positions(self):
        return self.invposlist

    @property
    def balances(self):
        return self.invbal


class INVSTMTTRNRQ(TrnRq):
    """ OFX section 13.9.1.1 """

    invstmtrq = SubAggregate(INVSTMTRQ, required=True)


class INVSTMTTRNRS(TrnRs):
    """ OFX section 13.9.2.1 """

    invstmtrs = SubAggregate(INVSTMTRS)

    @property
    def statement(self):
        return self.invstmtrs
