# coding: utf-8
""" Unit tests for models/base.py """
# stdlib imports
import unittest
from collections import OrderedDict
import xml.etree.ElementTree as ET
from datetime import datetime


# local imports
from ofxtools import models
from ofxtools.models.base import Aggregate, List, SubAggregate, Unsupported
from ofxtools.Types import String, DateTime, Bool
from ofxtools.utils import UTC


class TESTSUBAGGREGATE(Aggregate):
    data = String(32, required=True)


class TESTAGGREGATE(Aggregate):
    metadata = String(32, required=True)
    option00 = Bool()
    option01 = Bool()
    option10 = Bool()
    option11 = Bool()
    req00 = Bool()
    req01 = Bool()
    req10 = Bool()
    req11 = Bool()
    testsubaggregate = SubAggregate(TESTSUBAGGREGATE)
    dontuse = Unsupported()

    optionalMutexes = [('option00', 'option01'), ('option10', 'option11')]
    requiredMutexes = [('req00', 'req01'), ('req10', 'req11')]


class TESTLIST(List):
    dataTags = ("TESTAGGREGATE",)


class AggregateTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # monkey-patch ofxtools.models so Aggregate.from_etree() picks up
        # our fake OFX aggregates/elements
        models.TESTSUBAGGREGATE = TESTSUBAGGREGATE
        models.TESTAGGREGATE = TESTAGGREGATE

    @classmethod
    def tearDownClass(cls):
        # Remove monkey patch
        del models.TESTSUBAGGREGATE
        del models.TESTAGGREGATE

    @property
    def instance_no_subagg(self):
        return TESTAGGREGATE(metadata="foo", req00=True, req11=False)

    @property
    def instance_with_subagg(self):
        subagg = TESTSUBAGGREGATE(data="bar")
        return TESTAGGREGATE(metadata="foo", req00=True, req11=False, testsubaggregate=subagg)

    def testInitMissingRequired(self):
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(ValueError):
            TESTAGGREGATE(testsubaggregate=subagg, bogus=None)

    def testInitWrongType(self):
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata=subagg, testsubaggregate=subagg)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", testsubaggregate="foo")

    def testInitWithTooManyArgs(self):
        # Pass extra args not in TESTAGGREGATE.spec
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", testsubaggregate=subagg, bogus=None)

    def testValidateKwargs(self):
        # optionalMutexes - either is OK, but both is not OK
        TESTAGGREGATE(metadata="foo", option00=True, req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", option01=True, req00=True, req11=False)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", option00=True, option01=False, req00=True, req11=False)

        TESTAGGREGATE(metadata="foo", option10=True, req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", option11=True, req00=True, req11=False)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", option10=True, option11=False, req00=True, req11=False)

        # requiredMutexes - 1 is OK, 0 or 2 is not OK
        TESTAGGREGATE(metadata="foo", req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", req01=True, req10=False)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", req11=False)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", req00=True)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", req00=True, req01=False, req11=False)
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata="foo", req00=True, req10=True, req11=False)

    def testFromEtree(self):
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "REQ00").text = "Y"
        ET.SubElement(root, "REQ11").text = "N"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, TESTAGGREGATE)
        self.assertEqual(instance.metadata, "metadata")
        self.assertEqual(instance.req00, True)
        self.assertEqual(instance.req11, False)
        self.assertIsInstance(instance.testsubaggregate, TESTSUBAGGREGATE)
        self.assertEqual(instance.testsubaggregate.data, "data")
        self.assertIsNone(instance.dontuse)

    def testFromEtreeMissingRequired(self):
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "REQ00").text = "Y"
        ET.SubElement(root, "REQ11").text = "N"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testFromEtreeMissingUnrequired(self):
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "REQ00").text = "Y"
        ET.SubElement(root, "REQ11").text = "N"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, TESTAGGREGATE)
        self.assertEqual(instance.metadata, "metadata")
        self.assertEqual(instance.req00, True)
        self.assertEqual(instance.req11, False)
        self.assertIsNone(instance.dontuse)

    def testFromEtreeDuplicates(self):
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testFromEtreeWrongOrder(self):
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "METADATA").text = "metadata"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "METADATA").text = "metadata"

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testFromEtreeBadArg(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(None)

    def testGroom(self):
        pass

    def testUngroom(self):
        pass

    def testOrderedAttrs(self):
        """
        models.base._ordered_attrs() takes a predicate, and returns OrderedDict
        of matching items from cls.__dict__.

        N.B. predicate tests *values* of cls.__dict__
             (not keys i.e. attribute names)
        """

        def predicate(v):
            return v.__class__.__name__.startswith("S")

        # Matches are returned in the order of the class definition
        matches = TESTAGGREGATE._ordered_attrs(predicate)
        self.assertIsInstance(matches, OrderedDict)
        self.assertEqual(len(matches), 2)
        (name0, instance0), (name1, instance1) = matches.items()

        # N.B. Because no instance of class TestAggregate has been created,
        # calls to TestAggregate.metadata will fail.
        self.assertEqual(name0, "metadata")
        self.assertIsInstance(instance0, String)
        self.assertEqual(name1, "testsubaggregate")
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance1, SubAggregate)

    def testSpec(self):
        spec = TESTAGGREGATE.spec
        self.assertIsInstance(spec, OrderedDict)
        self.assertEqual(len(spec), 11)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "metadata")
        self.assertIsInstance(instance, String)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "option00")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "option01")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "option10")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "option11")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "req00")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "req01")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "req10")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "req11")
        self.assertIsInstance(instance, Bool)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "testsubaggregate")
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance, SubAggregate)

        name, instance = spec.popitem(last=False)
        self.assertEqual(name, "dontuse")
        self.assertIsInstance(instance, Unsupported)

    def testElements(self):
        elements = TESTAGGREGATE.elements
        self.assertIsInstance(elements, OrderedDict)
        self.assertEqual(len(elements), 9)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "metadata")
        self.assertIsInstance(instance, String)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "option00")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "option01")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "option10")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "option11")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "req00")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "req01")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "req10")
        self.assertIsInstance(instance, Bool)

        name, instance = elements.popitem(last=False)
        self.assertEqual(name, "req11")
        self.assertIsInstance(instance, Bool)

    def testSubaggregates(self):
        subaggs = TESTAGGREGATE.subaggregates
        self.assertIsInstance(subaggs, OrderedDict)
        self.assertEqual(len(subaggs), 1)
        name, instance = subaggs.popitem()
        self.assertEqual(name, "testsubaggregate")
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance, SubAggregate)

    def testUnsupported(self):
        unsupported = TESTAGGREGATE.unsupported
        self.assertIsInstance(unsupported, OrderedDict)
        self.assertEqual(len(unsupported), 1)
        name, instance = unsupported.popitem()
        self.assertEqual(name, "dontuse")
        self.assertIsInstance(instance, Unsupported)

    def testSpecRepr(self):
        #  Sequence of (name, repr()) for each non-empty attribute in ``_spec``
        spec_repr = self.instance_no_subagg._spec_repr
        self.assertEqual(len(spec_repr), 3)

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "metadata")
        self.assertEqual(val, "'foo'")  # N.B. repr(str) is quoted

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "req00")
        self.assertEqual(val, "True")

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "req11")
        self.assertEqual(val, "False")

        spec_repr = self.instance_with_subagg._spec_repr
        self.assertEqual(len(spec_repr), 4)

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "metadata")
        self.assertEqual(val, "'foo'")  # N.B. repr(str) is quoted

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "req00")
        self.assertEqual(val, "True")

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "req11")
        self.assertEqual(val, "False")

        name, val = spec_repr.pop(0)
        self.assertEqual(name, "testsubaggregate")
        self.assertEqual(val, "<TESTSUBAGGREGATE(data='bar')>")

    def testRepr(self):
        pass

    def testGetattr(self):
        pass


class SubAggregateTestCase(unittest.TestCase):
    @property
    def instance(self):
        return TESTSUBAGGREGATE(data="foo")

    def testInit(self):
        pass

    def testConvert(self):
        pass

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep, "<TESTSUBAGGREGATE(data='foo')>")


class UnsupportedTestCase(unittest.TestCase):
    @property
    def instance(self):
        return Unsupported()

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep, "<Unsupported>")


class ListTestCase(unittest.TestCase):
    @property
    def instance(self):
        subagg0 = TESTSUBAGGREGATE(data="quux")
        agg0 = TESTAGGREGATE(metadata="foo", req00=True, req11=False, testsubaggregate=subagg0)
        subagg1 = TESTSUBAGGREGATE(data="quuz")
        agg1 = TESTAGGREGATE(metadata="bar", req00=False, req11=True, testsubaggregate=subagg1)
        return TESTLIST(agg0, agg1)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertIsInstance(root, ET.Element)
        self.assertEqual(root.tag, "TESTLIST")
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 2)
        agg0, agg1 = root[:]

        self.assertIsInstance(agg0, ET.Element)
        self.assertEqual(agg0.tag, "TESTAGGREGATE")
        self.assertIsNone(agg0.text)
        self.assertEqual(len(agg0), 4)

        metadata, req00, req11, subagg = agg0[:]

        self.assertIsInstance(metadata, ET.Element)
        self.assertEqual(metadata.tag, "METADATA")
        self.assertEqual(metadata.text, "foo")

        self.assertIsInstance(req00, ET.Element)
        self.assertEqual(req00.tag, "REQ00")
        self.assertEqual(req00.text, "Y")

        self.assertIsInstance(req11, ET.Element)
        self.assertEqual(req11.tag, "REQ11")
        self.assertEqual(req11.text, "N")

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, "TESTSUBAGGREGATE")
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        self.assertEqual(len(subagg), 1)
        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, "DATA")
        self.assertEqual(elem.text, "quux")
        self.assertEqual(len(elem), 0)

        self.assertIsInstance(agg1, ET.Element)
        self.assertEqual(agg1.tag, "TESTAGGREGATE")
        self.assertIsNone(agg1.text)
        self.assertEqual(len(agg1), 4)

        metadata, req00, req11, subagg = agg1[:]

        self.assertIsInstance(metadata, ET.Element)
        self.assertEqual(metadata.tag, "METADATA")
        self.assertEqual(metadata.text, "bar")

        self.assertIsInstance(req00, ET.Element)
        self.assertEqual(req00.tag, "REQ00")
        self.assertEqual(req00.text, "N")

        self.assertIsInstance(req11, ET.Element)
        self.assertEqual(req11.tag, "REQ11")
        self.assertEqual(req11.text, "Y")

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, "TESTSUBAGGREGATE")
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        self.assertEqual(len(subagg), 1)
        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, "DATA")
        self.assertEqual(elem.text, "quuz")
        self.assertEqual(len(elem), 0)

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep, "<TESTLIST len=2>")


if __name__ == "__main__":
    unittest.main()
