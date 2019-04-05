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


# local imports
from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.common import BAL, SVCSTATUSES
import ofxtools.models
from ofxtools.models.bank.stmt import (
    TRNTYPES, INV401KSOURCES,
    BANKACCTFROM, BANKACCTINFO, CCACCTFROM, CCACCTINFO,
    LEDGERBAL, AVAILBAL, BALLIST,
    INCTRAN, BANKTRANLIST, PAYEE, REWARDINFO,
    STMTRQ, STMTRS, CCSTMTRQ, CCSTMTRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import UTC


# test imports
import base
from test_models_common import BalTestCase
from test_models_i18n import CurrencyTestCase, OrigcurrencyTestCase


class BankacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKID", "ACCTID", "ACCTTYPE"]
    optionalElements = ["BRANCHID", "ACCTKEY"]
    tag = "BANKACCTFROM"

    @property
    def root(self):
        root = Element(self.tag)
        SubElement(root, "BANKID").text = "111000614"
        SubElement(root, "BRANCHID").text = "11223344"
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTTYPE").text = "CHECKING"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, getattr(ofxtools.models, self.tag))
        self.assertEqual(root.bankid, "111000614")
        self.assertEqual(root.branchid, "11223344")
        self.assertEqual(root.acctid, "123456789123456789")
        self.assertEqual(root.accttype, "CHECKING")
        self.assertEqual(root.acctkey, "DEADBEEF")

    def testOneOf(self):
        self.oneOfTest(
            "ACCTTYPE", ("CHECKING", "SAVINGS", "MONEYMRKT", "CREDITLINE", "CD")
        )


class BankaccttoTestCase(BankacctfromTestCase):
    tag = "BANKACCTTO"


class BankacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS"]

    @property
    def root(self):
        root = Element("BANKACCTINFO")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, "SUPTXDL").text = "Y"
        SubElement(root, "XFERSRC").text = "N"
        SubElement(root, "XFERDEST").text = "Y"
        SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKACCTINFO)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertEqual(root.suptxdl, True)
        self.assertEqual(root.xfersrc, False)
        self.assertEqual(root.xferdest, True)
        self.assertEqual(root.svcstatus, "AVAIL")

    def testOneOf(self):
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)


class CcacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ACCTID"]
    optionalElements = ["ACCTKEY"]
    tag = "CCACCTFROM"

    @property
    def root(self):
        root = Element(self.tag)
        SubElement(root, "ACCTID").text = "123456789123456789"
        SubElement(root, "ACCTKEY").text = "DEADBEEF"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, getattr(ofxtools.models, self.tag))
        self.assertEqual(root.acctid, "123456789123456789")


class CcaccttoTestCase(CcacctfromTestCase):
    tag = "CCACCTTO"


class CcacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CCACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS"]

    @property
    def root(self):
        root = Element("CCACCTINFO")
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, "SUPTXDL").text = "Y"
        SubElement(root, "XFERSRC").text = "N"
        SubElement(root, "XFERDEST").text = "Y"
        SubElement(root, "SVCSTATUS").text = "PEND"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCACCTINFO)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertEqual(root.suptxdl, True)
        self.assertEqual(root.xfersrc, False)
        self.assertEqual(root.xferdest, True)
        self.assertEqual(root.svcstatus, "PEND")

    def testOneOf(self):
        self.oneOfTest("SVCSTATUS", SVCSTATUSES)


class InctranTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INCLUDE"]
    optionalElements = ["DTSTART", "DTEND"]

    @property
    def root(self):
        root = Element("INCTRAN")
        SubElement(root, "DTSTART").text = "20110401"
        SubElement(root, "DTEND").text = "20110430"
        SubElement(root, "INCLUDE").text = "Y"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INCTRAN)
        self.assertEqual(root.dtstart, datetime(2011, 4, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2011, 4, 30, tzinfo=UTC))
        self.assertEqual(root.include, True)


class StmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM"]
    optionalElements = ["INCTRAN", "INCLUDEPENDING", "INCTRANIMG"]

    @property
    def root(self):
        root = Element("STMTRQ")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        inctran = InctranTestCase().root
        root.append(inctran)
        SubElement(root, "INCLUDEPENDING").text = "Y"
        SubElement(root, "INCTRANIMG").text = "N"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTRQ)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(root.inctran, INCTRAN)
        self.assertEqual(root.includepending, True)
        self.assertEqual(root.inctranimg, False)


class PayeeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "ADDR1", "CITY", "STATE", "POSTALCODE", "PHONE"]
    optionalElements = ["ADDR2", "ADDR3", "COUNTRY"]

    @property
    def root(self):
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

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PAYEE)
        self.assertEqual(root.name, "Wrigley Field")
        self.assertEqual(root.addr1, "3717 N Clark St")
        self.assertEqual(root.addr2, "Dugout Box, Aisle 19")
        self.assertEqual(root.addr3, "Seat A1")
        self.assertEqual(root.city, "Chicago")
        self.assertEqual(root.state, "IL")
        self.assertEqual(root.postalcode, "60613")
        self.assertEqual(root.country, "USA")
        self.assertEqual(root.phone, "(773) 309-1027")

    def testConvertNameTooLong(self):
        """ Don't enforce length restriction on NAME; raise Warning """
        # Issue #12
        copy_root = deepcopy(self.root)
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
    """ STMTTRN with CURRENCY """

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
    unsupported = ["imagedata"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STMTTRN")
        SubElement(root, "TRNTYPE").text = "CHECK"
        SubElement(root, "DTPOSTED").text = "20130615"
        SubElement(root, "DTUSER").text = "20130614"
        SubElement(root, "DTAVAIL").text = "20130616"
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
    def validSoup(cls):
        name = Element("NAME")
        name.text = "Tweet E. Bird"
        payee = PayeeTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctto = CcaccttoTestCase().root
        currency = CurrencyTestCase().root
        origcurrency = OrigcurrencyTestCase().root
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

    @property
    def root(self):
        return list(self.validSoup)[-1]

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = cls.emptyBase

        name = Element("NAME")
        name.text = "Tweet E. Bird"
        payee = PayeeTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctto = CcaccttoTestCase().root
        currency = CurrencyTestCase().root
        origcurrency = OrigcurrencyTestCase().root

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

    def testOneOf(self):
        self.oneOfTest("TRNTYPE", TRNTYPES)
        self.oneOfTest("INV401KSOURCE", INV401KSOURCES)

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for unsupp in self.unsupported:
            setattr(root, unsupp, "FOOBAR")
            self.assertIsNone(getattr(root, unsupp))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.curtype, "ORIGCURRENCY")
        self.assertEqual(root.cursym, root.origcurrency.cursym)
        self.assertEqual(root.currate, root.origcurrency.currate)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class BanktranlistTestCase(unittest.TestCase, base.TranlistTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trn = StmttrnTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trn))
                yield root


class LedgerbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [ "BALAMT", "DTASOF" ]

    @property
    def root(self):
        root = Element("LEDGERBAL")
        SubElement(root, "BALAMT").text = "12345.67"
        SubElement(root, "DTASOF").text = "20051029101003"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LEDGERBAL)
        self.assertEqual(root.balamt, Decimal("12345.67"))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))


class AvailbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [ "BALAMT", "DTASOF" ]

    @property
    def root(self):
        root = Element("AVAILBAL")
        SubElement(root, "BALAMT").text = "12345.67"
        SubElement(root, "DTASOF").text = "20051029101003"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, AVAILBAL)
        self.assertEqual(root.balamt, Decimal("12345.67"))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))


class BallistTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    optionalElements = ()  # FIXME - how to handle multiple BALs?

    @property
    def root(self):
        root = Element("BALLIST")
        bal1 = BalTestCase().root
        bal2 = deepcopy(bal1)
        root.append(bal1)
        root.append(bal2)

        return root

    def testdataTags(self):
        # BALLLIST may only contain BAL
        allowedTags = BALLIST.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(StmttrnTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BALLIST)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], BAL)
        self.assertIsInstance(root[1], BAL)


class StmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [ "CURDEF", "BANKACCTFROM", "LEDGERBAL" ]
    optionalElements = [ "BANKTRANLIST",
                        "AVAILBAL",
                        "CASHADVBALAMT",
                        "INTRATE",
                        "BALLIST",
                        "MKTGINFO",
                       ]
    unsupported = ["banktranlistp"]

    @property
    def root(self):
        root = Element("STMTRS")
        SubElement(root, "CURDEF").text = "USD"
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        tranlist = BanktranlistTestCase().root
        root.append(tranlist)
        tranlist = SubElement(root, "BANKTRANLISTP")
        SubElement(tranlist, "DTASOF").text = "20130101"
        stmttrnp = SubElement(tranlist, "STMTTRNP")
        SubElement(stmttrnp, "TRNTYPE").text = "FEE"
        SubElement(stmttrnp, "DTTRAN").text = "20130101"
        SubElement(stmttrnp, "TRNAMT").text = "5.99"
        SubElement(stmttrnp, "NAME").text = "Usury"
        ledgerbal = LedgerbalTestCase().root
        root.append(ledgerbal)
        availbal = AvailbalTestCase().root
        root.append(availbal)
        SubElement(root, "CASHADVBALAMT").text = "10000.00"
        SubElement(root, "INTRATE").text = "20.99"
        ballist = BallistTestCase().root
        root.append(ballist)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTRS)
        self.assertIn(root.curdef, CURRENCY_CODES)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal("10000"))
        self.assertEqual(root.intrate, Decimal("20.99"))
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, "Get Free Stuff NOW!!")

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for tag in self.unsupported:
            setattr(root, tag, "FOOBAR")
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.account, BANKACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class StmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StmtrqTestCase


class StmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StmtrsTestCase

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        stmt = instance.statement
        self.assertIsInstance(stmt, STMTRS)


class RewardinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("REWARDINFO")
        SubElement(root, "NAME").text = "Cash Back"
        SubElement(root, "REWARDBAL").text = "655"
        SubElement(root, "REWARDEARNED").text = "200"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, REWARDINFO)
        self.assertEqual(root.name, "Cash Back")
        self.assertEqual(root.rewardbal, Decimal("655"))
        self.assertEqual(root.rewardearned, Decimal("200"))


class CcstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CCACCTFROM"]
    optionalElements = ["INCTRAN", "INCLUDEPENDING", "INCTRANIMG"]

    @property
    def root(self):
        root = Element("CCSTMTRQ")
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        inctran = InctranTestCase().root
        root.append(inctran)
        SubElement(root, "INCLUDEPENDING").text = "N"
        SubElement(root, "INCTRANIMG").text = "Y"

        return root

    def testConvert(self):
        # Test *TRNRQ wrapper and direct child elements
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTRQ)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.inctran, INCTRAN)
        self.assertEqual(root.includepending, False)
        self.assertEqual(root.inctranimg, True)


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
    unsupported = ["banktranlistp"]

    @property
    def root(self):
        root = Element("CCSTMTRS")
        SubElement(root, "CURDEF").text = "USD"
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        tranlist = BanktranlistTestCase().root
        root.append(tranlist)
        ledgerbal = LedgerbalTestCase().root
        root.append(ledgerbal)
        availbal = AvailbalTestCase().root
        root.append(availbal)
        SubElement(root, "CASHADVBALAMT").text = "10000.00"
        SubElement(root, "INTRATEPURCH").text = "20.99"
        SubElement(root, "INTRATECASH").text = "25.99"
        SubElement(root, "INTRATEXFER").text = "21.99"
        rewardinfo = RewardinfoTestCase().root
        root.append(rewardinfo)
        ballist = BallistTestCase().root
        root.append(ballist)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTRS)
        self.assertEqual(root.curdef, "USD")
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal("10000"))
        self.assertEqual(root.intratepurch, Decimal("20.99"))
        self.assertEqual(root.intratecash, Decimal("25.99"))
        self.assertEqual(root.intratexfer, Decimal("21.99"))
        self.assertIsInstance(root.rewardinfo, REWARDINFO)
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, "Get Free Stuff NOW!!")

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for tag in self.unsupported:
            setattr(root, tag, "FOOBAR")
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.account, CCACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class CcstmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = CcstmtrqTestCase


class CcstmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = CcstmtrsTestCase


if __name__ == "__main__":
    unittest.main()
