# coding: utf-8
""" Common classes reused by unit tests in this package """

# stdlib imports
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
import itertools
from typing import List, Dict, Sequence, Any

# local imports
import ofxtools.models
from ofxtools.models.base import Aggregate, UnknownTagWarning
from ofxtools.models.common import STATUS
from ofxtools.utils import classproperty, indent
from ofxtools.Parser import OFXTree, TreeBuilder


class TestAggregate:
    __test__ = False

    # Here "Element" refers to ``xml.etree.ElementTree.Element``,
    # not ``ofxtools.Types.Element`` (i.e. includes both Aggregates & Elements)
    requiredElements: List[str] = []
    optionalElements: List[str] = []
    oneOfs: Dict[str, Sequence[str]] = {}
    unsupported: List[str] = []

    etree: Any = NotImplemented
    aggregate: Any = NotImplemented

    @classproperty
    @classmethod
    def validSoup(cls):
        """Define in subclass"""
        yield from ()

    @classproperty
    @classmethod
    def invalidSoup(cls):
        """Define in subclass"""
        yield ET.Element("NOTAREALOFXTAG")

    def testValidSoup(self):
        for etree in self.validSoup:
            Aggregate.from_etree(etree)

    def testInvalidSoup(self):
        for etree in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(etree)

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                etree = deepcopy(self.etree)
                child = etree.find(tag)
                try:
                    etree.remove(child)
                except TypeError:
                    msg = "Can't find {} (from requiredElements) under {}"
                    raise ValueError(msg.format(tag, etree.tag))
                with self.assertRaises(ValueError):
                    Aggregate.from_etree(etree)

    def testOptional(self):
        if self.optionalElements:
            for tag in self.optionalElements:
                etree = deepcopy(self.etree)
                child = etree.find(tag)
                try:
                    etree.remove(child)
                except TypeError:
                    msg = "Can't find {} (from optionalElements) under {}"
                    raise ValueError(msg.format(tag, etree.tag))
                Aggregate.from_etree(etree)

    def testExtraElement(self):
        #  OFXv1 Section 2.3.1:
        #    Open Financial Exchange is not completely SGML-compliant because the
        #    specification allows unrecognized tags to be present. Clients and servers
        #    must skip over the unrecognized tags. That is, if a client or server does
        #    not recognize <XYZ>, it must ignore the tag and its enclosed data.
        etree = deepcopy(self.etree)
        ET.SubElement(etree, "FAKEELEMENT").text = "garbage"
        with self.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(etree)

    def oneOfTest(self, tag, texts):
        # Make sure OneOf validator allows all legal values and disallows
        # illegal values
        for text in texts:
            etree = deepcopy(self.etree)
            target = etree.find(".//%s" % tag)
            target.text = text
            Aggregate.from_etree(etree)

        etree = deepcopy(self.etree)
        target = etree.find(".//%s" % tag)
        target.text = "garbage"
        with self.assertRaises(ValueError):
            Aggregate.from_etree(etree)

    def assertElement(self, elem, tag, text, length):
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, tag)
        self.assertEqual(elem.text, text)
        self.assertEqual(len(elem), length)

    def _eqEtree(self, elem0, elem1):
        """Equality testing for ``xml.etree.ElementTree`` instances.

        Instances are equal if tag, text, and children are equal.
        """

        self.assertIsInstance(elem0, ET.Element)
        self.assertIsInstance(elem1, ET.Element)
        self.assertEqual(elem0.tag, elem1.tag)
        self.assertEqual(elem0.text, elem1.text)
        self.assertEqual(len(elem0), len(elem1))
        for child0, child1 in zip(elem0, elem1):
            self._eqEtree(child0, child1)

    def _eqAggregate(self, agg0, agg1):
        """Equality testing for ``ofxtools.models.base.Aggregate`` instances.

        Run down the list of the spec of class attributes (excluding contained list
        elements/aggregates) and test equality of each instance attribute.

        Then use the list API to test equality of each contained list element/aggregate.
        """
        self.assertIsInstance(agg0, Aggregate)
        self.assertIsInstance(agg1, Aggregate)
        self.assertIs(agg0.__class__, agg1.__class__)
        for attr in agg0.spec_no_listaggregates:
            attr0 = getattr(agg0, attr)
            attr1 = getattr(agg1, attr)
            if isinstance(attr0, Aggregate):
                self.assertIsInstance(attr1, Aggregate)
                self._eqAggregate(attr0, attr1)
            else:
                self.assertEqual(attr0, attr1)

        self.assertEqual(len(agg0), len(agg1))
        for n, item0 in enumerate(agg0):
            item1 = agg1[n]
            if isinstance(item0, Aggregate):
                self.assertIsInstance(item1, Aggregate)
                self._eqAggregate(item0, item1)
            else:
                self.assertEqual(item0, item1)

    def testFromEtree(self):
        self._eqAggregate(self.aggregate, Aggregate.from_etree(self.etree))

    def testToEtree(self):
        self._eqEtree(self.etree, self.aggregate.to_etree())

    def testOneOf(self):
        for tag, choices in self.oneOfs.items():
            self.oneOfTest(tag, choices)

    def testUnsupported(self):
        instance = Aggregate.from_etree(self.etree)
        for unsupp in self.unsupported:
            setattr(instance, unsupp, "FOOBAR")
            self.assertIsNone(getattr(instance, unsupp))


# StatusTestCase needs to be defined here (rather than test_models_common)
# in order to avoid circular imports
class StatusTestCase(unittest.TestCase, TestAggregate):
    __test__ = True

    requiredElements = ["CODE", "SEVERITY"]
    optionalElements = ["MESSAGE"]
    oneOfs = {"SEVERITY": ("INFO", "WARN", "ERROR")}

    @classproperty
    @classmethod
    def etree(cls):
        etree = ET.Element("STATUS")
        ET.SubElement(etree, "CODE").text = "0"
        ET.SubElement(etree, "SEVERITY").text = "INFO"
        ET.SubElement(etree, "MESSAGE").text = "Do your laundry!"
        return etree

    @classproperty
    @classmethod
    def aggregate(cls):
        return STATUS(code=0, severity="INFO", message="Do your laundry!")


class TrnrqTestCase(TestAggregate):
    """
    Cf. models.wrapperbases.TrnRq
    """

    wraps: Any = NotImplemented
    optionalElements = ["CLTCOOKIE", "TAN"]

    @classproperty
    @classmethod
    def requiredElements(cls):
        tag = cls.wraps.__name__.replace("TestCase", "").upper()
        return ["TRNUID", tag]

    @classproperty
    @classmethod
    def wrapped(cls):
        return cls.wraps().etree

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        tag = cls.wraps.__name__.replace("TestCase", "").upper()
        Model = getattr(ofxtools.models, tag)
        return Model(
            cls.wraps.aggregate, trnuid="DEADBEEF", cltcookie="B00B135", tan="B16B00B5"
        )

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        etree = ET.Element(tag)
        ET.SubElement(etree, "TRNUID").text = "DEADBEEF"
        ET.SubElement(etree, "CLTCOOKIE").text = "B00B135"
        ET.SubElement(etree, "TAN").text = "B16B00B5"
        return etree

    @classproperty
    @classmethod
    def validSoup(cls):
        etree = cls.emptyBase
        etree.append(cls.wrapped)
        yield etree

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        etree_ = ET.Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = ET.Element("TRNUID")
        trnuid.text = "DEADBEEF"
        cltcookie = ET.Element("CLTCOOKIE")
        cltcookie.text = "B00B135"
        tan = ET.Element("TAN")
        tan.text = "B16B00B5"

        legal = [trnuid, cltcookie, tan]
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            etree = deepcopy(etree_)
            for element in elements:
                etree.append(element)
            etree.append(cls.wrapped)
            yield etree

        # Don't need to test missing wrapped aggregate, since this case is
        # tested by ``requiredElements``

        # Wrapped aggregate in the wrong place (should be right after TAN)
        for etree_ in cls.validSoup:
            index = list(etree_).index(etree_.find("TAN"))
            for n in range(index):
                etree = deepcopy(etree_)
                etree.insert(n, cls.wrapped)
                yield etree


class TrnrsTestCase(TestAggregate):
    """
    Cf. models.wrapperbases.TrnRs
    """

    wraps: Any = NotImplemented
    optionalElements = ["CLTCOOKIE"]
    requiredElements = ["TRNUID", "STATUS"]

    @classproperty
    @classmethod
    def wrapped(cls):
        return cls.wraps().etree

    @classproperty
    @classmethod
    def etree(self):
        return next(self.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        raise NotImplementedError

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        etree = ET.Element(tag)
        ET.SubElement(etree, "TRNUID").text = "DEADBEEF"
        status = StatusTestCase().etree
        etree.append(status)
        ET.SubElement(etree, "CLTCOOKIE").text = "B00B135"
        return etree

    @classproperty
    @classmethod
    def validSoup(cls):
        etree = deepcopy(cls.emptyBase)
        etree.append(cls.wrapped)
        yield etree

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing TRNUID, since this case is
        # tested by ``requiredElements``
        tag = cls.__name__.replace("TestCase", "").upper()
        etree_ = ET.Element(tag)

        # TRNUID/COOKIE/TAN out of order
        trnuid = ET.Element("TRNUID")
        trnuid.text = "DEADBEEF"
        status = StatusTestCase().etree
        cltcookie = ET.Element("CLTCOOKIE")
        cltcookie.text = "B00B135"

        legal = [trnuid, status, cltcookie]
        legal_tags = [el.tag for el in legal]
        for elements in itertools.permutations(legal):
            if [el.tag for el in elements] == legal_tags:
                continue
            etree = deepcopy(etree_)
            for element in elements:
                etree.append(element)
            etree.append(cls.wrapped)
            yield etree

        # Don't need to test missing wrapped aggregate, since this case is
        # tested by ``requiredElements``

        # Wrapped aggregate in the wrong place (should be right after CLTCOOKIE)
        for etree_ in cls.validSoup:
            index = list(etree_).index(etree_.find("CLTCOOKIE"))
            for n in range(index):
                etree = deepcopy(etree_)
                etree.insert(n, cls.wrapped)
                yield etree


class TranlistTestCase(TestAggregate):
    """
    Cf. models.common.TranList
    """

    requiredElements = ["DTSTART", "DTEND"]

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def validSoup(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        ET.SubElement(root, "DTSTART").text = "20160101000000.000[+0:UTC]"
        ET.SubElement(root, "DTEND").text = "20161231000000.000[+0:UTC]"
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Don't need to test missing DTSTART/DTEND, since this case is
        # tested by ``requiredElements``
        # FIXME
        yield from ()


class SyncrqTestCase(TestAggregate):
    """
    Cf. models.common.SyncRqlist
    """

    requiredElements = ["REJECTIFMISSING"]
    mutexes = [("TOKEN", "DEADBEEF"), ("TOKENONLY", "Y"), ("REFRESH", "N")]

    @classproperty
    @classmethod
    def etree(self):
        # Use the first return value for TestAggregate test methods
        return next(self.validSoup)

    @classproperty
    @classmethod
    def emptyBase(cls):
        tag = cls.__name__.replace("TestCase", "").upper()
        root = ET.Element(tag)
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        # One of each TOKEN/TOKENONLY/REFRESH
        for tag, text in cls.mutexes:
            root = cls.emptyBase
            ET.SubElement(root, tag).text = text
            ET.SubElement(root, "REJECTIFMISSING").text = "Y"
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # TOKEN/TOKENONLY/REFRESH missing
        yield cls.emptyBase

        # TOKEN/TOKENONLY/REFRESH out of order
        for tag, text in cls.mutexes:
            root = cls.emptyBase
            sub = ET.Element(tag)
            sub.text = text
            root.insert(1, sub)  # Should be etree.insert(0, sub) to be valid
            yield root

        # TOKEN/TOKENONLY/REFRESH duplicated
        for tag, text in cls.mutexes:
            root = cls.emptyBase
            sub = ET.Element(tag)
            sub.text = text
            root.insert(0, sub)
            root.insert(0, sub)
            yield root

        # REJECTIFMISSING duplicated
        root = cls.emptyBase
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        yield root


class SyncrsTestCase(TestAggregate):
    """
    Cf. models.common.SyncRslist
    """

    requiredElements = ["TOKEN"]
    optionalElements = ["LOSTSYNC"]

    @classproperty
    @classmethod
    def etree(self):
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
        etree = ET.Element(tag)
        ET.SubElement(etree, "LOSTSYNC").text = "Y"
        ET.SubElement(etree, "TOKEN").text = "DEADBEEF"

        yield etree


class OfxTestCase:
    ofx: Any = NotImplemented

    @classmethod
    def setUpClass(cls):
        cls.tree = OFXTree()
        parser = TreeBuilder()
        parser.feed(cls.ofx)
        cls.tree._root = parser.close()

    def _eqAggregate(self, agg0, agg1):
        self.assertIsInstance(agg0, Aggregate)
        self.assertIsInstance(agg1, Aggregate)
        self.assertIs(agg0.__class__, agg1.__class__)
        for attr in agg0.spec_no_listaggregates:
            attr0 = getattr(agg0, attr)
            attr1 = getattr(agg1, attr)
            if isinstance(attr0, Aggregate):
                self.assertIsInstance(attr1, Aggregate)
                self._eqAggregate(attr0, attr1)
            else:
                self.assertEqual(attr0, attr1)

        self.assertEqual(len(agg0), len(agg1))
        for n, item0 in enumerate(agg0):
            item1 = agg1[n]
            if isinstance(item0, Aggregate):
                self.assertIsInstance(item1, Aggregate)
                self._eqAggregate(item0, item1)
            else:
                self.assertEqual(item0, item1)

    def _eqOfx(self, string0, string1):
        string0 = string0.strip()
        string1 = string0.strip()
        for line0, line1 in zip(string0.splitlines(), string1.splitlines()):
            self.assertEqual(line0.strip(), line1.strip())

    def testFromOfx(self):
        self.assertIsInstance(self.tree._root, ET.Element)
        self._eqAggregate(self.aggregate, self.tree.convert())

    def testToOfx(self):
        root = self.aggregate.to_etree()
        indent(root)
        # ``method="html"`` skips the initial XML declaration
        ofx = ET.tostring(root, method="html").decode()
        self._eqOfx(self.ofx, ofx)
