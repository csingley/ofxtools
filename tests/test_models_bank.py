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
from ofxtools.models.bank import *
from ofxtools.models.i18n import CURRENCY, ORIGCURRENCY, CURRENCY_CODES, COUNTRY_CODES


class BankacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [ "BANKID", "ACCTID", "ACCTTYPE" ]
    optionalElements = [ "BRANCHID", "ACCTKEY" ]
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

    requiredElements = [ "BANKACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS" ]

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

    requiredElements = [ "ACCTID" ]
    optionalElements = [ "ACCTKEY", ]
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

    requiredElements = [ "CCACCTFROM", "SUPTXDL", "XFERSRC", "XFERDEST", "SVCSTATUS" ]

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

    requiredElements = [ "INCLUDE", ]
    optionalElements = [ "DTSTART", "DTEND" ]

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

    requiredElements = [ "BANKACCTFROM", ]
    optionalElements = [ "INCTRAN", "INCLUDEPENDING", "INCTRANIMG" ]

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

    requiredElements = [ "NAME", "ADDR1", "CITY", "STATE", "POSTALCODE", "PHONE" ]
    optionalElements = [ "ADDR2", "ADDR3", "COUNTRY" ]

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

    requiredElements = ["SRVRTID", "XFERINFO"]

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

    requiredElements = ["SRVRTID"]

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

    requiredElements = ["SRVRTID", "XFERINFO"]

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

    requiredElements = ["SRVRTID"]

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
        for rq in (
            StmttrnrqTestCase, StmtendtrnrqTestCase, StpchktrnrqTestCase,
            IntratrnrqTestCase,
            # RecintratrnrqTestCase, BankmailtrnrqTestCase,
            StpchksyncrqTestCase, IntrasyncrqTestCase,
            # RecintrasyncrqTestCase, BankmailsyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # BANKMSGSRQV1 may contain
        # ["STMTTRNRQ", "STMTENDTRNRQ", "STPCHKTRNRQ", "INTRATRNRQ",
        # "RECINTRATRNRQ", "BANKMAILTRNRQ", "STPCHKSYNCRQ", "INTRASYNCRQ",
        # "RECINTRASYNCRQ", "BANKMAILSYNCRQ"]

        allowedTags = BANKMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 10)
        root = deepcopy(self.root)
        root.append(StmttrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BANKMSGSRQV1)
        self.assertEqual(len(instance), 12)
        self.assertIsInstance(instance[0], STMTTRNRQ)
        self.assertIsInstance(instance[1], STMTTRNRQ)
        self.assertIsInstance(instance[2], STMTENDTRNRQ)
        self.assertIsInstance(instance[3], STMTENDTRNRQ)
        self.assertIsInstance(instance[4], STPCHKTRNRQ)
        self.assertIsInstance(instance[5], STPCHKTRNRQ)
        self.assertIsInstance(instance[6], INTRATRNRQ)
        self.assertIsInstance(instance[7], INTRATRNRQ)
        self.assertIsInstance(instance[8], STPCHKSYNCRQ)
        self.assertIsInstance(instance[9], STPCHKSYNCRQ)
        self.assertIsInstance(instance[10], INTRASYNCRQ)
        self.assertIsInstance(instance[11], INTRASYNCRQ)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("BANKMSGSRSV1")
        for rs in (
            StmttrnrsTestCase, StmtendtrnrsTestCase, StpchktrnrsTestCase,
            IntratrnrsTestCase,
            # RecintratrnrsTestCase, BankmailtrnrsTestCase,
            StpchksyncrsTestCase, IntrasyncrsTestCase,
            # RecintrasyncrsTestCase, BankmailsyncrsTestCase,
        ):
            for i in range(2):
                root.append(rs().root)
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
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, BANKMSGSRSV1)
        self.assertEqual(len(instance), 12)
        self.assertIsInstance(instance[0], STMTTRNRS)
        self.assertIsInstance(instance[1], STMTTRNRS)
        self.assertIsInstance(instance[2], STMTENDTRNRS)
        self.assertIsInstance(instance[3], STMTENDTRNRS)
        self.assertIsInstance(instance[4], STPCHKTRNRS)
        self.assertIsInstance(instance[5], STPCHKTRNRS)
        self.assertIsInstance(instance[6], INTRATRNRS)
        self.assertIsInstance(instance[7], INTRATRNRS)
        self.assertIsInstance(instance[8], STPCHKSYNCRS)
        self.assertIsInstance(instance[9], STPCHKSYNCRS)
        self.assertIsInstance(instance[10], INTRASYNCRS)
        self.assertIsInstance(instance[11], INTRASYNCRS)

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance.statements, list)
        self.assertEqual(len(instance.statements), 2)
        self.assertIsInstance(instance.statements[0], STMTRS)
        self.assertIsInstance(instance.statements[1], STMTRS)


class InterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["XFERINFO"]

    @property
    def root(self):
        root = Element("INTERRQ")
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)


class InterrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "XFERINFO"]
    optionalElements = ["REFNUM", "RECSRVRTID", "XFERPRCSTS"]

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "20150704000000"
        dtposted = Element("DTPOSTED")
        dtposted.text = "20150704000000"

        for dtChoice in (None, dtxferprj, dtposted):
            root = Element("INTERRS")
            SubElement(root, "CURDEF").text = "EUR"
            SubElement(root, "SRVRTID").text = "DEADBEEF"
            xferinfo = XferinfoTestCase().root
            root.append(xferinfo)
            if dtChoice is not None:
                root.append(dtChoice)
            SubElement(root, "REFNUM").text = "B00B135"
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

        root = Element("INTERRS")
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


class IntermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTERMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERMODRQ)
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTERCANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERCANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "XFERINFO"]

    @property
    def root(self):
        root = Element("INTERMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        xferinfo = XferinfoTestCase().root
        root.append(xferinfo)
        xferprcsts = XferprcstsTestCase().root
        root.append(xferprcsts)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERMODRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.xferinfo, XFERINFO)
        self.assertIsInstance(instance.xferprcsts, XFERPRCSTS)


class IntercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("INTERCANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERCANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class IntertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrqTestCase, IntermodrqTestCase, IntercanrqTestCase:
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

        #  requiredMutex= ("interrq", "intermodrq", "intercanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTERRQ/INTERMODRQ/INTERCANRQ
        yield root

        # Multiple INTERRQ/INTERMODRQ/INTERCANRQ
        for Tests in [
            (InterrqTestCase, IntermodrqTestCase),
            (InterrqTestCase, IntercanrqTestCase),
            (IntermodrqTestCase, IntercanrqTestCase),
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


class IntertrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = InterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in InterrsTestCase, IntermodrsTestCase, IntercanrsTestCase:
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

        #  requiredMutex= ("interrs", "intermodrs", "intercanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing INTERRS/INTERMODRS/INTERCANRS
        yield root

        # Multiple INTERRS/INTERMODRS/INTERCANRS
        for Tests in [
            (InterrsTestCase, IntermodrsTestCase),
            (InterrsTestCase, IntercanrsTestCase),
            (IntermodrsTestCase, IntercanrsTestCase),
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


class IntersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrq = IntertrnrqTestCase().root

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
        trnrq = IntertrnrsTestCase().root

        # SYNCRQ base malformed; INTER additions OK
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

        # SYNCRQ base OK; INTER additions malformed
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


class IntersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        trnrs = IntertrnrsTestCase().root

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
        trnrs = IntertrnrsTestCase().root

        # SYNCRS base malformed; INTER additions OK
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

        # SYNCRS base OK; INTER additions malformed
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


class Interxfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRQV1")
        for rq in (
            IntertrnrqTestCase,
            #  RecintertrnrqTestCase,
            IntersyncrqTestCase,
            # RecintersyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRQV1 may contain
        # ["INTERTRNRQ", "RECINTERTRNRQ", "INTERSYNCRQ", "RECINTERSYNCRQ"]
        allowedTags = INTERXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRQV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], INTERTRNRQ)
        self.assertIsInstance(instance[1], INTERTRNRQ)
        self.assertIsInstance(instance[2], INTERSYNCRQ)
        self.assertIsInstance(instance[3], INTERSYNCRQ)


class Interxfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("INTERXFERMSGSRSV1")
        for rq in (
            IntertrnrsTestCase,
            #  RecintertrnrsTestCase,
            IntersyncrsTestCase,
            # RecintersyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # INTERXFERMSGSRSV1 may contain
        # ["INTERTRNRS", "RECINTERTRNRS", "INTERSYNCRS", "RECINTERSYNCRS"]
        allowedTags = INTERXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 4)
        root = deepcopy(self.root)
        root.append(IntertrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, INTERXFERMSGSRSV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], INTERTRNRS)
        self.assertIsInstance(instance[1], INTERTRNRS)
        self.assertIsInstance(instance[2], INTERSYNCRS)
        self.assertIsInstance(instance[3], INTERSYNCRS)


class WirebeneficiaryTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKACCTTO"]
    optionalElements = ["MEMO"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element('WIREBENEFICIARY')
        SubElement(root, "NAME").text = "Elmer Fudd"
        root.append(BankaccttoTestCase().root)
        SubElement(root, "MEMO").text = "For hunting wabbits"
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class ExtbankdescTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKID", "ADDR1", "CITY", "STATE", "POSTALCODE"]
    optionalElements = ["ADDR2", "ADDR3", "COUNTRY", "PHONE"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("EXTBANKDESC")
        SubElement(root, "NAME").text = "Lakov Trust"
        SubElement(root, "BANKID").text = "123456789"
        SubElement(root, "ADDR1").text = "123 Main St"
        SubElement(root, "ADDR2").text = "Suite 200"
        SubElement(root, "ADDR3").text = "Attn: Transfer Dept"
        SubElement(root, "CITY").text = "Dime Box"
        SubElement(root, "STATE").text = "TX"
        SubElement(root, "POSTALCODE").text = "77853"
        SubElement(root, "COUNTRY").text = "USA"
        SubElement(root, "PHONE").text = "8675309"
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest("COUNTRY", COUNTRY_CODES)


class WiredestbankTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["EXTBANKDESC"]

    @property
    def root(self):
        root = Element("WIREDESTBANK")
        root.append(ExtbankdescTestCase().root)

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREDESTBANK)
        self.assertIsInstance(instance.extbankdesc, EXTBANKDESC)


class WirerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "WIREBENEFICIARY", "TRNAMT"]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT"]

    @property
    def root(self):
        root = Element("WIRERQ")
        root.append(BankacctfromTestCase().root)
        root.append(WirebeneficiaryTestCase().root)
        root.append(WiredestbankTestCase().root)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRERQ)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.wirebeneficiary, WIREBENEFICIARY)
        self.assertIsInstance(instance.wiredestbank, WIREDESTBANK)
        self.assertEqual(instance.trnamt, Decimal("123.45"))
        self.assertEqual(instance.dtdue, datetime(1776, 7, 4, tzinfo=UTC))
        self.assertEqual(instance.payinstruct, "Fold until all sharp corners")


class WirersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURDEF", "SRVRTID", "BANKACCTFROM", "WIREBENEFICIARY", "TRNAMT"]
    optionalElements = ["WIREDESTBANK", "DTDUE", "PAYINSTRUCT", "FEE", "CONFMSG"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = Element("WIRERS")
        SubElement(root, "CURDEF").text = "USD"
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(BankacctfromTestCase().root)
        root.append(WirebeneficiaryTestCase().root)
        root.append(WiredestbankTestCase().root)
        SubElement(root, "TRNAMT").text = "123.45"
        SubElement(root, "DTDUE").text = "17760704"
        SubElement(root, "PAYINSTRUCT").text = "Fold until all sharp corners"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704"

        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704"

        for dtChoice in dtxferprj, dtposted:
            root = cls.emptyBase
            root.append(dtChoice)
            SubElement(root, "FEE").text = "123.45"
            SubElement(root, "CONFMSG").text = "You're good!"

            yield root

        # Opional mutex
        yield cls.emptyBase

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        dtxferprj = Element("DTXFERPRJ")
        dtxferprj.text = "17760704"

        dtposted = Element("DTPOSTED")
        dtposted.text = "17760704"

        # Mutex
        root = cls.emptyBase
        root.append(dtxferprj)
        root.append(dtposted)
        yield from ()

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class WirecanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("WIRECANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRECANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class WirecanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("WIRECANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIRECANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class WiretrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = WirerqTestCase


class WiretrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = WirersTestCase


class WiresyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = WiretrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = IntratrnrsTestCase().root

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class WiresyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = WiretrnrsTestCase().root

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class Wirexfermsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRQV1")
        for rq in (
            WiretrnrqTestCase,
            WiresyncrqTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIREXFERMSGSRQV1 may contain
        # ["WIRETRNRQ", "WIREERSYNCRQ"]
        allowedTags = WIREXFERMSGSRQV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrsTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRQV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRQ)
        self.assertIsInstance(instance[1], WIRETRNRQ)
        self.assertIsInstance(instance[2], WIRESYNCRQ)
        self.assertIsInstance(instance[3], WIRESYNCRQ)


class Wirexfermsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("WIREXFERMSGSRSV1")
        for rq in (
            WiretrnrsTestCase,
            WiresyncrsTestCase,
        ):
            for i in range(2):
                root.append(rq().root)
        return root

    def testdataTags(self):
        # WIRERXFERMSGSRSV1 may contain
        # ["WIRETRNRS", "WIRESYNCRS"]
        allowedTags = WIREXFERMSGSRSV1.dataTags
        self.assertEqual(len(allowedTags), 2)
        root = deepcopy(self.root)
        root.append(WiretrnrqTestCase().root)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, WIREXFERMSGSRSV1)
        self.assertEqual(len(instance), 4)
        self.assertIsInstance(instance[0], WIRETRNRS)
        self.assertIsInstance(instance[1], WIRETRNRS)
        self.assertIsInstance(instance[2], WIRESYNCRS)
        self.assertIsInstance(instance[3], WIRESYNCRS)


class RecurrinstTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["FREQ"]
    optionalElements = ["NINSTS"]

    @property
    def root(self):
        root = Element("RECURRINST")
        SubElement(root, "NINSTS").text = "3"
        SubElement(root, "FREQ").text = "MONTHLY"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECURRINST)
        self.assertEqual(instance.ninsts, 3)
        self.assertEqual(instance.freq, "MONTHLY")

    def testOneOf(self):
        self.oneOfTest("FREQ", FREQUENCIES)


class RecintrarqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "INTRARQ"]

    @property
    def root(self):
        root = Element("RECINTRARQ")
        root.append(RecurrinstTestCase().root)
        root.append(IntrarqTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRARQ)
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.intrarq, INTRARQ)


class RecintrarsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARS"]

    @property
    def root(self):
        root = Element("RECINTRARS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(IntrarsTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRARS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.intrars, INTRARS)


class RecintramodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARQ", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTRAMODRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(IntrarqTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRAMODRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.intrarq, INTRARQ)
        self.assertEqual(instance.modpending, False)


class RecintramodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTRARS", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTRAMODRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(IntrarsTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRAMODRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.intrars, INTRARS)
        self.assertEqual(instance.modpending, False)


class RecintracanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTRACANRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRACANRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintracanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTRACANRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTRACANRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintratrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecintrarqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecintrarqTestCase, RecintramodrqTestCase, RecintracanrqTestCase:
            root = cls.emptyBase
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

        #  requiredMutex= ("recintrarq", "recintramodrq", "recintracanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTRARQ/RECINTRAMODRQ/RECINTRACANRQ
        yield root

        # Multiple RECINTRARQ/RECINTRAMODRQ/RECINTRACANRQ
        for Tests in [
            (RecintrarqTestCase, RecintramodrqTestCase, RecintracanrqTestCase),
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


class RecintratrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecintrarsTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecintrarsTestCase, RecintramodrsTestCase, RecintracanrsTestCase:
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

        #  requiredMutex= ("recintrars", "recintramodrs", "recintracanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTRARS/RECINTRAMODRS/RECINTRACANRS
        yield root

        # Multiple INTERRS/INTERMODRS/INTERCANRS
        for Tests in [
            (RecintrarrsTestCase, RecintramodrsTestCase, RecintracanrsTestCase),
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


class RecintrasyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintratrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintratrnrqTestCase().root

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintrasyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintratrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintratrnrsTestCase().root

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecinterrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECURRINST", "INTERRQ"]

    @property
    def root(self):
        root = Element("RECINTERRQ")
        root.append(RecurrinstTestCase().root)
        root.append(InterrqTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERRQ)
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrq, INTERRQ)


class RecinterrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS"]

    @property
    def root(self):
        root = Element("RECINTERRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(InterrsTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrs, INTERRS)


class RecintermodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRQ", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTERMODRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(InterrqTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERMODRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrq, INTERRQ)
        self.assertEqual(instance.modpending, False)


class RecintermodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "RECURRINST", "INTERRS", "MODPENDING"]

    @property
    def root(self):
        root = Element("RECINTERMODRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        root.append(RecurrinstTestCase().root)
        root.append(InterrsTestCase().root)
        SubElement(root, "MODPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERMODRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertIsInstance(instance.recurrinst, RECURRINST)
        self.assertIsInstance(instance.interrs, INTERRS)
        self.assertEqual(instance.modpending, False)


class RecintercanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTERCANRQ")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERCANRQ)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintercanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["RECSRVRTID", "CANPENDING"]

    @property
    def root(self):
        root = Element("RECINTERCANRS")
        SubElement(root, "RECSRVRTID").text = "DEADBEEF"
        SubElement(root, "CANPENDING").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, RECINTERCANRS)
        self.assertEqual(instance.recsrvrtid, "DEADBEEF")
        self.assertEqual(instance.canpending, False)


class RecintertrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = RecinterrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase:
            root = cls.emptyBase
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

        #  requiredMutex= ("recinterrq", "recintermodrq", "recintercanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTERRQ/RECINTERMODRQ/RECINTERCANRQ
        yield root

        # Multiple RECINTERRQ/RECINTERMODRQ/RECINTERCANRQ
        for Tests in [
            (RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase),
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


class RecintertrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = RecintrarsTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase:
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

        #  requiredMutex= ("recinterrs", "recintermodrs", "recintercanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing RECINTERRS/RECINTERMODRS/RECINTERCANRS
        yield root

        # Multiple RECINTERRS/RECINTERMODRS/RECINTERCANRS
        for Tests in [
            (RecinterrrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase),
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


class RecintersyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = ["REJECTIFMISSING", "BANKACCTFROM"]

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintertrnrqTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            root.append(trnrq)
            yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrq = RecintertrnrqTestCase().root

        # SYNCRQ base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrq)
                yield root

        # SYNCRQ base OK; WIRE additions malformed
        for root in super().validSoup:
            # *ACCTFROM in the wrong place
            # (should be right after REJECTIFMISSING)
            index = list(root).index(root.find("REJECTIFMISSING"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRQ in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class RecintersyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintertrnrsTestCase().root

        for root in super().validSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        acctfrom = BankacctfromTestCase().root
        trnrs = RecintertrnrsTestCase().root

        # SYNCRS base malformed; WIRE additions OK
        for root in super().invalidSoup:
            root.append(acctfrom)
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(trnrs)
                yield root

        # SYNCRS base OK; WIRE additions malformed
        for root in super().validSoup:

            # *ACCTFROM in the wrong place
            # (should be right after LOSTSYNC)
            index = list(root).index(root.find("LOSTSYNC"))
            for n in range(index):
                root.insert(n, acctfrom)
                yield root

            #  *TRNRS in the wrong place
            #  (should be right after *ACCTFROM)
            #
            # FIXME
            # Currently the ``List`` data model offers no way to verify that
            # data appears in correct position relative to metadata, since
            # ``dataTags`` doesn't appear in the ``cls.spec``.


class EmailprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("EMAILPROF")
        SubElement(root, "CANEMAIL").text = "Y"
        SubElement(root, "CANNOTIFY").text = "N"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, EMAILPROF)
        self.assertEqual(instance.canemail, True)
        self.assertEqual(instance.cannotify, False)


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
