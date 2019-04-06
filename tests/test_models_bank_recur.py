# coding: utf-8
"""
Unit tests for models.bank.recur
"""
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy
import itertools


# local imports
from ofxtools.models.base import Aggregate, classproperty
from ofxtools.models.bank.intraxfer import INTRARQ, INTRARS
from ofxtools.models.bank.interxfer import INTERRQ, INTERRS
from ofxtools.models.bank.recur import (
    FREQUENCIES,
    RECURRINST,
    RECINTRARQ,
    RECINTRARS,
    RECINTERRQ,
    RECINTERRS,
    RECINTRAMODRQ,
    RECINTRAMODRS,
    RECINTRACANRQ,
    RECINTRACANRS,
    RECINTERMODRQ,
    RECINTERMODRS,
    RECINTERCANRQ,
    RECINTERCANRS,
)


# test imports
import base
from test_models_bank_intraxfer import IntrarqTestCase, IntrarsTestCase
from test_models_bank_interxfer import InterrqTestCase, InterrsTestCase


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
            (RecintrarqTestCase, RecintramodrqTestCase, RecintracanrqTestCase)
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

        # Multiple RECINTRARS/RECINTRAMODRS/RECINTRACANRS
        for Tests in [
            (RecintrarsTestCase, RecintramodrsTestCase, RecintracanrsTestCase)
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
            (RecinterrqTestCase, RecintermodrqTestCase, RecintercanrqTestCase)
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

    wraps = RecinterrsTestCase

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
            (RecinterrsTestCase, RecintermodrsTestCase, RecintercanrsTestCase)
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
