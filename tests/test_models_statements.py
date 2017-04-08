# coding: utf-8

# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import common
from . import test_models_base
from . import test_models_accounts
from . import test_models_balances
from . import test_models_lists

from ofxtools.models import (
    Aggregate,
    STMTTRNRS, CCSTMTTRNRS,
    STATUS,
    BANKACCTFROM,
    BANKTRANLIST, BALLIST,
    LEDGERBAL, AVAILBAL,
)
from ofxtools.lib import CURRENCY_CODES


class StmttrnrsTestCase(unittest.TestCase, common.TestAggregate):
    """
    """
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
        self.assertIsInstance(root.ballist, BALLIST)

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
        stmtrs = SubElement(root, 'STMTRS')
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
        self.assertIsInstance(root.ballist, BALLIST)

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


if __name__ == '__main__':
    unittest.main()
