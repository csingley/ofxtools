# coding: utf-8
"""
"""
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
    STATUS, OFXEXTENSION, MSGSETCORE,
)
from ofxtools.models.bank import (
    STMTTRN, BALLIST, INV401KSOURCES,
    TRNTYPES,
)
from ofxtools.models.investment import (
    INVTRAN, INVBUY, INVSELL, SECID,
    INVBANKTRAN, BUYDEBT, BUYMF, BUYOPT, BUYOTHER, BUYSTOCK, CLOSUREOPT,
    INCOME, INVEXPENSE, JRNLFUND, JRNLSEC, MARGININTEREST, REINVEST, RETOFCAP,
    SELLDEBT, SELLMF, SELLOPT, SELLOTHER, SELLSTOCK, SPLIT, TRANSFER,
    INVPOS, POSDEBT, POSMF, POSOPT, POSOTHER, POSSTOCK,
    OO, OOBUYDEBT, OOBUYMF, OOBUYOPT, OOBUYOTHER, OOBUYSTOCK,
    OOSELLDEBT, OOSELLMF, OOSELLOPT, OOSELLOTHER, OOSELLSTOCK, SWITCHMF,
    INVTRANLIST, INVPOSLIST, INVOOLIST, INVACCTFROM,
    INV401KBAL, INVBAL, INVSTMTRS, INVSTMTTRNRS, INVSTMTMSGSRSV1,
    BUYTYPES, SELLTYPES, OPTBUYTYPES, OPTSELLTYPES, INCOMETYPES, UNITTYPES,
    INVSUBACCTS, INVSTMTMSGSETV1, INVSTMTMSGSET,
)
from ofxtools.models.i18n import (
    CURRENCY, CURRENCY_CODES,
)
from ofxtools.utils import UTC
from . import base
from . import test_models_common
from . import test_bank
from . import test_seclist
from . import test_i18n


class InvacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('BROKERID', 'ACCTID',)

    @property
    def root(self):
        root = Element('INVACCTFROM')
        SubElement(root, 'BROKERID').text = '111000614'
        SubElement(root, 'ACCTID').text = '123456789123456789'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        # self.assertIsInstance(root, INVACCTFROM)
        self.assertEqual(root.brokerid, '111000614')
        self.assertEqual(root.acctid, '123456789123456789')


class InvposlistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('INVPOSLIST')
        for invpos in ('Posdebt', 'Posmf', 'Posopt', 'Posother', 'Posstock'):
            testCase = '{}TestCase'.format(invpos)
            elem = globals()[testCase]().root
            root.append(elem)
        return root

    def testConvert(self):
        # Test INVPOSLIST wrapper.  INVPOS members are tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVPOSLIST)
        self.assertEqual(len(root), 5)
        self.assertIsInstance(root[0], POSDEBT)
        self.assertIsInstance(root[1], POSMF)
        self.assertIsInstance(root[2], POSOPT)
        self.assertIsInstance(root[3], POSOTHER)
        self.assertIsInstance(root[4], POSSTOCK)

    def testToEtree(self):
        root = Aggregate.from_etree(self.root)
        elem = root.to_etree()


class InvoolistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle OO subclasses?

    @property
    def root(self):
        root = Element('INVOOLIST')
        SubElement(root, 'DTSTART').text = '20130601'
        SubElement(root, 'DTEND').text = '20130630'
        for oo in ('Oobuydebt', 'Oobuymf', 'Oobuyopt', 'Oobuyother',
                   'Oobuystock', 'Ooselldebt', 'Oosellmf', 'Oosellopt',
                   'Oosellother', 'Oosellstock', 'Switchmf',):
            testCase = '{}TestCase'.format(oo)
            elem = globals()[testCase]().root
            root.append(elem)
        return root

    def testConvert(self):
        # Test OOLIST wrapper.  OO members are tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVOOLIST)
        self.assertEqual(len(root), 11)
        self.assertIsInstance(root[0], OOBUYDEBT)
        self.assertIsInstance(root[1], OOBUYMF)
        self.assertIsInstance(root[2], OOBUYOPT)
        self.assertIsInstance(root[3], OOBUYOTHER)
        self.assertIsInstance(root[4], OOBUYSTOCK)
        self.assertIsInstance(root[5], OOSELLDEBT)
        self.assertIsInstance(root[6], OOSELLMF)
        self.assertIsInstance(root[7], OOSELLOPT)
        self.assertIsInstance(root[8], OOSELLOTHER)
        self.assertIsInstance(root[9], OOSELLSTOCK)
        self.assertIsInstance(root[10], SWITCHMF)

    def testToEtree(self):
        root = Aggregate.from_etree(self.root)
        elem = root.to_etree()


class InvbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('AVAILCASH', 'MARGINBALANCE', 'SHORTBALANCE',)
    optionalElements = ('BUYPOWER',)
    # BALLIST blows up _flatten(); don't test it here

    @property
    def root(self):
        root = Element('INVBAL')
        SubElement(root, 'AVAILCASH').text = '12345.67'
        SubElement(root, 'MARGINBALANCE').text = '23456.78'
        SubElement(root, 'SHORTBALANCE').text = '34567.89'
        SubElement(root, 'BUYPOWER').text = '45678.90'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVBAL)
        self.assertEqual(root.availcash, Decimal('12345.67'))
        self.assertEqual(root.marginbalance, Decimal('23456.78'))
        self.assertEqual(root.shortbalance, Decimal('34567.89'))
        self.assertEqual(root.buypower, Decimal('45678.90'))


class InvtranlistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('DTSTART', 'DTEND',)
    optionalElements = ()  # FIXME - how to handle INVTRAN subclasses?

    @property
    def root(self):
        root = Element('INVTRANLIST')
        SubElement(root, 'DTSTART').text = '20130601'
        SubElement(root, 'DTEND').text = '20130630'
        for it in ('Invbanktran', 'Buydebt', 'Buymf', 'Buyopt', 'Buyother',
                   'Buystock', 'Closureopt', 'Income', 'Invexpense',
                   'Jrnlfund', 'Jrnlsec', 'Margininterest', 'Reinvest',
                   'Retofcap', 'Selldebt', 'Sellmf', 'Sellopt', 'Sellother',
                   'Sellstock', 'Split', 'Transfer',):
            testcase = '{}TestCase'.format(it)
            invtran = globals()[testcase]
            root.append(invtran().root)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1, tzinfo=UTC))
        self.assertEqual(root.dtend, datetime(2013, 6, 30, tzinfo=UTC))
        self.assertEqual(len(root), 21)
        for i, it in enumerate((INVBANKTRAN, BUYDEBT, BUYMF, BUYOPT, BUYOTHER,
                                BUYSTOCK, CLOSUREOPT, INCOME, INVEXPENSE,
                                JRNLFUND, JRNLSEC, MARGININTEREST, REINVEST,
                                RETOFCAP, SELLDEBT, SELLMF, SELLOPT, SELLOTHER,
                                SELLSTOCK, SPLIT, TRANSFER,)):
            self.assertIsInstance(root[i], it)

    def testToEtree(self):
        root = Aggregate.from_etree(self.root)
        elem = root.to_etree()


class InvbanktranTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ['STMTTRN', 'SUBACCTFUND', ]

    @property
    def root(self):
        root = Element('INVBANKTRAN')
        stmttrn = test_bank.StmttrnTestCase().root
        root.append(stmttrn)
        SubElement(root, 'SUBACCTFUND').text = 'MARGIN'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVBANKTRAN)
        self.assertIsInstance(root.stmttrn, STMTTRN)
        self.assertEqual(root.subacctfund, 'MARGIN')

    def testOneOf(self):
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        stmttrn = Aggregate.from_etree(test_bank.StmttrnTestCase().root)
        self.assertEqual(root.trntype,  stmttrn.trntype)
        self.assertEqual(root.dtposted,  stmttrn.dtposted)
        self.assertEqual(root.trnamt,  stmttrn.trnamt)
        self.assertEqual(root.fitid,  stmttrn.fitid)
        self.assertEqual(root.memo,  stmttrn.memo)


class InvtranTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
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
        self.assertEqual(root.dttrade, datetime(2004, 7, 1, tzinfo=UTC))
        self.assertEqual(root.dtsettle, datetime(2004, 7, 4, tzinfo=UTC))
        self.assertEqual(root.reversalfitid, '3003')
        self.assertEqual(root.memo, 'Investment Transaction')
        return root


class InvbuyTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'UNITS', 'UNITPRICE', 'TOTAL',
                        'SUBACCTSEC', 'SUBACCTFUND')
    optionalElements = ('MARKUP', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                        'CURRENCY', 'LOANID', 'LOANPRINCIPAL', 'LOANINTEREST',
                        'INV401KSOURCE', 'DTPAYROLL', 'PRIORYEARCONTRIB')

    @property
    def root(self):
        root = Element('INVBUY')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'UNITPRICE').text = '1.50'
        SubElement(root, 'MARKUP').text = '0'
        SubElement(root, 'COMMISSION').text = '9.99'
        SubElement(root, 'TAXES').text = '0'
        SubElement(root, 'FEES').text = '1.50'
        SubElement(root, 'LOAD').text = '0'
        SubElement(root, 'TOTAL').text = '-161.49'
        currency = test_i18n.CurrencyTestCase().root
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

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.markup, Decimal('0'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('0'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.loanid, '1')
        self.assertEqual(root.loanprincipal, Decimal('1.50'))
        self.assertEqual(root.loaninterest, Decimal('3.50'))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        self.assertEqual(root.dtpayroll, datetime(2004, 6, 15, tzinfo=UTC))
        self.assertEqual(root.prioryearcontrib, True)
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)


class InvsellTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'UNITS', 'UNITPRICE', 'TOTAL',
                        'SUBACCTSEC', 'SUBACCTFUND')
    optionalElements = ('MARKDOWN', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                        'WITHHOLDING', 'TAXEXEMPT', 'GAIN', 'CURRENCY',
                        'LOANID', 'STATEWITHHOLDING', 'PENALTY',
                        'INV401KSOURCE',)

    @property
    def root(self):
        root = Element('INVSELL')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITS').text = '-100'
        SubElement(root, 'UNITPRICE').text = '1.50'
        SubElement(root, 'MARKDOWN').text = '0'
        SubElement(root, 'COMMISSION').text = '9.99'
        SubElement(root, 'TAXES').text = '2'
        SubElement(root, 'FEES').text = '1.50'
        SubElement(root, 'LOAD').text = '0'
        SubElement(root, 'WITHHOLDING').text = '3'
        SubElement(root, 'TAXEXEMPT').text = 'N'
        SubElement(root, 'TOTAL').text = '131.00'
        SubElement(root, 'GAIN').text = '3.47'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'LOANID').text = '1'
        SubElement(root, 'STATEWITHHOLDING').text = '2.50'
        SubElement(root, 'PENALTY').text = '0.01'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.units, Decimal('-100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.markdown, Decimal('0'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('2'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.withholding, Decimal('3'))
        self.assertEqual(root.taxexempt, False)
        self.assertEqual(root.total, Decimal('131'))
        self.assertEqual(root.gain, Decimal('3.47'))
        self.assertIsInstance(root.currency, CURRENCY)
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

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)


class BuydebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVBUY', )
    optionalElements = ('ACCRDINT', )

    @property
    def root(self):
        root = Element('BUYDEBT')
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, 'ACCRDINT').text = '25.50'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BUYDEBT)
        self.assertIsInstance(root.invbuy, INVBUY)
        self.assertEqual(root.accrdint, Decimal('25.50'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invbuy.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invbuy.secid.uniqueidtype)
        self.assertEqual(root.units, root.invbuy.units)
        self.assertEqual(root.unitprice, root.invbuy.unitprice)
        self.assertEqual(root.total, root.invbuy.total)
        self.assertEqual(root.curtype, root.invbuy.curtype)
        self.assertEqual(root.cursym, root.invbuy.cursym)
        self.assertEqual(root.currate, root.invbuy.currate)
        self.assertEqual(root.subacctsec, root.invbuy.subacctsec)
        self.assertEqual(root.fitid, root.invbuy.invtran.fitid)
        self.assertEqual(root.dttrade, root.invbuy.invtran.dttrade)
        self.assertEqual(root.memo, root.invbuy.invtran.memo)


class BuymfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVBUY', 'BUYTYPE', )
    optionalElements = ('RELFITID', )

    @property
    def root(self):
        root = Element('BUYMF')
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        SubElement(root, 'RELFITID').text = '1015'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BUYMF)
        self.assertIsInstance(root.invbuy, INVBUY)
        self.assertEqual(root.buytype, 'BUYTOCOVER')
        self.assertEqual(root.relfitid, '1015')

    def testOneOf(self):
        self.oneOfTest('BUYTYPE', BUYTYPES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invbuy.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invbuy.secid.uniqueidtype)
        self.assertEqual(root.units, root.invbuy.units)
        self.assertEqual(root.unitprice, root.invbuy.unitprice)
        self.assertEqual(root.total, root.invbuy.total)
        self.assertEqual(root.curtype, root.invbuy.curtype)
        self.assertEqual(root.cursym, root.invbuy.cursym)
        self.assertEqual(root.currate, root.invbuy.currate)
        self.assertEqual(root.subacctsec, root.invbuy.subacctsec)
        self.assertEqual(root.fitid, root.invbuy.invtran.fitid)
        self.assertEqual(root.dttrade, root.invbuy.invtran.dttrade)
        self.assertEqual(root.memo, root.invbuy.invtran.memo)


class BuyoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVBUY', 'OPTBUYTYPE', 'SHPERCTRCT', )

    @property
    def root(self):
        root = Element('BUYOPT')
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        SubElement(root, 'OPTBUYTYPE').text = 'BUYTOCLOSE'
        SubElement(root, 'SHPERCTRCT').text = '100'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BUYOPT)
        self.assertIsInstance(root.invbuy, INVBUY)
        self.assertEqual(root.optbuytype, 'BUYTOCLOSE')
        self.assertEqual(root.shperctrct, 100)

    def testOneOf(self):
        self.oneOfTest('OPTBUYTYPE', ('BUYTOOPEN', 'BUYTOCLOSE',))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invbuy.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invbuy.secid.uniqueidtype)
        self.assertEqual(root.units, root.invbuy.units)
        self.assertEqual(root.unitprice, root.invbuy.unitprice)
        self.assertEqual(root.total, root.invbuy.total)
        self.assertEqual(root.curtype, root.invbuy.curtype)
        self.assertEqual(root.cursym, root.invbuy.cursym)
        self.assertEqual(root.currate, root.invbuy.currate)
        self.assertEqual(root.subacctsec, root.invbuy.subacctsec)
        self.assertEqual(root.fitid, root.invbuy.invtran.fitid)
        self.assertEqual(root.dttrade, root.invbuy.invtran.dttrade)
        self.assertEqual(root.memo, root.invbuy.invtran.memo)


class BuyotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVBUY', )

    @property
    def root(self):
        root = Element('BUYOTHER')
        invbuy = InvbuyTestCase().root
        root.append(invbuy)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BUYOTHER)
        self.assertIsInstance(root.invbuy, INVBUY)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invbuy.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invbuy.secid.uniqueidtype)
        self.assertEqual(root.units, root.invbuy.units)
        self.assertEqual(root.unitprice, root.invbuy.unitprice)
        self.assertEqual(root.total, root.invbuy.total)
        self.assertEqual(root.curtype, root.invbuy.curtype)
        self.assertEqual(root.cursym, root.invbuy.cursym)
        self.assertEqual(root.currate, root.invbuy.currate)
        self.assertEqual(root.subacctsec, root.invbuy.subacctsec)
        self.assertEqual(root.fitid, root.invbuy.invtran.fitid)
        self.assertEqual(root.dttrade, root.invbuy.invtran.dttrade)
        self.assertEqual(root.memo, root.invbuy.invtran.memo)


class BuystockTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVBUY', 'BUYTYPE', )

    @property
    def root(self):
        root = Element('BUYSTOCK')
        invbuy = InvbuyTestCase().root
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        root.append(invbuy)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BUYSTOCK)
        self.assertIsInstance(root.invbuy, INVBUY)
        self.assertEqual(root.buytype, 'BUYTOCOVER')

    def testOneOf(self):
        self.oneOfTest('BUYTYPE', BUYTYPES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invbuy.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invbuy.secid.uniqueidtype)
        self.assertEqual(root.units, root.invbuy.units)
        self.assertEqual(root.unitprice, root.invbuy.unitprice)
        self.assertEqual(root.total, root.invbuy.total)
        self.assertEqual(root.curtype, root.invbuy.curtype)
        self.assertEqual(root.cursym, root.invbuy.cursym)
        self.assertEqual(root.currate, root.invbuy.currate)
        self.assertEqual(root.subacctsec, root.invbuy.subacctsec)
        self.assertEqual(root.fitid, root.invbuy.invtran.fitid)
        self.assertEqual(root.dttrade, root.invbuy.invtran.dttrade)
        self.assertEqual(root.memo, root.invbuy.invtran.memo)


class ClosureoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'OPTACTION', 'UNITS', 'SHPERCTRCT',
                        'SUBACCTSEC', )
    optionalElements = ('RELFITID', 'GAIN', )

    @property
    def root(self):
        root = Element('CLOSUREOPT')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'OPTACTION').text = 'EXERCISE'
        SubElement(root, 'UNITS').text = '200'
        SubElement(root, 'SHPERCTRCT').text = '100'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'RELFITID').text = '1001'
        SubElement(root, 'GAIN').text = '123.45'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CLOSUREOPT)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.optaction, 'EXERCISE')
        self.assertEqual(root.units, Decimal('200'))
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.relfitid, '1001')
        self.assertEqual(root.gain, Decimal('123.45'))
        return root

    def testOneOf(self):
        self.oneOfTest('OPTACTION', ('EXERCISE', 'ASSIGN', 'EXPIRE'))
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)


class IncomeTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'INCOMETYPE', 'TOTAL',
                        'SUBACCTSEC', 'SUBACCTFUND', )
    optionalElements = ('TAXEXEMPT', 'WITHHOLDING', 'CURRENCY',
                        'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('INCOME')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'INCOMETYPE').text = 'CGLONG'
        SubElement(root, 'TOTAL').text = '1500'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'TAXEXEMPT').text = 'Y'
        SubElement(root, 'WITHHOLDING').text = '123.45'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INCOME)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.incometype, 'CGLONG')
        self.assertEqual(root.total, Decimal('1500'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.taxexempt, True)
        self.assertEqual(root.withholding, Decimal('123.45'))
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('INCOMETYPE', INCOMETYPES)
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class InvexpenseTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'TOTAL', 'SUBACCTSEC',
                        'SUBACCTFUND', )
    optionalElements = ('CURRENCY', 'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('INVEXPENSE')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'TOTAL').text = '-161.49'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVEXPENSE)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class JrnlfundTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SUBACCTTO', 'SUBACCTFROM', 'TOTAL', )

    @property
    def root(self):
        root = Element('JRNLFUND')
        invtran = InvtranTestCase().root
        root.append(invtran)
        SubElement(root, 'SUBACCTTO').text = 'MARGIN'
        SubElement(root, 'SUBACCTFROM').text = 'CASH'
        SubElement(root, 'TOTAL').text = '161.49'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, JRNLFUND)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertEqual(root.subacctto, 'MARGIN')
        self.assertEqual(root.subacctfrom, 'CASH')
        self.assertEqual(root.total, Decimal('161.49'))

    def testOneOf(self):
        self.oneOfTest('SUBACCTTO', INVSUBACCTS)
        self.oneOfTest('SUBACCTFROM', INVSUBACCTS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)


class JrnlsecTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'SUBACCTTO', 'SUBACCTFROM',
                        'UNITS', )

    @property
    def root(self):
        root = Element('JRNLSEC')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTTO').text = 'MARGIN'
        SubElement(root, 'SUBACCTFROM').text = 'CASH'
        SubElement(root, 'UNITS').text = '1600'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, JRNLSEC)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.subacctto, 'MARGIN')
        self.assertEqual(root.subacctfrom, 'CASH')
        self.assertEqual(root.units, Decimal('1600'))

    def testOneOf(self):
        self.oneOfTest('SUBACCTTO', INVSUBACCTS)
        self.oneOfTest('SUBACCTFROM', INVSUBACCTS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)


class MargininterestTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'TOTAL', 'SUBACCTFUND', )
    optionalElements = ('CURRENCY', )

    @property
    def root(self):
        root = Element('MARGININTEREST')
        invtran = InvtranTestCase().root
        root.append(invtran)
        SubElement(root, 'TOTAL').text = '161.49'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MARGININTEREST)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertEqual(root.total, Decimal('161.49'))
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertIsInstance(root.currency, CURRENCY)
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class ReinvestTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'INCOMETYPE', 'TOTAL',
                        'SUBACCTSEC', 'UNITS', 'UNITPRICE', )
    optionalElements = ('COMMISSION',  'TAXES', 'FEES', 'LOAD', 'TAXEXEMPT',
                        'CURRENCY', 'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('REINVEST')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'TOTAL').text = '-161.49'
        SubElement(root, 'INCOMETYPE').text = 'CGLONG'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'UNITPRICE').text = '1.50'
        SubElement(root, 'COMMISSION').text = '9.99'
        SubElement(root, 'TAXES').text = '0'
        SubElement(root, 'FEES').text = '1.50'
        SubElement(root, 'LOAD').text = '0'
        SubElement(root, 'TAXEXEMPT').text = 'Y'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, REINVEST)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.incometype, 'CGLONG')
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('0'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.taxexempt, True)
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('INCOMETYPE', INCOMETYPES)
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class RetofcapTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN', 'SECID', 'TOTAL', 'SUBACCTSEC',
                        'SUBACCTFUND', )
    optionalElements = ('CURRENCY', 'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('RETOFCAP')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'TOTAL').text = '-161.49'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, RETOFCAP)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class SelldebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVSELL', 'SELLREASON', )
    optionalElements = ('ACCRDINT', )

    @property
    def root(self):
        root = Element('SELLDEBT')
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, 'SELLREASON').text = 'MATURITY'
        SubElement(root, 'ACCRDINT').text = '25.50'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SELLDEBT)
        self.assertIsInstance(root.invsell, INVSELL)
        self.assertEqual(root.sellreason, 'MATURITY')
        self.assertEqual(root.accrdint, Decimal('25.50'))

    def testOneOf(self):
        self.oneOfTest('SELLREASON', ('CALL', 'SELL', 'MATURITY'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invsell.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invsell.secid.uniqueidtype)
        self.assertEqual(root.units, root.invsell.units)
        self.assertEqual(root.unitprice, root.invsell.unitprice)
        self.assertEqual(root.total, root.invsell.total)
        self.assertEqual(root.curtype, root.invsell.curtype)
        self.assertEqual(root.cursym, root.invsell.cursym)
        self.assertEqual(root.currate, root.invsell.currate)
        self.assertEqual(root.subacctsec, root.invsell.subacctsec)
        self.assertEqual(root.fitid, root.invsell.invtran.fitid)
        self.assertEqual(root.dttrade, root.invsell.invtran.dttrade)
        self.assertEqual(root.memo, root.invsell.invtran.memo)


class SellmfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVSELL', 'SELLTYPE', )
    optionalElements = ('AVGCOSTBASIS', 'RELFITID',)

    @property
    def root(self):
        root = Element('SELLMF')
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        SubElement(root, 'AVGCOSTBASIS').text = '2.50'
        SubElement(root, 'RELFITID').text = '1015'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SELLMF)
        self.assertIsInstance(root.invsell, INVSELL)
        self.assertEqual(root.selltype, 'SELLSHORT')
        self.assertEqual(root.relfitid, '1015')

    def testOneOf(self):
        self.oneOfTest('SELLTYPE', SELLTYPES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invsell.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invsell.secid.uniqueidtype)
        self.assertEqual(root.units, root.invsell.units)
        self.assertEqual(root.unitprice, root.invsell.unitprice)
        self.assertEqual(root.total, root.invsell.total)
        self.assertEqual(root.curtype, root.invsell.curtype)
        self.assertEqual(root.cursym, root.invsell.cursym)
        self.assertEqual(root.currate, root.invsell.currate)
        self.assertEqual(root.subacctsec, root.invsell.subacctsec)
        self.assertEqual(root.fitid, root.invsell.invtran.fitid)
        self.assertEqual(root.dttrade, root.invsell.invtran.dttrade)
        self.assertEqual(root.memo, root.invsell.invtran.memo)


class SelloptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVSELL', 'OPTSELLTYPE', 'SHPERCTRCT',)
    optionalElements = ('RELFITID', 'RELTYPE', 'SECURED', )

    @property
    def root(self):
        root = Element('SELLOPT')
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, 'OPTSELLTYPE').text = 'SELLTOCLOSE'
        SubElement(root, 'SHPERCTRCT').text = '100'
        SubElement(root, 'RELFITID').text = '1001'
        SubElement(root, 'RELTYPE').text = 'STRADDLE'
        SubElement(root, 'SECURED').text = 'NAKED'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SELLOPT)
        self.assertIsInstance(root.invsell, INVSELL)
        self.assertEqual(root.optselltype, 'SELLTOCLOSE')
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.relfitid, '1001')
        self.assertEqual(root.reltype, 'STRADDLE')
        self.assertEqual(root.secured, 'NAKED')

    def testOneOf(self):
        self.oneOfTest('OPTSELLTYPE', ('SELLTOCLOSE', 'SELLTOOPEN',))
        self.oneOfTest('RELTYPE', ('SPREAD', 'STRADDLE', 'NONE', 'OTHER'))
        self.oneOfTest('SECURED', ('NAKED', 'COVERED'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invsell.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invsell.secid.uniqueidtype)
        self.assertEqual(root.units, root.invsell.units)
        self.assertEqual(root.unitprice, root.invsell.unitprice)
        self.assertEqual(root.total, root.invsell.total)
        self.assertEqual(root.curtype, root.invsell.curtype)
        self.assertEqual(root.cursym, root.invsell.cursym)
        self.assertEqual(root.currate, root.invsell.currate)
        self.assertEqual(root.subacctsec, root.invsell.subacctsec)
        self.assertEqual(root.fitid, root.invsell.invtran.fitid)
        self.assertEqual(root.dttrade, root.invsell.invtran.dttrade)
        self.assertEqual(root.memo, root.invsell.invtran.memo)


class SellotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVSELL', )

    @property
    def root(self):
        root = Element('SELLOTHER')
        invsell = InvsellTestCase().root
        root.append(invsell)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SELLOTHER)
        self.assertIsInstance(root.invsell, INVSELL)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invsell.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invsell.secid.uniqueidtype)
        self.assertEqual(root.units, root.invsell.units)
        self.assertEqual(root.unitprice, root.invsell.unitprice)
        self.assertEqual(root.total, root.invsell.total)
        self.assertEqual(root.curtype, root.invsell.curtype)
        self.assertEqual(root.cursym, root.invsell.cursym)
        self.assertEqual(root.currate, root.invsell.currate)
        self.assertEqual(root.subacctsec, root.invsell.subacctsec)
        self.assertEqual(root.fitid, root.invsell.invtran.fitid)
        self.assertEqual(root.dttrade, root.invsell.invtran.dttrade)
        self.assertEqual(root.memo, root.invsell.invtran.memo)


class SellstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVSELL',  'SELLTYPE', )

    @property
    def root(self):
        root = Element('SELLSTOCK')
        invsell = InvsellTestCase().root
        root.append(invsell)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SELLSTOCK)
        self.assertIsInstance(root.invsell, INVSELL)
        self.assertEqual(root.selltype, 'SELLSHORT')

    def testOneOf(self):
        self.oneOfTest('SELLTYPE', SELLTYPES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invsell.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invsell.secid.uniqueidtype)
        self.assertEqual(root.units, root.invsell.units)
        self.assertEqual(root.unitprice, root.invsell.unitprice)
        self.assertEqual(root.total, root.invsell.total)
        self.assertEqual(root.curtype, root.invsell.curtype)
        self.assertEqual(root.cursym, root.invsell.cursym)
        self.assertEqual(root.currate, root.invsell.currate)
        self.assertEqual(root.subacctsec, root.invsell.subacctsec)
        self.assertEqual(root.fitid, root.invsell.invtran.fitid)
        self.assertEqual(root.dttrade, root.invsell.invtran.dttrade)
        self.assertEqual(root.memo, root.invsell.invtran.memo)


class SplitTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN',  'SECID',  'SUBACCTSEC', 'OLDUNITS',
                        'NEWUNITS', 'NUMERATOR', 'DENOMINATOR', )
    optionalElements = ('CURRENCY', 'FRACCASH', 'SUBACCTFUND',
                        'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('SPLIT')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'OLDUNITS').text = '200'
        SubElement(root, 'NEWUNITS').text = '100'
        SubElement(root, 'NUMERATOR').text = '1'
        SubElement(root, 'DENOMINATOR').text = '2'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'FRACCASH').text = '0.50'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SPLIT)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.oldunits, Decimal('200'))
        self.assertEqual(root.newunits, Decimal('100'))
        self.assertEqual(root.numerator, Decimal('1'))
        self.assertEqual(root.denominator, Decimal('2'))
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.fraccash, Decimal('0.50'))
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)
        self.assertEqual(root.curtype, 'CURRENCY')
        self.assertEqual(root.cursym, root.currency.cursym)
        self.assertEqual(root.currate, root.currency.currate)


class TransferTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVTRAN',  'SECID',  'SUBACCTSEC', 'UNITS',
                        'TFERACTION', 'POSTYPE', )
    optionalElements = ('INVACCTFROM', 'AVGCOSTBASIS', 'UNITPRICE',
                        'DTPURCHASE', 'INV401KSOURCE', )

    @property
    def root(self):
        root = Element('TRANSFER')
        invtran = InvtranTestCase().root
        root.append(invtran)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'TFERACTION').text = 'OUT'
        SubElement(root, 'POSTYPE').text = 'LONG'
        invacctfrom = InvacctfromTestCase().root
        root.append(invacctfrom)
        SubElement(root, 'AVGCOSTBASIS').text = '22.22'
        SubElement(root, 'UNITPRICE').text = '23.01'
        SubElement(root, 'DTPURCHASE').text = '19991231'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, TRANSFER)
        self.assertIsInstance(root.invtran, INVTRAN)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.tferaction, 'OUT')
        self.assertEqual(root.postype, 'LONG')
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)
        self.assertEqual(root.avgcostbasis, Decimal('22.22'))
        self.assertEqual(root.unitprice, Decimal('23.01'))
        self.assertEqual(root.dtpurchase, datetime(1999, 12, 31, tzinfo=UTC))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('TFERACTION', ('IN', 'OUT'))
        self.oneOfTest('POSTYPE', ('LONG', 'SHORT'))
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, root.invtran.fitid)
        self.assertEqual(root.dttrade, root.invtran.dttrade)
        self.assertEqual(root.memo, root.invtran.memo)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)


class Inv401kbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('TOTAL',)
    optionalElements = ('CASHBAL', 'PRETAX', 'AFTERTAX', 'MATCH',
                        'PROFITSHARING', 'ROLLOVER', 'OTHERVEST',
                        'OTHERNONVEST',)

    @property
    def root(self):
        root = Element('INV401KBAL')
        SubElement(root, 'CASHBAL').text = '1'
        SubElement(root, 'PRETAX').text = '2'
        SubElement(root, 'AFTERTAX').text = '3'
        SubElement(root, 'MATCH').text = '4'
        SubElement(root, 'PROFITSHARING').text = '5'
        SubElement(root, 'ROLLOVER').text = '6'
        SubElement(root, 'OTHERVEST').text = '7'
        SubElement(root, 'OTHERNONVEST').text = '8'
        SubElement(root, 'TOTAL').text = '36'
        ballist = test_bank.BallistTestCase().root
        root.append(ballist)
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INV401KBAL)
        self.assertEqual(root.cashbal, Decimal('1'))
        self.assertEqual(root.pretax, Decimal('2'))
        self.assertEqual(root.aftertax, Decimal('3'))
        self.assertEqual(root.match, Decimal('4'))
        self.assertEqual(root.profitsharing, Decimal('5'))
        self.assertEqual(root.rollover, Decimal('6'))
        self.assertEqual(root.othervest, Decimal('7'))
        self.assertEqual(root.othernonvest, Decimal('8'))
        self.assertEqual(root.total, Decimal('36'))
        self.assertIsInstance(root.ballist, BALLIST)


class InvposTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = False
    requiredElements = ('SECID', 'HELDINACCT', 'POSTYPE', 'UNITS', 'UNITPRICE',
                        'MKTVAL', 'DTPRICEASOF')
    optionalElements = ('AVGCOSTBASIS', 'CURRENCY', 'MEMO', 'INV401KSOURCE')

    @property
    def root(self):
        root = Element('INVPOS')
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'HELDINACCT').text = 'MARGIN'
        SubElement(root, 'POSTYPE').text = 'LONG'
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'UNITPRICE').text = '90'
        SubElement(root, 'MKTVAL').text = '9000'
        SubElement(root, 'AVGCOSTBASIS').text = '85'
        SubElement(root, 'DTPRICEASOF').text = '20130630'
        currency = test_i18n.CurrencyTestCase().root
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


class PosdebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVPOS', )

    @property
    def root(self):
        root = Element('POSDEBT')
        invpos = InvposTestCase().root
        root.append(invpos)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, POSDEBT)
        self.assertIsInstance(root.invpos, INVPOS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class PosmfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVPOS', )
    optionalElements = ('UNITSSTREET', 'UNITSUSER', 'REINVDIV', 'REINVCG', )

    @property
    def root(self):
        root = Element('POSMF')
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, 'UNITSSTREET').text = '200'
        SubElement(root, 'UNITSUSER').text = '300'
        SubElement(root, 'REINVDIV').text = 'N'
        SubElement(root, 'REINVCG').text = 'Y'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, POSMF)
        self.assertIsInstance(root.invpos, INVPOS)
        self.assertEqual(root.unitsstreet, Decimal('200'))
        self.assertEqual(root.unitsuser, Decimal('300'))
        self.assertEqual(root.reinvdiv, False)
        self.assertEqual(root.reinvcg, True)

    def testOneOf(self):
        self.oneOfTest('REINVDIV', ('Y', 'N'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class PosoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVPOS', )
    optionalElements = ('SECURED', )

    @property
    def root(self):
        root = Element('POSOPT')
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, 'SECURED').text = 'COVERED'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, POSOPT)
        self.assertIsInstance(root.invpos, INVPOS)
        self.assertEqual(root.secured, 'COVERED')

    def testOneOf(self):
        self.oneOfTest('SECURED', ('NAKED', 'COVERED'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class PosotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVPOS', )

    @property
    def root(self):
        root = Element('POSOTHER')
        invpos = InvposTestCase().root
        root.append(invpos)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, POSOTHER)
        self.assertIsInstance(root.invpos, INVPOS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class PosstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('INVPOS', )
    optionalElements = ('UNITSSTREET', 'UNITSUSER', 'REINVDIV', )

    @property
    def root(self):
        root = Element('POSSTOCK')
        invpos = InvposTestCase().root
        root.append(invpos)
        SubElement(root, 'UNITSSTREET').text = '200'
        SubElement(root, 'UNITSUSER').text = '300'
        SubElement(root, 'REINVDIV').text = 'N'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, POSSTOCK)
        self.assertIsInstance(root.invpos, INVPOS)
        self.assertEqual(root.unitsstreet, Decimal('200'))
        self.assertEqual(root.unitsuser, Decimal('300'))
        self.assertEqual(root.reinvdiv, False)

    def testOneOf(self):
        self.oneOfTest('REINVDIV', ('Y', 'N'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class OoTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    requiredElements = ('FITID', 'SECID', 'DTPLACED', 'UNITS', 'SUBACCT',
                        'DURATION', 'RESTRICTION',)
    optionalElements = ('SRVRTID', 'MINUNITS', 'LIMITPRICE', 'STOPPRICE',
                        'MEMO', 'CURRENCY', 'INV401KSOURCE',)

    @property
    def root(self):
        root = Element('OO')
        SubElement(root, 'FITID').text = '1001'
        SubElement(root, 'SRVRTID').text = '2002'
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'DTPLACED').text = '20040701'
        SubElement(root, 'UNITS').text = '150'
        SubElement(root, 'SUBACCT').text = 'CASH'
        SubElement(root, 'DURATION').text = 'GOODTILCANCEL'
        SubElement(root, 'RESTRICTION').text = 'ALLORNONE'
        SubElement(root, 'MINUNITS').text = '100'
        SubElement(root, 'LIMITPRICE').text = '10.50'
        SubElement(root, 'STOPPRICE').text = '10.00'
        SubElement(root, 'MEMO').text = 'Open Order'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, '1001')
        self.assertEqual(root.srvrtid, '2002')
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.dtplaced, datetime(2004, 7, 1))
        self.assertEqual(root.units, Decimal('150'))
        self.assertEqual(root.subacct, 'CASH')
        self.assertEqual(root.duration, 'GOODTILCANCEL')
        self.assertEqual(root.restriction, 'ALLORNONE')
        self.assertEqual(root.minunits, Decimal('100'))
        self.assertEqual(root.limitprice, Decimal('10.50'))
        self.assertEqual(root.stopprice, Decimal('10.00'))
        self.assertEqual(root.memo, 'Open Order')
        self.assertIsInstance(root.currency, CURRENCY)
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCT', INVSUBACCTS)
        self.oneOfTest('DURATION', ('DAY', 'GOODTILCANCEL', 'IMMEDIATE'))
        self.oneOfTest('RESTRICTION', ('ALLORNONE', 'MINUNITS', 'NONE'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.invpos.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.invpos.secid.uniqueidtype)
        self.assertEqual(root.heldinacct, root.invpos.heldinacct)
        self.assertEqual(root.postype, root.invpos.postype)
        self.assertEqual(root.units, root.invpos.units)
        self.assertEqual(root.unitprice, root.invpos.unitprice)
        self.assertEqual(root.mktval, root.invpos.mktval)
        self.assertEqual(root.dtpriceasof, root.invpos.dtpriceasof)
        self.assertEqual(root.cursym, root.invpos.currency.cursym)
        self.assertEqual(root.currate, root.invpos.currency.currate)


class OobuydebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'AUCTION', )
    optionalElements = ('DTAUCTION', )

    @property
    def root(self):
        root = Element('OOBUYDEBT')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'AUCTION').text = 'N'
        SubElement(root, 'DTAUCTION').text = '20120109'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.auction, False)
        self.assertEqual(root.dtauction, datetime(2012, 1, 9, tzinfo=UTC))


class OobuymfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'BUYTYPE', 'UNITTYPE', )

    @property
    def root(self):
        root = Element('OOBUYMF')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'BUYTYPE').text = 'BUY'
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.buytype, 'BUY')
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        self.oneOfTest('BUYTYPE', BUYTYPES)
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OobuyoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'OPTBUYTYPE', )

    @property
    def root(self):
        root = Element('OOBUYOPT')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'OPTBUYTYPE').text = 'BUYTOOPEN'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.optbuytype, 'BUYTOOPEN')

    def testOneOf(self):
        self.oneOfTest('OPTBUYTYPE', OPTBUYTYPES)


class OobuyotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'UNITTYPE', )

    @property
    def root(self):
        root = Element('OOBUYOTHER')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OobuystockTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'BUYTYPE', )

    @property
    def root(self):
        root = Element('OOBUYSTOCK')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.buytype, 'BUYTOCOVER')

    def testOneOf(self):
        self.oneOfTest('BUYTYPE', BUYTYPES)


class OoselldebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('OOSELLDEBT')
        oo = OoTestCase().root
        root.append(oo)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)


class OosellmfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'SELLTYPE', 'UNITTYPE', 'SELLALL', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('OOSELLMF')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        SubElement(root, 'SELLALL').text = 'Y'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.selltype, 'SELLSHORT')
        self.assertEqual(root.unittype, 'SHARES')
        self.assertEqual(root.sellall, True)

    def testOneOf(self):
        self.oneOfTest('SELLTYPE', SELLTYPES)
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OoselloptTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'OPTSELLTYPE', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('OOSELLOPT')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'OPTSELLTYPE').text = 'SELLTOCLOSE'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.optselltype, 'SELLTOCLOSE')

    def testOneOf(self):
        self.oneOfTest('OPTSELLTYPE', OPTSELLTYPES)


class OosellotherTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'UNITTYPE', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('OOSELLOTHER')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OosellstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'SELLTYPE', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('OOSELLSTOCK')
        oo = OoTestCase().root
        root.append(oo)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertEqual(root.selltype, 'SELLSHORT')

    def testOneOf(self):
        self.oneOfTest('SELLTYPE', SELLTYPES)


class SwitchmfTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    requiredElements = ('OO', 'SECID', 'UNITTYPE', 'SWITCHALL', )
    optionalElements = ()

    @property
    def root(self):
        root = Element('SWITCHMF')
        oo = OoTestCase().root
        root.append(oo)
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        SubElement(root, 'SWITCHALL').text = 'Y'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root.oo, OO)
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.unittype, 'SHARES')
        self.assertEqual(root.switchall, True)

    def testOneOf(self):
        self.oneOfTest('UNITTYPE', UNITTYPES)


class InvstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('DTASOF', 'CURDEF', 'INVACCTFROM',)
    optionalElements = ('INVTRANLIST', 'INVPOSLIST', 'INVBAL',
                        # FIXME - INVOOLIST
                        'INVOOLIST', 'MKTGINFO', 'INV401KBAL',)
                        # 'MKTGINFO', 'INV401KBAL',)
    unsupported = ('INV401K', )

    @property
    def root(self):
        root = Element('INVSTMTRS')
        SubElement(root, 'DTASOF').text = '20010530'
        SubElement(root, 'CURDEF').text = 'USD'
        acctfrom = InvacctfromTestCase().root
        root.append(acctfrom)
        tranlist = InvtranlistTestCase().root
        root.append(tranlist)
        poslist = InvposlistTestCase().root
        root.append(poslist)
        invbal = InvbalTestCase().root
        root.append(invbal)
        # FIXME - INVOOLIST
        invoolist = InvoolistTestCase().root
        root.append(invoolist)
        SubElement(root, 'MKTGINFO').text = 'Get Free Stuff NOW!!'
        # FIXME - INV401K
        inv401kbal = Inv401kbalTestCase().root
        root.append(inv401kbal)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTRS)
        self.assertEqual(root.dtasof, datetime(2001, 5, 30, tzinfo=UTC))
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.invacctfrom, INVACCTFROM)
        self.assertIsInstance(root.invtranlist, INVTRANLIST)
        self.assertIsInstance(root.invposlist, INVPOSLIST)
        self.assertIsInstance(root.invbal, INVBAL)
        self.assertIsInstance(root.invoolist, INVOOLIST)
        self.assertEqual(root.mktginfo, 'Get Free Stuff NOW!!')
        self.assertIsInstance(root.inv401kbal, INV401KBAL)

    def testUnsupported(self):
        root = self.root
        for tag in self.unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.account, root.invacctfrom)
        self.assertIs(root.balances, root.invbal)
        self.assertIs(root.transactions, root.invtranlist)
        self.assertIs(root.positions, root.invposlist)


class InvstmttrnrsTestCase(unittest.TestCase, base.TestAggregate):
    """
    """
    __test__ = True
    requiredElements = ('TRNUID', 'STATUS', )
    optionalElements = ('CLIENTCOOKIE', 'OFXEXTENSION', 'INVSTMTRS', )

    @property
    def root(self):
        root = Element('INVSTMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_common.StatusTestCase().root
        root.append(status)
        SubElement(root, 'CLIENTCOOKIE').text = 'DEADBEEF'
        ofxextension = test_models_common.OfxextensionTestCase().root
        root.append(ofxextension)
        stmtrs = InvstmtrsTestCase().root
        root.append(stmtrs)

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.clientcookie, 'DEADBEEF')
        self.assertIsInstance(root.ofxextension, OFXEXTENSION)
        self.assertIsInstance(root.invstmtrs, INVSTMTRS)

    def testUnsupported(self):
        root = self.root
        for tag in INVSTMTTRNRS.unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.statement, root.invstmtrs)


class Invstmtmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('INVSTMTMSGSRSV1')
        for i in range(2):
            stmttrnrs = InvstmttrnrsTestCase().root
            root.append(stmttrnrs)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTMSGSRSV1)
        self.assertEqual(len(root), 2)
        for stmttrnrs in root:
            self.assertIsInstance(stmttrnrs, INVSTMTTRNRS)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.statements[0], root[0].invstmtrs)


class Invstmtmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ['MSGSETCORE', 'TRANDNLD', 'OODNLD', 'POSDNLD',
                        'BALDNLD', 'CANEMAIL', ]
    # optionalElements = ['INV401KDNLD', 'CLOSINGAVAIL', ]

    @property
    def root(self):
        root = Element('INVSTMTMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, 'TRANDNLD').text = 'Y'
        SubElement(root, 'OODNLD').text = 'Y'
        SubElement(root, 'POSDNLD').text = 'Y'
        SubElement(root, 'BALDNLD').text = 'Y'
        SubElement(root, 'CANEMAIL').text = 'N'
        # SubElement(root, 'INV401KDNLD').text = 'N'
        # SubElement(root, 'CLOSINGAVAIL').text = 'Y'

        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.trandnld, True)
        self.assertEqual(root.oodnld, True)
        self.assertEqual(root.posdnld, True)
        self.assertEqual(root.baldnld, True)
        self.assertEqual(root.canemail, False)
        # self.assertEqual(root.inv401kdnld, False)
        # self.assertEqual(root.closingavail, True)


class InvstmtmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('INVSTMTMSGSET')
        invstmtmsgsetv1 = Invstmtmsgsetv1TestCase().root
        root.append(invstmtmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVSTMTMSGSET)
        self.assertIsInstance(root.invstmtmsgsetv1, INVSTMTMSGSETV1)
