# coding: utf-8
""" Unit tests for models/base.py """
# stdlib imports
import unittest
import xml.etree.ElementTree as ET


# local imports
from ofxtools import models, Types
from ofxtools.Types import (
    String,
    Bool,
    SubAggregate,
    Unsupported,
    ListAggregate,
    ListElement,
)
from ofxtools.models.base import (
    Aggregate,
    ElementList,
    OFXSpecError,
)


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

    optionalMutexes = [["option00", "option01"], ["option10", "option11"]]
    requiredMutexes = [["req00", "req01"], ["req10", "req11"]]


class TESTAGGREGATE2(Aggregate):
    metadata = String(32, required=True)


class TESTLIST(Aggregate):
    metadata = String(32)
    testaggregate = ListAggregate(TESTAGGREGATE)
    testaggregate2 = ListAggregate(TESTAGGREGATE2)


class TESTELEMENTLIST(ElementList):
    metadata = String(32)
    tag = ListElement(Bool())


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
        return TESTAGGREGATE(
            metadata="foo", req00=True, req11=False, testsubaggregate=subagg
        )

    def testInitMissingRequired(self):
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(testsubaggregate=subagg, req00=True)

    def testInitWrongType(self):
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(TypeError):
            TESTAGGREGATE(
                metadata=subagg, testsubaggregate=subagg, req00=True, req11=False
            )
        with self.assertRaises(TypeError):
            TESTAGGREGATE(
                metadata="foo", testsubaggregate="foo", req00=True, req11=False
            )

    def testInitWithTooManyArgs(self):
        # Pass extra args not in TESTAGGREGATE.spec
        subagg = TESTSUBAGGREGATE(data="bar")
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(
                metadata="foo",
                testsubaggregate=subagg,
                req00=True,
                req11=False,
                bogus=None,
            )

    def testValidateKwargs(self):
        # optionalMutexes - either is OK, but both is not OK
        TESTAGGREGATE(metadata="foo", option00=True, req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", option01=True, req00=True, req11=False)
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(
                metadata="foo", option00=True, option01=False, req00=True, req11=False
            )

        TESTAGGREGATE(metadata="foo", option10=True, req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", option11=True, req00=True, req11=False)
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(
                metadata="foo", option10=True, option11=False, req00=True, req11=False
            )

        # requiredMutexes - 1 is OK, 0 or 2 is not OK
        TESTAGGREGATE(metadata="foo", req00=True, req11=False)
        TESTAGGREGATE(metadata="foo", req01=True, req10=False)
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(metadata="foo", req11=False)
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(metadata="foo", req00=True)
        with self.assertRaises(OFXSpecError):
            TESTAGGREGATE(metadata="foo", req00=True, req01=False, req11=False)
        with self.assertRaises(OFXSpecError):
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

        with self.assertRaises(Types.OFXSpecError):
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

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

    def testFromEtreeWrongOrder(self):
        # Correct sequence:
        # [metadata (required), option00, option01, option10, option11,
        #  req00, req01, req10, req11, testsubaggregate, dontuse]
        #
        # requiredMutexes = [["req00", "req01"], ["req10", "req11"]]
        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "REQ00").text = "Y"
        ET.SubElement(root, "REQ11").text = "N"
        sub = ET.SubElement(root, "TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        Aggregate.from_etree(root)

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "REQ00").text = "Y"
        ET.SubElement(root, "REQ11").text = "N"
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        sub = ET.SubElement(root, "TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"

        with self.assertRaises(OFXSpecError) as exc:
            Aggregate.from_etree(root)

        self.assertIn("out of order", exc.exception.args[0].lower())

        root = ET.Element("TESTAGGREGATE")
        sub = ET.SubElement(root, "TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "METADATA").text = "metadata"
        ET.SubElement(root, "DONTUSE").text = "dontuse"

        with self.assertRaises(OFXSpecError) as exc:
            Aggregate.from_etree(root)

        self.assertIn("out of order", exc.exception.args[0].lower())

        root = ET.Element("TESTAGGREGATE")
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "METADATA").text = "metadata"

        with self.assertRaises(OFXSpecError) as exc:
            Aggregate.from_etree(root)

        self.assertIn("out of order", exc.exception.args[0].lower())

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        ET.SubElement(root, "METADATA").text = "metadata"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)

        with self.assertRaises(OFXSpecError) as exc:
            Aggregate.from_etree(root)

        self.assertIn("out of order", exc.exception.args[0].lower())

        root = ET.Element("TESTAGGREGATE")
        ET.SubElement(root, "DONTUSE").text = "dontuse"
        sub = ET.Element("TESTSUBAGGREGATE")
        ET.SubElement(sub, "DATA").text = "data"
        root.append(sub)
        ET.SubElement(root, "METADATA").text = "metadata"

        with self.assertRaises(OFXSpecError) as exc:
            Aggregate.from_etree(root)

        self.assertIn("out of order", exc.exception.args[0].lower())

    def testFromEtreeBadArg(self):
        with self.assertRaises(TypeError):
            Aggregate.from_etree(None)

    def testGroom(self):
        pass

    def testUngroom(self):
        pass

    def testFilterAttrs(self):
        """
        models.base._filter_attrs() takes a predicate, and returns mapping
        of matching items from cls.__dict__.

        N.B. predicate tests *values* of cls.__dict__
             (not keys i.e. attribute names)
        """

        def predicate(v):
            return v.__class__.__name__.startswith("S")

        # Matches are returned in the order of the class definition
        matches = TESTAGGREGATE._filter_attrs(predicate)
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
        self.assertEqual(len(spec), 11)

        [
            (name0, instance0),
            (name1, instance1),
            (name2, instance2),
            (name3, instance3),
            (name4, instance4),
            (name5, instance5),
            (name6, instance6),
            (name7, instance7),
            (name8, instance8),
            (name9, instance9),
            (name10, instance10),
        ] = spec.items()

        self.assertEqual(name0, "metadata")
        self.assertIsInstance(instance0, String)

        self.assertEqual(name1, "option00")
        self.assertIsInstance(instance1, Bool)

        self.assertEqual(name2, "option01")
        self.assertIsInstance(instance2, Bool)

        self.assertEqual(name3, "option10")
        self.assertIsInstance(instance3, Bool)

        self.assertEqual(name4, "option11")
        self.assertIsInstance(instance4, Bool)

        self.assertEqual(name5, "req00")
        self.assertIsInstance(instance5, Bool)

        self.assertEqual(name6, "req01")
        self.assertIsInstance(instance6, Bool)

        self.assertEqual(name7, "req10")
        self.assertIsInstance(instance7, Bool)

        self.assertEqual(name8, "req11")
        self.assertIsInstance(instance8, Bool)

        self.assertEqual(name9, "testsubaggregate")
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance9, SubAggregate)

        self.assertEqual(name10, "dontuse")
        self.assertIsInstance(instance10, Unsupported)

    def testElements(self):
        elements = TESTAGGREGATE.elements
        self.assertEqual(len(elements), 9)

        [
            (name0, instance0),
            (name1, instance1),
            (name2, instance2),
            (name3, instance3),
            (name4, instance4),
            (name5, instance5),
            (name6, instance6),
            (name7, instance7),
            (name8, instance8),
        ] = elements.items()

        self.assertEqual(name0, "metadata")
        self.assertIsInstance(instance0, String)

        self.assertEqual(name1, "option00")
        self.assertIsInstance(instance1, Bool)

        self.assertEqual(name2, "option01")
        self.assertIsInstance(instance2, Bool)

        self.assertEqual(name3, "option10")
        self.assertIsInstance(instance3, Bool)

        self.assertEqual(name4, "option11")
        self.assertIsInstance(instance4, Bool)

        self.assertEqual(name5, "req00")
        self.assertIsInstance(instance5, Bool)

        self.assertEqual(name6, "req01")
        self.assertIsInstance(instance6, Bool)

        self.assertEqual(name7, "req10")
        self.assertIsInstance(instance7, Bool)

        self.assertEqual(name8, "req11")
        self.assertIsInstance(instance8, Bool)

    def testSubaggregates(self):
        subaggs = TESTAGGREGATE.subaggregates
        self.assertEqual(len(subaggs), 1)
        name, instance = subaggs.popitem()
        self.assertEqual(name, "testsubaggregate")
        # N.B. on the class TestAggregate, 'sub' is an instance of SubAggregate
        # but on instances of the class, it's reeplaced by TestSubaggregate
        # (to which it refers)
        self.assertIsInstance(instance, SubAggregate)

    def testUnsupported(self):
        unsupported = TESTAGGREGATE.unsupported
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
        rep = repr(self.instance_with_subagg)
        self.assertEqual(
            rep,
            "<TESTAGGREGATE(metadata='foo', req00=True, req11=False, testsubaggregate=<TESTSUBAGGREGATE(data='bar')>)>",
        )

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
    @classmethod
    def setUpClass(cls):
        # monkey-patch ofxtools.models so Aggregate.from_etree() picks up
        # our fake OFX aggregates/elements
        models.TESTSUBAGGREGATE = TESTSUBAGGREGATE
        models.TESTAGGREGATE = TESTAGGREGATE
        models.TESTAGGREGATE2 = TESTAGGREGATE2
        models.TESTLIST = TESTLIST

    @classmethod
    def tearDownClass(cls):
        # Remove monkey patch
        del models.TESTSUBAGGREGATE
        del models.TESTAGGREGATE
        del models.TESTAGGREGATE2
        del models.TESTLIST

    def assertElement(self, elem, tag, text, len):
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, tag)
        self.assertEqual(elem.text, text)

    @property
    def instance(self):
        subagg0 = TESTSUBAGGREGATE(data="quux")
        agg0 = TESTAGGREGATE(
            metadata="foo", req00=True, req11=False, testsubaggregate=subagg0
        )
        subagg1 = TESTSUBAGGREGATE(data="quuz")
        agg1 = TESTAGGREGATE(
            metadata="bar", req00=False, req11=True, testsubaggregate=subagg1
        )
        agg2 = TESTAGGREGATE2(metadata="dumbo")
        return TESTLIST(agg0, agg1, agg2, metadata="foo")

    @property
    def root(self):
        root = ET.Element("TESTLIST")
        ET.SubElement(root, "METADATA").text = "foo"
        agg0 = ET.SubElement(root, "TESTAGGREGATE")
        agg1 = ET.SubElement(root, "TESTAGGREGATE")
        agg2 = ET.SubElement(root, "TESTAGGREGATE2")

        ET.SubElement(agg0, "METADATA").text = "foo"
        ET.SubElement(agg0, "REQ00").text = "Y"
        ET.SubElement(agg0, "REQ11").text = "N"
        subagg0 = ET.SubElement(agg0, "TESTSUBAGGREGATE")
        ET.SubElement(subagg0, "DATA").text = "quux"

        ET.SubElement(agg1, "METADATA").text = "bar"
        ET.SubElement(agg1, "REQ00").text = "N"
        ET.SubElement(agg1, "REQ11").text = "Y"
        subagg1 = ET.SubElement(agg1, "TESTSUBAGGREGATE")
        ET.SubElement(subagg1, "DATA").text = "quuz"

        ET.SubElement(agg2, "METADATA").text = "dumbo"

        return root

    def testFromEtree(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, TESTLIST)
        self.assertEqual(instance.metadata, "foo")
        self.assertEqual(len(instance), 3)
        agg0, agg1, agg2 = instance[:]

        self.assertIsInstance(agg0, TESTAGGREGATE)
        self.assertIsInstance(agg1, TESTAGGREGATE)
        self.assertIsInstance(agg2, TESTAGGREGATE2)

    def testFromEtreeWrongOrder(self):
        root = ET.Element("TESTLIST")
        agg = ET.SubElement(root, "TESTAGGREGATE2")
        ET.SubElement(agg, "METADATA").text = "dumbo"
        ET.SubElement(root, "METADATA").text = "foo"

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

    def testInitInstancesDistinct(self):
        # Test that separate List class instances contain separate data
        instance0 = self.instance

        subagg0 = TESTSUBAGGREGATE(data="read")
        agg0 = TESTAGGREGATE(
            metadata="orange", req00=True, req11=False, testsubaggregate=subagg0
        )
        subagg1 = TESTSUBAGGREGATE(data="yellow")
        agg1 = TESTAGGREGATE(
            metadata="green", req00=False, req11=True, testsubaggregate=subagg1
        )
        instance1 = TESTLIST(agg0, agg1, metadata="blue")

        self.assertIsInstance(instance0, TESTLIST)
        self.assertEqual(instance0.metadata, "foo")
        self.assertEqual(len(instance0), 3)
        ag0, ag1, ag2 = instance0[:]

        self.assertIsInstance(ag0, TESTAGGREGATE)
        self.assertEqual(ag0.metadata, "foo")
        self.assertEqual(ag0.req00, True)
        self.assertEqual(ag0.req11, False)
        sub0 = ag0.testsubaggregate
        self.assertIsInstance(sub0, TESTSUBAGGREGATE)
        self.assertEqual(sub0.data, "quux")

        self.assertIsInstance(ag1, TESTAGGREGATE)
        self.assertEqual(ag1.metadata, "bar")
        self.assertEqual(ag1.req00, False)
        self.assertEqual(ag1.req11, True)
        sub1 = ag1.testsubaggregate
        self.assertIsInstance(sub1, TESTSUBAGGREGATE)
        self.assertEqual(sub1.data, "quuz")

        self.assertIsInstance(ag2, TESTAGGREGATE2)
        self.assertEqual(ag2.metadata, "dumbo")

        self.assertIsInstance(instance1, TESTLIST)
        self.assertEqual(instance1.metadata, "blue")
        self.assertEqual(len(instance1), 2)
        self.assertEqual(instance1[0], agg0)
        self.assertEqual(instance1[1], agg1)

    def testInitListAggregatesAsKwargs(self):
        # Test that passing in list aggregates as keyword arguments
        # (rather than positional args) raises an error
        subagg0 = TESTSUBAGGREGATE(data="quux")
        agg0 = TESTAGGREGATE(
            metadata="foo", req00=True, req11=False, testsubaggregate=subagg0
        )
        subagg1 = TESTSUBAGGREGATE(data="quuz")
        agg1 = TESTAGGREGATE(
            metadata="bar", req00=False, req11=True, testsubaggregate=subagg1
        )
        agg2 = TESTAGGREGATE2(metadata="dumbo")

        with self.assertRaises(SyntaxError):
            TESTLIST(metadata="foo", testaggregate=agg0)

        with self.assertRaises(SyntaxError):
            TESTLIST(metadata="foo", testaggregate2=agg2)

        with self.assertRaises(SyntaxError):
            TESTLIST(agg0, metadata="foo", testaggregate=agg1)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertElement(root, tag="TESTLIST", text=None, len=4)
        metadata, agg0, agg1, agg2 = root[:]

        self.assertElement(metadata, tag="METADATA", text="foo", len=0)

        self.assertElement(agg0, tag="TESTAGGREGATE", text=None, len=4)
        metadata, req00, req11, subagg = agg0[:]

        self.assertElement(metadata, tag="METADATA", text="foo", len=0)
        self.assertElement(req00, tag="REQ00", text="Y", len=0)
        self.assertElement(req11, tag="REQ11", text="N", len=0)
        self.assertElement(subagg, tag="TESTSUBAGGREGATE", text=None, len=1)
        elem = subagg[0]
        self.assertElement(elem, tag="DATA", text="quux", len=0)

        self.assertElement(agg1, tag="TESTAGGREGATE", text=None, len=4)
        metadata, req00, req11, subagg = agg1[:]
        self.assertElement(metadata, tag="METADATA", text="bar", len=0)
        self.assertElement(req00, tag="REQ00", text="N", len=0)
        self.assertElement(req11, tag="REQ11", text="Y", len=0)
        self.assertElement(subagg, tag="TESTSUBAGGREGATE", text=None, len=1)
        elem = subagg[0]
        self.assertElement(elem, tag="DATA", text="quuz", len=0)

        self.assertElement(agg2, tag="TESTAGGREGATE2", text=None, len=1)
        metadata = agg2[0]
        self.assertElement(metadata, tag="METADATA", text="dumbo", len=0)

    def testRepr(self):
        rep = repr(self.instance)
        self.assertEqual(rep, "<TESTLIST(metadata='foo'), len=3>")


class ElementListTestCase(unittest.TestCase):
    __test__ = True

    @classmethod
    def setUpClass(cls):
        # monkey-patch ofxtools.models so Aggregate.from_etree() picks up
        # our fake OFX aggregates/elements
        models.TESTELEMENTLIST = TESTELEMENTLIST

    @classmethod
    def tearDownClass(cls):
        # Remove monkey patch
        del models.TESTELEMENTLIST

    def assertElement(self, elem, tag, text, len):
        self.assertIsInstance(elem, ET.Element)
        self.assertEqual(elem.tag, tag)
        self.assertEqual(elem.text, text)

    @property
    def root(self):
        root = ET.Element("TESTELEMENTLIST")
        ET.SubElement(root, "METADATA").text = "something"
        ET.SubElement(root, "TAG").text = "N"
        ET.SubElement(root, "TAG").text = "Y"
        return root

    @property
    def instance(self):
        return TESTELEMENTLIST(False, True, metadata="something")

    def testInit(self):
        # Single element
        lst = TESTELEMENTLIST(True, metadata="something")
        self.assertEqual(lst.metadata, "something")
        self.assertEqual(len(lst), 1)
        self.assertEqual(lst[0], True)

        # Multiple elements
        lst = TESTELEMENTLIST(False, True, metadata="something")
        self.assertEqual(lst.metadata, "something")
        self.assertEqual(len(lst), 2)
        self.assertEqual(lst[0], False)
        self.assertEqual(lst[1], True)

        # Validators apply
        with self.assertRaises(Types.OFXSpecError):
            TESTELEMENTLIST("123", metadata="something")

        # Only one ListElement may be defined on the class
        class BADELEMENTLIST(ElementList):
            metadata = String(32)
            tag = ListElement(Bool)
            tag2 = ListElement(Bool)

        with self.assertRaises(AssertionError):
            BADELEMENTLIST(True, metadata="something")

    def testFromEtree(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, TESTELEMENTLIST)
        self.assertEqual(instance.metadata, "something")
        self.assertEqual(len(instance), 2)
        self.assertEqual(instance[0], False)
        self.assertEqual(instance[1], True)

        # Out of order - invalid
        root = ET.Element("TESTELEMENTLIST")
        ET.SubElement(root, "TAG").text = "N"
        ET.SubElement(root, "TAG").text = "Y"
        ET.SubElement(root, "METADATA").text = "something"

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

        root = ET.Element("TESTELEMENTLIST")
        ET.SubElement(root, "TAG").text = "N"
        ET.SubElement(root, "METADATA").text = "something"
        ET.SubElement(root, "TAG").text = "Y"

        with self.assertRaises(OFXSpecError):
            Aggregate.from_etree(root)

    def testToEtree(self):
        root = self.instance.to_etree()
        self.assertElement(root, tag="TESTELEMENTLIST", text=None, len=3)
        metadata, tag0, tag1 = root[:]

        self.assertElement(metadata, tag="METADATA", text="something", len=0)
        self.assertElement(tag0, tag="TAG", text="N", len=0)
        self.assertElement(tag1, tag="TAG", text="Y", len=0)


if __name__ == "__main__":
    unittest.main()
