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
)
from ofxtools.lib import (
    LANG_CODES,
    CURRENCY_CODES,
)


#with open('tests/data/invstmtrs.ofx') as f:
    ## Strip the OFX header
    #sgml = ''.join(f.readlines()[3:])
    #parser = ofxtools.Parser.TreeBuilder(element_factory=ofxtools.Parser.Element)
    #parser.feed(sgml)
    #ofx = parser.close()

#invstmtrs = ofx[1][0][2]
#invtranlist = invstmtrs[3]
#invposlist = invstmtrs[4]
#seclist = ofx[2][0]

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
        """
        Adding an extra Element not in the spec makes Aggregate.__init__()
        throw a ValueError.
        """
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


class SonrsTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('DTSERVER',)
    optionalElements = ('USERKEY', 'TSKEYEXPIRE', 'DTPROFUP', 'DTACCTUP', 'FI',
                        'SESSCOOKIE', 'ACCESSKEY')

    @property
    def root(self):
        root = Element('SONRS')
        status = SubElement(root, 'STATUS')
        SubElement(status, 'CODE').text = '0'
        SubElement(status, 'SEVERITY').text = 'INFO'
        SubElement(root, 'DTSERVER').text = '20051029101003'
        SubElement(root, 'USERKEY').text = 'DEADBEEF'
        SubElement(root, 'TSKEYEXPIRE').text = '20051231'
        SubElement(root, 'LANGUAGE').text = 'ENG'
        SubElement(root, 'DTPROFUP').text = '20050101'
        SubElement(root, 'DTACCTUP').text = '20050102'
        fi = SubElement(root, 'FI')
        SubElement(fi, 'ORG').text = 'NCH'
        SubElement(fi, 'FID').text = '1001'
        SubElement(root, 'SESSCOOKIE').text = 'BADA55'
        SubElement(root, 'ACCESSKEY').text = 'CAFEBABE'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SONRS)
        self.assertEqual(root.code, 0)
        self.assertEqual(root.severity, 'INFO')
        self.assertEqual(root.dtserver, datetime(2005, 10, 29, 10, 10, 3))
        self.assertEqual(root.userkey, 'DEADBEEF')
        self.assertEqual(root.tskeyexpire, datetime(2005, 12, 31))
        self.assertEqual(root.language, 'ENG')
        self.assertEqual(root.dtprofup, datetime(2005, 1, 1))
        self.assertEqual(root.dtacctup, datetime(2005, 1, 2))
        self.assertEqual(root.org, 'NCH')
        self.assertEqual(root.fid, '1001')
        self.assertEqual(root.sesscookie, 'BADA55')
        self.assertEqual(root.accesskey, 'CAFEBABE')

    def testRequired(self):
        if self.requiredElements:
            for tag in self.requiredElements:
                root = deepcopy(self.root)
                parent = root.find('.//%s/..' % tag)
                parent = root.find('.//%s/..' % tag)
                if parent is None:
                    raise ValueError("Can't find parent of %s" % tag)
                required = parent.find('./%s' % tag)
                parent.remove(required)
                try:
                    with self.assertRaises(ValueError):
                        Aggregate.from_etree(root)
                except AssertionError:
                    raise ValueError("Tag %s should be required, but isn't" % tag)

    def testOneOf(self):
        self.oneOfTest('SEVERITY', ('INFO', 'WARN', 'ERROR'))
        self.oneOfTest('LANGUAGE', LANG_CODES)


class BankacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BANKID', 'ACCTID', 'ACCTTYPE',)
    optionalElements = ('BRANCHID', 'ACCTKEY',)

    @property
    def root(self):
        root = Element('BANKACCTFROM')
        SubElement(root, 'BANKID').text='111000614'
        SubElement(root, 'BRANCHID').text='11223344'
        SubElement(root, 'ACCTID').text='123456789123456789'
        SubElement(root, 'ACCTTYPE').text='CHECKING'
        SubElement(root, 'ACCTKEY').text='DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKACCTFROM)
        self.assertEqual(root.bankid, '111000614')
        self.assertEqual(root.branchid, '11223344')
        self.assertEqual(root.acctid, '123456789123456789')
        self.assertEqual(root.accttype, 'CHECKING')
        self.assertEqual(root.acctkey, 'DEADBEEF')

    def testOneOf(self):
        self.oneOfTest('ACCTTYPE', 
                       ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
                      )


class CCacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('ACCTID',)
    optionalElements = ('ACCTKEY',)

    @property
    def root(self):
        root = Element('CCACCTFROM')
        SubElement(root, 'ACCTID').text='123456789123456789'
        SubElement(root, 'ACCTKEY').text='DEADBEEF'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, CCACCTFROM)
        self.assertEqual(root.acctid, '123456789123456789')


class InvacctfromTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BROKERID', 'ACCTID',)

    @property
    def root(self):
        root = Element('INVACCTFROM')
        SubElement(root, 'BROKERID').text='111000614'
        SubElement(root, 'ACCTID').text='123456789123456789'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVACCTFROM)
        self.assertEqual(root.brokerid, '111000614')
        self.assertEqual(root.acctid, '123456789123456789')


class LedgerbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('LEDGERBAL')
        SubElement(root, 'BALAMT').text='12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LEDGERBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3))


class AvailbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('BALAMT', 'DTASOF',)

    @property
    def root(self):
        root = Element('AVAILBAL')
        SubElement(root, 'BALAMT').text='12345.67'
        SubElement(root, 'DTASOF').text = '20051029101003'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, AVAILBAL)
        self.assertEqual(root.balamt, Decimal('12345.67'))
        self.assertEqual(root.dtasof, datetime(2005, 10, 29, 10, 10, 3))


class InvbalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('AVAILCASH', 'MARGINBALANCE', 'SHORTBALANCE',)
    optionalElements = ('BUYPOWER',)
    # BALLIST blows up _flatten(); don't test it here

    @property
    def root(self):
        root = Element('INVBAL')
        SubElement(root, 'AVAILCASH').text='12345.67'
        SubElement(root, 'MARGINBALANCE').text='23456.78'
        SubElement(root, 'SHORTBALANCE').text='34567.89'
        SubElement(root, 'BUYPOWER').text='45678.90'
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


class BalTestCase(unittest.TestCase, TestAggregate):
    __test__ = True
    requiredElements = ('NAME', 'DESC', 'BALTYPE', 'VALUE')
    optionalElements = ('DTASOF', 'CURRATE', 'CURSYM')

    @property
    def root(self):
        root = Element('BAL')
        SubElement(root, 'NAME').text='PETTYCASH'
        SubElement(root, 'DESC').text='Walking around money'
        SubElement(root, 'BALTYPE').text='DOLLAR'
        SubElement(root, 'VALUE').text='1234567.89'
        SubElement(root, 'DTASOF').text='20140615'
        currency = SubElement(root, 'CURRENCY')
        SubElement(currency, 'CURSYM').text='USD'
        SubElement(currency, 'CURRATE').text='1.57'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BAL)
        self.assertEqual(root.name, 'PETTYCASH')
        self.assertEqual(root.desc, 'Walking around money')
        self.assertEqual(root.baltype, 'DOLLAR')
        self.assertEqual(root.value, Decimal('1234567.89'))
        self.assertEqual(root.dtasof, datetime(2014, 6, 15))
        self.assertEqual(root.cursym, 'USD')
        self.assertEqual(root.currate, Decimal('1.57'))

    def testOneOf(self):
        self.oneOfTest('BALTYPE', ('DOLLAR', 'PERCENT', 'NUMBER'))
        self.oneOfTest('CURSYM', CURRENCY_CODES)


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


##class ModelTestCase(unittest.TestCase, TestAggregate):
    ##testfile = 'tests/data/invstmtrs.ofx'

    ##def setUp(self):
        ##parser = ofxtools.Parser.TreeBuilder(element_factory=ofxtools.Parser.Element)
        ##with open(self.testfile) as f:
            ### Strip the OFX header
            ##sgml = ''.join(f.readlines()[3:])
            ##parser.feed(sgml)
            ##self.ofx = parser.close()

            ### Some useful locations
            ##self.sonrs = self.ofx[0][0]
            ##self.invstmtrs = self.ofx[1][0][2]
            ##self.invtranlist = self.invstmtrs[3]
            ##self.invposlist = self.invstmtrs[4]
            ##self.seclist = self.ofx[2][0]

    ##def test_invtran(self):
        ##buystock = invtranlist[2]

        ### Test missing required elements
        ##c = deepcopy(buystock)
        ##invtran = c[0][0]
        ##invtran.remove(invtran[0]) # fitid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invtran = c[0][0]
        ##invtran.remove(invtran[1]) # dttrade
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##secid = c[0][1]
        ##secid.remove(secid[0]) # uniqueid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##secid = c[0][1]
        ##secid.remove(secid[1]) # uniqueidtype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invbuy = c[0]
        ##invbuy.remove(invbuy[2]) # units
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invbuy = c[0]
        ##invbuy.remove(invbuy[3]) # unitprice
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invbuy = c[0]
        ##invbuy.remove(invbuy[5]) # total
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invbuy = c[0]
        ##invbuy.remove(invbuy[6]) # subacctsec
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##invbuy = c[0]
        ##invbuy.remove(invbuy[6]) # subacctfund
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(buystock)
        ##c.remove(c[1]) # buytype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(buystock)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##buystock = Aggregate.from_etree(buystock)
        ##self.assertEqual(buystock.fitid, '23321')
        ##self.assertEqual(buystock.dttrade, datetime(2005, 8, 25))
        ##self.assertEqual(buystock.dtsettle, datetime(2005, 8, 28))
        ##self.assertEqual(buystock.uniqueid, '123456789')
        ##self.assertEqual(buystock.uniqueidtype, 'CUSIP')
        ##self.assertEqual(buystock.units, Decimal('100'))
        ##self.assertEqual(buystock.unitprice, Decimal('50.00'))
        ##self.assertEqual(buystock.commission, Decimal('25.00'))
        ##self.assertEqual(buystock.total, Decimal('-5025.00'))
        ##self.assertEqual(buystock.subacctsec, 'CASH')
        ##self.assertEqual(buystock.subacctfund, 'CASH')

    ##def test_invbanktran(self):
        ##invbanktran = invtranlist[3]

        ### Test missing required elements
        ##c = deepcopy(invbanktran)
        ##stmttrn = c[0]
        ##stmttrn.remove(stmttrn[0]) # trntype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(invbanktran)
        ##stmttrn = c[0]
        ##stmttrn.remove(stmttrn[1]) # dtposted
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(invbanktran)
        ##stmttrn = c[0]
        ##stmttrn.remove(stmttrn[3]) # trnamt
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(invbanktran)
        ##stmttrn = c[0]
        ##stmttrn.remove(stmttrn[4]) # fitid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(invbanktran)
        ##c.remove(c[1]) # subacctfund
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(invbanktran)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##invbanktran = Aggregate.from_etree(invbanktran)
        ##self.assertEqual(invbanktran.trntype, 'CREDIT')
        ##self.assertEqual(invbanktran.dtposted, datetime(2005, 8, 25))
        ##self.assertEqual(invbanktran.dtuser, datetime(2005, 8, 25))
        ##self.assertEqual(invbanktran.trnamt, Decimal('1000.00'))
        ##self.assertEqual(invbanktran.fitid, '12345')
        ##self.assertEqual(invbanktran.name, 'Customer deposit')
        ##self.assertEqual(invbanktran.memo, 'Your check #1034')
        ##self.assertEqual(invbanktran.subacctfund, 'CASH')

    ##def test_posstock(self):
        ##posstock = invposlist[0]

        ### Test missing required elements
        ##c = deepcopy(posstock)
        ##secinfo = c[0][0]
        ##secinfo.remove(secinfo[0]) # uniqueid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##secinfo = c[0][0]
        ##secinfo.remove(secinfo[1]) # uniqueidtype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[1]) # heldinacct
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[2]) # postype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[3]) # units
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # unitprice
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # mktval
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posstock)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # dtpriceasof
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(posstock)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##posstock = Aggregate.from_etree(posstock)
        ##self.assertEqual(posstock.uniqueid, '123456789')
        ##self.assertEqual(posstock.uniqueidtype, 'CUSIP')
        ##self.assertEqual(posstock.heldinacct, 'CASH')
        ##self.assertEqual(posstock.postype, 'LONG')
        ##self.assertEqual(posstock.units, Decimal('200'))
        ##self.assertEqual(posstock.unitprice, Decimal('49.50'))
        ##self.assertEqual(posstock.mktval, Decimal('9900.00'))
        ##self.assertEqual(posstock.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        ##self.assertEqual(posstock.memo, 'Next dividend payable Sept 1')

    ##def test_posopt(self):
        ##posopt = invposlist[1]

        ### Test missing required elements
        ##c = deepcopy(posopt)
        ##secinfo = c[0][0]
        ##secinfo.remove(secinfo[0]) # uniqueid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##secinfo = c[0][0]
        ##secinfo.remove(secinfo[1]) # uniqueidtype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[1]) # heldinacct
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[2]) # postype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[3]) # units
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # unitprice
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # mktval
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(posopt)
        ##invpos = c[0]
        ##invpos.remove(invpos[4]) # dtpriceasof
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(posopt)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##posopt = Aggregate.from_etree(posopt)
        ##self.assertEqual(posopt.uniqueid, '000342222')
        ##self.assertEqual(posopt.uniqueidtype, 'CUSIP')
        ##self.assertEqual(posopt.heldinacct, 'CASH')
        ##self.assertEqual(posopt.postype, 'LONG')
        ##self.assertEqual(posopt.units, Decimal('1'))
        ##self.assertEqual(posopt.unitprice, Decimal('5'))
        ##self.assertEqual(posopt.mktval, Decimal('500'))
        ##self.assertEqual(posopt.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        ##self.assertEqual(posopt.memo, 'Option is in the money')

    ##def test_bal(self):
        ##bal = invstmtrs[5][3][0]

        ### Test missing required elements
        ##c = deepcopy(bal)
        ##c.remove(c[0]) # name
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(bal)
        ##c.remove(c[1]) # desc
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(bal)
        ##c.remove(c[2]) # baltype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(bal)
        ##c.remove(c[3]) # value
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(bal)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##bal = Aggregate.from_etree(bal)
        ##self.assertEqual(bal.name, 'Margin Interest Rate')
        ##self.assertEqual(bal.desc, 'Current interest rate on margin balances')
        ##self.assertEqual(bal.baltype, 'PERCENT')
        ##self.assertEqual(bal.value, Decimal('7.85'))
        ##self.assertEqual(bal.dtasof, datetime(2005, 8, 27, 1, 0, 0))

    ##def test_stockinfo(self):
        ##stockinfo = seclist[1]

        ### Test missing required elements
        ##c = deepcopy(stockinfo)
        ##secid = c[0][0]
        ##secid.remove(secid[0]) # uniqueid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(stockinfo)
        ##secid = c[0][0]
        ##secid.remove(secid[1]) # uniqueidtype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(stockinfo)
        ##secinfo = c[0]
        ##secinfo.remove(secinfo[1]) # secname
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(stockinfo)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##stockinfo = Aggregate.from_etree(stockinfo)
        ##self.assertEqual(stockinfo.uniqueid, '666678578')
        ##self.assertEqual(stockinfo.uniqueidtype, 'CUSIP')
        ##self.assertEqual(stockinfo.secname , 'Hackson Unlimited, Inc.')
        ##self.assertEqual(stockinfo.ticker, 'HACK')
        ##self.assertEqual(stockinfo.fiid, '1027')
        ##self.assertEqual(stockinfo.yld, Decimal('17'))
        ##self.assertEqual(stockinfo.assetclass, 'SMALLSTOCK')

    ##def test_optinfo(self):
        ##optinfo = seclist[2]

        ### Test missing required elements
        ##c = deepcopy(optinfo)
        ##secid = c[0][0]
        ##secid.remove(secid[0]) # uniqueid
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### @@FIXME - we don't handle two <SECID> aggregates within <OPTINFO>
        ##c = deepcopy(optinfo)
        ##secid = c[0][0]
        ##secid.remove(secid[1]) # uniqueidtype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(optinfo)
        ##secinfo = c[0]
        ##secinfo.remove(secinfo[1]) # secname
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(optinfo)
        ##c.remove(c[1]) # opttype
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(optinfo)
        ##c.remove(c[2]) # strikeprice
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(optinfo)
        ##c.remove(c[3]) # dtexpire
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ##c = deepcopy(optinfo)
        ##c.remove(c[4]) # shperctrct
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Test invalid extra elements
        ##c = deepcopy(optinfo)
        ##ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        ##with self.assertRaises(ValueError):
            ##Aggregate.from_etree(c)

        ### Make sure Aggregate.from_etree() calls Element.convert() and sets
        ### Aggregate instance attributes with the result
        ##optinfo = Aggregate.from_etree(optinfo)
        ##self.assertEqual(optinfo.uniqueid, '000342222')
        ##self.assertEqual(optinfo.uniqueidtype, 'CUSIP')
        ##self.assertEqual(optinfo.secname , 'Lucky Airlines Jan 97 Put')
        ##self.assertEqual(optinfo.ticker, 'LUAXX')
        ##self.assertEqual(optinfo.fiid, '0013')
        ##self.assertEqual(optinfo.opttype, 'PUT')
        ##self.assertEqual(optinfo.strikeprice, Decimal('35.00'))
        ##self.assertEqual(optinfo.dtexpire, datetime(2005, 1, 21))
        ##self.assertEqual(optinfo.shperctrct, 100)
        ##self.assertEqual(optinfo.assetclass, 'LARGESTOCK')

if __name__=='__main__':
    unittest.main()
