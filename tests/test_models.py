# coding: utf-8

import unittest
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
from copy import deepcopy

import ofxtools
from ofxtools.Parser import (
    Element,
    SubElement,
)
from ofxtools.models import (
    Aggregate,
    SONRS,
    BANKACCTFROM,
    CCACCTFROM,
    INVACCTFROM,
    LEDGERBAL,
    AVAILBAL,
    INVBAL,
    DEBTINFO,
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


class SonrsTestCase(unittest.TestCase):
    def setUp(self):
        sonrs = Element('SONRS')
        status = SubElement(sonrs, 'STATUS')
        SubElement(status, 'CODE').text = '0'
        SubElement(status, 'SEVERITY').text = 'INFO'
        SubElement(sonrs, 'DTSERVER').text = '20051029101003'
        SubElement(sonrs, 'LANGUAGE').text = 'ENG'
        fi = SubElement(sonrs, 'FI')
        SubElement(fi, 'ORG').text = 'NCH'
        SubElement(fi, 'FID').text = '1001'
        self.sonrs = sonrs

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        sonrs = Aggregate.from_etree(self.sonrs)
        self.assertIsInstance(sonrs, SONRS)
        self.assertEqual(sonrs.code, 0)
        self.assertEqual(sonrs.severity, 'INFO')
        self.assertEqual(sonrs.dtserver, datetime(2005, 10, 29, 10, 10, 3))
        self.assertEqual(sonrs.language, 'ENG')
        self.assertEqual(sonrs.org, 'NCH')
        self.assertEqual(sonrs.fid, '1001')

    def testExtraElement(self):
        # Test invalid extra elements
        SubElement(self.sonrs, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.sonrs)

    def testMissingDtserver(self):
        # Test missing required elements
        self.sonrs.remove(self.sonrs[1]) # dtserver
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.sonrs)


class BankacctfromTestCase(unittest.TestCase):
    def setUp(self):
        acctfrom = Element('BANKACCTFROM')
        SubElement(acctfrom, 'BANKID').text='111000614'
        SubElement(acctfrom, 'ACCTID').text='123456789123456789'
        SubElement(acctfrom, 'ACCTTYPE').text='CHECKING'
        self.acctfrom = acctfrom

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        acctfrom = Aggregate.from_etree(self.acctfrom)
        self.assertIsInstance(acctfrom, BANKACCTFROM)
        self.assertEqual(acctfrom.bankid, '111000614')
        self.assertEqual(acctfrom.acctid, '123456789123456789')
        self.assertEqual(acctfrom.accttype, 'CHECKING')

    def testBankacctfromExtraElement(self):
        SubElement(self.acctfrom, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingBankid(self):
        self.acctfrom.remove(self.acctfrom[0]) # bankid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingAcctid(self):
        self.acctfrom.remove(self.acctfrom[1]) # acctid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingAccttype(self):
        self.acctfrom.remove(self.acctfrom[2]) # accttype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)


class CCacctfromTestCase(unittest.TestCase):
    def setUp(self):
        acctfrom = Element('CCACCTFROM')
        SubElement(acctfrom, 'ACCTID').text='123456789123456789'
        self.acctfrom = acctfrom

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        acctfrom = Aggregate.from_etree(self.acctfrom)
        self.assertIsInstance(acctfrom, CCACCTFROM)
        self.assertEqual(acctfrom.acctid, '123456789123456789')

    def testExtraElement(self):
        SubElement(self.acctfrom, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingAccttype(self):
        self.acctfrom.remove(self.acctfrom[0]) # acctid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)


class InvacctfromTestCase(unittest.TestCase):
    def setUp(self):
        acctfrom = Element('INVACCTFROM')
        SubElement(acctfrom, 'BROKERID').text='111000614'
        SubElement(acctfrom, 'ACCTID').text='123456789123456789'
        self.acctfrom = acctfrom

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        acctfrom = Aggregate.from_etree(self.acctfrom)
        self.assertIsInstance(acctfrom, INVACCTFROM)
        self.assertEqual(acctfrom.brokerid, '111000614')
        self.assertEqual(acctfrom.acctid, '123456789123456789')

    def testExtraElement(self):
        SubElement(self.acctfrom, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingBrokerid(self):
        self.acctfrom.remove(self.acctfrom[0]) # brokerid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.acctfrom)

    def testMissingAcctid(self):
        self.acctfrom.remove(self.acctfrom[1]) # acctid


class LedgerbalTestCase(unittest.TestCase):
    def setUp(self):
        balance = Element('LEDGERBAL')
        SubElement(balance, 'BALAMT').text='12345.67'
        SubElement(balance, 'DTASOF').text = '20051029101003'
        self.balance = balance 

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        balance = Aggregate.from_etree(self.balance)
        self.assertIsInstance(balance, LEDGERBAL)
        self.assertEqual(balance.balamt, Decimal('12345.67'))
        self.assertEqual(balance.dtasof, datetime(2005, 10, 29, 10, 10, 3))

    def testExtraElement(self):
        SubElement(self.balance, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingBalamt(self):
        self.balance.remove(self.balance[0]) # balamt
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingDtasof(self):
        self.balance.remove(self.balance[1]) # dtasof
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)


class AvailbalTestCase(unittest.TestCase):
    def setUp(self):
        balance = Element('AVAILBAL')
        SubElement(balance, 'BALAMT').text='12345.67'
        SubElement(balance, 'DTASOF').text = '20051029101003'
        self.balance = balance 

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        balance = Aggregate.from_etree(self.balance)
        self.assertIsInstance(balance, AVAILBAL)
        self.assertEqual(balance.balamt, Decimal('12345.67'))
        self.assertEqual(balance.dtasof, datetime(2005, 10, 29, 10, 10, 3))

    def testExtraElement(self):
        SubElement(self.balance, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingBalamt(self):
        self.balance.remove(self.balance[0]) # balamt
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingDtasof(self):
        self.balance.remove(self.balance[1]) # dtasof
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)


class InvbalTestCase(unittest.TestCase):
    def setUp(self):
        balance = Element('INVBAL')
        SubElement(balance, 'AVAILCASH').text='12345.67'
        SubElement(balance, 'MARGINBALANCE').text='23456.78'
        SubElement(balance, 'SHORTBALANCE').text='34567.89'
        self.balance = balance 

    def testConvert(self):
        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        balance = Aggregate.from_etree(self.balance)
        self.assertIsInstance(balance, INVBAL)
        self.assertEqual(balance.availcash, Decimal('12345.67'))
        self.assertEqual(balance.marginbalance, Decimal('23456.78'))
        self.assertEqual(balance.shortbalance, Decimal('34567.89'))

    def testExtraElement(self):
        SubElement(self.balance, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingAvailcash(self):
        self.balance.remove(self.balance[0]) # availcash 
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingMarginbalance(self):
        self.balance.remove(self.balance[1]) # marginbalance
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)

    def testMissingShortbalance(self):
        self.balance.remove(self.balance[2]) # shortbalance
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.balance)


class BalTestCase(unittest.TestCase):
    # FIXME
    pass


class DebtinfoTestCase(unittest.TestCase):
    def setUp(self):
        info = Element('DEBTINFO')
        secinfo = SubElement(info, 'SECINFO')
        secid = SubElement(secinfo, 'SECID')
        SubElement(secid, 'UNIQUEID').text = '123456789'
        SubElement(secid, 'UNIQUEIDTYPE').text = 'CUSIP'
        SubElement(secinfo, 'SECNAME').text = 'Acme Development, Inc.'
        SubElement(info, 'PARVALUE').text = '1000'
        SubElement(info, 'DEBTTYPE').text = 'COUPON'
        self.info = info
        self.secinfo = info[0]
        self.secid = self.secinfo[0]

    def testConvert(self):
        info = Aggregate.from_etree(self.info)
        self.assertIsInstance(info, DEBTINFO)
        self.assertEqual(info.uniqueid, '123456789')
        self.assertEqual(info.uniqueidtype, 'CUSIP')
        self.assertEqual(info.secname, 'Acme Development, Inc.')
        self.assertEqual(info.parvalue, Decimal('1000'))
        self.assertEqual(info.debttype, 'COUPON')

    def testMissingUniqueid(self):
        self.secid.remove(self.secid[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.info)

    def testMissingUniqueidtype(self):
        self.secid.remove(self.secid[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.info)

    def testMissingSecname(self):
        self.secinfo.remove(self.secinfo[0]) # secname
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.info)

    def testMissingParvalue(self):
        self.info.remove(self.info[1]) # parvalue
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.info)

    def testMissingDebttype(self):
        self.info.remove(self.info[2]) # debttype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(self.info)


class ModelTestCase(unittest.TestCase):
    testfile = 'tests/data/invstmtrs.ofx'

    #def setUp(self):
        #parser = ofxtools.Parser.TreeBuilder(element_factory=ofxtools.Parser.Element)
        #with open(self.testfile) as f:
            ## Strip the OFX header
            #sgml = ''.join(f.readlines()[3:])
            #parser.feed(sgml)
            #self.ofx = parser.close()

            ## Some useful locations
            #self.sonrs = self.ofx[0][0]
            #self.invstmtrs = self.ofx[1][0][2]
            #self.invtranlist = self.invstmtrs[3]
            #self.invposlist = self.invstmtrs[4]
            #self.seclist = self.ofx[2][0]

    #def test_invtran(self):
        #buystock = invtranlist[2]

        ## Test missing required elements
        #c = deepcopy(buystock)
        #invtran = c[0][0]
        #invtran.remove(invtran[0]) # fitid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invtran = c[0][0]
        #invtran.remove(invtran[1]) # dttrade
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #secid = c[0][1]
        #secid.remove(secid[0]) # uniqueid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #secid = c[0][1]
        #secid.remove(secid[1]) # uniqueidtype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invbuy = c[0]
        #invbuy.remove(invbuy[2]) # units
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invbuy = c[0]
        #invbuy.remove(invbuy[3]) # unitprice
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invbuy = c[0]
        #invbuy.remove(invbuy[5]) # total
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invbuy = c[0]
        #invbuy.remove(invbuy[6]) # subacctsec
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #invbuy = c[0]
        #invbuy.remove(invbuy[6]) # subacctfund
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(buystock)
        #c.remove(c[1]) # buytype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(buystock)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #buystock = Aggregate.from_etree(buystock)
        #self.assertEqual(buystock.fitid, '23321')
        #self.assertEqual(buystock.dttrade, datetime(2005, 8, 25))
        #self.assertEqual(buystock.dtsettle, datetime(2005, 8, 28))
        #self.assertEqual(buystock.uniqueid, '123456789')
        #self.assertEqual(buystock.uniqueidtype, 'CUSIP')
        #self.assertEqual(buystock.units, Decimal('100'))
        #self.assertEqual(buystock.unitprice, Decimal('50.00'))
        #self.assertEqual(buystock.commission, Decimal('25.00'))
        #self.assertEqual(buystock.total, Decimal('-5025.00'))
        #self.assertEqual(buystock.subacctsec, 'CASH')
        #self.assertEqual(buystock.subacctfund, 'CASH')

    #def test_invbanktran(self):
        #invbanktran = invtranlist[3]

        ## Test missing required elements
        #c = deepcopy(invbanktran)
        #stmttrn = c[0]
        #stmttrn.remove(stmttrn[0]) # trntype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbanktran)
        #stmttrn = c[0]
        #stmttrn.remove(stmttrn[1]) # dtposted
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbanktran)
        #stmttrn = c[0]
        #stmttrn.remove(stmttrn[3]) # trnamt
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbanktran)
        #stmttrn = c[0]
        #stmttrn.remove(stmttrn[4]) # fitid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbanktran)
        #c.remove(c[1]) # subacctfund
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(invbanktran)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #invbanktran = Aggregate.from_etree(invbanktran)
        #self.assertEqual(invbanktran.trntype, 'CREDIT')
        #self.assertEqual(invbanktran.dtposted, datetime(2005, 8, 25))
        #self.assertEqual(invbanktran.dtuser, datetime(2005, 8, 25))
        #self.assertEqual(invbanktran.trnamt, Decimal('1000.00'))
        #self.assertEqual(invbanktran.fitid, '12345')
        #self.assertEqual(invbanktran.name, 'Customer deposit')
        #self.assertEqual(invbanktran.memo, 'Your check #1034')
        #self.assertEqual(invbanktran.subacctfund, 'CASH')

    #def test_posstock(self):
        #posstock = invposlist[0]

        ## Test missing required elements
        #c = deepcopy(posstock)
        #secinfo = c[0][0]
        #secinfo.remove(secinfo[0]) # uniqueid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #secinfo = c[0][0]
        #secinfo.remove(secinfo[1]) # uniqueidtype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[1]) # heldinacct
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[2]) # postype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[3]) # units
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # unitprice
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # mktval
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posstock)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # dtpriceasof
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(posstock)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #posstock = Aggregate.from_etree(posstock)
        #self.assertEqual(posstock.uniqueid, '123456789')
        #self.assertEqual(posstock.uniqueidtype, 'CUSIP')
        #self.assertEqual(posstock.heldinacct, 'CASH')
        #self.assertEqual(posstock.postype, 'LONG')
        #self.assertEqual(posstock.units, Decimal('200'))
        #self.assertEqual(posstock.unitprice, Decimal('49.50'))
        #self.assertEqual(posstock.mktval, Decimal('9900.00'))
        #self.assertEqual(posstock.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        #self.assertEqual(posstock.memo, 'Next dividend payable Sept 1')

    #def test_posopt(self):
        #posopt = invposlist[1]

        ## Test missing required elements
        #c = deepcopy(posopt)
        #secinfo = c[0][0]
        #secinfo.remove(secinfo[0]) # uniqueid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #secinfo = c[0][0]
        #secinfo.remove(secinfo[1]) # uniqueidtype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[1]) # heldinacct
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[2]) # postype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[3]) # units
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # unitprice
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # mktval
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(posopt)
        #invpos = c[0]
        #invpos.remove(invpos[4]) # dtpriceasof
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(posopt)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #posopt = Aggregate.from_etree(posopt)
        #self.assertEqual(posopt.uniqueid, '000342222')
        #self.assertEqual(posopt.uniqueidtype, 'CUSIP')
        #self.assertEqual(posopt.heldinacct, 'CASH')
        #self.assertEqual(posopt.postype, 'LONG')
        #self.assertEqual(posopt.units, Decimal('1'))
        #self.assertEqual(posopt.unitprice, Decimal('5'))
        #self.assertEqual(posopt.mktval, Decimal('500'))
        #self.assertEqual(posopt.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        #self.assertEqual(posopt.memo, 'Option is in the money')

    #def test_invbal(self):
        #invbal = invstmtrs[5]
        ## Remove <BALLIST>, which blows up _flatten()
        #ballist = invbal[3]
        #invbal.remove(ballist)

        ## Test missing required elements
        #c = deepcopy(invbal)
        #c.remove(c[0]) # availcash
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbal)
        #c.remove(c[1]) # marginbalance
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(invbal)
        #c.remove(c[2]) # shortbalance
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(invbal)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #invbal = Aggregate.from_etree(invbal)
        #self.assertEqual(invbal.availcash, Decimal('200.00'))
        #self.assertEqual(invbal.marginbalance, Decimal('-50.00'))
        #self.assertEqual(invbal.shortbalance, Decimal('0'))

    #def test_bal(self):
        #bal = invstmtrs[5][3][0]

        ## Test missing required elements
        #c = deepcopy(bal)
        #c.remove(c[0]) # name
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(bal)
        #c.remove(c[1]) # desc
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(bal)
        #c.remove(c[2]) # baltype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(bal)
        #c.remove(c[3]) # value
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(bal)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #bal = Aggregate.from_etree(bal)
        #self.assertEqual(bal.name, 'Margin Interest Rate')
        #self.assertEqual(bal.desc, 'Current interest rate on margin balances')
        #self.assertEqual(bal.baltype, 'PERCENT')
        #self.assertEqual(bal.value, Decimal('7.85'))
        #self.assertEqual(bal.dtasof, datetime(2005, 8, 27, 1, 0, 0))

    #def test_stockinfo(self):
        #stockinfo = seclist[1]

        ## Test missing required elements
        #c = deepcopy(stockinfo)
        #secid = c[0][0]
        #secid.remove(secid[0]) # uniqueid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(stockinfo)
        #secid = c[0][0]
        #secid.remove(secid[1]) # uniqueidtype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(stockinfo)
        #secinfo = c[0]
        #secinfo.remove(secinfo[1]) # secname
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(stockinfo)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #stockinfo = Aggregate.from_etree(stockinfo)
        #self.assertEqual(stockinfo.uniqueid, '666678578')
        #self.assertEqual(stockinfo.uniqueidtype, 'CUSIP')
        #self.assertEqual(stockinfo.secname , 'Hackson Unlimited, Inc.')
        #self.assertEqual(stockinfo.ticker, 'HACK')
        #self.assertEqual(stockinfo.fiid, '1027')
        #self.assertEqual(stockinfo.yld, Decimal('17'))
        #self.assertEqual(stockinfo.assetclass, 'SMALLSTOCK')

    #def test_optinfo(self):
        #optinfo = seclist[2]

        ## Test missing required elements
        #c = deepcopy(optinfo)
        #secid = c[0][0]
        #secid.remove(secid[0]) # uniqueid
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## @@FIXME - we don't handle two <SECID> aggregates within <OPTINFO>
        #c = deepcopy(optinfo)
        #secid = c[0][0]
        #secid.remove(secid[1]) # uniqueidtype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(optinfo)
        #secinfo = c[0]
        #secinfo.remove(secinfo[1]) # secname
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(optinfo)
        #c.remove(c[1]) # opttype
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(optinfo)
        #c.remove(c[2]) # strikeprice
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(optinfo)
        #c.remove(c[3]) # dtexpire
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        #c = deepcopy(optinfo)
        #c.remove(c[4]) # shperctrct
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Test invalid extra elements
        #c = deepcopy(optinfo)
        #ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        #with self.assertRaises(ValueError):
            #Aggregate.from_etree(c)

        ## Make sure Aggregate.from_etree() calls Element.convert() and sets
        ## Aggregate instance attributes with the result
        #optinfo = Aggregate.from_etree(optinfo)
        #self.assertEqual(optinfo.uniqueid, '000342222')
        #self.assertEqual(optinfo.uniqueidtype, 'CUSIP')
        #self.assertEqual(optinfo.secname , 'Lucky Airlines Jan 97 Put')
        #self.assertEqual(optinfo.ticker, 'LUAXX')
        #self.assertEqual(optinfo.fiid, '0013')
        #self.assertEqual(optinfo.opttype, 'PUT')
        #self.assertEqual(optinfo.strikeprice, Decimal('35.00'))
        #self.assertEqual(optinfo.dtexpire, datetime(2005, 1, 21))
        #self.assertEqual(optinfo.shperctrct, 100)
        #self.assertEqual(optinfo.assetclass, 'LARGESTOCK')

if __name__=='__main__':
    unittest.main()
