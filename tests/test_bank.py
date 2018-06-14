# coding: utf-8

# stdlib imports
import unittest
import datetime
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from datetime import datetime
from decimal import Decimal


# local imports
from ofxtools.utils import UTC
from . import base
import ofxtools.models
from ofxtools.models.base import Aggregate
from ofxtools.models.common import (
    STATUS, BAL, MSGSETCORE,
)
from ofxtools.models.bank import (
    BANKACCTFROM, BANKACCTTO, CCACCTTO,
    PAYEE, LEDGERBAL, AVAILBAL, BALLIST,
    STMTTRN, BANKTRANLIST, STMTRS, STMTTRNRS, BANKMSGSRSV1,
    TRNTYPES, BANKMSGSETV1, BANKMSGSET, EMAILPROF,
    ACCTTYPES,
)
from ofxtools.models.i18n import (
    CURRENCY, ORIGCURRENCY,
    CURRENCY_CODES,
)
from . import test_models_common
from . import test_i18n


class BankacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('BANKID', 'ACCTID', 'ACCTTYPE',)
    optionalElements = ('BRANCHID', 'ACCTKEY',)
    tag = 'BANKACCTFROM'

    @property
    def root(self):
        root = Element(self.tag)
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
        self.assertIsInstance(root, getattr(ofxtools.models, self.tag))
        self.assertEqual(root.bankid, '111000614')
        self.assertEqual(root.branchid, '11223344')
        self.assertEqual(root.acctid, '123456789123456789')
        self.assertEqual(root.accttype, 'CHECKING')
        self.assertEqual(root.acctkey, 'DEADBEEF')

    def testOneOf(self):
        self.oneOfTest('ACCTTYPE',
                       ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE',
                        'CD',))


class BankaccttoTestCase(BankacctfromTestCase):
    tag = 'BANKACCTTO'


class CcacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('ACCTID',)
    optionalElements = ('ACCTKEY',)
    tag = 'CCACCTFROM'

    @property
    def root(self):
        root = Element(self.tag)
        SubElement(root, 'ACCTID').text = '123456789123456789'
        SubElement(root, 'ACCTKEY').text = 'DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, getattr(ofxtools.models, self.tag))
        self.assertEqual(root.acctid, '123456789123456789')


class CcaccttoTestCase(CcacctfromTestCase):
    tag = 'CCACCTTO'


class PayeeTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('NAME', 'ADDR1', 'CITY', 'STATE', 'POSTALCODE',
                        'PHONE')
    optionalElements = ('ADDR2', 'ADDR3', 'COUNTRY')

    @property
    def root(self):
        root = Element('PAYEE')
        SubElement(root, 'NAME').text = 'Wrigley Field'
        SubElement(root, 'ADDR1').text = '3717 N Clark St'
        SubElement(root, 'ADDR2').text = 'Dugout Box, Aisle 19'
        SubElement(root, 'ADDR3').text = 'Seat A1'
        SubElement(root, 'CITY').text = 'Chicago'
        SubElement(root, 'STATE').text = 'IL'
        SubElement(root, 'POSTALCODE').text = '60613'
        SubElement(root, 'COUNTRY').text = 'USA'
        SubElement(root, 'PHONE').text = '(773) 309-1027'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PAYEE)
        self.assertEqual(root.name, 'Wrigley Field')
        self.assertEqual(root.addr1, '3717 N Clark St')
        self.assertEqual(root.addr2, 'Dugout Box, Aisle 19')
        self.assertEqual(root.addr3, 'Seat A1')
        self.assertEqual(root.city, 'Chicago')
        self.assertEqual(root.state, 'IL')
        self.assertEqual(root.postalcode, '60613')
        self.assertEqual(root.country, 'USA')
        self.assertEqual(root.phone, '(773) 309-1027')


class BallistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle multiple BALs?

    @property
    def root(self):
        root = Element('BALLIST')
        bal1 = test_models_common.BalTestCase().root
        bal2 = test_models_common.BalTestCase().root
        root.append(bal1)
        root.append(bal2)

        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BALLIST)
        self.assertEqual(len(root), 2)
        self.assertIsInstance(root[0], BAL)
        self.assertIsInstance(root[1], BAL)


class StmttrnTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with CURRENCY """
    __test__ = True
    requiredElements = ['TRNTYPE', 'DTPOSTED', 'TRNAMT', 'FITID', ]
    optionalElements = ['DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'EXTDNAME', 'MEMO', 'CURRENCY',
                        'INV401KSOURCE', ]
    unsupported = ['imagedata', ]

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
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRN)
        self.assertEqual(root.trntype, 'CHECK')
        self.assertEqual(root.dtposted, datetime(2013, 6, 15, tzinfo=UTC))
        self.assertEqual(root.dtuser, datetime(2013, 6, 14, tzinfo=UTC))
        self.assertEqual(root.dtavail, datetime(2013, 6, 16, tzinfo=UTC))
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
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('TRNTYPE', TRNTYPES)

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for unsupp in self.unsupported:
            setattr(root, unsupp, 'FOOBAR')
            self.assertIsNone(getattr(root, unsupp))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class StmttrnOrigcurrencyTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with ORIGCURRENCY """
    optionalElements = ['DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'EXTDNAME', 'MEMO', 'ORIGCURRENCY',
                        'INV401KSOURCE', ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        name = root.find('CURRENCY')
        root.remove(name)
        origcurrency = test_i18n.OrigcurrencyTestCase().root
        root.append(origcurrency)
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
        self.assertIsInstance(root.origcurrency, ORIGCURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.curtype, 'ORIGCURRENCY')
        self.assertEqual(root.cursym, root.origcurrency.cursym)
        self.assertEqual(root.currate, root.origcurrency.currate)


class StmttrnPayeeTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with PAYEE """
    optionalElements = ['DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'PAYEE', 'EXTDNAME', 'MEMO', 'CURRENCY',
                        'INV401KSOURCE', ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        name = root.find('NAME')
        root.remove(name)
        payee = PayeeTestCase().root
        root.append(payee)
        return root

    def testConvert(self):
        root = StmttrnTestCase().root
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
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root


class StmttrnBankaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with BANKACCTTO """
    optionalElements = ['DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'EXTDNAME', 'BANKACCTTO', 'MEMO', 'CURRENCY',
                        'INV401KSOURCE', ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        bankacctto = BankaccttoTestCase().root
        root.append(bankacctto)
        return root

    def testConvert(self):
        root = StmttrnTestCase().root
        self.assertIsInstance(root.bankacctto, BANKACCTTO)


class StmttrnCcaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with CCACCTTO """
    requiredElements = ['TRNTYPE', 'DTPOSTED', 'TRNAMT', 'FITID', ]
    optionalElements = ['DTUSER', 'DTAVAIL', 'CORRECTFITID', 'CORRECTACTION',
                        'SRVRTID', 'CHECKNUM', 'REFNUM', 'SIC', 'PAYEEID',
                        'NAME', 'EXTDNAME', 'CCACCTTO', 'MEMO', 'CURRENCY',
                        'INV401KSOURCE', ]

    @property
    def root(self):
        root = StmttrnTestCase().root
        ccacctto = CcaccttoTestCase().root
        root.append(ccacctto)
        return root

    def testConvert(self):
        root = super(StmttrnCcaccttoTestCase, self).testConvert()
        self.assertIsInstance(root.ccacctto, CCACCTTO)


class StmttrnBankaccttoCcaccttoTestCase(unittest.TestCase, base.TestAggregate):
    """
    STMTTRN with both BANKACCTTO and CCACCTTO - not allowed per OFX spec
    """
    @property
    def root(self):
        root = StmttrnTestCase().root
        bankacctto = BankaccttoTestCase().root
        root.append(bankacctto)
        ccacctto = CcaccttoTestCase().root
        root.append(ccacctto)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)

    def testOneOf(self):
        pass

    def testUnsupported(self):
        pass

    def testPropertyAliases(self):
        pass


class StmttrnNamePayeeTestCase(unittest.TestCase, base.TestAggregate):
    """ STMTTRN with both NAME and PAYEE - not allowed per OFX spec """
    @property
    def root(self):
        root = StmttrnTestCase().root
        payee = PayeeTestCase().root
        root.append(payee)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class StmttrnCurrencyOrigCurrencyTestCase(unittest.TestCase, base.TestAggregate):
    """
    STMTTRN with both CURRENCY and ORIGCURRENCY - not allowed per OFX spec
    """
    @property
    def root(self):
        root = StmttrnTestCase().root
        origcurrency = test_i18n.OrigcurrencyTestCase().root
        root.append(origcurrency)
        return root

    def testConvert(self):
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.root)


class BanktranlistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('DTSTART', 'DTEND',)
    optionalElements = ('STMTTRN',)  # FIXME - *ALL* STMTTRN optional!

    @property
    def root(self):
        root = Element('BANKTRANLIST')
        SubElement(root, 'DTSTART').text = '20130601'
        SubElement(root, 'DTEND').text = '20130630'
        for i in range(2):
            stmttrn = StmttrnTestCase().root
            root.append(stmttrn)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2013, 6, 30, tzinfo=UTC))
        self.assertEqual(len(root), 2)
        for i in range(2):
            self.assertIsInstance(root[i], STMTTRN)


class LedgerbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('LEDGERBAL')
        SubElement(root, 'BALAMT').text = '12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LEDGERBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))


class AvailbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('AVAILBAL')
        SubElement(root, 'BALAMT').text = '12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, AVAILBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC))


class StmtrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('CURDEF', 'BANKACCTFROM', 'LEDGERBAL',)
    optionalElements = ('BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT', 'INTRATE',
                        'BALLIST', 'MKTGINFO',)
    unsupported = ['banktranlistp', ]

    @property
    def root(self):
        root = Element('STMTRS')
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        tranlist = BanktranlistTestCase().root
        root.append(tranlist)
        tranlist = SubElement(root, 'BANKTRANLISTP')
        SubElement(tranlist, 'DTASOF').text = '20130101'
        stmttrnp = SubElement(tranlist, 'STMTTRNP')
        SubElement(stmttrnp, 'TRNTYPE').text = 'FEE'
        SubElement(stmttrnp, 'DTTRAN').text = '20130101'
        SubElement(stmttrnp, 'TRNAMT').text = '5.99'
        SubElement(stmttrnp, 'NAME').text = 'Usury'
        ledgerbal = LedgerbalTestCase().root
        root.append(ledgerbal)
        availbal = AvailbalTestCase().root
        root.append(availbal)
        SubElement(root, 'CASHADVBALAMT').text = '10000.00'
        SubElement(root, 'INTRATE').text = '20.99'
        ballist = BallistTestCase().root
        root.append(ballist)
        SubElement(root, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTRS)
        self.assertIn(root.curdef, CURRENCY_CODES) 
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertEqual(root.cashadvbalamt, Decimal('10000'))
        self.assertEqual(root.intrate, Decimal('20.99'))
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(root.mktginfo, 'Get Free Stuff NOW!!')

    def testUnsupported(self):
        root = Aggregate.from_etree(self.root)
        for tag in self.unsupported:
            setattr(root, tag, 'FOOBAR')
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.account, BANKACCTFROM)
        self.assertIsInstance(root.transactions, BANKTRANLIST)
        self.assertIsInstance(root.balance, LEDGERBAL)


class StmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ['TRNUID', 'STATUS', ]
    optionalElements = ['STMTRS', ]

    @property
    def root(self):
        root = Element('STMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        stmtrs = StmtrsTestCase().root
        root.append(stmtrs)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertIsInstance(root.stmtrs, STMTRS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.statement, STMTRS)


class Bankmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('BANKMSGSRSV1')
        for i in range(2):
            stmttrnrs = StmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, STMTTRNRS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.statements, list)
        self.assertEqual(len(root.statements), 2)
        self.assertIsInstance(root.statements[0], STMTRS)
        self.assertIsInstance(root.statements[1], STMTRS)


class EmailprofTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('EMAILPROF')
        SubElement(root, 'CANEMAIL').text = 'Y'
        SubElement(root, 'CANNOTIFY').text = 'N'

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, EMAILPROF)
        self.assertEqual(root.canemail, True)
        self.assertEqual(root.cannotify, False)

class Bankmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('BANKMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, 'INVALIDACCTTYPE').text = 'CHECKING'
        SubElement(root, 'CLOSINGAVAIL').text = 'Y'
        SubElement(root, 'PENDINGAVAIL').text = 'N'
        emailprof = EmailprofTestCase().root
        root.append(emailprof)

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.invalidaccttype, 'CHECKING')
        self.assertEqual(root.closingavail, True)
        self.assertEqual(root.pendingavail, False)
        self.assertIsInstance(root.emailprof, EMAILPROF)

    def testOneOf(self):
        self.oneOfTest('INVALIDACCTTYPE', ACCTTYPES)


class BankmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('BANKMSGSET')
        bankmsgsetv1 = Bankmsgsetv1TestCase().root
        root.append(bankmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKMSGSET)
        self.assertIsInstance(root.bankmsgsetv1, BANKMSGSETV1)


if __name__ == '__main__':
    unittest.main()
