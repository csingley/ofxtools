# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from copy import deepcopy


# local imports
import ofxtools
from ofxtools.models import (
    Aggregate,
    SONRS,
    CURRENCY,
    BANKACCTFROM,
    CCACCTFROM,
    INVACCTFROM,
    LEDGERBAL,
    AVAILBAL,
    INVBAL,
    BAL,
    DEBTINFO,
    MFINFO,
    OPTINFO,
    OTHERINFO,
    STOCKINFO,
    PORTION,
    FIPORTION,
    STMTTRN,
    PAYEE,
    BANKACCTTO,
    CCACCTTO,
)
from ofxtools.lib import (
    LANG_CODES,
    CURRENCY_CODES,
)


#with open('tests/data/invstmtrs.ofx') as f:
    ## Strip the OFX header
    #sgml = ''.join(f.readlines()[3:])
    #parser = ofxtools.Parser.TreeBuilder(element_factory=ofxtools.Parser.Element)
    #parser.feed(sgml)
    #ofx = parser.close()

#invstmtrs = ofx[1][0][2]
#invtranlist = invstmtrs[3]
#invposlist = invstmtrs[4]
#seclist = ofx[2][0]

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


class SonrsTestCase(unittest.TestCase, TestAggregate):
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
                    raise ValueError("Tag %s should be required, but isn't" % tag)

    def testOneOf(self):
        self.oneOfTest('SEVERITY', ('INFO', 'WARN', 'ERROR'))
        self.oneOfTest('LANGUAGE', LANG_CODES)


class BankacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BANKID', 'ACCTID', 'ACCTTYPE',)
    optionalElements = ('BRANCHID', 'ACCTKEY',)

    @property
    def root(self):
        root = Element('BANKACCTFROM')
        SubElement(root, 'BANKID').text='111000614'
        SubElement(root, 'BRANCHID').text='11223344'
        SubElement(root, 'ACCTID').text='123456789123456789'
        SubElement(root, 'ACCTTYPE').text='CHECKING'
        SubElement(root, 'ACCTKEY').text='DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKACCTFROM)
        self.assertEqual(root.bankid, '111000614')
        self.assertEqual(root.branchid, '11223344')
        self.assertEqual(root.acctid, '123456789123456789')
        self.assertEqual(root.accttype, 'CHECKING')
        self.assertEqual(root.acctkey, 'DEADBEEF')

    def testOneOf(self):
        self.oneOfTest('ACCTTYPE', 
                       ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
                      )


class CCacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('ACCTID',)
    optionalElements = ('ACCTKEY',)

    @property
    def root(self):
        root = Element('CCACCTFROM')
        SubElement(root, 'ACCTID').text='123456789123456789'
        SubElement(root, 'ACCTKEY').text='DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCACCTFROM)
        self.assertEqual(root.acctid, '123456789123456789')


class InvacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BROKERID', 'ACCTID',)

    @property
    def root(self):
        root = Element('INVACCTFROM')
        SubElement(root, 'BROKERID').text='111000614'
        SubElement(root, 'ACCTID').text='123456789123456789'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVACCTFROM)
        self.assertEqual(root.brokerid, '111000614')
        self.assertEqual(root.acctid, '123456789123456789')


class LedgerbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('LEDGERBAL')
        SubElement(root, 'BALAMT').text='12345.67'
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
        SubElement(root, 'BALAMT').text='12345.67'
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
        SubElement(root, 'AVAILCASH').text='12345.67'
        SubElement(root, 'MARGINBALANCE').text='23456.78'
        SubElement(root, 'SHORTBALANCE').text='34567.89'
        SubElement(root, 'BUYPOWER').text='45678.90'
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
        SubElement(root, 'NAME').text='PETTYCASH'
        SubElement(root, 'DESC').text='Walking around money'
        SubElement(root, 'BALTYPE').text='DOLLAR'
        SubElement(root, 'VALUE').text='1234567.89'
        SubElement(root, 'DTASOF').text='20140615'
        currency = SubElement(root, 'CURRENCY')
        SubElement(currency, 'CURSYM').text='USD'
        SubElement(currency, 'CURRATE').text='1.57'
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


if __name__=='__main__':
    unittest.main()
