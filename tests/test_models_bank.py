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
    CHKRANGE,
    CHKDESC,
    STPCHKNUM,
    STPCHKRQ,
    STPCHKRS,
    STPCHKTRNRQ,
    STPCHKTRNRS,
    STPCHKSYNCRQ,
    STPCHKSYNCRS,
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
            stmttrn = deepcopy(StmttrnTestCase().root)
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

    requiredElements = ["TRNUID", "STMTRQ"]

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
    optionalElements = [
        "DTOPEN",
        "DTNEXT",
        "BALOPEN",
        "BALMIN",
        "DEPANDCREDIT",
        "CHKANDDEBIT",
        "TOTALFEES",
        "TOTALINT",
        "MKTGINFO",
        "CURRENCY",
    ]

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
        self.assertEqual(instance.balopen, Decimal("11"))
        self.assertEqual(instance.balclose, Decimal("20"))
        self.assertEqual(instance.balmin, Decimal("6"))
        self.assertEqual(instance.depandcredit, Decimal("14"))
        self.assertEqual(instance.chkanddebit, Decimal("-5"))
        self.assertEqual(instance.totalfees, Decimal("0"))
        self.assertEqual(instance.totalint, Decimal("0"))
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
        closing = ClosingTestCase().root
        root.append(closing)
        root.append(deepcopy(closing))

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

    requiredElements = ["TRNUID", "STMTENDRQ"]

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


class ChkrangeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CHKNUMSTART"]
    optionalElements = ["CHKNUMEND"]

    @property
    def root(self):
        root = Element("CHKRANGE")
        SubElement(root, "CHKNUMSTART").text = "123"
        SubElement(root, "CHKNUMEND").text = "125"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHKRANGE)
        self.assertEqual(instance.chknumstart, "123")
        self.assertEqual(instance.chknumend, "125")


class ChkdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME"]
    optionalElements = ["CHKNUM", "DTUSER", "TRNAMT"]

    @property
    def root(self):
        root = Element("CHKDESC")
        SubElement(root, "NAME").text = "Bucky Beaver"
        SubElement(root, "CHKNUM").text = "125"
        SubElement(root, "DTUSER").text = "20051122"
        SubElement(root, "TRNAMT").text = "2533"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHKDESC)
        self.assertEqual(instance.name, "Bucky Beaver")
        self.assertEqual(instance.dtuser, datetime(2005, 11, 22, tzinfo=UTC))
        self.assertEqual(instance.trnamt, Decimal("2533"))


class StpchkrqTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKRQ with CHKRANGE """

    __test__ = True

    requiredElements = ["BANKACCTFROM", "CHKRANGE"]  # requiredMutex

    @property
    def root(self):
        root = Element("STPCHKRQ")
        root.append(BankacctfromTestCase().root)
        root.append(ChkrangeTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKRQ)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.chkrange, CHKRANGE)


class StpchkrqChkdescTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKRQ with CHKDESC """

    __test__ = True

    requiredElements = ["BANKACCTFROM", "CHKDESC"]  # requiredMutex

    @property
    def root(self):
        root = Element("STPCHKRQ")
        root.append(BankacctfromTestCase().root)
        root.append(ChkdescTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKRQ)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.chkdesc, CHKDESC)


class StpchkrqChkrangeChkdescTestCase(unittest.TestCase):
    """ STPCHKRQ with both CHKRANGE and CHKDESC - not allowed """

    @property
    def root(self):
        root = Element("STPCHKRQ")
        root.append(BankacctfromTestCase().root)
        root.append(ChkrangeTestCase().root)
        root.append(ChkdescTestCase().root)

        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StpchknumTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKNUM with CURRENCY """

    __test__ = True

    requiredElements = ["CHECKNUM", "CHKSTATUS"]
    optionalElements = ["NAME", "DTUSER", "TRNAMT", "CHKERROR", "CURRENCY"]

    @property
    def root(self):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704"
        SubElement(root, "TRNAMT").text = "4500"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"
        currency = test_models_i18n.CurrencyTestCase().root
        root.append(currency)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKNUM)
        self.assertEqual(instance.checknum, "123")
        self.assertEqual(instance.name, "Buckaroo Banzai")
        self.assertEqual(instance.dtuser, datetime(1776, 7, 4, tzinfo=UTC))
        self.assertEqual(instance.trnamt, Decimal("4500"))
        self.assertEqual(instance.chkstatus, "0")
        self.assertEqual(instance.chkerror, "Stop check succeeded")
        self.assertIsInstance(instance.currency, CURRENCY)

    def testChkstatusConvert(self):
        """ CHKNUM.chkstatus validates enum """
        root = deepcopy(self.root)
        for code in ("0", "1", "100", "101"):
            chkstatus = root.find("CHKSTATUS")
            chkstatus.text = str(code)
            Aggregate.from_etree(root)

        chkstatus = root.find("CHKSTATUS")
        chkstatus.text = "2"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class StpchknumOrigcurrencyTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKNUM with ORIGCURRENCY """

    __test__ = True

    requiredElements = ["CHECKNUM", "CHKSTATUS"]
    optionalElements = ["NAME", "DTUSER", "TRNAMT", "CHKERROR", "ORIGCURRENCY"]

    @property
    def root(self):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704"
        SubElement(root, "TRNAMT").text = "4500"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
        root.append(origcurrency)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKNUM)
        self.assertEqual(instance.checknum, "123")
        self.assertEqual(instance.name, "Buckaroo Banzai")
        self.assertEqual(instance.dtuser, datetime(1776, 7, 4, tzinfo=UTC))
        self.assertEqual(instance.trnamt, Decimal("4500"))
        self.assertEqual(instance.chkstatus, "0")
        self.assertEqual(instance.chkerror, "Stop check succeeded")
        self.assertIsInstance(instance.origcurrency, ORIGCURRENCY)


class StpchknumCurrencyOrigcurrencyTestCase(unittest.TestCase):
    """ STPCHKNUM with both CURRENCY and ORIGCURRENCY - not allowed """

    @property
    def root(self):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704"
        SubElement(root, "TRNAMT").text = "4500"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"
        currency = test_models_i18n.CurrencyTestCase().root
        root.append(currency)
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
        root.append(origcurrency)

        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StpchkrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM", "FEE", "FEEMSG"]

    @property
    def root(self):
        root = Element("STPCHKRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(BankacctfromTestCase().root)
        stpchknum = StpchknumTestCase().root
        root.append(stpchknum)
        root.append(deepcopy(stpchknum))
        SubElement(root, "FEE").text = "25"
        SubElement(root, "FEEMSG").text = "Shit's expensive yo"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKRS)
        self.assertEqual(instance.curdef, "CAD")
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKNUM)
        self.assertIsInstance(instance[1], STPCHKNUM)
        self.assertEqual(instance.fee, Decimal("25"))
        self.assertEqual(instance.feemsg, "Shit's expensive yo")


class StpchktrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNUID", "STPCHKRQ"]

    @property
    def root(self):
        root = Element("STPCHKTRNRQ")
        SubElement(root, "TRNUID").text = "B16B00B5"
        root.append(StpchkrqTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKTRNRQ)
        self.assertEqual(instance.trnuid, "B16B00B5")
        self.assertIsInstance(instance.stpchkrq, STPCHKRQ)


class StpchktrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNUID", "STATUS"]
    optionalElements = ["STPCHKRS"]

    @property
    def root(self):
        root = Element("STPCHKTRNRS")
        SubElement(root, "TRNUID").text = "B16B00B5"
        status = test_models_common.StatusTestCase().root
        root.append(status)
        root.append(StpchkrsTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKTRNRS)
        self.assertEqual(instance.trnuid, "B16B00B5")
        self.assertIsInstance(instance.status, STATUS)
        self.assertIsInstance(instance.stpchkrs, STPCHKRS)


class StpchksyncrqTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKSYNCRQ with TOKEN """

    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def root(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(BankacctfromTestCase().root)
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)
        root.append(deepcopy(trnrq))
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKSYNCRQ)
        self.assertEqual(instance.token, "DEADBEEF")
        self.assertEqual(instance.rejectifmissing, True)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKTRNRQ)
        self.assertIsInstance(instance[1], STPCHKTRNRQ)


class StpchksyncrqTokenonlyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def root(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKENONLY").text = "Y"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(BankacctfromTestCase().root)
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)
        root.append(deepcopy(trnrq))
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKSYNCRQ)
        self.assertEqual(instance.tokenonly, True)
        self.assertEqual(instance.rejectifmissing, True)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKTRNRQ)
        self.assertIsInstance(instance[1], STPCHKTRNRQ)


class StpchksyncrqRefreshTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def root(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "REFRESH").text = "Y"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        root.append(BankacctfromTestCase().root)
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)
        root.append(deepcopy(trnrq))
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKSYNCRQ)
        self.assertEqual(instance.refresh, True)
        self.assertEqual(instance.rejectifmissing, True)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKTRNRQ)
        self.assertIsInstance(instance[1], STPCHKTRNRQ)


class StpchksyncrqEmptyTestCase(unittest.TestCase):
    @property
    def root(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StpchksyncrqMalformedTestCase(unittest.TestCase):
    def testTokenWithTokenOnly(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "TOKENONLY").text = "N"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenWithRefresh(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REFRESH").text = "N"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testTokenonlyWithRefresh(self):
        root = Element("STPCHKSYNCRQ")
        SubElement(root, "TOKENONLY").text = "N"
        SubElement(root, "REFRESH").text = "N"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        trnrq = StpchktrnrqTestCase().root
        root.append(trnrq)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class StpchksyncrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TOKEN", "BANKACCTFROM"]
    optionalElements = ["LOSTSYNC"]

    @property
    def root(self):
        root = Element("STPCHKSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(BankacctfromTestCase().root)
        trnrs = StpchktrnrsTestCase().root
        root.append(trnrs)
        root.append(deepcopy(trnrs))
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, STPCHKSYNCRS)
        self.assertEqual(instance.token, "DEADBEEF")
        self.assertEqual(instance.lostsync, True)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], STPCHKTRNRS)
        self.assertIsInstance(instance[1], STPCHKTRNRS)

    #  def testMissingAccttrnrs(self):
    #  root = deepcopy(self.root)
    #  for accttrnrs in root.findall("STPCHKTRNRS"):
    #  root.remove(accttrnrs)
    #  instance = Aggregate.from_etree(root)
    #  self.assertIsInstance(instance, STPCHKSYNCRS)
    #  self.assertEqual(instance.token, "DEADBEEF")
    #  self.assertEqual(instance.lostsync, True)
    #  self.assertEqual(len(instance), 0)


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
        stmttrnrs = StmttrnrsTestCase().root
        for i in range(2):
            root.append(deepcopy(stmttrnrs))
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
