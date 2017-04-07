# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import common
from ofxtools.models import (
    Aggregate,
    BANKACCTFROM,
    CCACCTFROM,
    INVACCTFROM,
)


class BankacctfromTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    requiredElements = ('BANKID', 'ACCTID', 'ACCTTYPE',)
    optionalElements = ('BRANCHID', 'ACCTKEY',)

    @property
    def root(self):
        root = Element('BANKACCTFROM')
        SubElement(root, 'BANKID').text = '111000614'
        SubElement(root, 'BRANCHID').text = '11223344'
        SubElement(root, 'ACCTID').text = '123456789123456789'
        SubElement(root, 'ACCTTYPE').text = 'CHECKING'
        SubElement(root, 'ACCTKEY').text = 'DEADBEEF'
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
                       ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE'))


class CCacctfromTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    requiredElements = ('ACCTID',)
    optionalElements = ('ACCTKEY',)

    @property
    def root(self):
        root = Element('CCACCTFROM')
        SubElement(root, 'ACCTID').text = '123456789123456789'
        SubElement(root, 'ACCTKEY').text = 'DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCACCTFROM)
        self.assertEqual(root.acctid, '123456789123456789')


class InvacctfromTestCase(unittest.TestCase, common.TestAggregate):
    __test__ = True
    requiredElements = ('BROKERID', 'ACCTID',)

    @property
    def root(self):
        root = Element('INVACCTFROM')
        SubElement(root, 'BROKERID').text = '111000614'
        SubElement(root, 'ACCTID').text = '123456789123456789'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVACCTFROM)
        self.assertEqual(root.brokerid, '111000614')
        self.assertEqual(root.acctid, '123456789123456789')


if __name__ == '__main__':
    unittest.main()
