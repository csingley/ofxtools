# coding: utf-8
"""
Unit tests for models.bank.mail
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models.base import Aggregate

from ofxtools.models.email import MAIL
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.bank.mail import CHKMAILRS, DEPMAILRS
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_email import MailTestCase
from test_models_bank_stmt import BankacctfromTestCase, CcacctfromTestCase


class BankmailrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        mail = MailTestCase().root
        for acctfrom in bankacctfrom, ccacctfrom:
            root = Element("BANKMAILRQ")
            root.append(acctfrom)
            root.append(mail)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        mail = MailTestCase().root

        #  requiredMutexes = [("bankacctfrom", "ccacctfrom")]
        #  Neither
        root = Element("BANKMAILRQ")
        root.append(mail)
        yield root
        #  Both
        root = Element("BANKMAILRQ")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(mail)
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


class BankmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def validSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        mail = MailTestCase().root
        for acctfrom in bankacctfrom, ccacctfrom:
            root = Element("BANKMAILRS")
            root.append(acctfrom)
            root.append(mail)
            yield root

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def invalidSoup(self):
        bankacctfrom = BankacctfromTestCase().root
        ccacctfrom = CcacctfromTestCase().root
        mail = MailTestCase().root

        #  requiredMutexes = [("bankacctfrom", "ccacctfrom")]
        #  Neither
        root = Element("BANKMAILRS")
        root.append(mail)
        yield root
        #  Both
        root = Element("BANKMAILRS")
        root.append(bankacctfrom)
        root.append(ccacctfrom)
        root.append(mail)
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


class ChkmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "MAIL", "CHECKNUM"]
    optionalElements = ["TRNAMT", "DTUSER", "FEE"]

    @property
    def root(self):
        bankacctfrom = BankacctfromTestCase().root
        mail = MailTestCase().root

        root = Element("CHKMAILRS")
        root.append(bankacctfrom)
        root.append(mail)
        SubElement(root, "CHECKNUM").text = "1001"
        SubElement(root, "TRNAMT").text = "321.45"
        SubElement(root, "DTUSER").text = "21060930"
        SubElement(root, "FEE").text = "21.50"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, CHKMAILRS)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.mail, MAIL)
        self.assertEqual(instance.checknum, "1001")
        self.assertEqual(instance.trnamt, Decimal("321.45"))
        self.assertEqual(instance.dtuser, datetime(2106, 9, 30, tzinfo=UTC))
        self.assertEqual(instance.fee, Decimal("21.50"))


class DepmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "MAIL", "TRNAMT"]
    optionalElements = ["DTUSER", "FEE"]

    @property
    def root(self):
        bankacctfrom = BankacctfromTestCase().root
        mail = MailTestCase().root

        root = Element("DEPMAILRS")
        root.append(bankacctfrom)
        root.append(mail)
        SubElement(root, "TRNAMT").text = "321.45"
        SubElement(root, "DTUSER").text = "21060930"
        SubElement(root, "FEE").text = "21.50"

        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, DEPMAILRS)
        self.assertIsInstance(instance.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(instance.mail, MAIL)
        self.assertEqual(instance.trnamt, Decimal("321.45"))
        self.assertEqual(instance.dtuser, datetime(2106, 9, 30, tzinfo=UTC))
        self.assertEqual(instance.fee, Decimal("21.50"))


class BankmailtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = BankmailrqTestCase


class BankmailtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = BankmailrsTestCase


if __name__ == "__main__":
    unittest.main()
