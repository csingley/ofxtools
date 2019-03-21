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
import base
import test_models_common
import test_models_bank
import test_models_i18n

from ofxtools.models.base import (
    Aggregate,
)
from ofxtools.models.common import (
    STATUS, MSGSETCORE,
)
from ofxtools.models.bank import (
    CCACCTFROM,
    LEDGERBAL, AVAILBAL, BALLIST,
    BANKTRANLIST, STMTRS, INCTRAN,
)
from ofxtools.models.creditcard import (
    CCSTMTRQ, CCSTMTRS, CCSTMTTRNRQ, CCSTMTTRNRS, CCSTMTENDRQ, CCSTMTENDRS,
    LASTPMTINFO, REWARDINFO, CCCLOSING,
    CCSTMTENDRQ, CCSTMTENDRS, CCSTMTENDTRNRQ, CCSTMTENDTRNRS,
    CREDITCARDMSGSRQV1, CREDITCARDMSGSRSV1, CREDITCARDMSGSETV1,
    CREDITCARDMSGSET, )
from ofxtools.models.i18n import (CURRENCY, CURRENCY_CODES)
from ofxtools.utils import UTC


class LastpmtinfoTestCase(unittest.TestCase, base.TestAggregate):
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


class CcstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['CCACCTFROM', ]
    optionalElements = ['INCTRAN', 'INCLUDEPENDING', 'INCTRANIMG']

    @property
    def root(self):
        root = Element('CCSTMTRQ')
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        inctran = test_models_bank.InctranTestCase().root
        root.append(inctran)
        SubElement(root, 'INCLUDEPENDING').text = 'N'
        SubElement(root, 'INCTRANIMG').text = 'Y'

        return root

    def testConvert(self):
        # Test *TRNRQ wrapper and direct child elements
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTRQ)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.inctran, INCTRAN)
        self.assertEqual(root.includepending, False)
        self.assertEqual(root.inctranimg, True)


class CcstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ['CURDEF', 'CCACCTFROM', 'LEDGERBAL', ]
    optionalElements = ['BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT',
                        'INTRATEPURCH', 'INTRATECASH', 'REWARDINFO',
                        'BALLIST', 'MKTGINFO', ]
    unsupported = ['banktranlistp', ]

    @property
    def root(self):
        root = Element('CCSTMTRS')
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        tranlist = test_models_bank.BanktranlistTestCase().root
        root.append(tranlist)
        ledgerbal = test_models_bank.LedgerbalTestCase().root
        root.append(ledgerbal)
        availbal = test_models_bank.AvailbalTestCase().root
        root.append(availbal)
        SubElement(root, 'CASHADVBALAMT').text = '10000.00'
        SubElement(root, 'INTRATEPURCH').text = '20.99'
        SubElement(root, 'INTRATECASH').text = '25.99'
        SubElement(root, 'INTRATEXFER').text = '21.99'
        rewardinfo = RewardinfoTestCase().root
        root.append(rewardinfo)
        ballist = test_models_bank.BallistTestCase().root
        root.append(ballist)
        SubElement(root, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and direct child elements.
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
        self.assertIsInstance(root.account, CCACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class CcstmttrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', )
    optionalElements = ('CCSTMTRQ', )

    @property
    def root(self):
        root = Element('CCSTMTTRNRQ')
        SubElement(root, 'TRNUID').text = '1001'
        stmtrq = CcstmtrqTestCase().root
        root.append(stmtrq)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTTRNRQ)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.ccstmtrq, CCSTMTRQ)


class CcstmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
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
        currency = test_models_i18n.CurrencyTestCase().root
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


class CcstmtendrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('CCACCTFROM', )
    optionalElements = ('DTSTART', 'DTEND', 'INCSTMTIMG', )

    @property
    def root(self):
        root = Element('CCSTMTENDRQ')
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        SubElement(root, 'DTSTART').text = '20040701'
        SubElement(root, 'DTEND').text = '20040704'
        SubElement(root, 'INCSTMTIMG').text = 'N'

        return root

    def testConvert(self):
        # Test *RQ and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDRQ)
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertEqual(root.dtstart, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.incstmtimg, False)


class CcstmtendrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('CURDEF', 'CCACCTFROM', )
    optionalElements = ('CCCLOSING', )

    @property
    def root(self):
        root = Element('CCSTMTENDRS')
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = test_models_bank.CcacctfromTestCase().root
        root.append(acctfrom)
        ccclosing = CcclosingTestCase().root
        root.append(ccclosing)

        return root

    def testConvert(self):
        # Test *RS and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDRS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.ccacctfrom, CCACCTFROM)
        self.assertIsInstance(root.ccclosing, CCCLOSING)


class CcstmtendtrnrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ('TRNUID', )
    optionalElements = ('CCSTMTENDRQ', )

    @property
    def root(self):
        root = Element('CCSTMTENDTRNRQ')
        SubElement(root, 'TRNUID').text = '1001'
        ccstmtendrq = CcstmtendrqTestCase().root
        root.append(ccstmtendrq)

        return root

    def testConvert(self):
        # Test *TRNRQ and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDTRNRQ)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.ccstmtendrq, CCSTMTENDRQ)


class CcstmtendtrnrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True 

    requiredElements = ('TRNUID', 'STATUS', )
    optionalElements = ('CCSTMTENDRS', )

    @property
    def root(self):
        root = Element('CCSTMTENDTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        ccstmtendrs = CcstmtendrsTestCase().root
        root.append(ccstmtendrs)

        return root

    def testConvert(self):
        # Test *TRNRS and direct child elements.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCSTMTENDTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.ccstmtendrs, CCSTMTENDRS)


class Creditcardmsgsrqv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('CREDITCARDMSGSRQV1')
        ccstmttrnrq = CcstmttrnrqTestCase().root
        root.append(ccstmttrnrq)
        ccstmtendtrnrq = CcstmtendtrnrqTestCase().root
        root.append(ccstmtendtrnrq)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRQV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], CCSTMTTRNRQ)
        self.assertIsInstance(root[1], CCSTMTENDTRNRQ)


class Creditcardmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('CREDITCARDMSGSRSV1')
        ccstmttrnrs = CcstmttrnrsTestCase().root
        root.append(ccstmttrnrs)
        ccstmtendtrnrs = CcstmtendtrnrsTestCase().root
        root.append(ccstmtendtrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CREDITCARDMSGSRSV1)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], CCSTMTTRNRS)
        self.assertIsInstance(root[1], CCSTMTENDTRNRS)


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
