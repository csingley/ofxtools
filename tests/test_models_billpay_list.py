# coding: utf-8
""" Unit tests for models.billpay.common """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
from ofxtools.Types import DateTime
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TranList
from ofxtools.models.common import BAL, OFXELEMENT, OFXEXTENSION
from ofxtools.models.bank.stmt import BANKACCTFROM, BANKACCTTO, PAYEE
from ofxtools.models.billpay.common import (
    BPACCTINFO,
    EXTDPAYEE,
)
from ofxtools.models.billpay.list import (
    PAYEERS,
    PAYEEMODRQ,
    PAYEEMODRS,
    PAYEEDELRQ,
    PAYEEDELRS,
)
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_i18n import CurrencyTestCase
from test_models_base import TESTAGGREGATE, TESTSUBAGGREGATE
from test_models_bank_stmt import BankaccttoTestCase, PayeeTestCase
from test_models_billpay_common import (
    ExtdpayeeTestCase,
)


class PayeerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def validSoup(cls):
        payeeid = Element("PAYEEID")
        payeeid.text = "DEADBEEF"
        payee = PayeeTestCase().root
        bankacctto = BankaccttoTestCase().root
        payacct = Element("PAYACCT")
        payacct.text = "123"

        for choice in payeeid, payee:
            root = Element("PAYEERQ")
            root.append(choice)
            root.append(bankacctto)
            root.append(payacct)
            yield root

        # FIXME
        # Multiple PAYACCT is valid

    @classproperty
    @classmethod
    def invalidSoup(cls):
        payeeid = Element("PAYEE")
        payeeid.text = "DEADBEEF"
        payee = PayeeTestCase().root
        bankacctto = BankaccttoTestCase().root
        payacct = Element("PAYACCT")
        payacct.text = "123"

        # Neither PAYEE nor PAYEEID
        root = Element("PAYEERQ")
        root.append(bankacctto)
        root.append(payacct)
        yield root

        # Both PAYEEID and PAYEE
        root = Element("PAYEERQ")
        root.append(payeeid)
        root.append(payee)
        root.append(bankacctto)
        root.append(payacct)
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class PayeersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "EXTDPAYEE", "PAYACCT"]

    @property
    def root(self):
        root = Element("PAYEERS")
        SubElement(root, "PAYEELSTID").text = "B16B00B5"
        root.append(PayeeTestCase().root)
        root.append(BankaccttoTestCase().root)
        root.append(ExtdpayeeTestCase().root)
        SubElement(root, "PAYACCT").text = "12345"
        return root

        # FIXME
        # Multiple PAYACCT is valid

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PAYEERS)
        self.assertEqual(instance.payeelstid, "B16B00B5")
        self.assertIsInstance(instance.payee, PAYEE)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)
        self.assertIsInstance(instance.extdpayee, EXTDPAYEE)
        self.assertEqual(instance.payacct, "12345")


class PayeemodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "PAYACCT"]

    @property
    def root(self):
        root = Element("PAYEEMODRQ")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        root.append(PayeeTestCase().root)
        root.append(BankaccttoTestCase().root)
        SubElement(root, "PAYACCT").text = "12345"
        return root

        # FIXME
        # Multiple PAYACCT is valid

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PAYEEMODRQ)
        self.assertEqual(instance.payeelstid, "DEADBEEF")
        self.assertIsInstance(instance.payee, PAYEE)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)
        self.assertEqual(instance.payacct, "12345")


class PayeemodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]
    optionalElements = ["PAYEE", "BANKACCTTO", "PAYACCT", "EXTDPAYEE"]

    @property
    def root(self):
        root = Element("PAYEEMODRS")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        root.append(PayeeTestCase().root)
        root.append(BankaccttoTestCase().root)
        # FIXME
        # Multiple PAYACCT is valid
        SubElement(root, "PAYACCT").text = "12345"
        root.append(ExtdpayeeTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PAYEEMODRS)
        self.assertEqual(instance.payeelstid, "DEADBEEF")
        self.assertIsInstance(instance.payee, PAYEE)
        self.assertIsInstance(instance.bankacctto, BANKACCTTO)
        self.assertEqual(instance.payacct, "12345")


class PayeedelrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]

    @property
    def root(self):
        root = Element("PAYEEDELRQ")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PAYEEDELRQ)
        self.assertEqual(instance.payeelstid, "DEADBEEF")


class PayeedelrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PAYEELSTID"]

    @property
    def root(self):
        root = Element("PAYEEDELRS")
        SubElement(root, "PAYEELSTID").text = "DEADBEEF"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PAYEEDELRS)
        self.assertEqual(instance.payeelstid, "DEADBEEF")


class PayeetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PayeerqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PayeerqTestCase, PayeemodrqTestCase, PayeedelrqTestCase:
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
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("payeerq", "payeemodrq", "payeedelrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing PAYEERQ/PAYEEMODRQ/PAYEEDELRQ
        yield root

        # Multiple PAYEERQ/PAYEEMODRQ/PAYEEDELRQ
        for Tests in [
            (PayeerqTestCase, PayeemodrqTestCase),
            (PayeerqTestCase, PayeedelrqTestCase),
            (PayeemodrqTestCase, PayeedelrqTestCase),
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


class PayeetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PayeersTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PayeersTestCase, PayeemodrsTestCase, PayeedelrsTestCase:
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
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            root = deepcopy(root_)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex = ("payeers", "payeemodrs", "payeemodrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing PAYEERS/PAYEEMODRS/PAYEEMODRS
        yield root

        # Multiple PAYEERS/PAYEEMODRS/PAYEEMODRS
        for Tests in [
            (PayeersTestCase, PayeemodrsTestCase),
            (PayeersTestCase, PayeemodrsTestCase),
            (PayeemodrsTestCase, PayeedelrsTestCase),
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


if __name__ == "__main__":
    unittest.main()
