# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy
import itertools


# local imports
import base
import test_models_common
import test_models_i18n

from ofxtools.utils import UTC
import ofxtools.models
from ofxtools.models.base import Aggregate, classproperty
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
    XFERINFO,
    XFERPRCSTS,
    INTRARQ,
    INTRARS,
    INTRAMODRQ,
    INTRAMODRS,
    INTRACANRQ,
    INTRACANRS,
    INTRATRNRQ,
    INTRATRNRS,
    INTRASYNCRQ,
    INTRASYNCRS,
    BANKMSGSETV1,
    BANKMSGSET,
    EMAILPROF,
    ACCTTYPES,
    INV401KSOURCES
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
        currency = test_models_i18n.CurrencyTestCase().root
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
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
        currency = test_models_i18n.CurrencyTestCase().root
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root

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


class StmtendtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StmtendrqTestCase


class StmtendtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StmtendrsTestCase


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

    requiredElements = ["BANKACCTFROM"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKRQ")
        root.append(BankacctfromTestCase().root)
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        chkrange = ChkrangeTestCase().root
        chkdesc = ChkdescTestCase().root
        for choice in chkrange, chkdesc:
            root = cls.emptyBase
            root.append(choice)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        chkrange = ChkrangeTestCase().root
        chkdesc = ChkdescTestCase().root

        #  requiredMutexes = [("chkrange", "chkdesc")]
        #  Neither
        root = cls.emptyBase
        yield root
        #  Both
        root.append(chkrange)
        root.append(chkdesc)
        yield root

        #  FIXME
        #  Check out-of-order errors

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class StpchknumTestCase(unittest.TestCase, base.TestAggregate):
    """ STPCHKNUM with CURRENCY """

    __test__ = True

    requiredElements = ["CHECKNUM", "CHKSTATUS"]
    optionalElements = ["NAME", "DTUSER", "TRNAMT", "CHKERROR"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("STPCHKNUM")
        SubElement(root, "CHECKNUM").text = "123"
        SubElement(root, "NAME").text = "Buckaroo Banzai"
        SubElement(root, "DTUSER").text = "17760704"
        SubElement(root, "TRNAMT").text = "4500"
        SubElement(root, "CHKSTATUS").text = "0"
        SubElement(root, "CHKERROR").text = "Stop check succeeded"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        currency = test_models_i18n.CurrencyTestCase().root
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root
        for currencyChoice in (None, currency, origcurrency):
            root = deepcopy(cls.emptyBase)
            if currencyChoice is not None:
                root.append(currencyChoice)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("currency", "origcurrency")]
        currency = test_models_i18n.CurrencyTestCase().root
        origcurrency = test_models_i18n.OrigcurrencyTestCase().root

        root = deepcopy(cls.emptyBase)
        root.append(currency)
        root.append(origcurrency)
        yield root

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest('CHKSTATUS', ["0", "1", "100", "101"])


class StpchkrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "BANKACCTFROM", "FEE", "FEEMSG"]

    @property
    def root(self):
        root = Element("STPCHKRS")
        SubElement(root, "CURDEF").text = "CAD"
        root.append(BankacctfromTestCase().root)
        #  SubElement(root, "FEE").text = "25"
        #  SubElement(root, "FEEMSG").text = "Shit's expensive yo"
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


class StpchktrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = StpchkrqTestCase


class StpchktrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = StpchkrsTestCase


class StpchksyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = StpchktrnrqTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            root.append(deepcopy(acctfrom))
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrq))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        #  trnrq = StpchktrnrqTestCase().root

        # SYNCRQ base malformed; STPCHK additions OK
        for root_ in super().invalidSoup:
            root = deepcopy(root_)
            root.append(acctfrom)
            yield root

        # SYNCRQ base OK; STPCHK additions malformed
        for root_ in super().validSoup:
            # BANKACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root_).index(root_.find("REJECTIFMISSING"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, acctfrom)
                yield root

            #  STPCHKTRNRQ in the wrong place
            #  (should be right after BANKACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class StpchksyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    requiredElements = base.SyncrsTestCase.requiredElements + ["BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = StpchktrnrsTestCase().root

        for root_ in super().validSoup:
            root = deepcopy(root_)
            root.append(deepcopy(acctfrom))
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        #  trnrs = StpchktrnrsTestCase().root

        # SYNCRS base malformed; STPCHK additions OK
        for root_ in super().invalidSoup:
            root = deepcopy(root_)
            root.append(acctfrom)
            yield root

        # SYNCRS base OK; STPCHK additions malformed
        for root_ in super().validSoup:
            # BANKACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root_).index(root_.find("LOSTSYNC"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, acctfrom)
                yield root

            #  STPCHKTRNRS in the wrong place
            #  (should be right after BANKACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class XferinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TRNAMT"]
    optionalElements = ["DTDUE"]

    @classproperty
    @classmethod
    def validSoup(cls):
        bankacctfrom = BankacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        ccacctto = CcaccttoTestCase().root

        for acctfrom in (bankacctfrom, ccacctfrom):
            for acctto in (bankacctto, ccacctto):
                root = Element('XFERINFO')
                root.append(acctfrom)
                root.append(acctto)
                SubElement(root, "TRNAMT").text = "257.53"
                SubElement(root, "DTDUE").text = "20080930000000"
                yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = Element('XFERINFO')

        bankacctfrom = BankacctfromTestCase().root
        bankacctto = BankaccttoTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        ccacctto = CcaccttoTestCase().root
        trnamt = Element("TRNAMT")
        trnamt.text = "257.53"

        # requiredMutexes = [("bankacctfrom", "ccacctfrom"), ("bankacctto", "ccacctto")]
        # Missing BANKACCTFROM/CCACCTFROM
        root = deepcopy(root_)
        root.append(bankacctto)
        root.append(trnamt)
        yield root

        root = deepcopy(root_)
        root.append(bankacctfrom)
        root.append(trnamt)
        yield root

        # Both BANKACCTFROM & CCACCTFROM / BANKACCTTO & CCACCTTO
        root = deepcopy(root_)
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(trnamt)
        yield root

        root = deepcopy(root_)
        root.append(bankacctto)
        root.append(ccacctto)
        root.append(trnamt)
        yield root

        # FIXME
        # test out-of-order errors

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class XferprcstsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERPRCCODE", "DTXFERPRC"]

    @property
    def root(self):
        root = Element("XFERPRCSTS")
        SubElement(root, "XFERPRCCODE").text = "POSTEDON"
        SubElement(root, "DTXFERPRC").text = "20071231000000"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, XFERPRCSTS)
        self.assertEqual(instance.xferprccode, "POSTEDON")
        self.assertEqual(instance.dtxferprc, datetime(2007, 12, 31, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest(
            "XFERPRCCODE",
            ["WILLPROCESSON", "POSTEDON", "NOFUNDSON", "CANCELEDON", "FAILEDON"],
        )


class IntrarqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @property
    def root(self):
        root = Element("INTRARQ")
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRARQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)


class IntrarsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["RECSRVRTID", "XFERPRCSTS"]

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        for dtChoice in (None, dtxferprj, dtposted):
            root = Element("INTRARS")
            SubElement(root, "CURDEF").text = "EUR"
            SubElement(root, "SRVRTID").text = "DEADBEEF"
            xferinfo = XferinfoTestCase().root
            root.append(xferinfo)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "RECSRVRTID").text = "B16B00B5"
            xferprcsts = XferprcstsTestCase().root
            root.append(xferprcsts)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  optionalMutexes = [("dtxferprj", "dtposted")]
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        root = Element("INTRARS")
        SubElement(root, "CURDEF").text = "EUR"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)
        root.append(dtxferprj)
        root.append(dtposted)

        yield root

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest('CURDEF', CURRENCY_CODES)


class IntramodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTRAMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRAMODRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntracanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTRACANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRACANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntramodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTRAMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)
        xferprcsts = XferprcstsTestCase().root
        root.append(xferprcsts)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRAMODRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertIsInstance(instance.xferprcsts, XFERPRCSTS)


class IntracanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTRACANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTRACANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntratrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = IntrarqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarqTestCase, IntramodrqTestCase, IntracanrqTestCase:
            root = deepcopy(cls.emptyBase)
            rq = Test().root
            root.append(rq)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = Element("TRNUID")
        trnuid.text = "DEADBEEF"
        cltcookie = Element("CLTCOOKIE")
        cltcookie.text = "B00B135"
        tan = Element("TAN")
        tan.text = "B16B00B5"

        legal = [trnuid, cltcookie, tan]
        for elements in itertools.permutations(legal):
            if elements == legal:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("intrarq", "intramodrq", "intracanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTRARQ/INTRAMODRQ/INTRACANRQ
        yield root

        # Multiple INTRARQ/INTRAMODRQ/INTRACANRQ
        for Tests in [
            (IntrarqTestCase, IntramodrqTestCase),
            (IntrarqTestCase, IntracanrqTestCase),
            (IntramodrqTestCase, IntracanrqTestCase),
        ]:
            root = deepcopy(cls.emptyBase)
            for Test in Tests:
                root.append(Test().root)
            yield root

        # Wrapped aggregate in the wrong place (should be right after TAN)

        root_ = deepcopy(cls.emptyBase)
        index = list(root_).index(root_.find("TAN"))
        for n in range(index):
            root = deepcopy(root_)
            root.insert(n, cls.wrapped)
            yield root


class IntratrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = IntrarqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in IntrarsTestCase, IntramodrsTestCase, IntracanrsTestCase:
            root = deepcopy(cls.emptyBase)
            rs = Test().root
            root.append(rs)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = Element(tag)

        # TRNUID/STATUS/CLTCOOKIE out of order
        trnuid = Element("TRNUID")
        trnuid.text = "DEADBEEF"
        status = base.StatusTestCase().root
        cltcookie = Element("CLTCOOKIE")
        cltcookie.text = "B00B135"

        legal = [trnuid, status, cltcookie]
        for elements in itertools.permutations(legal):
            if elements == legal:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("intrars", "intramodrs", "intracanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTRARS/INTRAMODRS/INTRACANRS
        yield root

        # Multiple INTRARS/INTRAMODRS/INTRACANRS
        for Tests in [
            (IntrarsTestCase, IntramodrsTestCase),
            (IntrarsTestCase, IntracanrsTestCase),
            (IntramodrsTestCase, IntracanrsTestCase),
        ]:
            root = deepcopy(cls.emptyBase)
            for Test in Tests:
                root.append(Test().root)
            yield root

        # Wrapped aggregate in the wrong place (should be right after CLTCOOKIE)

        root_ = deepcopy(cls.emptyBase)
        index = list(root_).index(root_.find("CLTCOOKIE"))
        for n in range(index):
            root = deepcopy(root_)
            root.insert(n, cls.wrapped)
            yield root


class IntrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntratrnrqTestCase().root

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

        # SYNCRQ base malformed; INTRA additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrq))
                    yield root

        # SYNCRQ base OK; INTRA additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("REJECTIFMISSING"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class IntrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntratrnrsTestCase().root

        for root_ in super().validSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

    @property
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntratrnrsTestCase().root

        # SYNCRS base malformed; INTRA additions OK
        for root_ in super().invalidSoup:
            for acctfrom in (bankacctfrom, ccacctfrom):
                root = deepcopy(root_)
                root.append(deepcopy(acctfrom))
                # 0 contained aggregrates
                yield root
                # 1 or more contained aggregates
                for n in range(2):
                    root.append(deepcopy(trnrs))
                    yield root

        # SYNCRS base OK; INTRA additions malformed
        for root_ in super().validSoup:
            # *ACCTFROM missing (required)
            yield root_
            # Both BANKACCTFROM and CCACCTFROM (mutex)
            root = deepcopy(root_)
            root.append(bankacctfrom)
            root.append(ccacctfrom)
            yield root

            root = deepcopy(root_)
            root.append(ccacctfrom)
            root.append(bankacctfrom)
            yield root

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            for acctfrom in (bankacctfrom, ccacctfrom):
                index = list(root_).index(root_.find("LOSTSYNC"))
                for n in range(index):
                    root = deepcopy(root_)
                    root.insert(n, acctfrom)
                    yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


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
