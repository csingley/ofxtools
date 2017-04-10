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
from . import test_models_base
from . import test_models_accounts
from ofxtools.models import (
    Aggregate,
    STMTTRN,
    PAYEE,
    BANKACCTTO, CCACCTTO,
)


class StmttrnTestCase(unittest.TestCase, common.TestAggregate):
    """ STMTTRN with CURRENCY """
    __test__ = True
    requiredElements = ('DTPOSTED', 'TRNAMT', 'FITID', 'TRNTYPE',)
    optionalElements = ('DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'MEMO', 'INV401KSOURCE', 'CURSYM', 'CURRATE',)
    currencyTag = 'CURRENCY'

    @property
    def root(self):
        root = Element('STMTTRN')
        SubElement(root, 'TRNTYPE').text = 'CHECK'
        SubElement(root, 'DTPOSTED').text = '20130615'
        SubElement(root, 'DTUSER').text = '20130614'
        SubElement(root, 'DTAVAIL').text = '20130616'
        SubElement(root, 'TRNAMT').text = '-433.25'
        SubElement(root, 'FITID').text = 'DEADBEEF'
        SubElement(root, 'CORRECTFITID').text = 'B00B5'
        SubElement(root, 'CORRECTACTION').text = 'REPLACE'
        SubElement(root, 'SRVRTID').text = '101A2'
        SubElement(root, 'CHECKNUM').text = '101'
        SubElement(root, 'REFNUM').text = '5A6B'
        SubElement(root, 'SIC').text = '171103'
        SubElement(root, 'PAYEEID').text = '77810'
        SubElement(root, 'NAME').text = 'Tweet E. Bird'
        SubElement(root, 'EXTDNAME').text = 'Singing yellow canary'
        SubElement(root, 'MEMO').text = 'Protection money'
        currency = SubElement(root, self.currencyTag)
        SubElement(currency, 'CURSYM').text = 'CAD'
        SubElement(currency, 'CURRATE').text = '1.1'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, 'CHECK')
        self.assertEqual(root.dtposted, datetime(2013, 6, 15))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16))
        self.assertEqual(root.trnamt, Decimal('-433.25'))
        self.assertEqual(root.fitid, 'DEADBEEF')
        self.assertEqual(root.correctfitid, 'B00B5')
        self.assertEqual(root.correctaction, 'REPLACE')
        self.assertEqual(root.srvrtid, '101A2')
        self.assertEqual(root.checknum, '101')
        self.assertEqual(root.refnum, '5A6B')
        self.assertEqual(root.sic, 171103)
        self.assertEqual(root.payeeid, '77810')
        self.assertEqual(root.name, 'Tweet E. Bird')
        self.assertEqual(root.extdname, 'Singing yellow canary')
        self.assertEqual(root.memo, 'Protection money')
        self.assertEqual(root.curtype, self.currencyTag)
        self.assertEqual(root.cursym, 'CAD')
        self.assertEqual(root.currate, Decimal('1.1'))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root


class StmttrnOrigcurrencyTestCase(StmttrnTestCase):
    """ STMTTRN with ORIGCURRENCY """
    currencyTag = 'CURRENCY'


class StmttrnPayeeTestCase(StmttrnTestCase):
    """ STMTTRN with PAYEE """
    optionalElements = ('DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'PAYEE', 'MEMO', 'INV401KSOURCE', 'CURSYM', 'CURRATE',)

    @property
    def root(self):
        root = super(self.__class__, self).root
        name = root.find('NAME')
        root.remove(name)
        payee = test_models_base.PayeeTestCase().root
        root.append(payee)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, 'CHECK')
        self.assertEqual(root.dtposted, datetime(2013, 6, 15))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16))
        self.assertEqual(root.trnamt, Decimal('-433.25'))
        self.assertEqual(root.fitid, 'DEADBEEF')
        self.assertEqual(root.correctfitid, 'B00B5')
        self.assertEqual(root.correctaction, 'REPLACE')
        self.assertEqual(root.srvrtid, '101A2')
        self.assertEqual(root.checknum, '101')
        self.assertEqual(root.refnum, '5A6B')
        self.assertEqual(root.sic, 171103)
        self.assertEqual(root.payeeid, '77810')
        self.assertIsInstance(root.payee, PAYEE)
        self.assertEqual(root.extdname, 'Singing yellow canary')
        self.assertEqual(root.memo, 'Protection money')
        self.assertEqual(root.curtype, self.currencyTag)
        self.assertEqual(root.cursym, 'CAD')
        self.assertEqual(root.currate, Decimal('1.1'))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root


class StmttrnBankaccttoTestCase(StmttrnTestCase):
    """ STMTTRN with BANKACCTTO """
    requiredElements = ('DTPOSTED', 'TRNAMT', 'FITID', 'TRNTYPE', 'BANKID',
                        'ACCTID', 'ACCTTYPE',)
    optionalElements = ('DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'MEMO', 'INV401KSOURCE', 'CURSYM', 'CURRATE',
                        'BRANCHID', 'ACCTKEY',)

    @property
    def root(self):
        root = super(self.__class__, self).root
        bankacctto = test_models_accounts.BankaccttoTestCase().root
        root.append(bankacctto)
        return root

    def testConvert(self):
        root = super(StmttrnBankaccttoTestCase, self).testConvert()
        self.assertIsInstance(root.bankacctto, BANKACCTTO)


class StmttrnCcaccttoTestCase(StmttrnTestCase):
    """ STMTTRN with CCACCTTO """
    requiredElements = ('DTPOSTED', 'TRNAMT', 'FITID', 'TRNTYPE', 'ACCTID')
    optionalElements = ('DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'MEMO', 'INV401KSOURCE', 'CURSYM', 'CURRATE',
                        'ACCTKEY',)

    @property
    def root(self):
        root = super(self.__class__, self).root
        ccacctto = test_models_accounts.CcaccttoTestCase().root
        root.append(ccacctto)
        return root

    def testConvert(self):
        root = super(StmttrnCcaccttoTestCase, self).testConvert()
        self.assertIsInstance(root.ccacctto, CCACCTTO)


class StmttrnBankaccttoCcaccttoTestCase(StmttrnTestCase):
    """
    STMTTRN with both BANKACCTTO and CCACCTTO - not allowed per OFX spec
    """
    # required/optional have already been tested in parent; skip here
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        root = super(self.__class__, self).root
        bankacctto = test_models_accounts.BankaccttoTestCase().root
        root.append(bankacctto)
        ccacctto = test_models_accounts.CcaccttoTestCase().root
        root.append(ccacctto)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StmttrnNamePayeeTestCase(StmttrnTestCase):
    """ STMTTRN with both NAME and PAYEE - not allowed per OFX spec """
    # required/optional have already been tested in parent; skip here
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        root = super(self.__class__, self).root
        payee = test_models_base.PayeeTestCase().root
        root.append(payee)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StmttrnCurrencyOrigCurrencyTestCase(StmttrnTestCase):
    """
    STMTTRN with both CURRENCY and ORIGCURRENCY - not allowed per OFX spec
    """
    # required/optional have already been tested in parent; skip here
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        root = super(self.__class__, self).root
        origcurrency = test_models_base.OrigcurrencyTestCase().root
        root.append(origcurrency)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)
