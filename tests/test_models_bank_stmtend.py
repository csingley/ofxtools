# coding: utf-8
"""
Unit tests for models.bank.stmtend
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.stmt import BANKACCTFROM, CCACCTFROM, REWARDINFO
from ofxtools.models.bank.stmtend import (
    CLOSING, LASTPMTINFO, STMTENDRQ, STMTENDRS,
    CCCLOSING, CCSTMTENDRQ, CCSTMTENDRS,
)
from ofxtools.models.i18n import CURRENCY
from ofxtools.utils import UTC


# test imports
import base
from test_models_i18n import CurrencyTestCase
from test_models_bank_stmt import (
    BankacctfromTestCase, CcacctfromTestCase, RewardinfoTestCase,
)


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
        currency = CurrencyTestCase().root
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


class LastpmtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element("LASTPMTINFO")
        SubElement(root, "LASTPMTDATE").text = "20170501"
        SubElement(root, "LASTPMTAMT").text = "655.50"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LASTPMTINFO)
        self.assertEqual(root.lastpmtdate, datetime(2017, 5, 1, tzinfo=UTC))
        self.assertEqual(root.lastpmtamt, Decimal("655.50"))


class CcclosingTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("FITID", "DTCLOSE", "BALCLOSE", "DTPOSTSTART", "DTPOSTEND")
    optionalElements = (
        "DTOPEN",
        "DTNEXT",
        "BALOPEN",
        "INTYTD",
        "DTPMTDUE",
        "MINPMTDUE",
        "PASTDUEAMT",
        "LATEFEEAMT",
        "FINCHG",
        "INTRATEPURCH",
        "INTRATECASH",
        "INTRATEXFER",
        "PAYANDCREDIT",
        "PURANDADV",
        "DEBADJ",
        "CREDITLIMIT",
        "CASHADVCREDITLIMIT",
        "AUTOPAY",
        "LASTPMTINFO",
        "REWARDINFO",
        "MKTGINFO",
        "CURRENCY",
    )
    unsupported = ["IMAGEDATA"]

    @property
    def root(self):
        root = Element("CCCLOSING")
        SubElement(root, "FITID").text = "1001"
        SubElement(root, "DTOPEN").text = "20040701"
        SubElement(root, "DTCLOSE").text = "20040704"
        SubElement(root, "DTNEXT").text = "20040804"
        SubElement(root, "BALOPEN").text = "24.5"
        SubElement(root, "BALCLOSE").text = "26.5"
        SubElement(root, "INTYTD").text = "0.01"
        SubElement(root, "DTPMTDUE").text = "20040715"
        SubElement(root, "MINPMTDUE").text = "7.65"
        SubElement(root, "PASTDUEAMT").text = "0.35"
        SubElement(root, "LATEFEEAMT").text = "5"
        SubElement(root, "FINCHG").text = "0.5"
        SubElement(root, "INTRATEPURCH").text = "26"
        SubElement(root, "INTRATECASH").text = "30"
        SubElement(root, "INTRATEXFER").text = "28"
        SubElement(root, "PAYANDCREDIT").text = "1.5"
        SubElement(root, "PURANDADV").text = "2.75"
        SubElement(root, "DEBADJ").text = "1.45"
        SubElement(root, "CREDITLIMIT").text = "50000"
        SubElement(root, "CASHADVCREDITLIMIT").text = "5000"
        SubElement(root, "DTPOSTSTART").text = "20040701"
        SubElement(root, "DTPOSTEND").text = "20040704"
        SubElement(root, "AUTOPAY").text = "Y"
        lastpmtinfo = LastpmtinfoTestCase().root
        root.append(lastpmtinfo)
        rewardinfo = RewardinfoTestCase().root
        root.append(rewardinfo)
        SubElement(root, "MKTGINFO").text = "It's a floor wax! And a dessert topping!!"
        currency = CurrencyTestCase().root
        root.append(currency)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCCLOSING)
        self.assertEqual(root.fitid, "1001")
        self.assertEqual(root.dtopen, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtclose, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.dtnext, datetime(2004, 8, 4, tzinfo=UTC))
        self.assertEqual(root.balopen, Decimal("24.5"))
        self.assertEqual(root.balclose, Decimal("26.5"))
        self.assertEqual(root.intytd, Decimal("0.01"))
        self.assertEqual(root.dtpmtdue, datetime(2004, 7, 15, tzinfo=UTC))
        self.assertEqual(root.minpmtdue, Decimal("7.65"))
        self.assertEqual(root.pastdueamt, Decimal("0.35"))
        self.assertEqual(root.latefeeamt, Decimal("5"))
        self.assertEqual(root.finchg, Decimal("0.5"))
        self.assertEqual(root.intratepurch, Decimal("26"))
        self.assertEqual(root.intratecash, Decimal("30"))
        self.assertEqual(root.intratexfer, Decimal("28"))
        self.assertEqual(root.payandcredit, Decimal("1.5"))
        self.assertEqual(root.purandadv, Decimal("2.75"))
        self.assertEqual(root.debadj, Decimal("1.45"))
        self.assertEqual(root.creditlimit, Decimal("50000"))
        self.assertEqual(root.cashadvcreditlimit, Decimal("5000"))
        self.assertEqual(root.dtpoststart, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtpostend, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.autopay, True)
        self.assertIsInstance(root.lastpmtinfo, LASTPMTINFO)
        self.assertIsInstance(root.rewardinfo, REWARDINFO)
        self.assertEqual(root.mktginfo, "It's a floor wax! And a dessert topping!!")
        self.assertIsInstance(root.currency, CURRENCY)


class CcstmtendrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("CCACCTFROM",)
    optionalElements = ("DTSTART", "DTEND", "INCSTMTIMG")

    @property
    def root(self):
        root = Element("CCSTMTENDRQ")
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, "DTSTART").text = "20040701"
        SubElement(root, "DTEND").text = "20040704"
        SubElement(root, "INCSTMTIMG").text = "N"

        return root

    def testConvert(self):
        # Test *RQ and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDRQ)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertEqual(root.dtstart, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.incstmtimg, False)


class CcstmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ("CURDEF", "CCACCTFROM")
    optionalElements = ("CCCLOSING",)

    @property
    def root(self):
        root = Element("CCSTMTENDRS")
        SubElement(root, "CURDEF").text = "USD"
        acctfrom = CcacctfromTestCase().root
        root.append(acctfrom)
        ccclosing = CcclosingTestCase().root
        root.append(ccclosing)
        root.append(ccclosing)

        return root

    def testConvert(self):
        # Test *RS and direct child elements.
        # Everything below that is tested elsewhere.
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CCSTMTENDRS)
        self.assertEqual(instance.curdef, "USD")
        self.assertIsInstance(instance.ccacctfrom, CCACCTFROM)
        self.assertEqual(len(instance), 2)
        self.assertIsInstance(instance[0], CCCLOSING)
        self.assertIsInstance(instance[1], CCCLOSING)


class CcstmtendtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = CcstmtendrqTestCase


class CcstmtendtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = CcstmtendrsTestCase


if __name__ == "__main__":
    unittest.main()
