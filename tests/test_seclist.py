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
from ofxtools.utils import UTC
from . import base
from . import test_seclist
from . import test_i18n
from . import test_models_common

from ofxtools.models.base import Aggregate
from ofxtools.models.common import MSGSETCORE

from ofxtools.models.seclist import (
    SECID, SECINFO, DEBTINFO, MFINFO, OPTINFO, OTHERINFO, STOCKINFO,
    PORTION, FIPORTION, MFASSETCLASS, FIMFASSETCLASS, ASSETCLASSES,
    SECLIST, SECLISTMSGSRSV1, SECLISTMSGSETV1, SECLISTMSGSET,
)


class SecidTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('UNIQUEID', 'UNIQUEIDTYPE')

    @property
    def root(self):
        root = Element('SECID')
        SubElement(root, 'UNIQUEID').text = '084670108'
        SubElement(root, 'UNIQUEIDTYPE').text = 'CUSIP'
        return root

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECID)
        self.assertEqual(root.uniqueid, '084670108')
        self.assertEqual(root.uniqueidtype, 'CUSIP')


class SecinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECID', 'SECNAME',)
    optionalElements = ('TICKER', 'FIID', 'RATING', 'UNITPRICE', 'DTASOF',
                        'CURRENCY',)

    @property
    def root(self):
        root = Element('SECINFO')
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(root, 'TICKER').text = 'ACME'
        SubElement(root, 'FIID').text = 'AC.ME'
        SubElement(root, 'RATING').text = 'Aa'
        SubElement(root, 'UNITPRICE').text = '94.5'
        SubElement(root, 'DTASOF').text = '20130615'
        currency = test_i18n.CurrencyTestCase().root
        root.append(currency)
        SubElement(root, 'MEMO').text = 'Foobar'
        return root

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secid.uniqueidtype)


class DebtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECINFO', 'PARVALUE', 'DEBTTYPE',)
    optionalElements = ('DEBTCLASS', 'COUPONRT', 'DTCOUPON', 'COUPONFREQ',
                        'CALLPRICE', 'YIELDTOCALL', 'DTCALL', 'CALLTYPE',
                        'YIELDTOMAT', 'DTMAT', 'ASSETCLASS', 'FIASSETCLASS',)

    @property
    def root(self):
        root = Element('DEBTINFO')
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
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
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.parvalue, Decimal('1000'))
        self.assertEqual(root.debttype, 'COUPON')
        self.assertEqual(root.debtclass, 'CORPORATE')
        self.assertEqual(root.couponrt, Decimal('5.125'))
        self.assertEqual(root.dtcoupon, datetime(2003, 12, 1, tzinfo=UTC))
        self.assertEqual(root.couponfreq, 'QUARTERLY')
        self.assertEqual(root.callprice, Decimal('1000'))
        self.assertEqual(root.yieldtocall, Decimal('6.5'))
        self.assertEqual(root.dtcall, datetime(2005, 12, 15, tzinfo=UTC))
        self.assertEqual(root.calltype, 'CALL')
        self.assertEqual(root.yieldtomat, Decimal('6.0'))
        self.assertEqual(root.dtmat, datetime(2006, 12, 15, tzinfo=UTC))
        self.assertEqual(root.assetclass, 'INTLBOND')
        self.assertEqual(root.fiassetclass, 'Fixed to floating bond')

    def testOneOf(self):
        self.oneOfTest('DEBTTYPE', ('COUPON', 'ZERO'))
        self.oneOfTest('DEBTCLASS',
                       ('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER'))
        self.oneOfTest('COUPONFREQ',
                       ('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                        'OTHER'))
        self.oneOfTest('CALLTYPE', ('CALL', 'PUT', 'PREFUND', 'MATURITY'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class PortionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('PORTION')
        SubElement(root, 'ASSETCLASS').text = 'DOMESTICBOND'
        SubElement(root, 'PERCENT').text = '15'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PORTION)
        self.assertEqual(root.assetclass, 'DOMESTICBOND')
        self.assertEqual(root.percent, Decimal('15'))

    def testOneOf(self):
        self.oneOfTest('ASSETCLASS', ASSETCLASSES)


class MfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    # requiredElements = ('PORTION',)  # FIXME - how to handle multiple PORTIONs?

    @property
    def root(self):
        root = Element('MFASSETCLASS')
        for i in range(4):
            portion = PortionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], PORTION)


class FiportionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('FIPORTION')
        SubElement(root, 'FIASSETCLASS').text = 'Foobar'
        SubElement(root, 'PERCENT').text = '50'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FIPORTION)
        self.assertEqual(root.fiassetclass, 'Foobar')
        self.assertEqual(root.percent, Decimal('50'))


class FimfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    # requiredElements = ('FIPORTION',)  # FIXME - how to handle multiple FIPORTIONs?

    @property
    def root(self):
        root = Element('FIMFASSETCLASS')
        for i in range(4):
            portion = FiportionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, FIMFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], FIPORTION)


class MfinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECINFO',)
    optionalElements = ('MFTYPE', 'YIELD', 'DTYIELDASOF', 'MFASSETCLASS',
                        'FIMFASSETCLASS',)

    @property
    def root(self):
        root = Element('MFINFO')
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, 'MFTYPE').text = 'OPENEND'
        SubElement(root, 'YIELD').text = '5.0'
        SubElement(root, 'DTYIELDASOF').text = '20030501'
        mfassetclass = MfassetclassTestCase().root
        root.append(mfassetclass)
        fimfassetclass = FimfassetclassTestCase().root
        root.append(fimfassetclass)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.mftype, 'OPENEND')
        self.assertEqual(root.yld, Decimal('5.0'))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1, tzinfo=UTC))
        self.assertIsInstance(root.mfassetclass, MFASSETCLASS)
        self.assertIsInstance(root.fimfassetclass, FIMFASSETCLASS)

    def testOneOf(self):
        self.oneOfTest('MFTYPE', ('OPENEND', 'CLOSEEND', 'OTHER'))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class OptinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECINFO', 'OPTTYPE', 'STRIKEPRICE', 'DTEXPIRE',
                        'SHPERCTRCT',)
    optionalElements = ('SECID', 'ASSETCLASS', 'FIASSETCLASS',)

    @property
    def root(self):
        root = Element('OPTINFO')
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, 'OPTTYPE').text = 'CALL'
        SubElement(root, 'STRIKEPRICE').text = '25.5'
        SubElement(root, 'DTEXPIRE').text = '20031215'
        SubElement(root, 'SHPERCTRCT').text = '100'
        secid = test_seclist.SecidTestCase().root
        root.append(secid)
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OPTINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.opttype, 'CALL')
        self.assertEqual(root.strikeprice, Decimal('25.5'))
        self.assertEqual(root.dtexpire, datetime(2003, 12, 15, tzinfo=UTC))
        self.assertEqual(root.shperctrct, 100)
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class OtherinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECINFO',)
    optionalElements = ('TYPEDESC', 'ASSETCLASS', 'FIASSETCLASS',)

    @property
    def root(self):
        root = Element('OTHERINFO')
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, 'TYPEDESC').text = 'Securitized baseball card pool'
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, OTHERINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.typedesc, 'Securitized baseball card pool')
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')

    def testOneOf(self):
        self.oneOfTest('ASSETCLASS', ASSETCLASSES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class StockinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    requiredElements = ('SECINFO',)
    optionalElements = ('STOCKTYPE', 'YIELD', 'DTYIELDASOF', 'ASSETCLASS',
                        'FIASSETCLASS',)

    @property
    def root(self):
        root = Element('STOCKINFO')
        secinfo = SecinfoTestCase().root
        root.append(secinfo)
        SubElement(root, 'STOCKTYPE').text = 'CONVERTIBLE'
        SubElement(root, 'YIELD').text = '5.0'
        SubElement(root, 'DTYIELDASOF').text = '20030501'
        SubElement(root, 'ASSETCLASS').text = 'SMALLSTOCK'
        SubElement(root, 'FIASSETCLASS').text = 'FOO'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STOCKINFO)
        self.assertIsInstance(root.secinfo, SECINFO)
        self.assertEqual(root.stocktype, 'CONVERTIBLE')
        self.assertEqual(root.yld, Decimal('5.0'))
        self.assertEqual(root.dtyieldasof, datetime(2003, 5, 1, tzinfo=UTC))
        self.assertEqual(root.assetclass, 'SMALLSTOCK')
        self.assertEqual(root.fiassetclass, 'FOO')

    def testOneOf(self):
        self.oneOfTest('ASSETCLASS', ASSETCLASSES)

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertEqual(root.uniqueid, root.secinfo.secid.uniqueid)
        self.assertEqual(root.uniqueidtype, root.secinfo.secid.uniqueidtype)


class SeclistTestCase(unittest.TestCase, base.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle SECINFO subclasses?

    @property
    def root(self):
        root = Element('SECLIST')
        secinfo = DebtinfoTestCase().root
        root.append(secinfo)
        secinfo = MfinfoTestCase().root
        root.append(secinfo)
        secinfo = OptinfoTestCase().root
        root.append(secinfo)
        secinfo = OtherinfoTestCase().root
        root.append(secinfo)
        secinfo = StockinfoTestCase().root
        root.append(secinfo)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLIST)
        self.assertEqual(len(root), 5)
        self.assertIsInstance(root[0], DEBTINFO)
        self.assertIsInstance(root[1], MFINFO)
        self.assertIsInstance(root[2], OPTINFO)
        self.assertIsInstance(root[3], OTHERINFO)
        self.assertIsInstance(root[4], STOCKINFO)


class Seclistmsgsrsv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    # FIXME
    # requiredElements = ('SECLIST',)

    @property
    def root(self):
        root = Element('SECLISTMSGSRSV1')
        seclist = SeclistTestCase().root
        root.append(seclist)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSRSV1)
        self.assertIsInstance(root.seclist, SECLIST)


class Seclistmsgsetv1TestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SECLISTMSGSETV1')
        msgsetcore = test_models_common.MsgsetcoreTestCase().root
        root.append(msgsetcore)
        SubElement(root, 'SECLISTRQDNLD').text = 'N'
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSETV1)
        self.assertIsInstance(root.msgsetcore, MSGSETCORE)
        self.assertEqual(root.seclistrqdnld, False)


class SeclistmsgsetTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = Element('SECLISTMSGSET')
        seclistmsgsetv1 = Seclistmsgsetv1TestCase().root
        root.append(seclistmsgsetv1)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, SECLISTMSGSET)
        self.assertIsInstance(root.seclistmsgsetv1, SECLISTMSGSETV1)


if __name__ == '__main__':
    unittest.main()
