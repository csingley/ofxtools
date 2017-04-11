# coding: utf-8
""" Unit tests for models/base.py """
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
from . import common
from ofxtools.models import (
    Aggregate,
    FI,
    STATUS,
    SONRS,
    CURRENCY,
    BAL,
    PAYEE,
    SECID,
    OFXELEMENT,
)
from ofxtools.lib import LANG_CODES, CURRENCY_CODES


class FiTestCase(unittest.TestCase, common.TestAggregate):
    # <FI> aggregates are optional in SONRQ/SONRS; not all firms use them.
    # Therefore we don't mark ORG as required, so SONRS (inherits from FI)
    # won't throw an error if <FI> is absent.
    __test__ = True
    optionalElements = ('FID',)

    @property
    def root(self):
        root = Element('FI')
        SubElement(root, 'ORG').text = 'IBLLC-US'
        SubElement(root, 'FID').text = '4705'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FI)
        self.assertEqual(root.org, 'IBLLC-US')
        self.assertEqual(root.fid, '4705')


class StatusTestCase(unittest.TestCase, common.TestAggregate):
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


class SonrsTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    requiredElements = ('DTSERVER',)
    optionalElements = ('USERKEY', 'TSKEYEXPIRE', 'DTPROFUP', 'DTACCTUP', 'FI',
                        'SESSCOOKIE', 'ACCESSKEY')

    @property
    def root(self):
        root = Element('SONRS')
        status = SubElement(root, 'STATUS')
        SubElement(status, 'CODE').text = '0'
        SubElement(status, 'SEVERITY').text = 'INFO'
        SubElement(root, 'DTSERVER').text = '20051029101003'
        SubElement(root, 'USERKEY').text = 'DEADBEEF'
        SubElement(root, 'TSKEYEXPIRE').text = '20051231'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        SubElement(root, 'DTPROFUP').text = '20050101'
        SubElement(root, 'DTACCTUP').text = '20050102'
        fi = SubElement(root, 'FI')
        SubElement(fi, 'ORG').text = 'NCH'
        SubElement(fi, 'FID').text = '1001'
        SubElement(root, 'SESSCOOKIE').text = 'BADA55'
        SubElement(root, 'ACCESSKEY').text = 'CAFEBABE'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRS)
        self.assertEqual(root.code, 0)
        self.assertEqual(root.severity, 'INFO')
        self.assertEqual(root.dtserver, datetime(2005, 10, 29, 10, 10, 3))
        self.assertEqual(root.userkey, 'DEADBEEF')
        self.assertEqual(root.tskeyexpire, datetime(2005, 12, 31))
        self.assertEqual(root.language, 'ENG')
        self.assertEqual(root.dtprofup, datetime(2005, 1, 1))
        self.assertEqual(root.dtacctup, datetime(2005, 1, 2))
        self.assertEqual(root.org, 'NCH')
        self.assertEqual(root.fid, '1001')
        self.assertEqual(root.sesscookie, 'BADA55')
        self.assertEqual(root.accesskey, 'CAFEBABE')

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                required = parent.find('./%s' % tag)
                parent.remove(required)
                try:
                    with self.assertRaises(ValueError):
                        Aggregate.from_etree(root)
                except AssertionError:
                    raise ValueError(
                        "Tag %s should be required, but isn't" % tag)

    def testOneOf(self):
        self.oneOfTest('SEVERITY', ('INFO', 'WARN', 'ERROR'))
        self.oneOfTest('LANGUAGE', LANG_CODES)


class CurrencyTestCase(unittest.TestCase, common.TestAggregate):
    # <CURRENCY> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True

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
    # <ORIGCURRENCY> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True

    @property
    def root(self):
        root = super(OrigcurrencyTestCase, self).root
        root.tag = 'ORIGCURRENCY'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CURRENCY)
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')


class BalTestCase(unittest.TestCase, common.TestAggregate):
    # <BAL> aggregates are mostly optional, so its elements
    # (which are mandatory per the OFX spec) aren't marked as required.
    __test__ = True

    @property
    def root(self):
        root = Element('BAL')
        SubElement(root, 'NAME').text = 'balance'
        SubElement(root, 'DESC').text = 'Balance'
        SubElement(root, 'BALTYPE').text = 'DOLLAR'
        SubElement(root, 'VALUE').text = '111.22'
        SubElement(root, 'DTASOF').text = '20010630'
        currency = CurrencyTestCase().root
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
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')

    def testOneOf(self):
        self.oneOfTest('BALTYPE', ('DOLLAR', 'PERCENT', 'NUMBER'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)


class PayeeTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('NAME', 'ADDR1', 'CITY', 'STATE', 'POSTALCODE',
                        'PHONE')
    optionalElements = ('ADDR2', 'ADDR3', 'COUNTRY')

    @property
    def root(self):
        root = Element('PAYEE')
        SubElement(root, 'NAME').text = 'Wrigley Field'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'PHONE').text = '(773) 309-1027'

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PAYEE)
        self.assertEqual(root.name, 'Wrigley Field')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.phone, '(773) 309-1027')


class SecidTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE')

    @property
    def root(self):
        root = Element('SECID')
        SubElement(root, 'UNIQUEID').text = '084670108'
        SubElement(root, 'UNIQUEIDTYPE').text = 'CUSIP'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECID)
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')


class OfxelementTestCase(unittest.TestCase, common.TestAggregate):
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


if __name__ == '__main__':
    unittest.main()
