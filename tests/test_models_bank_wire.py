# coding: utf-8
"""
Unit tests for models.bank.wire
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.bank.wire import (
    EXTBANKDESC,
    WIREDESTBANK,
    WIREBENEFICIARY,
    WIRERQ,
    WIRERS,
    WIRECANRQ,
    WIRECANRS,
    WIRETRNRQ,
    WIRETRNRS,
)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_bank_stmt import BankacctfromTestCase, BankaccttoTestCase


class WirebeneficiaryTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["NAME", "BANKACCTTO"]
    optionalElements = ["MEMO"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root = Element("WIREBENEFICIARY")
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

    requiredElements = [
        "CURDEF",
        "SRVRTID",
        "BANKACCTFROM",
        "WIREBENEFICIARY",
        "TRNAMT",
    ]
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


if __name__ == "__main__":
    unittest.main()
