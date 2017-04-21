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
    STATUS, MSGSETCORE,
)
from ofxtools.models.bank import (
    CCACCTFROM,
    LEDGERBAL, AVAILBAL, BALLIST,
    BANKTRANLIST, STMTRS,
)
from ofxtools.models.creditcard import (
    CCSTMTRS, CCSTMTTRNRS, REWARDINFO,
    CREDITCARDMSGSRSV1, CREDITCARDMSGSETV1, CREDITCARDMSGSET,
)
from ofxtools.models.i18n import CURRENCY_CODES

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
    unsupported = ['banktranlistp', ]

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
        root = Aggregate.from_etree(self.root)
        for tag in self.unsupported:
            setattr(root, tag, 'FOOBAR')
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIn(root.currency, CURRENCY_CODES)
        self.assertIsInstance(root.account, CCACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class CcstmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
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
        self.assertIsInstance(root.ccstmtrs, CCSTMTRS)


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


class Creditcardmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MSGSETCORE', 'CLOSINGAVAIL', ]
    optionalElements = ['PENDINGAVAIL', ]

    @property
    def root(self):
        root = Element('CREDITCARDMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, 'CLOSINGAVAIL').text = 'Y'
        SubElement(root, 'PENDINGAVAIL').text = 'N'

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.closingavail, True)
        self.assertEqual(root.pendingavail, False)


class CreditcardmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('CREDITCARDMSGSET')
        bankstmtmsgsetv1 = Creditcardmsgsetv1TestCase().root
        root.append(bankstmtmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSET)
        self.assertIsInstance(root.creditcardmsgsetv1, CREDITCARDMSGSETV1)


if __name__ == '__main__':
    unittest.main()
