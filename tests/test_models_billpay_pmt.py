# coding: utf-8
""" Unit tests for models.billpay.pmt """
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
from ofxtools.models.billpay.common import (
    PMTINFO,
    EXTDPAYEE,
    PMTPRCSTS,
)
from ofxtools.models.billpay.pmt import (
    PMTRQ,
    PMTRS,
    PMTMODRQ,
    PMTMODRS,
    PMTCANRQ,
    PMTCANRS,
    PMTINQRQ,
    PMTINQRS,
)
from ofxtools.models.i18n import CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_billpay_common import (
    PmtinfoTestCase,
    ExtdpayeeTestCase,
    PmtprcstsTestCase,
)


class PmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PMTINFO"]

    @property
    def root(self):
        root = Element("PMTRQ")
        root.append(PmtinfoTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTRQ)
        self.assertIsInstance(instance.pmtinfo, PMTINFO)


class PmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PAYEELSTID", "CURDEF", "PMTINFO", "PMTPRCSTS"]

    @property
    def root(self):
        root = Element("PMTRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        SubElement(root, "PAYEELSTID").text = "B16B00B5"
        SubElement(root, "CURDEF").text = "GBP"
        root.append(PmtinfoTestCase().root)
        root.append(ExtdpayeeTestCase().root)
        SubElement(root, "CHECKNUM").text = "215"
        root.append(PmtprcstsTestCase().root)
        SubElement(root, "RECSRVRTID").text = "B00B135"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertEqual(instance.payeelstid, "B16B00B5")
        self.assertEqual(instance.curdef, "GBP")
        self.assertIsInstance(instance.pmtinfo, PMTINFO)
        self.assertIsInstance(instance.extdpayee, EXTDPAYEE)
        self.assertEqual(instance.checknum, "215")
        self.assertIsInstance(instance.pmtprcsts, PMTPRCSTS)
        self.assertEqual(instance.recsrvrtid, "B00B135")

    def testOneOf(self):
        self.oneOfTest("CURDEF", CURRENCY_CODES)


class PmtmodrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTINFO"]

    @property
    def root(self):
        root = Element("PMTMODRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(PmtinfoTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTMODRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.pmtinfo, PMTINFO)


class PmtmodrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTINFO"]
    optionalElements = ["PMTPRCSTS"]

    @property
    def root(self):
        root = Element("PMTMODRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(PmtinfoTestCase().root)
        root.append(PmtprcstsTestCase().root)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTMODRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")
        self.assertIsInstance(instance.pmtinfo, PMTINFO)
        self.assertIsInstance(instance.pmtprcsts, PMTPRCSTS)


class PmtcanrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("PMTCANRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTCANRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class PmtcanrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("PMTCANRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTCANRS)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class PmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PmtrqTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        for Test in PmtrqTestCase, PmtmodrqTestCase, PmtcanrqTestCase:
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

        #  requiredMutex= ("pmtrq", "pmtmodrq", "pmtcanrq")
        root_ = deepcopy(cls.emptyBase)
        # Missing PMTRQ/PMTMODRQ/PMTCANRQ
        yield root

        # Multiple PMTRQ/PMTMODRQ/PMTCANRQ
        for Tests in [
            (PmtrqTestCase, PmtmodrqTestCase),
            (PmtrqTestCase, PmtcanrqTestCase),
            (PmtmodrqTestCase, PmtcanrqTestCase),
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

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class PmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PmtrsTestCase

    @classproperty
    @classmethod
    def validSoup(cls):
        # Empty *RS is OK
        yield cls.emptyBase

        for Test in PmtrsTestCase, PmtmodrsTestCase, PmtcanrsTestCase:
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
            root = Element(tag)
            for element in elements:
                root.append(element)
            root.append(cls.wrapped)
            yield root

        #  requiredMutex= ("pmtrs", "pmtmodrs", "pmtcanrs")
        root_ = deepcopy(cls.emptyBase)
        # Missing PMTRS/PMTMODRS/PMTCANRS
        yield root

        # Multiple PMTRS/PMTMODRS/PMTCANRS
        for Tests in [
            (PmtrsTestCase, PmtmodrsTestCase),
            (PmtrsTestCase, PmtcanrsTestCase),
            (PmtmodrsTestCase, PmtcanrsTestCase),
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

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class PmtinqrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID"]

    @property
    def root(self):
        root = Element("PMTINQRQ")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTINQRQ)
        self.assertEqual(instance.srvrtid, "DEADBEEF")


class PmtinqrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SRVRTID", "PMTPRCSTS"]
    optionalElements = ["CHECKNUM"]

    @property
    def root(self):
        root = Element("PMTINQRS")
        SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(PmtprcstsTestCase().root)
        SubElement(root, "CHECKNUM").text = "215"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, PMTINQRS)
        self.assertIsInstance(instance.pmtprcsts, PMTPRCSTS)


class PmtinqtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PmtinqrqTestCase


class PmtinqtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PmtinqrsTestCase


if __name__ == "__main__":
    unittest.main()
