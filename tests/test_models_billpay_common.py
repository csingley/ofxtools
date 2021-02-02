# coding: utf-8
""" Unit tests for models.billpay.common """
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from copy import deepcopy

import xml.etree.ElementTree as ET


# local imports
from ofxtools.models.billpay.common import (
    PMTINFO,
    BPACCTINFO,
    BILLPUBINFO,
    DISCOUNT,
    ADJUSTMENT,
    LINEITEM,
    INVOICE,
    EXTDPMT,
    EXTDPAYEE,
    EXTDPMTINV,
    PMTPRCSTS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt


class BpacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "SVCSTATUS"]

    oneOfs = {"SVCSTATUS": ("AVAIL", "PEND", "ACTIVE")}

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("BPACCTINFO")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        ET.SubElement(root, "SVCSTATUS").text = "AVAIL"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BPACCTINFO(
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate, svcstatus="AVAIL"
        )


class BillpubinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BILLPUB", "BILLID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("BILLPUBINFO")
        ET.SubElement(root, "BILLPUB").text = "Pubco"
        ET.SubElement(root, "BILLID").text = "54321"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return BILLPUBINFO(billpub="Pubco", billid="54321")


class PmtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BANKACCTFROM", "TRNAMT", "PAYACCT", "DTDUE"]
    optionalElements = [
        "PAYEELSTID",
        "BANKACCTTO",
        "MEMO",
        "BILLREFINFO",
        "BILLPUBINFO",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("PMTINFO")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        ET.SubElement(root, "TRNAMT").text = "313.45"
        ET.SubElement(root, "PAYEEID").text = "5112"
        ET.SubElement(root, "PAYEELSTID").text = "240"
        root.append(bk_stmt.BankaccttoTestCase.etree)
        root.append(ExtdpmtTestCase.etree)
        root.append(ExtdpmtTestCase.etree)
        ET.SubElement(root, "PAYACCT").text = "711"
        ET.SubElement(root, "DTDUE").text = "19240507000000.000[+0:UTC]"
        ET.SubElement(root, "MEMO").text = "Time's up"
        ET.SubElement(root, "BILLREFINFO").text = "Paying it"
        root.append(BillpubinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTINFO(
            ExtdpmtTestCase.aggregate,
            ExtdpmtTestCase.aggregate,
            bankacctfrom=bk_stmt.BankacctfromTestCase.aggregate,
            trnamt=Decimal("313.45"),
            payeeid="5112",
            payeelstid="240",
            bankacctto=bk_stmt.BankaccttoTestCase.aggregate,
            payacct="711",
            dtdue=datetime(1924, 5, 7, tzinfo=UTC),
            memo="Time's up",
            billrefinfo="Paying it",
            billpubinfo=BillpubinfoTestCase.aggregate,
        )

    @classproperty
    @classmethod
    def emptyBase(cls):
        root = ET.Element("PMTINFO")
        root.append(bk_stmt.BankacctfromTestCase.etree)
        ET.SubElement(root, "TRNAMT").text = "313.45"
        return root

    @classproperty
    @classmethod
    def validSoup(cls):
        payeeid = ET.Element("PAYEEID")
        payeeid.text = "5112"
        payee = bk_stmt.PayeeTestCase.etree
        extdpmt = next(ExtdpmtTestCase.validSoup)
        billpubinfo = BillpubinfoTestCase.etree
        for choice in payeeid, payee:
            root = cls.emptyBase
            root.append(choice)
            ET.SubElement(root, "PAYEELSTID").text = "240"
            acctto = bk_stmt.BankaccttoTestCase.etree
            root.append(acctto)
            for i in range(2):
                root.append(extdpmt)

            ET.SubElement(root, "PAYACCT").text = "711"
            ET.SubElement(root, "DTDUE").text = "19240507000000.000[+0:UTC]"
            ET.SubElement(root, "MEMO").text = "Time's up"
            ET.SubElement(root, "BILLREFINFO").text = "Paying it"
            root.append(billpubinfo)

            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # FIXME
        yield from ()


class DiscountTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DSCRATE", "DSCAMT", "DSCDESC"]
    optionalElements = ["DSCDATE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("DISCOUNT")
        ET.SubElement(root, "DSCRATE").text = "18"
        ET.SubElement(root, "DSCAMT").text = "13.50"
        ET.SubElement(root, "DSCDATE").text = "20170317000000.000[+0:UTC]"
        ET.SubElement(root, "DSCDESC").text = "Loyal customer discount"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return DISCOUNT(
            dscrate=Decimal("18"),
            dscamt=Decimal("13.50"),
            dscdate=datetime(2017, 3, 17, tzinfo=UTC),
            dscdesc="Loyal customer discount",
        )


class AdjustmentTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["ADJDESC", "ADJAMT"]
    optionalElements = ["ADJNO", "ADJDATE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("ADJUSTMENT")
        ET.SubElement(root, "ADJNO").text = "18"
        ET.SubElement(root, "ADJDESC").text = "We like you"
        ET.SubElement(root, "ADJAMT").text = "13.50"
        ET.SubElement(root, "ADJDATE").text = "20170317000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return ADJUSTMENT(
            adjno="18",
            adjdesc="We like you",
            adjamt=Decimal("13.50"),
            adjdate=datetime(2017, 3, 17, tzinfo=UTC),
        )


class LineitemTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["LITMAMT", "LITMDESC"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("LINEITEM")
        ET.SubElement(root, "LITMAMT").text = "13.50"
        ET.SubElement(root, "LITMDESC").text = "Purchase Item"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return LINEITEM(litmamt=Decimal("13.50"), litmdesc="Purchase Item")


class InvoiceTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVNO", "INVTOTALAMT", "INVPAIDAMT", "INVDATE", "INVDESC"]
    optionalElements = ["DISCOUNT", "ADJUSTMENT"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("INVOICE")
        ET.SubElement(root, "INVNO").text = "103"
        ET.SubElement(root, "INVTOTALAMT").text = "25"
        ET.SubElement(root, "INVPAIDAMT").text = "25"
        ET.SubElement(root, "INVDATE").text = "20150906000000.000[+0:UTC]"
        ET.SubElement(root, "INVDESC").text = "Purchase invoice"
        root.append(DiscountTestCase.etree)
        root.append(AdjustmentTestCase.etree)
        root.append(LineitemTestCase.etree)
        root.append(LineitemTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVOICE(
            LineitemTestCase.aggregate,
            LineitemTestCase.aggregate,
            invno="103",
            invtotalamt=Decimal("25"),
            invpaidamt=Decimal("25"),
            invdate=datetime(2015, 9, 6, tzinfo=UTC),
            invdesc="Purchase invoice",
            discount=DiscountTestCase.aggregate,
            adjustment=AdjustmentTestCase.aggregate,
        )


class ExtdpmtinvTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("EXTDPMTINV")
        invoice = InvoiceTestCase.etree
        root.append(invoice)
        root.append(invoice)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EXTDPMTINV(InvoiceTestCase.aggregate, InvoiceTestCase.aggregate)


class ExtdpmtTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    oneOfs = {"EXTDPMTFOR": ("INDIVIDUAL", "BUSINESS")}

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("EXTDPMT")
        ET.SubElement(root, "EXTDPMTFOR").text = "INDIVIDUAL"
        ET.SubElement(root, "EXTDPMTCHK").text = "112"
        ET.SubElement(root, "EXTDPMTDSC").text = "Here is your money"
        root.append(ExtdpmtinvTestCase.etree)
        root.append(ExtdpmtinvTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EXTDPMT(
            ExtdpmtinvTestCase.aggregate,
            ExtdpmtinvTestCase.aggregate,
            extdpmtfor="INDIVIDUAL",
            extdpmtchk="112",
            extdpmtdsc="Here is your money",
        )

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
        extdpmtinv = ExtdpmtinvTestCase.etree

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

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # Neither EXTDPMTDSC nor EXTDPMTINV
        yield cls.emptyBase


class ExtdpayeeTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    optionalElements = ["PAYEEID"]
    requiredElements = ["DAYSTOPAY"]
    oneOfs = {"IDSCOPE": ["GLOBAL", "USER"]}

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return EXTDPAYEE(
            payeeid="DEADBEEF", idscope="GLOBAL", name="Porky Pig", daystopay=30
        )

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


class PmtprcstsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["PMTPRCCODE", "DTPMTPRC"]
    oneOfs = {
        "PMTPRCCODE": (
            "WILLPROCESSON",
            "PROCESSEDON",
            "NOFUNDSON",
            "FAILEDON",
            "CANCELEDON",
        )
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("PMTPRCSTS")
        ET.SubElement(root, "PMTPRCCODE").text = "FAILEDON"
        ET.SubElement(root, "DTPMTPRC").text = "20010101000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTPRCSTS(
            pmtprccode="FAILEDON", dtpmtprc=datetime(2001, 1, 1, tzinfo=UTC)
        )


if __name__ == "__main__":
    unittest.main()
