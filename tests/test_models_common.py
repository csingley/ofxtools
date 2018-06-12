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
    STATUS, BAL, CURRENCY, OFXELEMENT, OFXEXTENSION, MSGSETCORE,
)
from ofxtools.models.i18n import (CURRENCY_CODES, LANG_CODES)
from ofxtools.utils import UTC


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
        self.assertEqual(root.dtasof, datetime(2001, 6, 30, tzinfo=UTC))
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
    optionalElements = []  # FIXME - how to handle multiple OFXELEMENTs?

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


class MsgsetcoreTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['VER', 'URL', 'OFXSEC', 'TRANSPSEC', 'SIGNONREALM',
                        'LANGUAGE', 'SYNCMODE', 'RESPFILEER']
    # optionalElements = ['REFRESHSUPT', 'SPNAME', 'OFXEXTENSION']

    @property
    def root(self):
        root = Element('MSGSETCORE')
        SubElement(root, 'VER').text = '1'
        SubElement(root, 'URL').text = 'https://ofxs.ameritrade.com/cgi-bin/apps/OFX'
        SubElement(root, 'OFXSEC').text = 'NONE'
        SubElement(root, 'TRANSPSEC').text = 'Y'
        SubElement(root, 'SIGNONREALM').text = 'AMERITRADE'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        SubElement(root, 'SYNCMODE').text = 'FULL'
        SubElement(root, 'REFRESHSUPT').text = 'N'
        SubElement(root, 'RESPFILEER').text = 'N'
        SubElement(root, 'INTU.TIMEOUT').text = '360'
        SubElement(root, 'SPNAME').text = 'Dewey Cheatham & Howe'
        ofxextension = OfxextensionTestCase().root
        root.append(ofxextension)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MSGSETCORE)
        self.assertEqual(root.ver, 1)
        self.assertEqual(root.url, 'https://ofxs.ameritrade.com/cgi-bin/apps/OFX')
        self.assertEqual(root.ofxsec, 'NONE')
        self.assertEqual(root.transpsec, True)
        self.assertEqual(root.signonrealm, 'AMERITRADE')
        self.assertEqual(root.language, 'ENG')
        self.assertEqual(root.syncmode, 'FULL')
        self.assertEqual(root.refreshsupt, False)
        self.assertEqual(root.respfileer, False)
        self.assertEqual(root.spname, 'Dewey Cheatham & Howe')
        self.assertIsInstance(root.ofxextension, OFXEXTENSION)

    def testOneOf(self):
        self.oneOfTest('OFXSEC', ('NONE', 'TYPE1'))
        self.oneOfTest('LANGUAGE', LANG_CODES)
        self.oneOfTest('SYNCMODE', ('FULL', 'LITE'))


if __name__ == '__main__':
    unittest.main()
