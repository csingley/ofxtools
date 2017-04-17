# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from decimal import Decimal


# local imports
from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.common import (
    STATUS,
)
from ofxtools.models.bank import (
    CCACCTFROM,
    LEDGERBAL, AVAILBAL, BALLIST,
    BANKTRANLIST, STMTRS,
)
from ofxtools.models.creditcard import (
    CCSTMTRS,
    CCSTMTTRNRS,
    REWARDINFO,
    CREDITCARDMSGSRSV1,
)

from . import base
from . import test_models_common
from . import test_bank


class RewardinfoTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    @property
    def root(self):
        root = Element('REWARDINFO')
        SubElement(root, 'NAME').text = 'Cash Back'
        SubElement(root, 'REWARDBAL').text = '655'
        SubElement(root, 'REWARDEARNED').text = '200'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, REWARDINFO)
        self.assertEqual(root.name, 'Cash Back') 
        self.assertEqual(root.rewardbal, Decimal('655')) 
        self.assertEqual(root.rewardearned, Decimal('200')) 


class CcstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    requiredElements = ['CURDEF', 'CCACCTFROM', 'LEDGERBAL', ]
    optionalElements = ['BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT',
                        'INTRATEPURCH', 'INTRATECASH', 'REWARDINFO',
                        'BALLIST', 'MKTGINFO', ]
    unsupported = ['BANKTRANLISTP', ]

    @property
    def root(self):
        root = Element('CCSTMTRS')
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = test_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        tranlist = test_bank.BanktranlistTestCase().root
        root.append(tranlist)
        ledgerbal = test_bank.LedgerbalTestCase().root
        root.append(ledgerbal)
        availbal = test_bank.AvailbalTestCase().root
        root.append(availbal)
        SubElement(root, 'CASHADVBALAMT').text = '10000.00'
        SubElement(root, 'INTRATEPURCH').text = '20.99'
        SubElement(root, 'INTRATECASH').text = '25.99'
        SubElement(root, 'INTRATEXFER').text = '21.99'
        rewardinfo = RewardinfoTestCase().root
        root.append(rewardinfo)
        ballist = test_bank.BallistTestCase().root
        root.append(ballist)
        SubElement(root, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTRS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal('10000'))
        self.assertEqual(root.intratepurch, Decimal('20.99'))
        self.assertEqual(root.intratecash, Decimal('25.99'))
        self.assertEqual(root.intratexfer, Decimal('21.99'))
        self.assertIsInstance(root.rewardinfo, REWARDINFO)
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, 'Get Free Stuff NOW!!')

    def testUnsupported(self):
        root = self.root
        for tag in self.unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.currency, root.curdef)
        self.assertIs(root.account, root.ccacctfrom)
        self.assertIs(root.transactions, root.banktranlist)


class CcstmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    requiredElements = ('TRNUID', 'STATUS',)
    optionalElements = ('CCSTMTRS', )

    @property
    def root(self):
        root = Element('CCSTMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        stmtrs = CcstmtrsTestCase().root
        root.append(stmtrs)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.stmtrs, STMTRS)


class Creditcardmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('CREDITCARDMSGSRSV1')
        for i in range(2):
            ccstmttrnrs = CcstmttrnrsTestCase().root
            root.append(ccstmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, CCSTMTTRNRS)


if __name__ == '__main__':
    unittest.main()
