# coding: utf-8

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
from . import test_models_banktransactions
from . import test_models_base
from ofxtools.models import (
    Aggregate,
    INVSUBACCTS, INV401KSOURCES,
)


class InvbanktranTestCase(test_models_banktransactions.StmttrnTestCase):
    """ """
    requiredElements = ('DTPOSTED', 'TRNAMT', 'FITID', 'TRNTYPE',
                        'SUBACCTFUND')

    @property
    def root(self):
        root = Element('INVBANKTRAN')
        stmttrn = super(InvbanktranTestCase, self).root
        root.append(stmttrn)
        SubElement(root, 'SUBACCTFUND').text = 'MARGIN'
        return root

    def testConvert(self):
        # Test only INVBANKTRAN wrapper; STMTTRN tested elsewhere
        root = super(InvbanktranTestCase, self).testConvert()
        self.assertEqual(root.subacctfund, 'MARGIN')

    def testOneOf(self):
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)


class InvtranTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    requiredElements = ('FITID', 'DTTRADE',)
    optionalElements = ('SRVRTID', 'DTSETTLE', 'REVERSALFITID', 'MEMO',)

    @property
    def root(self):
        root = Element('INVTRAN')
        SubElement(root, 'FITID').text = '1001'
        SubElement(root, 'SRVRTID').text = '2002'
        SubElement(root, 'DTTRADE').text = '20040701'
        SubElement(root, 'DTSETTLE').text = '20040704'
        SubElement(root, 'REVERSALFITID').text = '3003'
        SubElement(root, 'MEMO').text = 'Investment Transaction'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, '1001')
        self.assertEqual(root.srvrtid, '2002')
        self.assertEqual(root.dttrade, datetime(2004, 7, 1))
        self.assertEqual(root.dtsettle, datetime(2004, 7, 4))
        self.assertEqual(root.reversalfitid, '3003')
        self.assertEqual(root.memo, 'Investment Transaction')
        return root


class InvbuyTestCase(InvtranTestCase):
    """ """
    @property
    def root(self):
        root = Element('INVBUY')
        invtran = super(InvbuyTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'UNITPRICE').text = '1.50'
        SubElement(root, 'MARKUP').text = '0'
        SubElement(root, 'COMMISSION').text = '9.99'
        SubElement(root, 'TAXES').text = '0'
        SubElement(root, 'FEES').text = '1.50'
        SubElement(root, 'LOAD').text = '0'
        SubElement(root, 'TOTAL').text = '-161.49'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'LOANID').text = '1'
        SubElement(root, 'LOANPRINCIPAL').text = '1.50'
        SubElement(root, 'LOANINTEREST').text = '3.50'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        SubElement(root, 'DTPAYROLL').text = '20040615'
        SubElement(root, 'PRIORYEARCONTRIB').text = 'Y'
        return root

    @property
    def requiredElements(self):
        req = super(InvbuyTestCase, self).requiredElements
        req += ('SECID', 'UNITS', 'UNITPRICE', 'TOTAL', 'SUBACCTSEC',
                'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        req = super(InvbuyTestCase, self).optionalElements
        req += ('MARKUP', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                'CURRENCY', 'LOANID', 'LOANPRINCIPAL', 'LOANINTEREST',
                'INV401KSOURCE', 'DTPAYROLL', 'PRIORYEARCONTRIB')
        return req

    def testConvert(self):
        root = super(InvbuyTestCase, self).testConvert()
        test_models_base.SecidTestCase().root
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.markup, Decimal('0'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('0'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.total, Decimal('-161.49'))
        test_models_base.CurrencyTestCase().root
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.loanid, '1')
        self.assertEqual(root.loanprincipal, Decimal('1.50'))
        self.assertEqual(root.loaninterest, Decimal('3.50'))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        self.assertEqual(root.dtpayroll, datetime(2004, 6, 15))
        self.assertEqual(root.prioryearcontrib, True)
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class InvsellTestCase(InvtranTestCase):
    """ """
    @property
    def root(self):
        root = Element('INVSELL')
        invtran = super(InvsellTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITS').text = '-100'
        SubElement(root, 'UNITPRICE').text = '1.50'
        SubElement(root, 'MARKUP').text = '0'
        SubElement(root, 'COMMISSION').text = '9.99'
        SubElement(root, 'TAXES').text = '2'
        SubElement(root, 'FEES').text = '1.50'
        SubElement(root, 'LOAD').text = '0'
        SubElement(root, 'WITHHOLDING').text = '3'
        SubElement(root, 'TAXEXEMPT').text = 'N'
        SubElement(root, 'TOTAL').text = '131.00'
        SubElement(root, 'GAIN').text = '3.47'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'LOANID').text = '1'
        SubElement(root, 'STATEWITHHOLDING').text = '2.50'
        SubElement(root, 'PENALTY').text = '0.01'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(InvsellTestCase, self).requiredElements
        req += ('SECID', 'UNITS', 'UNITPRICE', 'TOTAL', 'SUBACCTSEC',
                'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        req = super(InvbuyTestCase, self).optionalElements
        req += ('MARKDOWN', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                'WITHHOLDING', 'TAXEXEMPT', 'GAIN', 'CURRENCY', 'LOANID',
                'STATEWITHHOLDING', 'PENALTY', 'INV401KSOURCE',)
        return req

    def testConvert(self):
        root = super(InvbuyTestCase, self).testConvert()
        test_models_base.SecidTestCase().root
        self.assertEqual(root.units, Decimal('-100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.markup, Decimal('0'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('2'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.withholding, Decimal('3'))
        self.assertEqual(root.taxexempt, False)
        self.assertEqual(root.total, Decimal('131'))
        self.assertEqual(root.gain, Decimal('3.47'))
        test_models_base.CurrencyTestCase().root
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.loanid, '1')
        self.assertEqual(root.statewithholding, Decimal('2.50'))
        self.assertEqual(root.penalty, Decimal('0.01'))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class BuydebtTestCase(InvbuyTestCase):
    """ """
    __test__ = True
    optionalElements = ('SRVRTID', 'DTSETTLE', 'REVERSALFITID', 'MEMO',
                        'MARKUP', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                        'CURRENCY', 'LOANID', 'LOANPRINCIPAL', 'LOANINTEREST',
                        'INV401KSOURCE', 'DTPAYROLL', 'PRIORYEARCONTRIB')

    @property
    def root(self):
        root = Element('BUYDEBT')
        invbuy = super(BuydebtTestCase, self).root
        root.append(invbuy)
        SubElement(root, 'ACCRDINT').text = '25.50'
        return root

    @property
    def optionalElements(self):
        req = super(BuydebtTestCase, self).optionalElements
        req += ('ACCRDINT',)
        return req

    def testConvert(self):
        root = super(BuydebtTestCase, self).testConvert()
        self.assertEqual(root.accrdint, Decimal('25.50'))
