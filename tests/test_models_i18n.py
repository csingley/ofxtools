# coding: utf-8
""" Unit tests for models/common.py """
# stdlib imports
import unittest
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import base
from ofxtools.models.base import Aggregate
from ofxtools.models.i18n import (
    CURRENCY, ORIGCURRENCY,
    CURRENCY_CODES
)


class CurrencyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('CURRATE', 'CURSYM', )

    @property
    def root(self):
        root = Element('CURRENCY')
        SubElement(root, 'CURRATE').text = '59.773'
        SubElement(root, 'CURSYM').text = 'EUR'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CURRENCY)
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')

    def testOneOf(self):
        self.oneOfTest('CURSYM', CURRENCY_CODES)


class OrigcurrencyTestCase(CurrencyTestCase):
    @property
    def root(self):
        root = super(OrigcurrencyTestCase, self).root
        root.tag = 'ORIGCURRENCY'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ORIGCURRENCY)
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')


if __name__ == '__main__':
    unittest.main()
