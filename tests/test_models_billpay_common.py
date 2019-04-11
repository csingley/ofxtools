# coding: utf-8
""" Unit tests for models.billpay.common """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from copy import deepcopy

import xml.etree.ElementTree as ET


# local imports
from ofxtools.Types import DateTime
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TranList
from ofxtools.models.common import BAL, OFXELEMENT, OFXEXTENSION
from ofxtools.models.bank.stmt import BANKACCTFROM
from ofxtools.models.billpay.common import (
    BPACCTINFO,
    BILLPUBINFO,
    DISCOUNT,
    ADJUSTMENT,
    LINEITEM,
    INVOICE,
    EXTDPMTINV,
    PMTPRCSTS,
)
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES
from ofxtools.utils import UTC, classproperty


# test imports
import base
from test_models_i18n import CurrencyTestCase
from test_models_bank_stmt import (
    BankacctfromTestCase, BankaccttoTestCase, PayeeTestCase,
)


class BpacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "SVCSTATUS"]

    @property
    def root(self):
        root = ET.Element("BPACCTINFO")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        ET.SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BPACCTINFO)
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertEqual(root.svcstatus, "AVAIL")

    def testOneOf(self):
        self.oneOfTest("SVCSTATUS", ("AVAIL", "PEND", "ACTIVE"))


class BillpubinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BILLPUB", "BILLID"]

    @property
    def root(self):
        root = ET.Element("BILLPUBINFO")
        ET.SubElement(root, "BILLPUB").text = "Pubco"
        ET.SubElement(root, "BILLID").text = "54321"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, BILLPUBINFO)
        self.assertEqual(root.billpub, "Pubco")
        self.assertEqual(root.billid, "54321")


class PmtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "TRNAMT", "PAYACCT", "DTDUE"]
    optionalElements = ["PAYEELSTID", "BANKACCTTO", "MEMO",
                        "BILLREFINFO", "BILLPUBINFO"]

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = ET.Element("PMTINFO")
        acctfrom = BankacctfromTestCase().root
        root.append(acctfrom)
        ET.SubElement(root, "TRNAMT").text = "313.45"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        payeeid = ET.Element("PAYEEID")
        payeeid.text = "5112"
        payee = PayeeTestCase().root
        extdpmt = next(ExtdpmtTestCase().validSoup)
        billpubinfo = BillpubinfoTestCase().root
        for choice in payeeid, payee:
            root = cls.emptyBase
            root.append(choice)
            ET.SubElement(root, "PAYEELSTID").text = "240"
            acctto = BankaccttoTestCase().root
            root.append(acctto)
            for i in range(2):
                root.append(extdpmt)

            ET.SubElement(root, "PAYACCT").text = "711"
            ET.SubElement(root, "DTDUE").text = "19240507"
            ET.SubElement(root, "MEMO").text = "Time's up"
            ET.SubElement(root, "BILLREFINFO").text = "Paying it"
            root.append(billpubinfo)

            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME
        yield from ()

    @property
    def root(self):
        return next(self.validSoup)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)


class DiscountTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DSCRATE", "DSCAMT", "DSCDESC"]
    optionalElements = ["DSCDATE"]

    @property
    def root(self):
        root = ET.Element("DISCOUNT")
        ET.SubElement(root, "DSCRATE").text = "18"
        ET.SubElement(root, "DSCAMT").text = "13.50"
        ET.SubElement(root, "DSCDATE").text = "20170317"
        ET.SubElement(root, "DSCDESC").text = "Loyal customer discount"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, DISCOUNT)
        self.assertEqual(root.dscrate, Decimal('18'))
        self.assertEqual(root.dscamt, Decimal('13.5'))
        self.assertEqual(root.dscdate, datetime(2017, 3, 17, tzinfo=UTC))
        self.assertEqual(root.dscdesc, "Loyal customer discount")


class AdjustmentTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ADJDESC", "ADJAMT"]
    optionalElements = ["ADJNO", "ADJDATE"]

    @property
    def root(self):
        root = ET.Element("ADJUSTMENT")
        ET.SubElement(root, "ADJNO").text = "18"
        ET.SubElement(root, "ADJDESC").text = "We like you"
        ET.SubElement(root, "ADJAMT").text = "13.50"
        ET.SubElement(root, "ADJDATE").text = "20170317"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, ADJUSTMENT)
        self.assertEqual(root.adjno,  "18")
        self.assertEqual(root.adjdesc, "We like you")
        self.assertEqual(root.adjamt, Decimal('13.5'))
        self.assertEqual(root.adjdate, datetime(2017, 3, 17, tzinfo=UTC))


class LineitemTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["LITMAMT", "LITMDESC"]

    @property
    def root(self):
        root = ET.Element("LINEITEM")
        ET.SubElement(root, "LITMAMT").text = "13.50"
        ET.SubElement(root, "LITMDESC").text = "Purchase Item"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, LINEITEM)
        self.assertEqual(root.litmamt, Decimal("13.5"))
        self.assertEqual(root.litmdesc, "Purchase Item")


class InvoiceTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVNO", "INVTOTALAMT", "INVPAIDAMT", "INVDATE", "INVDESC"]
    optionalElements = ["DISCOUNT", "ADJUSTMENT"]

    @property
    def root(self):
        root = ET.Element("INVOICE")
        ET.SubElement(root, "INVNO").text = "103"
        ET.SubElement(root, "INVTOTALAMT").text = "25"
        ET.SubElement(root, "INVPAIDAMT").text = "25"
        ET.SubElement(root, "INVDATE").text = "20150906"
        ET.SubElement(root, "INVDESC").text = "Purchase invoice"
        root.append(DiscountTestCase().root)
        root.append(AdjustmentTestCase().root)
        root.append(LineitemTestCase().root)
        root.append(LineitemTestCase().root)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, INVOICE)
        self.assertEqual(root.invno, "103")
        self.assertEqual(root.invtotalamt, Decimal("25"))
        self.assertEqual(root.invpaidamt, Decimal("25"))
        self.assertEqual(root.invdate, datetime(2015, 9, 6, tzinfo=UTC))
        self.assertEqual(root.invdesc, "Purchase invoice")
        self.assertIsInstance(root.discount, DISCOUNT)
        self.assertIsInstance(root.adjustment, ADJUSTMENT)
        self.assertEqual(len(root), 2)
        for item in root:
            self.assertIsInstance(item, LINEITEM)


class ExtdpmtinvTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @property
    def root(self):
        root = ET.Element("EXTDPMTINV")
        invoice = InvoiceTestCase().root
        root.append(invoice)
        root.append(invoice)
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, EXTDPMTINV)
        self.assertEqual(len(root), 2)
        for item in root:
            self.assertIsInstance(item, INVOICE)


class ExtdpmtTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = ET.Element("EXTDPMT")
        ET.SubElement(root, "EXTDPMTFOR").text = "INDIVIDUAL"
        ET.SubElement(root, "EXTDPMTCHK").text = "112"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        extdpmtdsc = ET.Element("EXTDPMTDSC")
        extdpmtdsc.text = "Here is your money"
        extdpmtinv = ExtdpmtinvTestCase().root

        # EXTDPMTDSC only
        root = cls.emptyBase
        root.append(extdpmtdsc)
        yield root

        # Single EXTDPMTINV only
        root = cls.emptyBase
        root.append(extdpmtinv)
        yield root

        # Multiple EXTDPMTINV only
        root = cls.emptyBase
        root.append(extdpmtinv)
        root.append(extdpmtinv)
        yield root

        # EXTDPMTDSC with single EXTDPMTINV
        root = cls.emptyBase
        root.append(extdpmtdsc)
        root.append(extdpmtinv)
        yield root

        # EXTDPMTDSC with multiple EXTDPMTINV
        root = cls.emptyBase
        root.append(extdpmtdsc)
        root.append(extdpmtinv)
        root.append(extdpmtinv)
        yield root

    @property
    def root(self):
        return list(self.validSoup)[-1]

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Neither EXTDPMTDSC nor EXTDPMTINV
        yield cls.emptyBase

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest("EXTDPMTFOR", ("INDIVIDUAL", "BUSINESS"))


class ExtdpayeeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ["PAYEEID"]
    requiredElements = ["DAYSTOPAY"]

    @classproperty
    @classmethod
    def validSoup(cls):
        root_ = ET.Element("EXTDPAYEE")
        payeeid = ET.Element("PAYEEID")
        payeeid.text = "DEADBEEF"
        idscope = ET.Element("IDSCOPE")
        idscope.text = "GLOBAL"
        name = ET.Element("NAME")
        name.text = "Porky Pig"
        daystopay = ET.Element("DAYSTOPAY")
        daystopay.text = "30"

        # Everything
        root = deepcopy(root_)
        for child in (payeeid, idscope, name, daystopay):
            root.append(child)
        yield root

        # No PAYEEID; IDSCOPE and NAME
        root = deepcopy(root_)
        for child in (idscope, name, daystopay):
            root.append(child)
        yield root

        # No PAYEEID; either IDSCOPE or NAME
        for child in (idscope, name):
            root = deepcopy(root_)
            root.append(child)
            root.append(daystopay)
            yield root

        # Only DAYSTOPLAY
        root = deepcopy(root_)
        root.append(daystopay)
        yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        root_ = ET.Element("EXTDPAYEE")
        payeeid = ET.Element("IDSCOPE")
        payeeid.text = "DEADBEEF"
        idscope = ET.Element("IDSCOPE")
        idscope.text = "GLOBAL"
        name = ET.Element("NAME")
        name.text = "Porky Pig"
        daystopay = ET.Element("DAYSTOPAY")
        daystopay.text = "30"

        # PAYEEID with neither IDSCOPE nor NAME
        root = deepcopy(root_)
        root.append(payeeid)
        root.append(daystopay)
        yield root

        # PAYEEID with IDSCOPE without NAME
        root = deepcopy(root_)
        root.append(payeeid)
        root.append(idscope)
        root.append(daystopay)
        yield root

        # PAYEEID with NAME without IDSCOPE
        root = deepcopy(root_)
        root.append(payeeid)
        root.append(name)
        root.append(daystopay)
        yield root

    @property
    def root(self):
        return next(self.validSoup)

    def testValidSoup(self):
        for root in self.validSoup:
            Aggregate.from_etree(root)

    def testInvalidSoup(self):
        for root in self.invalidSoup:
            with self.assertRaises(ValueError):
                Aggregate.from_etree(root)

    def testOneOf(self):
        self.oneOfTest("IDSCOPE", ["GLOBAL", "USER"])


class PmtprcstsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PMTPRCCODE", "DTPMTPRC"]

    @property
    def root(self):
        root = ET.Element("PMTPRCSTS")
        ET.SubElement(root, "PMTPRCCODE").text = "FAILEDON"
        ET.SubElement(root, "DTPMTPRC").text = "20010101"
        return root

    def testConvert(self):
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, PMTPRCSTS)
        self.assertEqual(root.pmtprccode, "FAILEDON")
        self.assertEqual(root.dtpmtprc, datetime(2001, 1, 1, tzinfo=UTC))

    def testOneOf(self):
        self.oneOfTest("PMTPRCCODE", ("WILLPROCESSON", "PROCESSEDON",
                                      "NOFUNDSON", "FAILEDON", "CANCELEDON"))


if __name__ == "__main__":
    unittest.main()
