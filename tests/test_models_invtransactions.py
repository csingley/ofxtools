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
    BUYDEBT, BUYMF, BUYOPT, BUYOTHER, BUYSTOCK,
    INVBANKTRAN,
    SELLDEBT, SELLMF, SELLOPT, SELLOTHER, SELLSTOCK,
    INVSUBACCTS, INV401KSOURCES, BUYTYPES, SELLTYPES,
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
        self.assertIsInstance(root, INVBANKTRAN)
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
        req += ('SECID', 'DTTRADE', 'UNITS', 'UNITPRICE', 'TOTAL',
                'SUBACCTSEC', 'SUBACCTFUND')
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
        SubElement(root, 'MARKDOWN').text = '0'
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
        req += ('SECID', 'DTTRADE', 'UNITS', 'UNITPRICE', 'TOTAL',
                'SUBACCTSEC', 'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        opt = super(InvsellTestCase, self).optionalElements
        opt += ('MARKDOWN', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                'WITHHOLDING', 'TAXEXEMPT', 'GAIN', 'CURRENCY', 'LOANID',
                'STATEWITHHOLDING', 'PENALTY', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(InvsellTestCase, self).testConvert()
        test_models_base.SecidTestCase().root
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

    @property
    def root(self):
        root = Element('BUYDEBT')
        invbuy = super(BuydebtTestCase, self).root
        root.append(invbuy)
        SubElement(root, 'ACCRDINT').text = '25.50'
        return root

    @property
    def optionalElements(self):
        opt = super(BuydebtTestCase, self).optionalElements
        opt += ('ACCRDINT',)
        return opt

    def testConvert(self):
        root = super(BuydebtTestCase, self).testConvert()
        self.assertIsInstance(root, BUYDEBT)
        self.assertEqual(root.accrdint, Decimal('25.50'))


class BuymfTestCase(InvbuyTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('BUYMF')
        invbuy = super(BuymfTestCase, self).root
        root.append(invbuy)
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        SubElement(root, 'RELFITID').text = '1015'
        return root

    @property
    def requiredElements(self):
        req = super(BuymfTestCase, self).requiredElements
        req += ('BUYTYPE',)
        return req

    @property
    def optionalElements(self):
        opt = super(BuymfTestCase, self).optionalElements
        opt += ('RELFITID',)
        return opt 

    def testConvert(self):
        root = super(BuymfTestCase, self).testConvert()
        self.assertIsInstance(root, BUYMF)
        self.assertEqual(root.buytype, 'BUYTOCOVER')
        self.assertEqual(root.relfitid, '1015')

    def testOneOf(self):
        super(BuymfTestCase, self).testOneOf()
        self.oneOfTest('BUYTYPE', BUYTYPES)


class BuyoptTestCase(InvbuyTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('BUYOPT')
        invbuy = super(BuyoptTestCase, self).root
        root.append(invbuy)
        SubElement(root, 'OPTBUYTYPE').text = 'BUYTOCLOSE'
        SubElement(root, 'SHPERCTRCT').text = '100'
        return root

    @property
    def requiredElements(self):
        req = super(BuyoptTestCase, self).requiredElements
        req += ('OPTBUYTYPE', 'SHPERCTRCT',)
        return req

    def testConvert(self):
        root = super(BuyoptTestCase, self).testConvert()
        self.assertIsInstance(root, BUYOPT)
        self.assertEqual(root.optbuytype, 'BUYTOCLOSE')
        self.assertEqual(root.shperctrct, 100)

    def testOneOf(self):
        super(BuyoptTestCase, self).testOneOf()
        self.oneOfTest('OPTBUYTYPE', ('BUYTOOPEN', 'BUYTOCLOSE',))


class BuyotherTestCase(InvbuyTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('BUYOTHER')
        invbuy = super(BuyotherTestCase, self).root
        root.append(invbuy)
        return root

    def testConvert(self):
        root = super(BuyotherTestCase, self).testConvert()
        self.assertIsInstance(root, BUYOTHER)


class BuystockTestCase(InvbuyTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('BUYSTOCK')
        invbuy = super(BuystockTestCase, self).root
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        root.append(invbuy)
        return root

    def testConvert(self):
        root = super(BuystockTestCase, self).testConvert()
        self.assertIsInstance(root, BUYSTOCK)
        self.assertEqual(root.buytype, 'BUYTOCOVER')

    def testOneOf(self):
        super(BuystockTestCase, self).testOneOf()
        self.oneOfTest('BUYTYPE', BUYTYPES)


class SelldebtTestCase(InvsellTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SELLDEBT')
        invsell = super(SelldebtTestCase, self).root
        root.append(invsell)
        SubElement(root, 'SELLREASON').text = 'MATURITY'
        SubElement(root, 'ACCRDINT').text = '25.50'
        return root

    @property
    def requiredElements(self):
        req = super(SelldebtTestCase, self).requiredElements
        req += ('SELLREASON',)
        return req

    @property
    def optionalElements(self):
        opt = super(SelldebtTestCase, self).optionalElements
        opt += ('ACCRDINT',)
        return opt

    def testConvert(self):
        root = super(SelldebtTestCase, self).testConvert()
        self.assertIsInstance(root, SELLDEBT)
        self.assertEqual(root.sellreason, 'MATURITY')
        self.assertEqual(root.accrdint, Decimal('25.50'))

    def testOneOf(self):
        super(SelldebtTestCase, self).testOneOf()
        self.oneOfTest('SELLREASON', ('CALL', 'SELL', 'MATURITY'))


class SellmfTestCase(InvsellTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SELLMF')
        invsell = super(SellmfTestCase, self).root
        root.append(invsell)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        SubElement(root, 'AVGCOSTBASIS').text = '2.50'
        SubElement(root, 'RELFITID').text = '1015'
        return root

    @property
    def requiredElements(self):
        req = super(SellmfTestCase, self).requiredElements
        req += ('SELLTYPE',)
        return req

    @property
    def optionalElements(self):
        opt = super(SellmfTestCase, self).optionalElements
        opt += ('AVGCOSTBASIS', 'RELFITID',)
        return opt

    def testConvert(self):
        root = super(SellmfTestCase, self).testConvert()
        self.assertIsInstance(root, SELLMF)
        self.assertEqual(root.selltype, 'SELLSHORT')
        self.assertEqual(root.relfitid, '1015')

    def testOneOf(self):
        super(SellmfTestCase, self).testOneOf()
        self.oneOfTest('SELLTYPE', SELLTYPES)


class SelloptTestCase(InvsellTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SELLOPT')
        invsell = super(SelloptTestCase, self).root
        root.append(invsell)
        SubElement(root, 'OPTSELLTYPE').text = 'SELLTOCLOSE'
        SubElement(root, 'SHPERCTRCT').text = '100'
        SubElement(root, 'RELFITID').text = '1001'
        SubElement(root, 'RELTYPE').text = 'STRADDLE'
        SubElement(root, 'SECURED').text = 'NAKED'
        return root

    @property
    def requiredElements(self):
        opt = super(SelloptTestCase, self).requiredElements
        opt += ('OPTSELLTYPE', 'SHPERCTRCT',)
        return opt

    def testConvert(self):
        root = super(SelloptTestCase, self).testConvert()
        self.assertIsInstance(root, SELLOPT)
        self.assertEqual(root.optselltype, 'SELLTOCLOSE')
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.relfitid, '1001')
        self.assertEqual(root.reltype, 'STRADDLE')
        self.assertEqual(root.secured, 'NAKED')

    def testOneOf(self):
        super(SelloptTestCase, self).testOneOf()
        self.oneOfTest('OPTSELLTYPE', ('SELLTOCLOSE', 'SELLTOOPEN',))
        self.oneOfTest('RELTYPE', ('SPREAD', 'STRADDLE', 'NONE', 'OTHER'))
        self.oneOfTest('SECURED', ('NAKED', 'COVERED'))


class SellotherTestCase(InvsellTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SELLOTHER')
        invsell = super(SellotherTestCase, self).root
        root.append(invsell)
        return root

    def testConvert(self):
        root = super(SellotherTestCase, self).testConvert()
        self.assertIsInstance(root, SELLOTHER)


class SellstockTestCase(InvsellTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SELLSTOCK')
        invsell = super(SellstockTestCase, self).root
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        root.append(invsell)
        return root

    @property
    def requiredElements(self):
        opt = super(SellstockTestCase, self).requiredElements
        opt += ('SELLTYPE',)
        return opt

    def testConvert(self):
        root = super(SellstockTestCase, self).testConvert()
        self.assertIsInstance(root, SELLSTOCK)
        self.assertEqual(root.selltype, 'SELLSHORT')

    def testOneOf(self):
        super(SellstockTestCase, self).testOneOf()
        self.oneOfTest('SELLTYPE', SELLTYPES)
