# coding: utf-8
""" """
# stdlib imports
import unittest
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from decimal import Decimal
from datetime import datetime


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
    CCSTMTRS, CCSTMTTRNRS, LASTPMTINFO, REWARDINFO, CCCLOSING,
    CREDITCARDMSGSRSV1, CREDITCARDMSGSETV1, CREDITCARDMSGSET,
)
from ofxtools.models.i18n import (CURRENCY, CURRENCY_CODES)
from ofxtools.utils import UTC

from . import base
from . import test_models_common
from . import test_bank
from . import test_i18n


class LastpmtinfoTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('LASTPMTINFO')
        SubElement(root, 'LASTPMTDATE').text = '20170501'
        SubElement(root, 'LASTPMTAMT').text = '655.50'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LASTPMTINFO)
        self.assertEqual(root.lastpmtdate, datetime(2017, 5, 1, tzinfo=UTC))
        self.assertEqual(root.lastpmtamt, Decimal('655.50'))


class RewardinfoTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True

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


class CcclosingTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('FITID', 'DTCLOSE', 'BALCLOSE', 'DTPOSTSTART',
                        'DTPOSTEND', )
    optionalElements = ('DTOPEN', 'DTNEXT', 'BALOPEN', 'INTYTD', 'DTPMTDUE',
                        'MINPMTDUE', 'PASTDUEAMT', 'LATEFEEAMT', 'FINCHG',
                        'INTRATEPURCH', 'INTRATECASH', 'INTRATEXFER',
                        'PAYANDCREDIT', 'PURANDADV', 'DEBADJ', 'CREDITLIMIT',
                        'CASHADVCREDITLIMIT', 'AUTOPAY', 'LASTPMTINFO',
                        'REWARDINFO', 'MKTGINFO', 'CURRENCY', )
    unsupported = ['IMAGEDATA', ]

    @property
    def root(self):
        root = Element('CCCLOSING')
        SubElement(root, 'FITID').text = '1001'
        SubElement(root, 'DTOPEN').text = '20040701'
        SubElement(root, 'DTCLOSE').text = '20040704'
        SubElement(root, 'DTNEXT').text = '20040804'
        SubElement(root, 'BALOPEN').text = '24.5'
        SubElement(root, 'BALCLOSE').text = '26.5'
        SubElement(root, 'INTYTD').text = '0.01'
        SubElement(root, 'DTPMTDUE').text = '20040715'
        SubElement(root, 'MINPMTDUE').text = '7.65'
        SubElement(root, 'PASTDUEAMT').text = '0.35'
        SubElement(root, 'LATEFEEAMT').text = '5'
        SubElement(root, 'FINCHG').text = '0.5'
        SubElement(root, 'INTRATEPURCH').text = '26'
        SubElement(root, 'INTRATECASH').text = '30'
        SubElement(root, 'INTRATEXFER').text = '28'
        SubElement(root, 'PAYANDCREDIT').text = '1.5'
        SubElement(root, 'PURANDADV').text = '2.75'
        SubElement(root, 'DEBADJ').text = '1.45'
        SubElement(root, 'CREDITLIMIT').text = '50000'
        SubElement(root, 'CASHADVCREDITLIMIT').text = '5000'
        SubElement(root, 'DTPOSTSTART').text = '20040701'
        SubElement(root, 'DTPOSTEND').text = '20040704'
        SubElement(root, 'AUTOPAY').text = 'Y'
        lastpmtinfo = LastpmtinfoTestCase().root
        root.append(lastpmtinfo)
        rewardinfo = RewardinfoTestCase().root
        root.append(rewardinfo)
        SubElement(root, 'MKTGINFO').text = "It's a floor wax! And a dessert topping!!"
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCCLOSING)
        self.assertEqual(root.fitid, '1001')
        self.assertEqual(root.dtopen, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtclose, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.dtnext, datetime(2004, 8, 4, tzinfo=UTC))
        self.assertEqual(root.balopen, Decimal('24.5'))
        self.assertEqual(root.balclose, Decimal('26.5'))
        self.assertEqual(root.intytd, Decimal('0.01'))
        self.assertEqual(root.dtpmtdue, datetime(2004, 7, 15, tzinfo=UTC))
        self.assertEqual(root.minpmtdue, Decimal('7.65'))
        self.assertEqual(root.pastdueamt, Decimal('0.35'))
        self.assertEqual(root.latefeeamt, Decimal('5'))
        self.assertEqual(root.finchg, Decimal('0.5'))
        self.assertEqual(root.intratepurch, Decimal('26'))
        self.assertEqual(root.intratecash, Decimal('30'))
        self.assertEqual(root.intratexfer, Decimal('28'))
        self.assertEqual(root.payandcredit, Decimal('1.5'))
        self.assertEqual(root.purandadv, Decimal('2.75'))
        self.assertEqual(root.debadj, Decimal('1.45'))
        self.assertEqual(root.creditlimit, Decimal('50000'))
        self.assertEqual(root.cashadvcreditlimit, Decimal('5000'))
        self.assertEqual(root.dtpoststart, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtpostend, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.autopay, True)
        self.assertIsInstance(root.lastpmtinfo, LASTPMTINFO)
        self.assertIsInstance(root.rewardinfo, REWARDINFO)
        self.assertEqual(root.mktginfo, "It's a floor wax! And a dessert topping!!")
        self.assertIsInstance(root.currency, CURRENCY)


class CcstmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    requiredElements = ['CURDEF', 'CCACCTFROM', ]
    optionalElements = ['CCCLOSING', ]

    @property
    def root(self):
        root = Element('CCSTMTENDRS')
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = test_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        ccclosing = CcclosingTestCase().root
        root.append(ccclosing)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDRS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.ccclosing, CCCLOSING)


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
