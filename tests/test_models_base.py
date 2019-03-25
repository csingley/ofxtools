# coding: utf-8
""" Unit tests for models/base.py """
# stdlib imports
import unittest
from collections import OrderedDict
import xml.etree.ElementTree as ET
from datetime import datetime


# local imports
from ofxtools import models
from ofxtools.models.base import (Aggregate, List, TranList, SubAggregate,
                                  Unsupported, )
from ofxtools.Types import (String, DateTime)
from ofxtools.utils import UTC


class TESTSUBAGGREGATE(Aggregate):
    data = String(32, required=True)


class TESTAGGREGATE(Aggregate):
    metadata = String(32, required=True)
    testsubaggregate = SubAggregate(TESTSUBAGGREGATE)
    dontuse = Unsupported()


class TESTLIST(List):
    dataTags = ('TESTAGGREGATE', )


class TESTTRANLIST(TranList):
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    dataTags = ('TESTAGGREGATE', )


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
        return TESTAGGREGATE(metadata='foo')

    @property
    def instance_with_subagg(self):
        subagg = TESTSUBAGGREGATE(data='bar')
        return TESTAGGREGATE(metadata='foo', testsubaggregate=subagg)

    def testInitExtraArgs(self):
        subagg = TESTSUBAGGREGATE(data='bar')
        with self.assertRaises(ValueError):
            TESTAGGREGATE(metadata='foo', testsubaggregate=subagg, bogus=None)

    def testValidateKwargs(self):
        pass

    def testFromEtree(self):
        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, TESTAGGREGATE)
        self.assertEqual(instance.metadata, 'metadata')
        self.assertIsInstance(instance.testsubaggregate, TESTSUBAGGREGATE)
        self.assertEqual(instance.testsubaggregate.data, 'data')
        self.assertIsNone(instance.dontuse)

    def testFromEtreeMissingRequired(self):
        root = ET.Element('TESTAGGREGATE')
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testFromEtreeMissingUnrequired(self):
        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        instance = Aggregate.from_etree(root)
        self.assertIsInstance(instance, TESTAGGREGATE)
        self.assertEqual(instance.metadata, 'metadata')
        self.assertIsNone(instance.dontuse)

    def testFromEtreeDuplicates(self):
        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        ET.SubElement(root, 'METADATA').text = 'metadata'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def testFromEtreeWrongOrder(self):
        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'METADATA').text = 'metadata'
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'METADATA').text = 'metadata'
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'
        ET.SubElement(root, 'METADATA').text = 'metadata'

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'
        ET.SubElement(root, 'METADATA').text = 'metadata'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)

        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

        root = ET.Element('TESTAGGREGATE')
        ET.SubElement(root, 'DONTUSE').text = 'dontuse'
        sub = ET.Element('TESTSUBAGGREGATE')
        ET.SubElement(sub, 'DATA').text = 'data'
        root.append(sub)
        ET.SubElement(root, 'METADATA').text = 'metadata'

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
            return v.__class__.__name__.startswith('S')

        # Matches are returned in the order of the class definition
        matches = TESTAGGREGATE._ordered_attrs(predicate)
        self.assertIsInstance(matches, OrderedDict)
        self.assertEqual(len(matches), 2)
        (name0, instance0), (name1, instance1) = matches.items()

        # N.B. Because no instance of class TestAggregate has been created,
        # calls to TestAggregate.metadata will fail.
        self.assertEqual(name0, 'metadata')
        self.assertIsInstance(instance0, String)
        self.assertEqual(name1, 'testsubaggregate')
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance1, SubAggregate)

    def testSpec(self):
        spec = TESTAGGREGATE.spec
        self.assertIsInstance(spec, OrderedDict)
        self.assertEqual(len(spec), 3)
        (name0, instance0), (name1, instance1), (name2, instance2) = spec.items()
        self.assertEqual(name0, 'metadata')
        self.assertIsInstance(instance0, String)
        self.assertEqual(name1, 'testsubaggregate')
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance1, SubAggregate)
        self.assertEqual(name2, 'dontuse')
        self.assertIsInstance(instance2, Unsupported)

    def testElements(self):
        elements = TESTAGGREGATE.elements
        self.assertIsInstance(elements, OrderedDict)
        self.assertEqual(len(elements), 1)
        name, instance = elements.popitem()
        self.assertEqual(name, 'metadata')
        self.assertIsInstance(instance, String)

    def testSubaggregates(self):
        subaggs = TESTAGGREGATE.subaggregates
        self.assertIsInstance(subaggs, OrderedDict)
        self.assertEqual(len(subaggs), 1)
        name, instance = subaggs.popitem()
        self.assertEqual(name, 'testsubaggregate')
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance, SubAggregate)

    def testUnsupported(self):
        unsupported = TESTAGGREGATE.unsupported
        self.assertIsInstance(unsupported, OrderedDict)
        self.assertEqual(len(unsupported), 1)
        name, instance = unsupported.popitem()
        self.assertEqual(name, 'dontuse')
        self.assertIsInstance(instance, Unsupported)

    def testSpecRepr(self):
        spec_repr = self.instance_no_subagg._spec_repr
        self.assertEqual(len(spec_repr), 1)
        name, val = spec_repr.pop()
        self.assertEqual(name, 'metadata')
        self.assertEqual(val, "'foo'")  # N.B. repr(str) is quoted

        spec_repr = self.instance_with_subagg._spec_repr
        self.assertEqual(len(spec_repr), 2)
        (name0, val0), (name1, val1) = spec_repr
        self.assertEqual(name0, 'metadata')
        self.assertEqual(val0, "'foo'")  # N.B. repr(str) is quoted
        self.assertEqual(name1, 'testsubaggregate')
        self.assertEqual(val1, "<TESTSUBAGGREGATE(data='bar')>")

    def testRepr(self):
        pass

    def testGetattr(self):
        pass


class ListTestCase(unittest.TestCase):
    @property
    def instance(self):
        subagg0 = TESTSUBAGGREGATE(data='quux')
        agg0 = TESTAGGREGATE(metadata='foo', testsubaggregate=subagg0)
        subagg1 = TESTSUBAGGREGATE(data='quuz')
        agg1 = TESTAGGREGATE(metadata='bar', testsubaggregate=subagg1)
        return TESTLIST(agg0, agg1)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertIsInstance(root, ET.Element)
        self.assertEqual(root.tag, 'TESTLIST')
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 2)
        agg0, agg1 = root[:]

        self.assertIsInstance(agg0, ET.Element)
        self.assertEqual(agg0.tag, 'TESTAGGREGATE')
        self.assertIsNone(agg0.text)
        self.assertEqual(len(agg0), 2)

        elem, subagg = agg0[:]

        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'METADATA')
        self.assertEqual(elem.text, 'foo')
        self.assertEqual(len(subagg), 1)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, 'TESTSUBAGGREGATE')
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'DATA')
        self.assertEqual(elem.text, 'quux')
        self.assertEqual(len(elem), 0)

        self.assertIsInstance(agg1, ET.Element)
        self.assertEqual(agg1.tag, 'TESTAGGREGATE')
        self.assertIsNone(agg1.text)
        self.assertEqual(len(agg1), 2)

        elem, subagg = agg1[:]

        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'METADATA')
        self.assertEqual(elem.text, 'bar')
        self.assertEqual(len(subagg), 1)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, 'TESTSUBAGGREGATE')
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'DATA')
        self.assertEqual(elem.text, 'quuz')
        self.assertEqual(len(elem), 0)

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep, "<TESTLIST len=2>")


class TranListTestCase(unittest.TestCase):
    @property
    def instance(self):
        subagg0 = TESTSUBAGGREGATE(data='baz')
        agg0 = TESTAGGREGATE(metadata='foo', testsubaggregate=subagg0)
        subagg1 = TESTSUBAGGREGATE(data='quux')
        agg1 = TESTAGGREGATE(metadata='bar', testsubaggregate=subagg1)
        dtstart = datetime(2015, 1, 1, tzinfo=UTC)
        dtend = datetime(2015, 3, 31, tzinfo=UTC)
        return TESTTRANLIST(dtstart, dtend, agg0, agg1)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertIsInstance(root, ET.Element)
        self.assertEqual(root.tag, 'TESTTRANLIST')
        self.assertIsNone(root.text)
        self.assertEqual(len(root), 4)
        dtstart, dtend, agg0, agg1 = root[:]

        self.assertIsInstance(dtstart, ET.Element)
        self.assertEqual(dtstart.tag, 'DTSTART')
        self.assertEqual(dtstart.text, '20150101000000')
        self.assertEqual(len(dtstart), 0)

        self.assertIsInstance(dtend, ET.Element)
        self.assertEqual(dtend.tag, 'DTEND')
        self.assertEqual(dtend.text, '20150331000000')
        self.assertEqual(len(dtend), 0)

        self.assertIsInstance(agg0, ET.Element)
        self.assertEqual(agg0.tag, 'TESTAGGREGATE')
        self.assertIsNone(agg0.text)
        self.assertEqual(len(agg0), 2)

        elem, subagg = agg0[:]

        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'METADATA')
        self.assertEqual(elem.text, 'foo')
        self.assertEqual(len(subagg), 1)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, 'TESTSUBAGGREGATE')
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'DATA')
        self.assertEqual(elem.text, 'baz')
        self.assertEqual(len(elem), 0)

        elem, subagg = agg1[:]

        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'METADATA')
        self.assertEqual(elem.text, 'bar')
        self.assertEqual(len(subagg), 1)

        self.assertIsInstance(subagg, ET.Element)
        self.assertEqual(subagg.tag, 'TESTSUBAGGREGATE')
        self.assertIsNone(subagg.text)
        self.assertEqual(len(subagg), 1)

        elem = subagg[0]
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, 'DATA')
        self.assertEqual(elem.text, 'quux')
        self.assertEqual(len(elem), 0)

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep,
                         "<TESTTRANLIST dtstart='{}' dtend='{}' len=2>".format(
                             datetime(2015, 1, 1, tzinfo=UTC),
                             datetime(2015, 3, 31, tzinfo=UTC)))


class SubAggregateTestCase(unittest.TestCase):
    @property
    def instance(self):
        return TESTSUBAGGREGATE(data='foo')

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


if __name__ == '__main__':
    unittest.main()
