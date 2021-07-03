# coding: utf-8
"""
Unit tests for models.bank.stmt
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy
from typing import List


# local imports
from ofxtools.models.base import Aggregate, UnknownTagWarning
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.bank.stmt import (
    TRNTYPES,
    INV401KSOURCES,
    BANKACCTFROM,
    BANKACCTTO,
    BANKACCTINFO,
    CCACCTFROM,
    CCACCTTO,
    CCACCTINFO,
    PAYEE,
    LEDGERBAL,
    AVAILBAL,
    BALLIST,
    INCTRAN,
    BANKTRANLIST,
    REWARDINFO,
    STMTTRN,
    STMTRQ,
    STMTRS,
    STMTTRNRQ,
    STMTTRNRS,
    CCSTMTRQ,
    CCSTMTRS,
    CCSTMTTRNRQ,
    CCSTMTTRNRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_common as common
import test_models_i18n as i18n


class BankacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKID", "ACCTID", "ACCTTYPE"]
    optionalElements = ["BRANCHID", "ACCTKEY"]
    oneOf = {"ACCTTYPE": ("CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKACCTFROM")
        SubElement(root, "BANKID").text = "111000614"
        SubElement(root, "BRANCHID").text = "11223344"
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTTYPE").text = "CHECKING"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKACCTFROM(
            bankid="111000614",
            branchid="11223344",
            acctid="123456789123456789",
            accttype="CHECKING",
            acctkey="DEADBEEF",
        )


class BankaccttoTestCase(BankacctfromTestCase):
    __test__ = True

    requiredElements = ["BANKID", "ACCTID", "ACCTTYPE"]
    optionalElements = ["BRANCHID", "ACCTKEY"]
    oneOf = {"ACCTTYPE": ("CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKACCTTO")
        SubElement(root, "BANKID").text = "111000614"
        SubElement(root, "BRANCHID").text = "11223344"
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTTYPE").text = "CHECKING"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKACCTTO(
            bankid="111000614",
            branchid="11223344",
            acctid="123456789123456789",
            accttype="CHECKING",
            acctkey="DEADBEEF",
        )


class BankacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS"]
    oneOfs = {"SVCSTATUS": SVCSTATUSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BANKACCTINFO")
        root.append(BankacctfromTestCase.etree)
        SubElement(root, "SUPTXDL").text = "Y"
        SubElement(root, "XFERSRC").text = "N"
        SubElement(root, "XFERDEST").text = "Y"
        SubElement(root, "SVCSTATUS").text = "ACTIVE"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKACCTINFO(
            bankacctfrom=BankacctfromTestCase.aggregate,
            suptxdl=True,
            xfersrc=False,
            xferdest=True,
            svcstatus="ACTIVE",
        )


class CcacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ACCTID"]
    optionalElements = ["ACCTKEY"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCACCTFROM")
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCACCTFROM(acctid="123456789123456789", acctkey="DEADBEEF")


class CcaccttoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ACCTID"]
    optionalElements = ["ACCTKEY"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCACCTTO")
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCACCTTO(acctid="123456789123456789", acctkey="DEADBEEF")


class CcacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CCACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS"]
    oneOfs = {"SVCSTATUS": SVCSTATUSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCACCTINFO")
        root.append(CcacctfromTestCase.etree)
        SubElement(root, "SUPTXDL").text = "Y"
        SubElement(root, "XFERSRC").text = "N"
        SubElement(root, "XFERDEST").text = "Y"
        SubElement(root, "SVCSTATUS").text = "ACTIVE"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCACCTINFO(
            ccacctfrom=CcacctfromTestCase.aggregate,
            suptxdl=True,
            xfersrc=False,
            xferdest=True,
            svcstatus="ACTIVE",
        )


class InctranTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INCLUDE"]
    optionalElements = ["DTSTART", "DTEND"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INCTRAN")
        SubElement(root, "DTSTART").text = "20110401000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20110430000000.000[+0:UTC]"
        SubElement(root, "INCLUDE").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INCTRAN(
            dtstart=datetime(2011, 4, 1, tzinfo=UTC),
            dtend=datetime(2011, 4, 30, tzinfo=UTC),
            include=True,
        )


class StmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM"]
    optionalElements = ["INCTRAN", "INCLUDEPENDING", "INCTRANIMG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STMTRQ")
        root.append(BankacctfromTestCase.etree)
        root.append(InctranTestCase.etree)
        SubElement(root, "INCLUDEPENDING").text = "Y"
        SubElement(root, "INCTRANIMG").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTRQ(
            bankacctfrom=BankacctfromTestCase.aggregate,
            inctran=InctranTestCase.aggregate,
            includepending=True,
            inctranimg=False,
        )


class PayeeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "ADDR1", "CITY", "STATE", "POSTALCODE", "PHONE"]
    optionalElements = ["ADDR2", "ADDR3", "COUNTRY"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PAYEE")
        SubElement(root, "NAME").text = "Wrigley Field"
        SubElement(root, "ADDR1").text = "3717 N Clark St"
        SubElement(root, "ADDR2").text = "Dugout Box, Aisle 19"
        SubElement(root, "ADDR3").text = "Seat A1"
        SubElement(root, "CITY").text = "Chicago"
        SubElement(root, "STATE").text = "IL"
        SubElement(root, "POSTALCODE").text = "60613"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "PHONE").text = "(773) 309-1027"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PAYEE(
            name="Wrigley Field",
            addr1="3717 N Clark St",
            addr2="Dugout Box, Aisle 19",
            addr3="Seat A1",
            city="Chicago",
            state="IL",
            postalcode="60613",
            country="USA",
            phone="(773) 309-1027",
        )

    def testConvertNameTooLong(self):
        """Don't enforce length restriction on NAME; raise Warning"""
        # Issue #12
        copy_root = deepcopy(self.etree)
        copy_element = Element("NAME")
        copy_element.text = """
        The true war is a celebration of markets. Organic markets, carefully
        styled "black" by the professionals, spring up everywhere.  Scrip,
        Sterling, Reichsmarks, continue to move, severe as classical ballet,
        inside their antiseptic marble chambers. But out here, down here among
        the people, the truer currencies come into being.  So, Jews are
        negotiable.  Every bit as negotiable as cigarettes, cunt, or Hershey
        bars.
        """
        copy_root[0] = copy_element
        with self.assertWarns(Warning):
            root = Aggregate.from_etree(copy_root)
        self.assertEqual(
            root.name,
            """
        The true war is a celebration of markets. Organic markets, carefully
        styled "black" by the professionals, spring up everywhere.  Scrip,
        Sterling, Reichsmarks, continue to move, severe as classical ballet,
        inside their antiseptic marble chambers. But out here, down here among
        the people, the truer currencies come into being.  So, Jews are
        negotiable.  Every bit as negotiable as cigarettes, cunt, or Hershey
        bars.
        """,
        )


class StmttrnTestCase(unittest.TestCase, base.TestAggregate):
    """STMTTRN with CURRENCY"""

    __test__ = True

    requiredElements = ["TRNTYPE", "DTPOSTED", "TRNAMT", "FITID"]
    optionalElements = [
        "DTUSER",
        "DTAVAIL",
        "CORRECTFITID",
        "CORRECTACTION",
        "SRVRTID",
        "CHECKNUM",
        "REFNUM",
        "SIC",
        "PAYEEID",
        "EXTDNAME",
        "MEMO",
        "INV401KSOURCE",
    ]
    oneOfs = {"TRNTYPE": TRNTYPES, "INV401KSOURCE": INV401KSOURCES}
    unsupported = ["imagedata"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STMTTRN")
        SubElement(root, "TRNTYPE").text = "CHECK"
        SubElement(root, "DTPOSTED").text = "20130615000000.000[+0:UTC]"
        SubElement(root, "DTUSER").text = "20130614000000.000[+0:UTC]"
        SubElement(root, "DTAVAIL").text = "20130616000000.000[+0:UTC]"
        SubElement(root, "TRNAMT").text = "-433.25"
        SubElement(root, "FITID").text = "DEADBEEF"
        SubElement(root, "CORRECTFITID").text = "B00B5"
        SubElement(root, "CORRECTACTION").text = "REPLACE"
        SubElement(root, "SRVRTID").text = "101A2"
        SubElement(root, "CHECKNUM").text = "101"
        SubElement(root, "REFNUM").text = "5A6B"
        SubElement(root, "SIC").text = "171103"
        SubElement(root, "PAYEEID").text = "77810"

        return root

    @classproperty
    @classmethod
    def etree(cls):
        root = cls.emptyBase
        SubElement(root, "NAME").text = "Porky Pig"
        SubElement(root, "EXTDNAME").text = "Walkin' bacon"
        root.append(BankaccttoTestCase.etree)
        SubElement(root, "MEMO").text = "Th-th-th-that's all folks!"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "INV401KSOURCE").text = "ROLLOVER"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTTRN(
            trntype="CHECK",
            dtposted=datetime(2013, 6, 15, tzinfo=UTC),
            dtuser=datetime(2013, 6, 14, tzinfo=UTC),
            dtavail=datetime(2013, 6, 16, tzinfo=UTC),
            trnamt=Decimal("-433.25"),
            fitid="DEADBEEF",
            correctfitid="B00B5",
            correctaction="REPLACE",
            srvrtid="101A2",
            checknum="101",
            refnum="5A6B",
            sic="171103",
            payeeid="77810",
            name="Porky Pig",
            extdname="Walkin' bacon",
            bankacctto=BankaccttoTestCase.aggregate,
            memo="Th-th-th-that's all folks!",
            currency=i18n.CurrencyTestCase.aggregate,
            inv401ksource="ROLLOVER",
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        name = Element("NAME")
        name.text = "Tweet E. Bird"
        payee = PayeeTestCase.etree
        bankacctto = BankaccttoTestCase.etree
        ccacctto = CcaccttoTestCase.etree
        currency = i18n.CurrencyTestCase.etree
        origcurrency = i18n.OrigcurrencyTestCase.etree
        for payeeChoice in (None, name, payee):
            for acctto in (None, bankacctto, ccacctto):
                for currencyChoice in (None, currency, origcurrency):
                    root = deepcopy(cls.emptyBase)
                    yield root
                    if payeeChoice is not None:
                        root.append(payeeChoice)
                        yield root
                    SubElement(root, "EXTDNAME").text = "Singing yellow canary"
                    yield root
                    if acctto is not None:
                        root.append(acctto)
                        yield root
                    SubElement(root, "MEMO").text = "Protection money"
                    yield root
                    if currencyChoice is not None:
                        root.append(currencyChoice)
                        yield root
                    SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
                    yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = cls.emptyBase

        name = Element("NAME")
        name.text = "Tweet E. Bird"
        payee = PayeeTestCase.etree
        bankacctto = BankaccttoTestCase.etree
        ccacctto = CcaccttoTestCase.etree
        currency = i18n.CurrencyTestCase.etree
        origcurrency = i18n.OrigcurrencyTestCase.etree

        #  optionalMutexes = [
        #  ("name", "payee"),
        #  ("ccacctto", "bankacctto"),
        #  ("currency", "origcurrency"),
        #  ]

        # Both NAME & PAYEE
        root = deepcopy(root_)
        root.append(name)
        root.append(payee)
        yield root

        # Both BANKACCTTO & CCACCTTO
        root = deepcopy(root_)
        root.append(bankacctto)
        root.append(ccacctto)
        yield root

        # Both CURRENCY & ORIGCURRENCY
        root = deepcopy(root_)
        root.append(currency)
        root.append(origcurrency)
        yield root

        # FIXME - add out-of-sequence errors

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.curtype, "CURRENCY")
        self.assertEqual(instance.cursym, instance.currency.cursym)
        self.assertEqual(instance.currate, instance.currency.currate)

    def testConvertNameTooLong(self):
        """Don't enforce length restriction on NAME; raise Warning"""
        # Issue #91
        copy_root = deepcopy(self.etree)
        copy_element = Element("NAME")
        copy_element.text = """
        The true war is a celebration of markets. Organic markets, carefully
        styled "black" by the professionals, spring up everywhere.  Scrip,
        Sterling, Reichsmarks, continue to move, severe as classical ballet,
        inside their antiseptic marble chambers. But out here, down here among
        the people, the truer currencies come into being.  So, Jews are
        negotiable.  Every bit as negotiable as cigarettes, cunt, or Hershey
        bars.
        """
        copy_root[13] = copy_element
        with self.assertWarns(Warning):
            root = Aggregate.from_etree(copy_root)
        self.assertEqual(
            root.name,
            """
        The true war is a celebration of markets. Organic markets, carefully
        styled "black" by the professionals, spring up everywhere.  Scrip,
        Sterling, Reichsmarks, continue to move, severe as classical ballet,
        inside their antiseptic marble chambers. But out here, down here among
        the people, the truer currencies come into being.  So, Jews are
        negotiable.  Every bit as negotiable as cigarettes, cunt, or Hershey
        bars.
        """,
        )


class BanktranlistTestCase(unittest.TestCase, base.TranlistTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = super().etree
        root.append(StmttrnTestCase.etree)
        root.append(StmttrnTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BANKTRANLIST(
            StmttrnTestCase.aggregate,
            StmttrnTestCase.aggregate,
            dtstart=datetime(2016, 1, 1, tzinfo=UTC),
            dtend=datetime(2016, 12, 31, tzinfo=UTC),
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(StmttrnTestCase.etree)
                yield root


class LedgerbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BALAMT", "DTASOF"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("LEDGERBAL")
        SubElement(root, "BALAMT").text = "12345.67"
        SubElement(root, "DTASOF").text = "20051029101003.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return LEDGERBAL(
            balamt=Decimal("12345.67"),
            dtasof=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
        )


class AvailbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BALAMT", "DTASOF"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("AVAILBAL")
        SubElement(root, "BALAMT").text = "12345.67"
        SubElement(root, "DTASOF").text = "20051029101003.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return AVAILBAL(
            balamt=Decimal("12345.67"),
            dtasof=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
        )


class BallistTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    optionalElements: List[str] = []  # FIXME - how to handle multiple BALs?

    def testListAggregates(self):
        # BALLLIST may only contain BAL
        listaggregates = BALLIST.listaggregates
        self.assertEqual(len(listaggregates), 1)
        root = self.etree
        root.append(StmttrnTestCase.etree)

        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("BALLIST")
        root.append(common.BalTestCase.etree)
        root.append(common.BalTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BALLIST(common.BalTestCase.aggregate, common.BalTestCase.aggregate)


class StmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM", "LEDGERBAL"]
    optionalElements = [
        "BANKTRANLIST",
        "AVAILBAL",
        "CASHADVBALAMT",
        "INTRATE",
        "BALLIST",
        "MKTGINFO",
    ]
    #  unsupported = ["banktranlistp"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STMTRS")
        SubElement(root, "CURDEF").text = "USD"
        root.append(BankacctfromTestCase.etree)
        root.append(BanktranlistTestCase.etree)
        #  tranlist = SubElement(root, "BANKTRANLISTP")
        #  SubElement(tranlist, "DTASOF").text = "20130101"
        #  stmttrnp = SubElement(tranlist, "STMTTRNP")
        #  SubElement(stmttrnp, "TRNTYPE").text = "FEE"
        #  SubElement(stmttrnp, "DTTRAN").text = "20130101"
        #  SubElement(stmttrnp, "TRNAMT").text = "5.99"
        #  SubElement(stmttrnp, "NAME").text = "Usury"
        root.append(LedgerbalTestCase.etree)
        root.append(AvailbalTestCase.etree)
        SubElement(root, "CASHADVBALAMT").text = "10000.00"
        SubElement(root, "INTRATE").text = "20.99"
        root.append(BallistTestCase.etree)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTRS(
            curdef="USD",
            bankacctfrom=BankacctfromTestCase.aggregate,
            banktranlist=BanktranlistTestCase.aggregate,
            ledgerbal=LedgerbalTestCase.aggregate,
            availbal=AvailbalTestCase.aggregate,
            cashadvbalamt=Decimal("10000.00"),
            intrate=Decimal("20.99"),
            ballist=BallistTestCase.aggregate,
            mktginfo="Get Free Stuff NOW!!",
        )

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.etree)
        self.assertIsInstance(root.account, BANKACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class StmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            stmtrq=StmtrqTestCase.aggregate,
        )


class StmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StmtrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return STMTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            stmtrs=StmtrsTestCase.aggregate,
        )

    def testPropertyAliases(self):
        instance = self.aggregate
        stmt = instance.statement
        self.assertIsInstance(stmt, STMTRS)


class RewardinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("REWARDINFO")
        SubElement(root, "NAME").text = "Cash Back"
        SubElement(root, "REWARDBAL").text = "655"
        SubElement(root, "REWARDEARNED").text = "200"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return REWARDINFO(
            name="Cash Back", rewardbal=Decimal("655"), rewardearned=Decimal("200")
        )


class CcstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CCACCTFROM"]
    optionalElements = ["INCTRAN", "INCLUDEPENDING", "INCTRANIMG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCSTMTRQ")
        root.append(CcacctfromTestCase.etree)
        root.append(InctranTestCase.etree)
        SubElement(root, "INCLUDEPENDING").text = "N"
        SubElement(root, "INCTRANIMG").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTRQ(
            ccacctfrom=CcacctfromTestCase.aggregate,
            inctran=InctranTestCase.aggregate,
            includepending=False,
            inctranimg=True,
        )


class CcstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "CCACCTFROM", "LEDGERBAL"]
    optionalElements = [
        "BANKTRANLIST",
        "AVAILBAL",
        "CASHADVBALAMT",
        "INTRATEPURCH",
        "INTRATECASH",
        "REWARDINFO",
        "BALLIST",
        "MKTGINFO",
    ]
    #  unsupported = ["banktranlistp"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CCSTMTRS")
        SubElement(root, "CURDEF").text = "USD"
        root.append(CcacctfromTestCase.etree)
        root.append(BanktranlistTestCase.etree)
        root.append(LedgerbalTestCase.etree)
        root.append(AvailbalTestCase.etree)
        SubElement(root, "CASHADVBALAMT").text = "10000.00"
        SubElement(root, "INTRATEPURCH").text = "20.99"
        SubElement(root, "INTRATECASH").text = "25.99"
        SubElement(root, "INTRATEXFER").text = "21.99"
        root.append(RewardinfoTestCase.etree)
        root.append(BallistTestCase.etree)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTRS(
            curdef="USD",
            ccacctfrom=CcacctfromTestCase.aggregate,
            banktranlist=BanktranlistTestCase.aggregate,
            ledgerbal=LedgerbalTestCase.aggregate,
            availbal=AvailbalTestCase.aggregate,
            cashadvbalamt=Decimal("10000.00"),
            intratepurch=Decimal("20.99"),
            intratecash=Decimal("25.99"),
            intratexfer=Decimal("21.99"),
            rewardinfo=RewardinfoTestCase.aggregate,
            ballist=BallistTestCase.aggregate,
            mktginfo="Get Free Stuff NOW!!",
        )

    def testPropertyAliases(self):
        instance = self.aggregate
        self.assertIsInstance(instance.account, CCACCTFROM)
        self.assertIsInstance(instance.transactions, BANKTRANLIST)
        self.assertIsInstance(instance.balance, LEDGERBAL)


class CcstmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = CcstmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            ccstmtrq=CcstmtrqTestCase.aggregate,
        )


class CcstmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = CcstmtrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return CCSTMTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            ccstmtrs=CcstmtrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
