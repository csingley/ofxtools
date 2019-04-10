# coding: utf-8
"""
Unit tests for models.bank.interxfer
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
import base
from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.bank.interxfer import (
    XFERINFO,
    XFERPRCSTS,
    INTERRQ,
    INTERRS,
    INTERMODRQ,
    INTERMODRS,
    INTERCANRQ,
    INTERCANRS,
    INTERTRNRQ,
    INTERTRNRS,
)
from ofxtools.models.i18n import CURRENCY_CODES


# test imports
from test_models_bank_xfer import XferinfoTestCase, XferprcstsTestCase


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
        self.oneOfTest("CURDEF", CURRENCY_CODES)


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
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
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
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
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


if __name__ == "__main__":
    unittest.main()
