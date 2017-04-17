# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime


# local imports
from ofxtools.models.common import STATUS

from ofxtools.models.signon import (
    FI, SONRS, SIGNONMSGSRSV1,
)
from ofxtools.models.base import Aggregate

from . import base
from . import test_models_common


class FiTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    optionalElements = ('FID',)

    @property
    def root(self):
        root = Element('FI')
        SubElement(root, 'ORG').text = 'IBLLC-US'
        SubElement(root, 'FID').text = '4705'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FI)
        self.assertEqual(root.org, 'IBLLC-US')
        self.assertEqual(root.fid, '4705')


class SonrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('STATUS', 'DTSERVER',)
    optionalElements = ('USERKEY', 'TSKEYEXPIRE', 'DTPROFUP', 'DTACCTUP', 'FI',
                        'SESSCOOKIE', 'ACCESSKEY')

    @property
    def root(self):
        root = Element('SONRS')
        status = test_models_common.StatusTestCase().root
        root.append(status)
        SubElement(root, 'DTSERVER').text = '20051029101003'
        SubElement(root, 'USERKEY').text = 'DEADBEEF'
        SubElement(root, 'TSKEYEXPIRE').text = '20051231'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        SubElement(root, 'DTPROFUP').text = '20050101'
        SubElement(root, 'DTACCTUP').text = '20050102'
        fi = FiTestCase().root
        root.append(fi)
        SubElement(root, 'SESSCOOKIE').text = 'BADA55'
        SubElement(root, 'ACCESSKEY').text = 'CAFEBABE'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRS)
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.dtserver, datetime(2005, 10, 29, 10, 10, 3))
        self.assertEqual(root.userkey, 'DEADBEEF')
        self.assertEqual(root.tskeyexpire, datetime(2005, 12, 31))
        self.assertEqual(root.language, 'ENG')
        self.assertEqual(root.dtprofup, datetime(2005, 1, 1))
        self.assertEqual(root.dtacctup, datetime(2005, 1, 2))
        self.assertIsInstance(root.fi, FI)
        self.assertEqual(root.sesscookie, 'BADA55')
        self.assertEqual(root.accesskey, 'CAFEBABE')


class Signonmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SIGNONMSGSRSV1')
        sonrs = SonrsTestCase().root
        root.append(sonrs)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SIGNONMSGSRSV1)
        self.assertIsInstance(root.sonrs, SONRS)


if __name__ == '__main__':
    unittest.main()
