# coding: utf-8
""" Unit tests for models/common.py """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import base
from . import test_i18n
from ofxtools.models.base import Aggregate
from ofxtools.models.common import (
    STATUS, BAL, CURRENCY, OFXELEMENT, OFXEXTENSION,
)
from ofxtools.models.i18n import CURRENCY_CODES


class AggregateTestCase(unittest.TestCase, base.TestAggregate):
    """ Test miscellaneous code paths in base.Aggregate) """
    __test__ = True

    def testExtraElement(self):
        pass


class StatusTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('CODE', 'SEVERITY')
    optionalElements = ('MESSAGE',)

    @property
    def root(self):
        root = Element('STATUS')
        SubElement(root, 'CODE').text = '0'
        SubElement(root, 'SEVERITY').text = 'INFO'
        SubElement(root, 'MESSAGE').text = 'Do your laundry!'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STATUS)
        self.assertEqual(root.code, 0)
        self.assertEqual(root.severity, 'INFO')
        self.assertEqual(root.message, 'Do your laundry!')

    def testOneOf(self):
        self.oneOfTest('SEVERITY', ('INFO', 'WARN', 'ERROR'))


class BalTestCase(unittest.TestCase, base.TestAggregate):
    # <BAL> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True
    requiredElements = ['NAME', 'DESC', 'BALTYPE', 'VALUE', ]
    optionalElements = ['DTASOF', 'CURRENCY', ]

    @property
    def root(self):
        root = Element('BAL')
        SubElement(root, 'NAME').text = 'balance'
        SubElement(root, 'DESC').text = 'Balance'
        SubElement(root, 'BALTYPE').text = 'DOLLAR'
        SubElement(root, 'VALUE').text = '111.22'
        SubElement(root, 'DTASOF').text = '20010630'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BAL)
        self.assertEqual(root.name, 'balance')
        self.assertEqual(root.desc, 'Balance')
        self.assertEqual(root.baltype, 'DOLLAR')
        self.assertEqual(root.value, Decimal('111.22'))
        self.assertEqual(root.dtasof, datetime(2001, 6, 30))
        self.assertIsInstance(root.currency, CURRENCY)

    def testOneOf(self):
        self.oneOfTest('BALTYPE', ('DOLLAR', 'PERCENT', 'NUMBER'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)


class OfxelementTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('OFXELEMENT')
        SubElement(root, 'TAGNAME').text = 'ABC.SOMETHING'
        SubElement(root, 'NAME').text = 'Some OFX extension'
        SubElement(root, 'TAGTYPE').text = 'A-32'
        SubElement(root, 'TAGVALUE').text = 'Foobar'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OFXELEMENT)
        self.assertEqual(root.tagname, 'ABC.SOMETHING')
        self.assertEqual(root.name, 'Some OFX extension')
        self.assertEqual(root.tagtype, 'A-32')
        self.assertEqual(root.tagvalue, 'Foobar')


class OfxextensionTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle multiple OFXELEMENTs?

    @property
    def root(self):
        root = Element('OFXEXTENSION')
        ofxelement1 = OfxelementTestCase().root
        ofxelement2 = OfxelementTestCase().root
        root.append(ofxelement1)
        root.append(ofxelement2)
        return root

    def testConvert(self):
        # Test OFXEXTENSIONS.  OFXELEMENT is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OFXEXTENSION)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], OFXELEMENT)
        self.assertIsInstance(root[1], OFXELEMENT)


if __name__ == '__main__':
    unittest.main()
