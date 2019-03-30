# coding: utf-8
""" Common classes reused by unit tests in this package """

# stdlib imports
import xml.etree.ElementTree as ET
from copy import deepcopy

# local imports
from ofxtools.models.base import Aggregate, classproperty


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


class SyncrqTestCase(TestAggregate):
    requiredElements = ["REJECTIFMISSING"]

    mutexes = [
        ('TOKEN', 'DEADBEEF'),
        ('TOKENONLY', 'Y'),
        ('REFRESH', 'N'),
    ]

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace('TestCase', '').upper()
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
        rejectifmissing = root.find('REJECTIFMISSING')
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
    requiredElements = ["TOKEN"]
    optionalElements = ["LOSTSYNC"]

    @property
    def root(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def validSoup(cls):
        tag = cls.__name__.replace('TestCase', '').upper()
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
