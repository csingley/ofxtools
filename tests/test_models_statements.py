# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.models import (
    Aggregate,
    STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS,
    STATUS,
    BANKACCTFROM, CCACCTFROM, INVACCTFROM,
    BANKTRANLIST, INVTRANLIST, INVPOSLIST, BALLIST,
    LEDGERBAL, AVAILBAL, INVBAL,
)
from ofxtools.lib import CURRENCY_CODES

from . import common
from . import test_models_base
from . import test_models_accounts
from . import test_models_balances
from . import test_models_lists


class StmttrnrsTestCase(unittest.TestCase, common.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('TRNUID', 'CODE', 'SEVERITY', 'CURDEF',
                        'BANKACCTFROM', 'LEDGERBAL',)
    optionalElements = ('BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT', 'INTRATE',
                        'BALLIST', 'MKTGINFO',)

    @property
    def root(self):
        root = Element('STMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_base.StatusTestCase().root
        root.append(status)
        stmtrs = SubElement(root, 'STMTRS')
        SubElement(stmtrs, 'CURDEF').text = 'USD'
        acctfrom = test_models_accounts.BankacctfromTestCase().root
        stmtrs.append(acctfrom)
        tranlist = test_models_lists.BanktranlistTestCase().root
        stmtrs.append(tranlist)
        tranlist = SubElement(stmtrs, 'BANKTRANLISTP')
        SubElement(tranlist, 'DTASOF').text = '20130101'
        stmttrnp = SubElement(tranlist, 'STMTTRNP')
        SubElement(stmttrnp, 'TRNTYPE').text = 'FEE'
        SubElement(stmttrnp, 'DTTRAN').text = '20130101'
        SubElement(stmttrnp, 'TRNAMT').text = '5.99'
        SubElement(stmttrnp, 'NAME').text = 'Usury'
        ledgerbal = test_models_balances.LedgerbalTestCase().root
        availbal = test_models_balances.AvailbalTestCase().root
        stmtrs.append(ledgerbal)
        stmtrs.append(availbal)
        SubElement(stmtrs, 'CASHADVBALAMT').text = '10000.00'
        SubElement(stmtrs, 'INTRATE').text = '20.99'
        ballist = test_models_lists.BallistTestCase().root
        stmtrs.append(ballist)
        SubElement(stmtrs, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal('10000')) 
        self.assertEqual(root.intrate, Decimal('20.99')) 
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, 'Get Free Stuff NOW!!')

    def testUnsupported(self):
        root = self.root
        for tag in STMTTRNRS._unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testOneOf(self):
        self.oneOfTest('CURSYM', CURRENCY_CODES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.currency, root.curdef)
        self.assertIs(root.account, root.bankacctfrom)
        self.assertIs(root.transactions, root.banktranlist)


class CctmttrnrsTestCase(StmttrnrsTestCase):
    """
    """
    requiredElements = ('TRNUID', 'CODE', 'SEVERITY', 'CURDEF',
                        'CCACCTFROM', 'LEDGERBAL',)
    optionalElements = ('BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT',
                        'INTRATEPURCH', 'INTRATECASH', 'REWARDINFO',
                        'BALLIST', 'MKTGINFO',)

    @property
    def root(self):
        root = Element('CCSTMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_base.StatusTestCase().root
        root.append(status)
        stmtrs = SubElement(root, 'CCSTMTRS')
        SubElement(stmtrs, 'CURDEF').text = 'USD'
        acctfrom = test_models_accounts.CcacctfromTestCase().root
        stmtrs.append(acctfrom)
        tranlist = test_models_lists.BanktranlistTestCase().root
        stmtrs.append(tranlist)
        tranlist = SubElement(stmtrs, 'BANKTRANLISTP')
        SubElement(tranlist, 'DTASOF').text = '20130101'
        stmttrnp = SubElement(tranlist, 'STMTTRNP')
        SubElement(stmttrnp, 'TRNTYPE').text = 'FEE'
        SubElement(stmttrnp, 'DTTRAN').text = '20130101'
        SubElement(stmttrnp, 'TRNAMT').text = '5.99'
        SubElement(stmttrnp, 'NAME').text = 'Usury'
        ledgerbal = test_models_balances.LedgerbalTestCase().root
        availbal = test_models_balances.AvailbalTestCase().root
        stmtrs.append(ledgerbal)
        stmtrs.append(availbal)
        SubElement(stmtrs, 'CASHADVBALAMT').text = '10000.00'
        SubElement(stmtrs, 'INTRATEPURCH').text = '20.99'
        SubElement(stmtrs, 'INTRATECASH').text = '25.99'
        SubElement(stmtrs, 'INTRATEXFER').text = '21.99'
        rewardinfo = SubElement(stmtrs, 'REWARDINFO')
        SubElement(rewardinfo, 'NAME').text = 'Cash Back'
        SubElement(rewardinfo, 'REWARDBAL').text = '655'
        SubElement(rewardinfo, 'REWARDEARNED').text = '200'
        ballist = test_models_lists.BallistTestCase().root
        stmtrs.append(ballist)
        SubElement(stmtrs, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal('10000'))
        self.assertEqual(root.intratepurch, Decimal('20.99'))
        self.assertEqual(root.intratecash, Decimal('25.99'))
        self.assertEqual(root.intratexfer, Decimal('21.99'))
        self.assertEqual(root.rewardname, 'Cash Back')
        self.assertEqual(root.rewardbal, Decimal('655'))
        self.assertEqual(root.rewardearned, Decimal('200'))
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, 'Get Free Stuff NOW!!')

    def testUnsupported(self):
        root = self.root
        for tag in STMTTRNRS._unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testOneOf(self):
        self.oneOfTest('CURSYM', CURRENCY_CODES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.currency, root.curdef)
        self.assertIs(root.account, root.ccacctfrom)
        self.assertIs(root.transactions, root.banktranlist)


class InvstmttrnrsTestCase(unittest.TestCase, common.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('TRNUID', 'CODE', 'SEVERITY', 'DTASOF', 'CURDEF',
                        'BROKERID', 'INVACCTFROM',)
    optionalElements = ('INVTRANLIST', 'INVPOSLIST', 'INVBAL',)

    @property
    def root(self):
        root = Element('INVSTMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_base.StatusTestCase().root
        root.append(status)
        SubElement(root, 'CLIENTCOOKIE').text = 'DEADBEEF'
        # FIXME - OFXEXTENSION
        stmtrs = SubElement(root, 'INVSTMTRS')
        SubElement(stmtrs, 'DTASOF').text = '20010530'
        SubElement(stmtrs, 'CURDEF').text = 'USD'
        acctfrom = test_models_accounts.InvacctfromTestCase().root
        stmtrs.append(acctfrom)
        tranlist = test_models_lists.InvtranlistTestCase().root
        stmtrs.append(tranlist)
        poslist = test_models_lists.InvposlistTestCase().root
        stmtrs.append(poslist)
        invbal = test_models_balances.InvbalTestCase().root
        stmtrs.append(invbal)
        invoolist = test_models_lists.InvoolistTestCase().root
        stmtrs.append(invoolist)
        SubElement(stmtrs, 'MKTGINFO').text = 'Get Free Stuff NOW!!'
        # FIXME - INV401K
        inv401kbal = test_models_balances.Inv401kbalTestCase().root
        stmtrs.append(inv401kbal)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.clientcookie, 'DEADBEEF')
        self.assertEqual(root.dtasof, datetime(2001, 5, 30))
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)
        self.assertIsInstance(root.invtranlist, INVTRANLIST)
        self.assertIsInstance(root.invposlist, INVPOSLIST)
        self.assertIsInstance(root.invbal, INVBAL)

    def testUnsupported(self):
        root = self.root
        for tag in INVSTMTTRNRS._unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testOneOf(self):
        self.oneOfTest('CURDEF', CURRENCY_CODES)
        self.oneOfTest('CURSYM', CURRENCY_CODES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.currency, root.curdef)
        self.assertIs(root.account, root.invacctfrom)
        self.assertIs(root.transactions, root.invtranlist)
        self.assertIs(root.datetime, root.dtasof)
        self.assertIs(root.positions, root.invposlist)


if __name__ == '__main__':
    unittest.main()
