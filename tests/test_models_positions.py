# coding: utf-8
""" """

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import common
from . import test_models_base
from ofxtools.models import (
    Aggregate,
    INVSUBACCTS, INV401KSOURCES,
    POSDEBT, POSMF, POSOPT, POSOTHER, POSSTOCK,
)


class InvposTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = False
    requiredElements = ('SECID', 'HELDINACCT', 'POSTYPE', 'UNITS', 'UNITPRICE',
                        'MKTVAL', 'DTPRICEASOF')
    optionalElements = ('AVGCOSTBASIS', 'CURRENCY', 'MEMO', 'INV401KSOURCE')

    @property
    def root(self):
        root = Element('INVPOS')
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'HELDINACCT').text = 'MARGIN'
        SubElement(root, 'POSTYPE').text = 'LONG'
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'UNITPRICE').text = '90'
        SubElement(root, 'MKTVAL').text = '9000'
        SubElement(root, 'AVGCOSTBASIS').text = '85'
        SubElement(root, 'DTPRICEASOF').text = '20130630'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'MEMO').text = 'Marked to myth'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.heldinacct, 'MARGIN')
        self.assertEqual(root.postype, 'LONG')
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.unitprice, Decimal('90'))
        self.assertEqual(root.mktval, Decimal('9000'))
        self.assertEqual(root.avgcostbasis, Decimal('85'))
        self.assertEqual(root.dtpriceasof, datetime(2013, 6, 30))
        self.assertEqual(root.memo, 'Marked to myth')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('HELDINACCT', INVSUBACCTS)
        self.oneOfTest('POSTYPE', ('SHORT', 'LONG'))
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class PosdebtTestCase(InvposTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('POSDEBT')
        invpos = super(PosdebtTestCase, self).root
        root.append(invpos)
        return root

    def testConvert(self):
        root = super(PosdebtTestCase, self).testConvert()
        self.assertIsInstance(root, POSDEBT)


class PosmfTestCase(InvposTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('POSMF')
        invpos = super(PosmfTestCase, self).root
        root.append(invpos)
        SubElement(root, 'UNITSSTREET').text = '200'
        SubElement(root, 'UNITSUSER').text = '300'
        SubElement(root, 'REINVDIV').text = 'N'
        SubElement(root, 'REINVCG').text = 'Y'
        return root

    def testConvert(self):
        root = super(PosmfTestCase, self).testConvert()
        self.assertIsInstance(root, POSMF)
        self.assertEqual(root.unitsstreet, Decimal('200'))
        self.assertEqual(root.unitsuser, Decimal('300'))
        self.assertEqual(root.reinvdiv, False)
        self.assertEqual(root.reinvcg, True)

    def testOneOf(self):
        super(PosmfTestCase, self).testOneOf()
        self.oneOfTest('REINVDIV', ('Y', 'N'))


class PosoptTestCase(InvposTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('POSOPT')
        invpos = super(PosoptTestCase, self).root
        root.append(invpos)
        SubElement(root, 'SECURED').text = 'COVERED'
        return root

    def testConvert(self):
        root = super(PosoptTestCase, self).testConvert()
        self.assertIsInstance(root, POSOPT)
        self.assertEqual(root.secured, 'COVERED')

    def testOneOf(self):
        super(PosoptTestCase, self).testOneOf()
        self.oneOfTest('SECURED', ('NAKED', 'COVERED'))


class PosotherTestCase(InvposTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('POSOTHER')
        invpos = super(PosotherTestCase, self).root
        root.append(invpos)
        return root

    def testConvert(self):
        root = super(PosotherTestCase, self).testConvert()
        self.assertIsInstance(root, POSOTHER)


class PosstockTestCase(InvposTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('POSSTOCK')
        invpos = super(PosstockTestCase, self).root
        root.append(invpos)
        SubElement(root, 'UNITSSTREET').text = '200'
        SubElement(root, 'UNITSUSER').text = '300'
        SubElement(root, 'REINVDIV').text = 'N'
        return root

    def testConvert(self):
        root = super(PosstockTestCase, self).testConvert()
        self.assertIsInstance(root, POSSTOCK)
        self.assertEqual(root.unitsstreet, Decimal('200'))
        self.assertEqual(root.unitsuser, Decimal('300'))
        self.assertEqual(root.reinvdiv, False)

    def testOneOf(self):
        super(PosstockTestCase, self).testOneOf()
        self.oneOfTest('REINVDIV', ('Y', 'N'))


if __name__ == '__main__':
    unittest.main()
