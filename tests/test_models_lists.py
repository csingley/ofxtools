# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import common
from . import test_models_base
from . import test_models_banktransactions
from . import test_models_invtransactions
from . import test_models_securities
from . import test_models_positions

from ofxtools.models import (
    Aggregate,
    STMTTRN,
    BANKTRANLIST, SECLIST, BALLIST, INVPOSLIST,
    DEBTINFO, MFINFO, OPTINFO, OTHERINFO, STOCKINFO,
    POSDEBT, POSMF, POSOPT, POSOTHER, POSSTOCK,
    MFASSETCLASS, PORTION, BAL,
    INVBANKTRAN, BUYDEBT, BUYMF, BUYOPT, BUYOTHER, BUYSTOCK, CLOSUREOPT,
    INCOME, INVEXPENSE, JRNLFUND, JRNLSEC, MARGININTEREST, REINVEST, RETOFCAP,
    SELLDEBT, SELLMF, SELLOPT, SELLOTHER, SELLSTOCK, SPLIT, TRANSFER,
)


class BanktranlistTestCase(unittest.TestCase, common.TestAggregate):
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
            stmttrn = test_models_banktransactions.StmttrnTestCase().root
            root.append(stmttrn)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1))
        self.assertEqual(root.dtend, datetime(2013, 6, 30))
        self.assertEqual(len(root), 2)
        for i in range(2):
            self.assertIsInstance(root[i], STMTTRN)


class InvtranlistTestCase(unittest.TestCase, common.TestAggregate):
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
            invtran = getattr(test_models_invtransactions,
                              '{}TestCase'.format(it))
            root.append(invtran().root)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BANKTRANLIST)
        self.assertEqual(root.dtstart, datetime(2013, 6, 1))
        self.assertEqual(root.dtend, datetime(2013, 6, 30))
        for i, it in enumerate((INVBANKTRAN, BUYDEBT, BUYMF, BUYOPT, BUYOTHER,
                                BUYSTOCK, CLOSUREOPT, INCOME, INVEXPENSE,
                                JRNLFUND, JRNLSEC, MARGININTEREST, REINVEST,
                                RETOFCAP, SELLDEBT, SELLMF, SELLOPT, SELLOTHER,
                                SELLSTOCK, SPLIT, TRANSFER,)):
            self.assertIsInstance(root[i], it)


class SeclistTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle SECINFO subclasses?

    @property
    def root(self):
        root = Element('SECLIST')
        secinfo = test_models_securities.DebtinfoTestCase().root
        root.append(secinfo)
        secinfo = test_models_securities.MfinfoTestCase().root
        root.append(secinfo)
        secinfo = test_models_securities.OptinfoTestCase().root
        root.append(secinfo)
        secinfo = test_models_securities.OtherinfoTestCase().root
        root.append(secinfo)
        secinfo = test_models_securities.StockinfoTestCase().root
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


class BallistTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    optionalElements = ()  # FIXME - how to handle multiple BALs?

    @property
    def root(self):
        root = Element('BALLIST')
        bal1 = test_models_base.BalTestCase().root
        bal2 = test_models_base.BalTestCase().root
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


class MfassetclassTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    # requiredElements = ('PORTION',)  # FIXME - how to handle multiple PORTIONs?

    @property
    def root(self):
        root = Element('MFASSETCLASS')
        for i in range(4):
            portion = test_models_securities.PortionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], PORTION)


class FimfassetclassTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True
    # requiredElements = ('FIPORTION',)  # FIXME - how to handle multiple FIPORTIONs?

    @property
    def root(self):
        root = Element('MFASSETCLASS')
        for i in range(4):
            portion = test_models_securities.PortionTestCase().root
            root.append(portion)
        return root

    def testConvert(self):
        # Test *TRANLIST wrapper.  STMTTRN is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, MFASSETCLASS)
        self.assertEqual(len(root), 4)
        for i in range(4):
            self.assertIsInstance(root[i], PORTION)


class InvposlistTestCase(unittest.TestCase, common.TestAggregate):
    """ """
    __test__ = True

    @property
    def root(self):
        root = Element('INVPOSLIST')
        for invpos in ('Posdebt', 'Posmf', 'Posopt', 'Posother', 'Posstock'):
            testCase = '{}TestCase'.format(invpos)
            elem = getattr(test_models_positions, testCase)().root
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


if __name__ == '__main__':
    unittest.main()
