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
from . import test_models_banktransactions
from . import test_models_accounts

from ofxtools.models import (
    Aggregate, SECID, INVBANKTRAN,
    BUYDEBT, BUYMF, BUYOPT, BUYOTHER, BUYSTOCK,
    SELLDEBT, SELLMF, SELLOPT, SELLOTHER, SELLSTOCK,
    INVSUBACCTS, INV401KSOURCES, CURRENCY_CODES,
    BUYTYPES, OPTBUYTYPES, SELLTYPES, OPTSELLTYPES, INCOMETYPES, UNITTYPES,
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
        req += ('SECID', 'UNITS', 'UNITPRICE', 'TOTAL',
                'SUBACCTSEC', 'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        opt = super(InvbuyTestCase, self).optionalElements
        opt += ('MARKUP', 'COMMISSION', 'TAXES', 'FEES', 'LOAD',
                'CURRENCY', 'LOANID', 'LOANPRINCIPAL', 'LOANINTEREST',
                'INV401KSOURCE', 'DTPAYROLL', 'PRIORYEARCONTRIB')
        return opt

    def testConvert(self):
        root = super(InvbuyTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.unitprice, Decimal('1.50'))
        self.assertEqual(root.markup, Decimal('0'))
        self.assertEqual(root.commission, Decimal('9.99'))
        self.assertEqual(root.taxes, Decimal('0'))
        self.assertEqual(root.fees, Decimal('1.50'))
        self.assertEqual(root.load, Decimal('0'))
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
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
        req += ('SECID', 'UNITS', 'UNITPRICE', 'TOTAL',
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
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
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
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
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

    @property
    def requiredElements(self):
        req = super(BuystockTestCase, self).requiredElements
        return req

    def testConvert(self):
        root = super(BuystockTestCase, self).testConvert()
        self.assertIsInstance(root, BUYSTOCK)
        self.assertEqual(root.buytype, 'BUYTOCOVER')

    def testOneOf(self):
        super(BuystockTestCase, self).testOneOf()
        self.oneOfTest('BUYTYPE', BUYTYPES)


class ClosureoptTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('CLOSUREOPT')
        invtran = super(ClosureoptTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'OPTACTION').text = 'EXERCISE'
        SubElement(root, 'UNITS').text = '200'
        SubElement(root, 'SHPERCTRCT').text = '100'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'RELFITID').text = '1001'
        SubElement(root, 'GAIN').text = '123.45'
        return root

    @property
    def requiredElements(self):
        req = super(ClosureoptTestCase, self).requiredElements
        req += ('SECID', 'OPTACTION', 'UNITS', 'SHPERCTRCT',
                'SUBACCTSEC',)
        return req

    @property
    def optionalElements(self):
        opt = super(ClosureoptTestCase, self).optionalElements
        opt += ('RELFITID', 'GAIN',)
        return opt

    def testConvert(self):
        root = super(ClosureoptTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
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


class IncomeTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('INCOME')
        invtran = super(IncomeTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'INCOMETYPE').text = 'CGLONG'
        SubElement(root, 'TOTAL').text = '1500'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'TAXEXEMPT').text = 'Y'
        SubElement(root, 'WITHHOLDING').text = '123.45'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(IncomeTestCase, self).requiredElements
        req += ('SECID', 'INCOMETYPE', 'TOTAL', 'SUBACCTSEC',
                'SUBACCTFUND', )
        return req

    @property
    def optionalElements(self):
        opt = super(IncomeTestCase, self).optionalElements
        opt += ('TAXEXEMPT', 'WITHHOLDING', 'CURRENCY', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(IncomeTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.incometype, 'CGLONG')
        self.assertEqual(root.total, Decimal('1500'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.taxexempt, True)
        self.assertEqual(root.withholding, Decimal('123.45'))
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('INCOMETYPE', INCOMETYPES)
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class InvexpenseTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('INVEXPENSE')
        invtran = super(InvexpenseTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'TOTAL').text = '-161.49'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(InvexpenseTestCase, self).requiredElements
        req += ('SECID', 'TOTAL', 'SUBACCTSEC', 'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        opt = super(InvexpenseTestCase, self).optionalElements
        opt += ('CURRENCY', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(InvexpenseTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class JrnlfundTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('JRNLFUND')
        invtran = super(JrnlfundTestCase, self).root
        root.append(invtran)
        SubElement(root, 'SUBACCTTO').text = 'MARGIN'
        SubElement(root, 'SUBACCTFROM').text = 'CASH'
        SubElement(root, 'TOTAL').text = '161.49'
        return root

    @property
    def requiredElements(self):
        req = super(JrnlfundTestCase, self).requiredElements
        req += ('SUBACCTTO', 'SUBACCTFROM', 'TOTAL',)
        return req

    def testConvert(self):
        root = super(JrnlfundTestCase, self).testConvert()
        self.assertEqual(root.subacctto, 'MARGIN')
        self.assertEqual(root.subacctfrom, 'CASH')
        self.assertEqual(root.total, Decimal('161.49'))

    def testOneOf(self):
        self.oneOfTest('SUBACCTTO', INVSUBACCTS)
        self.oneOfTest('SUBACCTFROM', INVSUBACCTS)


class JrnlsecTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('JRNLSEC')
        invtran = super(JrnlsecTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTTO').text = 'MARGIN'
        SubElement(root, 'SUBACCTFROM').text = 'CASH'
        SubElement(root, 'UNITS').text = '1600'
        return root

    @property
    def requiredElements(self):
        req = super(JrnlsecTestCase, self).requiredElements
        req += ('SECID', 'SUBACCTTO', 'SUBACCTFROM', 'UNITS',)
        return req

    def testConvert(self):
        root = super(JrnlsecTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.subacctto, 'MARGIN')
        self.assertEqual(root.subacctfrom, 'CASH')
        self.assertEqual(root.units, Decimal('1600'))

    def testOneOf(self):
        self.oneOfTest('SUBACCTTO', INVSUBACCTS)
        self.oneOfTest('SUBACCTFROM', INVSUBACCTS)


class MargininterestTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('MARGININTEREST')
        invtran = super(MargininterestTestCase, self).root
        root.append(invtran)
        SubElement(root, 'TOTAL').text = '161.49'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        return root

    @property
    def requiredElements(self):
        req = super(MargininterestTestCase, self).requiredElements
        req += ('TOTAL', 'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        opt = super(MargininterestTestCase, self).optionalElements
        opt += ('CURRENCY',)
        return opt

    def testConvert(self):
        root = super(MargininterestTestCase, self).testConvert()
        self.assertEqual(root.total, Decimal('161.49'))
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)


class ReinvestTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('REINVEST')
        invtran = super(ReinvestTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
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
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(ReinvestTestCase, self).requiredElements
        req += ('SECID', 'TOTAL', 'INCOMETYPE', 'SUBACCTSEC',
                'UNITS', 'UNITPRICE',)
        return req

    @property
    def optionalElements(self):
        opt = super(ReinvestTestCase, self).optionalElements
        opt += ('COMMISSION', 'TAXES', 'FEES', 'LOAD', 'TAXEXEMPT',
                'CURRENCY', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(ReinvestTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
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
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('INCOMETYPE', INCOMETYPES)
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class RetofcapTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('RETOFCAP')
        invtran = super(RetofcapTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'TOTAL').text = '-161.49'
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(RetofcapTestCase, self).requiredElements
        req += ('SECID', 'TOTAL', 'SUBACCTSEC', 'SUBACCTFUND')
        return req

    @property
    def optionalElements(self):
        opt = super(RetofcapTestCase, self).optionalElements
        opt += ('CURRENCY', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(RetofcapTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.total, Decimal('-161.49'))
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


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


class SplitTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SPLIT')
        invtran = super(SplitTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'OLDUNITS').text = '200'
        SubElement(root, 'NEWUNITS').text = '100'
        SubElement(root, 'NUMERATOR').text = '1'
        SubElement(root, 'DENOMINATOR').text = '2'
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'FRACCASH').text = '0.50'
        SubElement(root, 'SUBACCTFUND').text = 'CASH'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(SplitTestCase, self).requiredElements
        req += ('SECID', 'SUBACCTSEC', 'OLDUNITS', 'NEWUNITS',
                'NUMERATOR', 'DENOMINATOR',) 
        return req

    @property
    def optionalElements(self):
        opt = super(SplitTestCase, self).optionalElements
        opt += ('CURRENCY', 'FRACCASH', 'SUBACCTFUND', 'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(SplitTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.oldunits, Decimal('200'))
        self.assertEqual(root.newunits, Decimal('100'))
        self.assertEqual(root.numerator, Decimal('1'))
        self.assertEqual(root.denominator, Decimal('2'))
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.fraccash, Decimal('0.50'))
        self.assertEqual(root.subacctfund, 'CASH')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class TransferTestCase(InvtranTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('TRANSFER')
        invtran = super(TransferTestCase, self).root
        root.append(invtran)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SUBACCTSEC').text = 'MARGIN'
        SubElement(root, 'UNITS').text = '100'
        SubElement(root, 'TFERACTION').text = 'OUT'
        SubElement(root, 'POSTYPE').text = 'LONG'
        invacctfrom = test_models_accounts.InvacctfromTestCase().root
        root.append(invacctfrom)
        SubElement(root, 'AVGCOSTBASIS').text = '22.22'
        SubElement(root, 'UNITPRICE').text = '23.01'
        SubElement(root, 'DTPURCHASE').text = '19991231'
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    @property
    def requiredElements(self):
        req = super(TransferTestCase, self).requiredElements
        req += ('SECID', 'SUBACCTSEC', 'UNITS', 'TFERACTION',
                'POSTYPE',)
        return req

    @property
    def optionalElements(self):
        opt = super(TransferTestCase, self).optionalElements
        opt += ('INVACCTFROM', 'AVGCOSTBASIS', 'UNITPRICE', 'DTPURCHASE',
                'INV401KSOURCE',)
        return opt

    def testConvert(self):
        root = super(TransferTestCase, self).testConvert()
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.subacctsec, 'MARGIN')
        self.assertEqual(root.units, Decimal('100'))
        self.assertEqual(root.tferaction, 'OUT')
        self.assertEqual(root.postype, 'LONG')
        test_models_accounts.InvacctfromTestCase.testConvert(self)
        self.assertEqual(root.avgcostbasis, Decimal('22.22'))
        self.assertEqual(root.unitprice, Decimal('23.01'))
        self.assertEqual(root.dtpurchase, datetime(1999, 12, 31))
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCTSEC', INVSUBACCTS)
        self.oneOfTest('TFERACTION', ('IN', 'OUT'))
        self.oneOfTest('POSTYPE', ('LONG', 'SHORT'))
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class OoTestCase(unittest.TestCase, common.TestAggregate):
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
        secid = test_models_base.SecidTestCase().root
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
        currency = test_models_base.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'INV401KSOURCE').text = 'PROFITSHARING'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.fitid, '1001')
        self.assertEqual(root.srvrtid, '2002')
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.dtplaced, datetime(2004, 7, 1))
        self.assertEqual(root.units, Decimal('150'))
        self.assertEqual(root.subacct, 'CASH')
        self.assertEqual(root.duration, 'GOODTILCANCEL')
        self.assertEqual(root.restriction, 'ALLORNONE')
        self.assertEqual(root.minunits, Decimal('100'))
        self.assertEqual(root.limitprice, Decimal('10.50'))
        self.assertEqual(root.stopprice, Decimal('10.00'))
        self.assertEqual(root.memo, 'Open Order')
        self.assertEqual(root.currate, Decimal('59.773'))
        self.assertEqual(root.cursym, 'EUR')
        self.assertEqual(root.inv401ksource, 'PROFITSHARING')
        return root

    def testOneOf(self):
        self.oneOfTest('SUBACCT', INVSUBACCTS)
        self.oneOfTest('DURATION', ('DAY', 'GOODTILCANCEL', 'IMMEDIATE'))
        self.oneOfTest('RESTRICTION', ('ALLORNONE', 'MINUNITS', 'NONE'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)
        self.oneOfTest('INV401KSOURCE', INV401KSOURCES)


class OobuydebtTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOBUYDEBT')
        oo = super(OobuydebtTestCase, self).root
        root.append(oo)
        SubElement(root, 'AUCTION').text = 'N'
        SubElement(root, 'DTAUCTION').text = '20120109'
        return root

    @property
    def requiredElements(self):
        req = super(OobuydebtTestCase, self).requiredElements
        req += ('AUCTION',)
        return req

    @property
    def optionalElements(self):
        opt = super(OobuydebtTestCase, self).optionalElements
        opt += ('DTAUCTION',)
        return opt

    def testConvert(self):
        root = super(OobuydebtTestCase, self).testConvert()
        self.assertEqual(root.auction, False)
        self.assertEqual(root.dtauction, datetime(2012, 1, 9))


class OobuymfTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOBUYMF')
        oo = super(OobuymfTestCase, self).root
        root.append(oo)
        SubElement(root, 'BUYTYPE').text = 'BUY'
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    @property
    def requiredElements(self):
        req = super(OobuymfTestCase, self).requiredElements
        req += ('BUYTYPE', 'UNITTYPE',)
        return req

    def testConvert(self):
        root = super(OobuymfTestCase, self).testConvert()
        self.assertEqual(root.buytype, 'BUY')
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        super(OobuymfTestCase, self).testOneOf()
        self.oneOfTest('BUYTYPE', BUYTYPES)
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OobuyoptTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOBUYOPT')
        oo = super(OobuyoptTestCase, self).root
        root.append(oo)
        SubElement(root, 'OPTBUYTYPE').text = 'BUYTOOPEN'
        return root

    @property
    def requiredElements(self):
        req = super(OobuyoptTestCase, self).requiredElements
        req += ('OPTBUYTYPE',)
        return req

    def testConvert(self):
        root = super(OobuyoptTestCase, self).testConvert()
        self.assertEqual(root.optbuytype, 'BUYTOOPEN')

    def testOneOf(self):
        super(OobuyoptTestCase, self).testOneOf()
        self.oneOfTest('OPTBUYTYPE', OPTBUYTYPES)


class OobuyotherTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOBUYOTHER')
        oo = super(OobuyotherTestCase, self).root
        root.append(oo)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    @property
    def requiredElements(self):
        req = super(OobuyotherTestCase, self).requiredElements
        req += ('UNITTYPE',)
        return req

    def testConvert(self):
        root = super(OobuyotherTestCase, self).testConvert()
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        super(OobuyotherTestCase, self).testOneOf()
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OobuystockTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOBUYSTOCK')
        oo = super(OobuystockTestCase, self).root
        root.append(oo)
        SubElement(root, 'BUYTYPE').text = 'BUYTOCOVER'
        return root

    @property
    def requiredElements(self):
        req = super(OobuystockTestCase, self).requiredElements
        req += ('BUYTYPE',)
        return req

    def testConvert(self):
        root = super(OobuystockTestCase, self).testConvert()
        self.assertEqual(root.buytype, 'BUYTOCOVER')

    def testOneOf(self):
        super(OobuystockTestCase, self).testOneOf()
        self.oneOfTest('BUYTYPE', BUYTYPES)


class OoselldebtTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOSELLDEBT')
        oo = super(OoselldebtTestCase, self).root
        root.append(oo)
        return root


class OosellmfTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOSELLMF')
        oo = super(OosellmfTestCase, self).root
        root.append(oo)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        SubElement(root, 'SELLALL').text = 'Y'
        return root

    @property
    def requiredElements(self):
        req = super(OosellmfTestCase, self).requiredElements
        req += ('SELLTYPE', 'UNITTYPE', 'SELLALL',)
        return req

    def testConvert(self):
        root = super(OosellmfTestCase, self).testConvert()
        self.assertEqual(root.selltype, 'SELLSHORT')
        self.assertEqual(root.unittype, 'SHARES')
        self.assertEqual(root.sellall, True)

    def testOneOf(self):
        super(OosellmfTestCase, self).testOneOf()
        self.oneOfTest('SELLTYPE', SELLTYPES)
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OoselloptTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOSELLOPT')
        oo = super(OoselloptTestCase, self).root
        root.append(oo)
        SubElement(root, 'OPTSELLTYPE').text = 'SELLTOCLOSE'
        return root

    @property
    def requiredElements(self):
        req = super(OoselloptTestCase, self).requiredElements
        req += ('OPTSELLTYPE',)
        return req

    def testConvert(self):
        root = super(OoselloptTestCase, self).testConvert()
        self.assertEqual(root.optselltype, 'SELLTOCLOSE')

    def testOneOf(self):
        super(OoselloptTestCase, self).testOneOf()
        self.oneOfTest('OPTSELLTYPE', OPTSELLTYPES)


class OosellotherTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOSELLOTHER')
        oo = super(OosellotherTestCase, self).root
        root.append(oo)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        return root

    @property
    def requiredElements(self):
        req = super(OosellotherTestCase, self).requiredElements
        req += ('UNITTYPE',)
        return req

    def testConvert(self):
        root = super(OosellotherTestCase, self).testConvert()
        self.assertEqual(root.unittype, 'SHARES')

    def testOneOf(self):
        super(OosellotherTestCase, self).testOneOf()
        self.oneOfTest('UNITTYPE', UNITTYPES)


class OosellstockTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('OOSELLSTOCK')
        oo = super(OosellstockTestCase, self).root
        root.append(oo)
        SubElement(root, 'SELLTYPE').text = 'SELLSHORT'
        return root

    @property
    def requiredElements(self):
        req = super(OosellstockTestCase, self).requiredElements
        req += ('SELLTYPE',)
        return req

    def testConvert(self):
        root = super(OosellstockTestCase, self).testConvert()
        self.assertEqual(root.selltype, 'SELLSHORT')

    def testOneOf(self):
        super(OosellstockTestCase, self).testOneOf()
        self.oneOfTest('SELLTYPE', SELLTYPES)


class SwitchmfTestCase(OoTestCase):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('SWITCHMF')
        oo = super(SwitchmfTestCase, self).root
        root.append(oo)
        secid = test_models_base.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'UNITTYPE').text = 'SHARES'
        SubElement(root, 'SWITCHALL').text = 'Y'
        return root

    @property
    def requiredElements(self):
        req = super(SwitchmfTestCase, self).requiredElements
        # FIXME - this should really test for both SECIDs in SWITCHMF,
        # both of which are required by the OFX spec
        req += ('SECID', 'UNITTYPE', 'SWITCHALL',)
        return req

    def testConvert(self):
        root = super(SwitchmfTestCase, self).testConvert()
        self.assertIsInstance(root.secid, SECID)
        self.assertEqual(root.unittype, 'SHARES')
        self.assertEqual(root.switchall, True)

    def testOneOf(self):
        super(SwitchmfTestCase, self).testOneOf()
        self.oneOfTest('UNITTYPE', UNITTYPES)
