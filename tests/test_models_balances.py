# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from copy import deepcopy


# local imports
from ofxtools.models import (
    Aggregate,
    LEDGERBAL,
    AVAILBAL,
    INVBAL,
    BAL,
)
from ofxtools.lib import CURRENCY_CODES


class TestAggregate(object):
    """ """
    __test__ = False
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        """Define in subclass"""
        raise NotImplementedError

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                required = parent.find('./%s' % tag)
                parent.remove(required)
                with self.assertRaises(ValueError):
                    Aggregate.from_etree(root)

    def testOptional(self):
        if self.optionalElements:
            for tag in self.optionalElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                optional = parent.find('./%s' % tag)
                parent.remove(optional)
                Aggregate.from_etree(root)

    def testExtraElement(self):
        root = deepcopy(self.root)
        SubElement(root, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def oneOfTest(self, tag, texts):
        # Make sure OneOf validator allows all legal values and disallows
        # illegal values
        for text in texts:
            root = deepcopy(self.root)
            target = root.find('.//%s' % tag)
            target.text = text
            Aggregate.from_etree(root)

        root = deepcopy(self.root)
        target = root.find('.//%s' % tag)
        target.text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class LedgerbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('LEDGERBAL')
        SubElement(root, 'BALAMT').text = '12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LEDGERBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3))


class AvailbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('AVAILBAL')
        SubElement(root, 'BALAMT').text = '12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, AVAILBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3))


class InvbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('AVAILCASH', 'MARGINBALANCE', 'SHORTBALANCE',)
    optionalElements = ('BUYPOWER',)
    # BALLIST blows up _flatten(); don't test it here

    @property
    def root(self):
        root = Element('INVBAL')
        SubElement(root, 'AVAILCASH').text = '12345.67'
        SubElement(root, 'MARGINBALANCE').text = '23456.78'
        SubElement(root, 'SHORTBALANCE').text = '34567.89'
        SubElement(root, 'BUYPOWER').text = '45678.90'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVBAL)
        self.assertEqual(root.availcash, Decimal('12345.67'))
        self.assertEqual(root.marginbalance, Decimal('23456.78'))
        self.assertEqual(root.shortbalance, Decimal('34567.89'))
        self.assertEqual(root.buypower, Decimal('45678.90'))


class BalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('NAME', 'DESC', 'BALTYPE', 'VALUE')
    optionalElements = ('DTASOF', 'CURRATE', 'CURSYM')

    @property
    def root(self):
        root = Element('BAL')
        SubElement(root, 'NAME').text = 'PETTYCASH'
        SubElement(root, 'DESC').text = 'Walking around money'
        SubElement(root, 'BALTYPE').text = 'DOLLAR'
        SubElement(root, 'VALUE').text = '1234567.89'
        SubElement(root, 'DTASOF').text = '20140615'
        currency = SubElement(root, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.57'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BAL)
        self.assertEqual(root.name, 'PETTYCASH')
        self.assertEqual(root.desc, 'Walking around money')
        self.assertEqual(root.baltype, 'DOLLAR')
        self.assertEqual(root.value, Decimal('1234567.89'))
        self.assertEqual(root.dtasof, datetime(2014, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.57'))

    def testOneOf(self):
        self.oneOfTest('BALTYPE', ('DOLLAR', 'PERCENT', 'NUMBER'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)


if __name__ == '__main__':
    unittest.main()
