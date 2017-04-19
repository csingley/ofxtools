# coding: utf-8
"""
Data structures for bank download - OFX Section 11
"""
# local imports
from ofxtools.Types import (
    String,
    NagString,
    Decimal,
    Integer,
    OneOf,
    DateTime,
)
from ofxtools.models.base import (
    Aggregate,
    List,
    TranList,
    SubAggregate,
    Unsupported,
)
from ofxtools.models.common import STATUS
from ofxtools.models.i18n import (
    Origcurrency,
    CURRENCY_CODES, COUNTRY_CODES,
)


# Enums used in aggregate validation
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING',
                  'ROLLOVER', 'OTHERVEST', 'OTHERNONVEST')
# OFX section 11.3.1.1
ACCTTYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE', 'CD')
TRNTYPES = ('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG',
            'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT',
            'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT',
            'OTHER')


class BANKACCTFROM(Aggregate):
    """ OFX section 11.3.1 """
    bankid = String(9, required=True)
    branchid = String(22)
    acctid = String(22, required=True)
    accttype = OneOf(*ACCTTYPES, required=True)
    acctkey = String(22)


class BANKACCTTO(BANKACCTFROM):
    """ OFX section 11.3.1 """
    pass


class CCACCTFROM(Aggregate):
    """ OFX section 11.3.2 """
    acctid = String(22, required=True)
    acctkey = String(22)


class CCACCTTO(CCACCTFROM):
    """ OFX section 11.3.2 """
    pass


class PAYEE(Aggregate):
    """ OFX section 12.5.2.1 """
    # name = String(32, required=True)
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
    """ OFX section 11.4.4.1 """
    trntype = OneOf(*TRNTYPES, required=True)
    dtposted = DateTime(required=True)
    dtuser = DateTime()
    dtavail = DateTime()
    trnamt = Decimal(required=True)
    fitid = String(255, required=True)
    correctfitid = String(255)
    correctaction = OneOf('REPLACE', 'DELETE')
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
    inv401ksource = OneOf(*INV401KSOURCES)

    mutexes = [("CCACCTTO", "BANKACCTTO"), ("NAME", "PAYEE"),
               ("CURRENCY", "ORIGCURRENCY")]


class BANKTRANLIST(TranList):
    """ OFX section 11.4.2.2 """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    memberTags = ['STMTTRN', ]


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
    memberTags = ['BAL', ]


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

    # Human-friendly attribute aliases
    @property
    def currency(self):
        return self.curdef

    @property
    def account(self):
        return self.bankacctfrom

    @property
    def transactions(self):
        return self.banktranlist

    @property
    def balance(self):
        return self.ledgerbal


class STMTTRNRS(Aggregate):
    """ OFX section 11.4.2.2 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    stmtrs = SubAggregate(STMTRS)

    @property
    def statement(self):
        return self.stmtrs


class BANKMSGSRSV1(List):
    """ OFX section 11.13.1.1.2 """
    memberTags = ['STMTTRNRS', ]

    @property
    def statements(self):
        return [trnrs.stmtrs for trnrs in self]
