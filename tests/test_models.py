# coding: utf-8

import unittest
from datetime import datetime
from decimal import Decimal
import xml.etree.ElementTree as ET
from copy import deepcopy

import ofxtools
from ofxtools.models import (
    Aggregate,
    SONRS,
    INVACCTFROM,
)


with open('tests/data/invstmtrs.ofx') as f:
    # Strip the OFX header
    sgml = ''.join(f.readlines()[3:])
    parser = ofxtools.Parser.TreeBuilder(element_factory=ofxtools.Parser.Element)
    parser.feed(sgml)
    ofx = parser.close()

invstmtrs = ofx[1][0][2]
invtranlist = invstmtrs[3]
invposlist = invstmtrs[4]
seclist = ofx[2][0]


class ModelTestCase(unittest.TestCase):
    def test_sonrs(self):
        sonrs = ofx[0][0]

        # Test missing required elements
        c = deepcopy(sonrs)
        c.remove(c[1]) # dtserver
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(sonrs)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        sonrs = Aggregate.from_etree(sonrs)
        self.assertIsInstance(sonrs, SONRS)
        self.assertEqual(sonrs.code, 0)
        self.assertEqual(sonrs.severity, 'INFO')
        self.assertEqual(sonrs.dtserver, datetime(2005, 10, 29, 10, 10, 03))
        self.assertEqual(sonrs.language, 'ENG')
        self.assertEqual(sonrs.dtprofup, datetime(1999, 10, 29, 10, 10, 03))
        self.assertEqual(sonrs.dtacctup, datetime(2003, 10, 29, 10, 10, 03))
        self.assertEqual(sonrs.org, 'NCH')
        self.assertEqual(sonrs.fid, '1001')

    def test_acctfrom(self):
        acctfrom = invstmtrs[2]

        # Test missing required elements
        c = deepcopy(acctfrom)
        c.remove(c[0]) # brokerid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(acctfrom)
        c.remove(c[1]) # acctid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(acctfrom)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        acctfrom = Aggregate.from_etree(acctfrom)
        self.assertIsInstance(acctfrom, INVACCTFROM)
        self.assertEqual(acctfrom.brokerid, '121099999')
        self.assertEqual(acctfrom.acctid, '999988')

    def test_invtran(self):
        buystock = invtranlist[2]

        # Test missing required elements
        c = deepcopy(buystock)
        invtran = c[0][0]
        invtran.remove(invtran[0]) # fitid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invtran = c[0][0]
        invtran.remove(invtran[1]) # dttrade
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        secid = c[0][1]
        secid.remove(secid[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        secid = c[0][1]
        secid.remove(secid[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invbuy = c[0]
        invbuy.remove(invbuy[2]) # units
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invbuy = c[0]
        invbuy.remove(invbuy[3]) # unitprice
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invbuy = c[0]
        invbuy.remove(invbuy[5]) # total
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invbuy = c[0]
        invbuy.remove(invbuy[6]) # subacctsec
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        invbuy = c[0]
        invbuy.remove(invbuy[6]) # subacctfund
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(buystock)
        c.remove(c[1]) # buytype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(buystock)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        buystock = Aggregate.from_etree(buystock)
        self.assertEqual(buystock.fitid, '23321')
        self.assertEqual(buystock.dttrade, datetime(2005, 8, 25))
        self.assertEqual(buystock.dtsettle, datetime(2005, 8, 28))
        self.assertEqual(buystock.uniqueid, '123456789')
        self.assertEqual(buystock.uniqueidtype, 'CUSIP')
        self.assertEqual(buystock.units, Decimal('100'))
        self.assertEqual(buystock.unitprice, Decimal('50.00'))
        self.assertEqual(buystock.commission, Decimal('25.00'))
        self.assertEqual(buystock.total, Decimal('-5025.00'))
        self.assertEqual(buystock.subacctsec, 'CASH')
        self.assertEqual(buystock.subacctfund, 'CASH')

    def test_invbanktran(self):
        invbanktran = invtranlist[3]

        # Test missing required elements
        c = deepcopy(invbanktran)
        stmttrn = c[0]
        stmttrn.remove(stmttrn[0]) # trntype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbanktran)
        stmttrn = c[0]
        stmttrn.remove(stmttrn[1]) # dtposted
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbanktran)
        stmttrn = c[0]
        stmttrn.remove(stmttrn[3]) # trnamt
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbanktran)
        stmttrn = c[0]
        stmttrn.remove(stmttrn[4]) # fitid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbanktran)
        c.remove(c[1]) # subacctfund
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(invbanktran)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        invbanktran = Aggregate.from_etree(invbanktran)
        self.assertEqual(invbanktran.trntype, 'CREDIT')
        self.assertEqual(invbanktran.dtposted, datetime(2005, 8, 25))
        self.assertEqual(invbanktran.dtuser, datetime(2005, 8, 25))
        self.assertEqual(invbanktran.trnamt, Decimal('1000.00'))
        self.assertEqual(invbanktran.fitid, '12345')
        self.assertEqual(invbanktran.name, 'Customer deposit')
        self.assertEqual(invbanktran.memo, 'Your check #1034')
        self.assertEqual(invbanktran.subacctfund, 'CASH')

    def test_posstock(self):
        posstock = invposlist[0]

        # Test missing required elements
        c = deepcopy(posstock)
        secinfo = c[0][0]
        secinfo.remove(secinfo[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        secinfo = c[0][0]
        secinfo.remove(secinfo[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[1]) # heldinacct
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[2]) # postype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[3]) # units
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[4]) # unitprice
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[4]) # mktval
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posstock)
        invpos = c[0]
        invpos.remove(invpos[4]) # dtpriceasof
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(posstock)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        posstock = Aggregate.from_etree(posstock)
        self.assertEqual(posstock.uniqueid, '123456789')
        self.assertEqual(posstock.uniqueidtype, 'CUSIP')
        self.assertEqual(posstock.heldinacct, 'CASH')
        self.assertEqual(posstock.postype, 'LONG')
        self.assertEqual(posstock.units, Decimal('200'))
        self.assertEqual(posstock.unitprice, Decimal('49.50'))
        self.assertEqual(posstock.mktval, Decimal('9900.00'))
        self.assertEqual(posstock.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        self.assertEqual(posstock.memo, 'Next dividend payable Sept 1')

    def test_posopt(self):
        posopt = invposlist[1]

        # Test missing required elements
        c = deepcopy(posopt)
        secinfo = c[0][0]
        secinfo.remove(secinfo[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        secinfo = c[0][0]
        secinfo.remove(secinfo[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[1]) # heldinacct
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[2]) # postype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[3]) # units
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[4]) # unitprice
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[4]) # mktval
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(posopt)
        invpos = c[0]
        invpos.remove(invpos[4]) # dtpriceasof
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(posopt)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        posopt = Aggregate.from_etree(posopt)
        self.assertEqual(posopt.uniqueid, '000342222')
        self.assertEqual(posopt.uniqueidtype, 'CUSIP')
        self.assertEqual(posopt.heldinacct, 'CASH')
        self.assertEqual(posopt.postype, 'LONG')
        self.assertEqual(posopt.units, Decimal('1'))
        self.assertEqual(posopt.unitprice, Decimal('5'))
        self.assertEqual(posopt.mktval, Decimal('500'))
        self.assertEqual(posopt.dtpriceasof, datetime(2005, 8, 27, 1, 0, 0))
        self.assertEqual(posopt.memo, 'Option is in the money')

    def test_invbal(self):
        invbal = invstmtrs[5]
        # Remove <BALLIST>, which blows up _flatten()
        ballist = invbal[3]
        invbal.remove(ballist)

        # Test missing required elements
        c = deepcopy(invbal)
        c.remove(c[0]) # availcash
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbal)
        c.remove(c[1]) # marginbalance
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(invbal)
        c.remove(c[2]) # shortbalance
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(invbal)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        invbal = Aggregate.from_etree(invbal)
        self.assertEqual(invbal.availcash, Decimal('200.00'))
        self.assertEqual(invbal.marginbalance, Decimal('-50.00'))
        self.assertEqual(invbal.shortbalance, Decimal('0'))

    def test_bal(self):
        bal = invstmtrs[5][3][0]

        # Test missing required elements
        c = deepcopy(bal)
        c.remove(c[0]) # name
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(bal)
        c.remove(c[1]) # desc
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(bal)
        c.remove(c[2]) # baltype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(bal)
        c.remove(c[3]) # value
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(bal)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        bal = Aggregate.from_etree(bal)
        self.assertEqual(bal.name, 'Margin Interest Rate')
        self.assertEqual(bal.desc, 'Current interest rate on margin balances')
        self.assertEqual(bal.baltype, 'PERCENT')
        self.assertEqual(bal.value, Decimal('7.85'))
        self.assertEqual(bal.dtasof, datetime(2005, 8, 27, 1, 0, 0))

    def test_stockinfo(self):
        stockinfo = seclist[1]

        # Test missing required elements
        c = deepcopy(stockinfo)
        secid = c[0][0]
        secid.remove(secid[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(stockinfo)
        secid = c[0][0]
        secid.remove(secid[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(stockinfo)
        secinfo = c[0]
        secinfo.remove(secinfo[1]) # secname
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(stockinfo)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        stockinfo = Aggregate.from_etree(stockinfo)
        self.assertEqual(stockinfo.uniqueid, '666678578')
        self.assertEqual(stockinfo.uniqueidtype, 'CUSIP')
        self.assertEqual(stockinfo.secname , 'Hackson Unlimited, Inc.')
        self.assertEqual(stockinfo.ticker, 'HACK')
        self.assertEqual(stockinfo.fiid, '1027')
        self.assertEqual(stockinfo.yld, Decimal('17'))
        self.assertEqual(stockinfo.assetclass, 'SMALLSTOCK')

    def test_optinfo(self):
        optinfo = seclist[2]

        # Test missing required elements
        c = deepcopy(optinfo)
        secid = c[0][0]
        secid.remove(secid[0]) # uniqueid
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # @@FIXME - we don't handle two <SECID> aggregates within <OPTINFO>
        c = deepcopy(optinfo)
        secid = c[0][0]
        secid.remove(secid[1]) # uniqueidtype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(optinfo)
        secinfo = c[0]
        secinfo.remove(secinfo[1]) # secname
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(optinfo)
        c.remove(c[1]) # opttype
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(optinfo)
        c.remove(c[2]) # strikeprice
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(optinfo)
        c.remove(c[3]) # dtexpire
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        c = deepcopy(optinfo)
        c.remove(c[4]) # shperctrct
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Test invalid extra elements
        c = deepcopy(optinfo)
        ET.SubElement(c, 'FAKEELEMENT').text = 'garbage'
        with self.assertRaises(ValueError):
            Aggregate.from_etree(c)

        # Make sure Aggregate.from_etree() calls Element.convert() and sets
        # Aggregate instance attributes with the result
        optinfo = Aggregate.from_etree(optinfo)
        # @@FIXME - we don't handle two <SECID> aggregates within <OPTINFO>
        self.assertEqual(optinfo.uniqueid, '000342222')
        self.assertEqual(optinfo.uniqueidtype, 'CUSIP')
        self.assertEqual(optinfo.secname , 'Lucky Airlines Jan 97 Put')
        self.assertEqual(optinfo.ticker, 'LUAXX')
        self.assertEqual(optinfo.fiid, '0013')
        self.assertEqual(optinfo.opttype, 'PUT')
        self.assertEqual(optinfo.strikeprice, Decimal('35.00'))
        self.assertEqual(optinfo.dtexpire, datetime(2005, 1, 21))
        self.assertEqual(optinfo.shperctrct, 100)
        self.assertEqual(optinfo.assetclass, 'LARGESTOCK')

