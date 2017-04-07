# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import (
    Element,
    SubElement,
)
from copy import deepcopy


# local imports
import ofxtools
from ofxtools.models import (
    Aggregate,
    SONRS,
    CURRENCY,
    BANKACCTFROM,
    CCACCTFROM,
    INVACCTFROM,
    LEDGERBAL,
    AVAILBAL,
    INVBAL,
    BAL,
    DEBTINFO,
    MFINFO,
    OPTINFO,
    OTHERINFO,
    STOCKINFO,
    PORTION,
    FIPORTION,
    STMTTRN,
    PAYEE,
    BANKACCTTO,
    CCACCTTO,
)
from ofxtools.lib import (
    LANG_CODES,
    CURRENCY_CODES,
)

class TestAggregate(object):
    """ """
    __test__ = False
    requiredElements = ()
    optionalElements = ()

    @property
    def root(self):
        """Define in subclass"""
        raise NotImplementedError

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                required = parent.find('./%s' % tag)
                parent.remove(required)
                with self.assertRaises(ValueError):
                    Aggregate.from_etree(root)

    def testOptional(self):
        if self.optionalElements:
            for tag in self.optionalElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                optional = parent.find('./%s' % tag)
                parent.remove(optional)
                Aggregate.from_etree(root)

    def testExtraElement(self):
        root = deepcopy(self.root)
        SubElement(root, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)

    def oneOfTest(self, tag, texts):
        # Make sure OneOf validator allows all legal values and disallows
        # illegal values
        for text in texts:
            root = deepcopy(self.root)
            target = root.find('.//%s' % tag)
            target.text = text
            Aggregate.from_etree(root)

        root = deepcopy(self.root)
        target = root.find('.//%s' % tag)
        target.text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(root)


class DebtinfoTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE', 'SECNAME', 'PARVALUE', 
                        'DEBTTYPE'
                       )
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURSYM', 'CURRATE', 'MEMO', 'DEBTCLASS', 'COUPONRT',
                        'DTCOUPON', 'COUPONFREQ', 'CALLPRICE', 'YIELDTOCALL',
                        'DTCALL', 'CALLTYPE', 'YIELDTOMAT', 'DTMAT',
                        'ASSETCLASS', 'FIASSETCLASS',
                       )

    @property
    def root(self):
        root = Element('DEBTINFO')
        secinfo = SubElement(root, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(secinfo, 'TICKER').text = 'ACME'
        SubElement(secinfo, 'FIID').text = 'AC.ME'
        SubElement(secinfo, 'RATING').text = 'Aa'
        SubElement(secinfo, 'UNITPRICE').text = '94.5'
        SubElement(secinfo, 'DTASOF').text = '20130615'
        currency = SubElement(secinfo, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.45'
        SubElement(secinfo, 'MEMO').text = 'Foobar'
        SubElement(root, 'PARVALUE').text = '1000'
        SubElement(root, 'DEBTTYPE').text = 'COUPON'
        SubElement(root, 'DEBTCLASS').text = 'CORPORATE'
        SubElement(root, 'COUPONRT').text = '5.125'
        SubElement(root, 'DTCOUPON').text = '20031201'
        SubElement(root, 'COUPONFREQ').text = 'QUARTERLY'
        SubElement(root, 'CALLPRICE').text = '1000'
        SubElement(root, 'YIELDTOCALL').text = '6.5'
        SubElement(root, 'DTCALL').text = '20051215'
        SubElement(root, 'CALLTYPE').text = 'CALL'
        SubElement(root, 'YIELDTOMAT').text = '6.0'
        SubElement(root, 'DTMAT').text = '20061215'
        SubElement(root, 'ASSETCLASS').text = 'INTLBOND'
        SubElement(root, 'FIASSETCLASS').text = 'Fixed to floating bond'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, DEBTINFO)
        self.assertEqual(root.uniqueid, '123456789')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.secname, 'Acme Development, Inc.')
        self.assertEqual(root.ticker, 'ACME')
        self.assertEqual(root.fiid, 'AC.ME')
        self.assertEqual(root.rating, 'Aa')
        self.assertEqual(root.unitprice, Decimal('94.5'))
        self.assertEqual(root.dtasof, datetime(2013, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.45'))
        self.assertEqual(root.memo, 'Foobar')
        self.assertEqual(root.parvalue, Decimal('1000'))
        self.assertEqual(root.debttype, 'COUPON')
        self.assertEqual(root.debtclass, 'CORPORATE')
        self.assertEqual(root.couponrt, Decimal('5.125'))
        self.assertEqual(root.dtcoupon, datetime(2003, 12, 1))
        self.assertEqual(root.couponfreq, 'QUARTERLY')
        self.assertEqual(root.callprice, Decimal('1000'))
        self.assertEqual(root.yieldtocall, Decimal('6.5'))
        self.assertEqual(root.dtcall, datetime(2005, 12, 15))
        self.assertEqual(root.calltype, 'CALL')
        self.assertEqual(root.yieldtomat, Decimal('6.0'))
        self.assertEqual(root.dtmat, datetime(2006, 12, 15))
        self.assertEqual(root.assetclass, 'INTLBOND')
        self.assertEqual(root.fiassetclass, 'Fixed to floating bond')

    def testOneOf(self):
        self.oneOfTest('CURSYM', CURRENCY_CODES)
        self.oneOfTest('DEBTTYPE', ('COUPON', 'ZERO'))
        self.oneOfTest('DEBTCLASS',
                       ('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
                      )
        self.oneOfTest('COUPONFREQ', 
                       ('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL', 'OTHER')
                      )
        self.oneOfTest('CALLTYPE', ('CALL', 'PUT', 'PREFUND', 'MATURITY'))


class MfinfoTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE', 'SECNAME',)
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURSYM', 'CURRATE', 'MEMO', 'YIELD', 'DTYIELDASOF', 
                        'MFASSETCLASS', 'FIMFASSETCLASS',
                       )

    @property
    def root(self):
        root = Element('MFINFO')
        secinfo = SubElement(root, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(secinfo, 'TICKER').text = 'ACME'
        SubElement(secinfo, 'FIID').text = 'AC.ME'
        SubElement(secinfo, 'RATING').text = 'Aa'
        SubElement(secinfo, 'UNITPRICE').text = '94.5'
        SubElement(secinfo, 'DTASOF').text = '20130615'
        currency = SubElement(secinfo, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.45'
        SubElement(secinfo, 'MEMO').text = 'Foobar'
        SubElement(root, 'YIELD').text = '5.0'
        SubElement(root, 'DTYIELDASOF').text = '20030501'
        mfassetclass = SubElement(root, 'MFASSETCLASS')
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'DOMESTICBOND'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'INTLBOND'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'LARGESTOCK'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'INTLSTOCK'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'MONEYMRKT'
        SubElement(portion, 'PERCENT').text = '15'
        portion = SubElement(mfassetclass, 'PORTION')
        SubElement(portion, 'ASSETCLASS').text = 'OTHER'
        SubElement(portion, 'PERCENT').text = '10'
        fimfassetclass = SubElement(root, 'FIMFASSETCLASS')
        portion = SubElement(fimfassetclass, 'FIPORTION')
        SubElement(portion, 'FIASSETCLASS').text = 'FOO'
        SubElement(portion, 'PERCENT').text = '50'
        portion = SubElement(fimfassetclass, 'FIPORTION')
        SubElement(portion, 'FIASSETCLASS').text = 'BAR'
        SubElement(portion, 'PERCENT').text = '50'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFINFO)
        self.assertEqual(root.uniqueid, '123456789')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.secname, 'Acme Development, Inc.')
        self.assertEqual(root.ticker, 'ACME')
        self.assertEqual(root.fiid, 'AC.ME')
        self.assertEqual(root.rating, 'Aa')
        self.assertEqual(root.unitprice, Decimal('94.5'))
        self.assertEqual(root.dtasof, datetime(2013, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.45'))
        self.assertEqual(root.memo, 'Foobar')
        self.assertEqual(root.yld, Decimal('5.0'))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1))
        
        for p in root.mfassetclass:
            self.assertIsInstance(p, PORTION)
        p = root.mfassetclass
        self.assertEqual(p[0].assetclass, 'DOMESTICBOND')
        self.assertEqual(p[0].percent, Decimal('15'))
        self.assertEqual(p[1].assetclass, 'INTLBOND')
        self.assertEqual(p[1].percent, Decimal('15'))
        self.assertEqual(p[2].assetclass, 'LARGESTOCK')
        self.assertEqual(p[2].percent, Decimal('15'))
        self.assertEqual(p[3].assetclass, 'SMALLSTOCK')
        self.assertEqual(p[3].percent, Decimal('15'))
        self.assertEqual(p[4].assetclass, 'INTLSTOCK')
        self.assertEqual(p[4].percent, Decimal('15'))
        self.assertEqual(p[5].assetclass, 'MONEYMRKT')
        self.assertEqual(p[5].percent, Decimal('15'))
        self.assertEqual(p[6].assetclass, 'OTHER')
        self.assertEqual(p[6].percent, Decimal('10'))

        for p in root.fimfassetclass:
            self.assertIsInstance(p, FIPORTION)
        p = root.fimfassetclass
        self.assertEqual(p[0].fiassetclass, 'FOO')
        self.assertEqual(p[0].percent, Decimal('50'))
        self.assertEqual(p[1].fiassetclass, 'BAR')
        self.assertEqual(p[1].percent, Decimal('50'))

    def testOneOf(self):
        self.oneOfTest('CURSYM', CURRENCY_CODES)


class OptinfoTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE', 'SECNAME', 'OPTTYPE',
                        'STRIKEPRICE', 'DTEXPIRE', 'SHPERCTRCT')
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURSYM', 'CURRATE', 'MEMO', 'ASSETCLASS', 
                        'FIASSETCLASS')

    @property
    def root(self):
        root = Element('OPTINFO')
        secinfo = SubElement(root, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(secinfo, 'TICKER').text = 'ACME'
        SubElement(secinfo, 'FIID').text = 'AC.ME'
        SubElement(secinfo, 'RATING').text = 'Aa'
        SubElement(secinfo, 'UNITPRICE').text = '94.5'
        SubElement(secinfo, 'DTASOF').text = '20130615'
        currency = SubElement(secinfo, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.45'
        SubElement(secinfo, 'MEMO').text = 'Foobar'
        SubElement(root, 'OPTTYPE').text = 'CALL'
        SubElement(root, 'STRIKEPRICE').text = '25.5'
        SubElement(root, 'DTEXPIRE').text = '20031215'
        SubElement(root, 'SHPERCTRCT').text = '100'
        secid = SubElement(root, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '987654321'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OPTINFO)
        self.assertEqual(root.uniqueid, '123456789')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.secname, 'Acme Development, Inc.')
        self.assertEqual(root.ticker, 'ACME')
        self.assertEqual(root.fiid, 'AC.ME')
        self.assertEqual(root.rating, 'Aa')
        self.assertEqual(root.unitprice, Decimal('94.5'))
        self.assertEqual(root.dtasof, datetime(2013, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.45'))
        self.assertEqual(root.memo, 'Foobar')
        self.assertEqual(root.opttype, 'CALL')
        self.assertEqual(root.strikeprice, Decimal('25.5'))
        self.assertEqual(root.dtexpire, datetime(2003, 12, 15))
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')


class OtherinfoTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE', 'SECNAME',)
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURSYM', 'CURRATE', 'MEMO', 'TYPEDESC', 'ASSETCLASS', 
                        'FIASSETCLASS',
                       )

    @property
    def root(self):
        root = Element('OTHERINFO')
        secinfo = SubElement(root, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(secinfo, 'TICKER').text = 'ACME'
        SubElement(secinfo, 'FIID').text = 'AC.ME'
        SubElement(secinfo, 'RATING').text = 'Aa'
        SubElement(secinfo, 'UNITPRICE').text = '94.5'
        SubElement(secinfo, 'DTASOF').text = '20130615'
        currency = SubElement(secinfo, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.45'
        SubElement(secinfo, 'MEMO').text = 'Foobar'
        SubElement(root, 'TYPEDESC').text = 'Securitized baseball card pool'
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OTHERINFO)
        self.assertEqual(root.uniqueid, '123456789')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.secname, 'Acme Development, Inc.')
        self.assertEqual(root.ticker, 'ACME')
        self.assertEqual(root.fiid, 'AC.ME')
        self.assertEqual(root.rating, 'Aa')
        self.assertEqual(root.unitprice, Decimal('94.5'))
        self.assertEqual(root.dtasof, datetime(2013, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.45'))
        self.assertEqual(root.memo, 'Foobar')
        self.assertEqual(root.typedesc, 'Securitized baseball card pool')
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')


class StockinfoTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE', 'SECNAME',)
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURSYM', 'CURRATE', 'MEMO', 'STOCKTYPE', 'YIELD', 
                        'DTYIELDASOF', 'ASSETCLASS', 'FIASSETCLASS',
                       )

    @property
    def root(self):
        root = Element('STOCKINFO')
        secinfo = SubElement(root, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(secinfo, 'TICKER').text = 'ACME'
        SubElement(secinfo, 'FIID').text = 'AC.ME'
        SubElement(secinfo, 'RATING').text = 'Aa'
        SubElement(secinfo, 'UNITPRICE').text = '94.5'
        SubElement(secinfo, 'DTASOF').text = '20130615'
        currency = SubElement(secinfo, 'CURRENCY')
        SubElement(currency, 'CURSYM').text = 'USD'
        SubElement(currency, 'CURRATE').text = '1.45'
        SubElement(secinfo, 'MEMO').text = 'Foobar'
        SubElement(root, 'STOCKTYPE').text = 'CONVERTIBLE'
        SubElement(root, 'YIELD').text = '5.0'
        SubElement(root, 'DTYIELDASOF').text = '20030501'
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STOCKINFO)
        self.assertEqual(root.uniqueid, '123456789')
        self.assertEqual(root.uniqueidtype, 'CUSIP')
        self.assertEqual(root.secname, 'Acme Development, Inc.')
        self.assertEqual(root.ticker, 'ACME')
        self.assertEqual(root.fiid, 'AC.ME')
        self.assertEqual(root.rating, 'Aa')
        self.assertEqual(root.unitprice, Decimal('94.5'))
        self.assertEqual(root.dtasof, datetime(2013, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.45'))
        self.assertEqual(root.memo, 'Foobar')
        self.assertEqual(root.stocktype, 'CONVERTIBLE')
        self.assertEqual(root.yld, Decimal('5.0'))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1))
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')


if __name__=='__main__':
    unittest.main()
