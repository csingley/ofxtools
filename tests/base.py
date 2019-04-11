# coding: utf-8
""" Common classes reused by unit tests in this package """

# stdlib imports
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
import itertools

# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.common import STATUS
from ofxtools.utils import classproperty


class TestAggregate:
    __test__ = False

    # Here "Element" refers to ``xml.etree.ElementTree.Element``,
    # not ``ofxtools.Types.Element`` (i.e. includes both Aggregates & Elements)
    requiredElements = []
    optionalElements = []

    @property
    def root(self):
        """Define in subclass"""
        raise NotImplementedError

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                child = root.find(tag)
                try:
                    root.remove(child)
                except TypeError:
                    msg = "Can't find {} (from requiredElements) under {}"
                    raise ValueError(msg.format(tag, root.tag))
                with self.assertRaises(ValueError):
                    Aggregate.from_etree(root)

    def testOptional(self):
        if self.optionalElements:
            for tag in self.optionalElements:
                root = deepcopy(self.root)
                child = root.find(tag)
                try:
                    root.remove(child)
                except TypeError:
                    msg = "Can't find {} (from optionalElements) under {}"
                    raise ValueError(msg.format(tag, root.tag))
                Aggregate.from_etree(root)

    def testExtraElement(self):
        root = deepcopy(self.root)
        ET.SubElement(root, "FAKEELEMENT").text = "garbage"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def oneOfTest(self, tag, texts):
        # Make sure OneOf validator allows all legal values and disallows
        # illegal values
        for text in texts:
            root = deepcopy(self.root)
            target = root.find(".//%s" % tag)
            target.text = text
            Aggregate.from_etree(root)

        root = deepcopy(self.root)
        target = root.find(".//%s" % tag)
        target.text = "garbage"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


# StatusTestCase needs to be defined here (rather than test_models_common)
# in order to avoid circular imports
class StatusTestCase(unittest.TestCase, TestAggregate):
    __test__ = True

    requiredElements = ("CODE", "SEVERITY")
    optionalElements = ("MESSAGE",)

    @property
    def root(self):
        root = ET.Element("STATUS")
        ET.SubElement(root, "CODE").text = "0"
        ET.SubElement(root, "SEVERITY").text = "INFO"
        ET.SubElement(root, "MESSAGE").text = "Do your laundry!"
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STATUS)
        self.assertEqual(root.code, 0)
        self.assertEqual(root.severity, "INFO")
        self.assertEqual(root.message, "Do your laundry!")

    def testOneOf(self):
        self.oneOfTest("SEVERITY", ("INFO", "WARN", "ERROR"))


class TrnrqTestCase(TestAggregate):
    """
    Cf. models.common.TrnRq
    """

    wraps = NotImplemented
    optionalElements = ["CLTCOOKIE", "TAN"]

    @classproperty
    @classmethod
    def requiredElements(cls):
        tag = cls.wraps.__name__.replace("TestCase", "").upper()
        return ["TRNUID", tag]

    @classproperty
    @classmethod
    def wrapped(cls):
        return cls.wraps().root

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "TRNUID").text = "DEADBEEF"
        ET.SubElement(root, "CLTCOOKIE").text = "B00B135"
        ET.SubElement(root, "TAN").text = "B16B00B5"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        root = deepcopy(cls.emptyBase)
        root.append(cls.wrapped)
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = ET.Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = ET.Element("TRNUID")
        trnuid.text = "DEADBEEF"
        cltcookie = ET.Element("CLTCOOKIE")
        cltcookie.text = "B00B135"
        tan = ET.Element("TAN")
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

        # Don't need to test missing wrapped aggregate, since this case is
        # tested by ``requiredElements``

        # Wrapped aggregate in the wrong place (should be right after TAN)
        for root_ in cls.validSoup:
            index = list(root_).index(root_.find("TAN"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, cls.wrapped)
                yield root

    @property
    def root(self):
        return next(self.validSoup)


class TrnrsTestCase(TestAggregate):
    """
    Cf. models.common.TrnRs
    """

    wraps = NotImplemented
    optionalElements = ["CLTCOOKIE"]
    requiredElements = ["TRNUID", "STATUS"]

    @classproperty
    @classmethod
    def wrapped(cls):
        return cls.wraps().root

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "TRNUID").text = "DEADBEEF"
        status = StatusTestCase().root
        root.append(status)
        ET.SubElement(root, "CLTCOOKIE").text = "B00B135"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        root = deepcopy(cls.emptyBase)
        root.append(cls.wrapped)
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        root_ = ET.Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = ET.Element("TRNUID")
        trnuid.text = "DEADBEEF"
        status = StatusTestCase().root
        cltcookie = ET.Element("CLTCOOKIE")
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

        # Don't need to test missing wrapped aggregate, since this case is
        # tested by ``requiredElements``

        # Wrapped aggregate in the wrong place (should be right after CLTCOOKIE)
        for root_ in cls.validSoup:
            index = list(root_).index(root_.find("CLTCOOKIE"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, cls.wrapped)
                yield root

    @property
    def root(self):
        return next(self.validSoup)


class TranlistTestCase(TestAggregate):
    """
    Cf. models.common.TranList
    """

    requiredElements = ["DTSTART", "DTEND"]

    @classproperty
    @classmethod
    def validSoup(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "DTSTART").text = "20160101000000"
        ET.SubElement(root, "DTEND").text = "20161231000000"
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing DTSTART/DTEND, since this case is
        # tested by ``requiredElements``
        yield from ()

    @property
    def root(self):
        return next(self.validSoup)


class SyncrqTestCase(TestAggregate):
    """
    Cf. models.common.SyncRqlist
    """

    requiredElements = ["REJECTIFMISSING"]

    mutexes = [("TOKEN", "DEADBEEF"), ("TOKENONLY", "Y"), ("REFRESH", "N")]

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"

        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        # One of each TOKEN/TOKENONLY/REFRESH
        for tag, text in cls.mutexes:
            root = deepcopy(cls.emptyBase)
            sub = ET.Element(tag)
            sub.text = text
            root.insert(0, sub)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # TOKEN/TOKENONLY/REFRESH out of order
        for tag, text in cls.mutexes:
            root = deepcopy(cls.emptyBase)
            sub = ET.Element(tag)
            sub.text = text
            root.insert(1, sub)  # Should be root.insert(0, sub) to be valid
            yield root

        # TOKEN/TOKENONLY/REFRESH missing
        yield cls.emptyBase

        # TOKEN/TOKENONLY/REFRESH duplicated
        for tag, text in cls.mutexes:
            root = deepcopy(cls.emptyBase)
            sub = ET.Element(tag)
            sub.text = text
            root.insert(0, sub)
            root.insert(0, sub)
            yield root

        # REJECTIFMISSING duplicated
        root = deepcopy(cls.emptyBase)
        rejectifmissing = root.find("REJECTIFMISSING")
        root.append(rejectifmissing)
        root.append(rejectifmissing)

        yield root

    @property
    def root(self):
        # Use the first return value for TestAggregate test methods
        return next(self.validSoup)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class SyncrsTestCase(TestAggregate):
    """
    Cf. models.common.SyncRslist
    """

    requiredElements = ["TOKEN"]
    optionalElements = ["LOSTSYNC"]

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def validSoup(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "LOSTSYNC").text = "Y"

        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # TOKEN/LOSTSYNC out of order
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "LOSTSYNC").text = "Y"
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"

        yield root

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)
