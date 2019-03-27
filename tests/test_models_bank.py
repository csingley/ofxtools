# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy


# local imports
import base
import test_models_common
import test_models_i18n

from ofxtools.utils import UTC
import ofxtools.models
from ofxtools.models.base import Aggregate
from ofxtools.models.common import STATUS, BAL, MSGSETCORE, SVCSTATUSES
from ofxtools.models.bank import (
    BANKACCTFROM,
    BANKACCTTO,
    BANKACCTINFO,
    CCACCTTO,
    CCACCTFROM,
    CCACCTINFO,
    INCTRAN,
    PAYEE,
    LEDGERBAL,
    AVAILBAL,
    BALLIST,
    STMTTRN,
    BANKTRANLIST,
    STMTRS,
    STMTTRNRS,
    BANKMSGSRSV1,
    STMTRQ,
    STMTTRNRQ,
    BANKMSGSRQV1,
    TRNTYPES,
    CLOSING,
    STMTENDRQ,
    STMTENDRS,
    STMTENDTRNRQ,
    STMTENDTRNRS,
    BANKMSGSETV1,
    BANKMSGSET,
    EMAILPROF,
    ACCTTYPES,
)
from ofxtools.models.i18n import CURRENCY, ORIGCURRENCY, CURRENCY_CODES


class BankacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("BANKID", "ACCTID", "ACCTTYPE")
    optionalElements = ("BRANCHID", "ACCTKEY")
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
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
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

    requiredElements = ("BANKACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS")

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

    requiredElements = ("ACCTID",)
    optionalElements = ("ACCTKEY",)
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

    requiredElements = ("CCACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS")

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

    requiredElements = ("INCLUDE",)
    optionalElements = ("DTSTART", "DTEND")

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

    requiredElements = ("BANKACCTFROM",)
    optionalElements = ("INCTRAN", "INCLUDEPENDING", "INCTRANIMG")

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

    requiredElements = ("NAME", "ADDR1", "CITY", "STATE", "POSTALCODE", "PHONE")
    optionalElements = ("ADDR2", "ADDR3", "COUNTRY")

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
        "NAME",
        "EXTDNAME",
        "MEMO",
        "CURRENCY",
        "INV401KSOURCE",
    ]
    unsupported = ["imagedata"]

    @property
    def root(self):
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
        SubElement(root, "NAME").text = "Tweet E. Bird"
        SubElement(root, "EXTDNAME").text = "Singing yellow canary"
        SubElement(root, "MEMO").text = "Protection money"
        currency = test_models_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, "CHECK")
        self.assertEqual(root.dtposted, datetime(2013, 6, 15, tzinfo=UTC))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14, tzinfo=UTC))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16, tzinfo=UTC))
        self.assertEqual(root.trnamt, Decimal("-433.25"))
        self.assertEqual(root.fitid, "DEADBEEF")
        self.assertEqual(root.correctfitid, "B00B5")
        self.assertEqual(root.correctaction, "REPLACE")
        self.assertEqual(root.srvrtid, "101A2")
        self.assertEqual(root.checknum, "101")
        self.assertEqual(root.refnum, "5A6B")
        self.assertEqual(root.sic, 171103)
        self.assertEqual(root.payeeid, "77810")
        self.assertEqual(root.name, "Tweet E. Bird")
        self.assertEqual(root.extdname, "Singing yellow canary")
        self.assertEqual(root.memo, "Protection money")
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, "PROFITSHARING")
        return root

    def testOneOf(self):
        self.oneOfTest("TRNTYPE", TRNTYPES)

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for unsupp in self.unsupported:
            setattr(root, unsupp, "FOOBAR")
            self.assertIsNone(getattr(root, unsupp))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.curtype, "CURRENCY")
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class StmttrnOrigcurrencyTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with ORIGCURRENCY """

    __test__ = True

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
        "NAME",
        "EXTDNAME",
        "MEMO",
        "ORIGCURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        name = root.find("CURRENCY")
        root.remove(name)
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
        root.insert(16, origcurrency)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, "CHECK")
        self.assertEqual(root.dtposted, datetime(2013, 6, 15, tzinfo=UTC))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14, tzinfo=UTC))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16, tzinfo=UTC))
        self.assertEqual(root.trnamt, Decimal("-433.25"))
        self.assertEqual(root.fitid, "DEADBEEF")
        self.assertEqual(root.correctfitid, "B00B5")
        self.assertEqual(root.correctaction, "REPLACE")
        self.assertEqual(root.srvrtid, "101A2")
        self.assertEqual(root.checknum, "101")
        self.assertEqual(root.refnum, "5A6B")
        self.assertEqual(root.sic, 171103)
        self.assertEqual(root.payeeid, "77810")
        self.assertEqual(root.name, "Tweet E. Bird")
        self.assertEqual(root.extdname, "Singing yellow canary")
        self.assertEqual(root.memo, "Protection money")
        self.assertIsInstance(root.origcurrency, ORIGCURRENCY)
        self.assertEqual(root.inv401ksource, "PROFITSHARING")
        return root

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.curtype, "ORIGCURRENCY")
        self.assertEqual(root.cursym, root.origcurrency.cursym)
        self.assertEqual(root.currate, root.origcurrency.currate)


class StmttrnPayeeTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with PAYEE """

    __test__ = True

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
        "PAYEE",
        "EXTDNAME",
        "MEMO",
        "CURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        name = root.find("NAME")
        root.remove(name)
        payee = PayeeTestCase().root
        root.insert(13, payee)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, "CHECK")
        self.assertEqual(root.dtposted, datetime(2013, 6, 15, tzinfo=UTC))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14, tzinfo=UTC))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16, tzinfo=UTC))
        self.assertEqual(root.trnamt, Decimal("-433.25"))
        self.assertEqual(root.fitid, "DEADBEEF")
        self.assertEqual(root.correctfitid, "B00B5")
        self.assertEqual(root.correctaction, "REPLACE")
        self.assertEqual(root.srvrtid, "101A2")
        self.assertEqual(root.checknum, "101")
        self.assertEqual(root.refnum, "5A6B")
        self.assertEqual(root.sic, 171103)
        self.assertEqual(root.payeeid, "77810")
        self.assertIsInstance(root.payee, PAYEE)
        self.assertEqual(root.extdname, "Singing yellow canary")
        self.assertEqual(root.memo, "Protection money")
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, "PROFITSHARING")
        return root


class StmttrnBankaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with BANKACCTTO """

    __test__ = True

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
        "NAME",
        "EXTDNAME",
        "BANKACCTTO",
        "MEMO",
        "CURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        bankacctto = BankaccttoTestCase().root
        root.insert(-3, bankacctto)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.bankacctto, BANKACCTTO)


class StmttrnCcaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with CCACCTTO """

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
        "NAME",
        "EXTDNAME",
        "CCACCTTO",
        "MEMO",
        "CURRENCY",
        "INV401KSOURCE",
    ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        ccacctto = CcaccttoTestCase().root
        root.insert(-3, ccacctto)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.ccacctto, CCACCTTO)


class StmttrnBankaccttoCcaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """
    STMTTRN with both BANKACCTTO and CCACCTTO - not allowed per OFX spec
    """

    __test__ = True

    @property
    def root(self):
        root = StmttrnTestCase().root
        bankacctto = BankaccttoTestCase().root
        root.append(bankacctto)
        ccacctto = CcaccttoTestCase().root
        root.append(ccacctto)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)

    def testOneOf(self):
        pass

    def testUnsupported(self):
        pass

    def testPropertyAliases(self):
        pass


class StmttrnNamePayeeTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with both NAME and PAYEE - not allowed per OFX spec """

    __test__ = True

    @property
    def root(self):
        root = StmttrnTestCase().root
        payee = PayeeTestCase().root
        root.append(payee)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StmttrnCurrencyOrigCurrencyTestCase(unittest.TestCase, base.TestAggregate):
    """
    STMTTRN with both CURRENCY and ORIGCURRENCY - not allowed per OFX spec
    """

    __test__ = True

    @property
    def root(self):
        root = StmttrnTestCase().root
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
        root.append(origcurrency)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class BanktranlistTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ("DTSTART", "DTEND")
    optionalElements = ("STMTTRN",)  # FIXME - *ALL* STMTTRN optional!

    @property
    def root(self):
        root = Element("BANKTRANLIST")
        SubElement(root, "DTSTART").text = "20130601"
        SubElement(root, "DTEND").text = "20130630"
        for i in range(2):
            stmttrn = StmttrnTestCase().root
            root.append(stmttrn)
        return root

    def testdataTags(self):
        # BANKTRANLIST may only contain STMTTRN
        allowedTags = BANKTRANLIST.dataTags
        self.assertEqual(len(allowedTags), 1)
        root = deepcopy(self.root)
        root.append(test_models_common.BalTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2013, 6, 30, tzinfo=UTC))
        self.assertEqual(len(root), 2)
        for i in range(2):
            self.assertIsInstance(root[i], STMTTRN)


class LedgerbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("BALAMT", "DTASOF")

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

    requiredElements = ("BALAMT", "DTASOF")

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
        bal1 = test_models_common.BalTestCase().root
        bal2 = test_models_common.BalTestCase().root
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

    requiredElements = ("CURDEF", "BANKACCTFROM", "LEDGERBAL")
    optionalElements = (
        "BANKTRANLIST",
        "AVAILBAL",
        "CASHADVBALAMT",
        "INTRATE",
        "BALLIST",
        "MKTGINFO",
    )
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


class StmttrnrqTestCase(unittest.TestCase, base.TestAggregate):
    """
    """

    __test__ = True

    requiredElements = ["TRNUID"]
    optionalElements = ["STMTRQ"]

    @property
    def root(self):
        root = Element("STMTTRNRQ")
        SubElement(root, "TRNUID").text = "1001"
        stmtrq = StmtrqTestCase().root
        root.append(stmtrq)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRNRQ)
        self.assertEqual(root.trnuid, "1001")
        self.assertIsInstance(root.stmtrq, STMTRQ)


class StmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNUID", "STATUS"]
    optionalElements = ["STMTRS"]

    @property
    def root(self):
        root = Element("STMTTRNRS")
        SubElement(root, "TRNUID").text = "1001"
        status = test_models_common.StatusTestCase().root
        root.append(status)
        stmtrs = StmtrsTestCase().root
        root.append(stmtrs)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STMTTRNRS)
        self.assertEqual(instance.trnuid, "1001")
        self.assertIsInstance(instance.status, STATUS)
        self.assertIsInstance(instance.stmtrs, STMTRS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.statement, STMTRS)


class ClosingTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FITID", "DTCLOSE", "BALCLOSE", "DTPOSTSTART", "DTPOSTEND"]
    optionalElements = ["DTOPEN", "DTNEXT", "BALOPEN", "BALMIN", "DEPANDCREDIT", "CHKANDDEBIT", "TOTALFEES", "TOTALINT", "MKTGINFO", "CURRENCY"]

    @property
    def root(self):
        root = Element("CLOSING")
        SubElement(root, "FITID").text = "DEADBEEF"
        SubElement(root, "DTOPEN").text = "20161201"
        SubElement(root, "DTCLOSE").text = "20161225"
        SubElement(root, "DTNEXT").text = "20170101"
        SubElement(root, "BALOPEN").text = "11"
        SubElement(root, "BALCLOSE").text = "20"
        SubElement(root, "BALMIN").text = "6"
        SubElement(root, "DEPANDCREDIT").text = "14"
        SubElement(root, "CHKANDDEBIT").text = "-5"
        SubElement(root, "TOTALFEES").text = "0"
        SubElement(root, "TOTALINT").text = "0"
        SubElement(root, "DTPOSTSTART").text = "20161201"
        SubElement(root, "DTPOSTEND").text = "20161225"
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        currency = test_models_i18n.CurrencyTestCase().root
        root.append(currency)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CLOSING)
        self.assertEqual(instance.fitid, "DEADBEEF")
        self.assertEqual(instance.dtopen, datetime(2016, 12, 1, tzinfo=UTC))
        self.assertEqual(instance.dtclose, datetime(2016, 12, 25, tzinfo=UTC))
        self.assertEqual(instance.dtnext, datetime(2017, 1, 1, tzinfo=UTC))
        self.assertEqual(instance.balopen, Decimal('11'))
        self.assertEqual(instance.balclose, Decimal('20'))
        self.assertEqual(instance.balmin, Decimal('6'))
        self.assertEqual(instance.depandcredit, Decimal('14'))
        self.assertEqual(instance.chkanddebit, Decimal('-5'))
        self.assertEqual(instance.totalfees, Decimal('0'))
        self.assertEqual(instance.totalint, Decimal('0'))
        self.assertEqual(instance.dtpoststart, datetime(2016, 12, 1, tzinfo=UTC))
        self.assertEqual(instance.dtpostend, datetime(2016, 12, 25, tzinfo=UTC))
        self.assertEqual(instance.mktginfo, "Get Free Stuff NOW!!")
        self.assertIsInstance(instance.currency, CURRENCY)


class StmtendrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM"]
    optionalElements = ["DTSTART", "DTEND"]

    @property
    def root(self):
        root = Element("STMTENDRQ")
        root.append(BankacctfromTestCase().root)
        SubElement(root, "DTSTART").text = "20161201"
        SubElement(root, "DTEND").text = "20161225"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STMTENDRQ)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(instance.dtstart, datetime(2016, 12, 1, tzinfo=UTC))
        self.assertEqual(instance.dtend, datetime(2016, 12, 25, tzinfo=UTC))


class StmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM"]
    optionalElements = ["CLOSING"]

    @property
    def root(self):
        root = Element("STMTENDRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(BankacctfromTestCase().root)
        root.append(ClosingTestCase().root)
        root.append(ClosingTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STMTENDRS)
        self.assertEqual(instance.curdef, "CAD")
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CLOSING)
        self.assertIsInstance(instance[1], CLOSING)


class StmtendtrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNUID"]
    optionalElements = ["STMTENDRQ"]

    @property
    def root(self):
        root = Element("STMTENDTRNRQ")
        SubElement(root, "TRNUID").text = "B16B00B5"
        root.append(StmtendrqTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STMTENDTRNRQ)
        self.assertEqual(instance.trnuid, "B16B00B5")
        self.assertIsInstance(instance.stmtendrq, STMTENDRQ)


class StmtendtrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNUID", "STATUS"]
    optionalElements = ["STMTENDRS"]

    @property
    def root(self):
        root = Element("STMTENDTRNRS")
        SubElement(root, "TRNUID").text = "B16B00B5"
        status = test_models_common.StatusTestCase().root
        root.append(status)
        root.append(StmtendrsTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STMTENDTRNRS)
        self.assertEqual(instance.trnuid, "B16B00B5")
        self.assertIsInstance(instance.status, STATUS)
        self.assertIsInstance(instance.stmtendrs, STMTENDRS)


class Bankmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSRQV1")
        for i in range(2):
            stmttrnrq = StmttrnrqTestCase().root
            root.append(stmttrnrq)
        return root

    def testdataTags(self):
        # BANKMSGSRQV! may contain
        # ["STMTTRNRQ", "STMTENDRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        allowedTags = BANKMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 10)
        root = deepcopy(self.root)
        root.append(StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSRQV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, STMTTRNRQ)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSRSV1")
        for i in range(2):
            stmttrnrs = StmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testdataTags(self):
        # BANKMSGSRSV! may contain
        # dataTags = ["STMTTRNRS", "STMTENDRS", "STPCHKTRNRS", "INTRATRNRS",
        # "RECINTRATRNRS", "BANKMAILTRNRS", "STPCHKSYNCRS", "INTRASYNCRS",
        # "RECINTRASYNCRS", "BANKMAILSYNCRS"]
        allowedTags = BANKMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 10)
        root = deepcopy(self.root)
        root.append(StmttrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, STMTTRNRS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.statements, list)
        self.assertEqual(len(root.statements), 2)
        self.assertIsInstance(root.statements[0], STMTRS)
        self.assertIsInstance(root.statements[1], STMTRS)


class EmailprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILPROF")
        SubElement(root, "CANEMAIL").text = "Y"
        SubElement(root, "CANNOTIFY").text = "N"

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, EMAILPROF)
        self.assertEqual(root.canemail, True)
        self.assertEqual(root.cannotify, False)


class Bankmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSETV1")
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, "INVALIDACCTTYPE").text = "CHECKING"
        SubElement(root, "CLOSINGAVAIL").text = "Y"
        SubElement(root, "PENDINGAVAIL").text = "N"
        emailprof = EmailprofTestCase().root
        root.append(emailprof)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.invalidaccttype, "CHECKING")
        self.assertEqual(root.closingavail, True)
        self.assertEqual(root.pendingavail, False)
        self.assertIsInstance(root.emailprof, EMAILPROF)

    def testOneOf(self):
        self.oneOfTest("INVALIDACCTTYPE", ACCTTYPES)


class BankmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSET")
        bankmsgsetv1 = Bankmsgsetv1TestCase().root
        root.append(bankmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSET)
        self.assertIsInstance(root.bankmsgsetv1, BANKMSGSETV1)


if __name__ == "__main__":
    unittest.main()
