# coding: utf-8
""" Unit tests for ofxtools.models.seclist """

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.invest.securities import (
    ASSETCLASSES,
    SECID,
    SECINFO,
    DEBTINFO,
    MFINFO,
    OPTINFO,
    OTHERINFO,
    STOCKINFO,
    PORTION,
    FIPORTION,
    MFASSETCLASS,
    FIMFASSETCLASS,
    SECLIST,
    SECRQ,
    SECLISTRQ,
    SECLISTRS,
    SECLISTTRNRQ,
    SECLISTTRNRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_i18n as i18n


class SecidTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["UNIQUEID", "UNIQUEIDTYPE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECID")
        SubElement(root, "UNIQUEID").text = "084670108"
        SubElement(root, "UNIQUEIDTYPE").text = "CUSIP"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECID(uniqueid="084670108", uniqueidtype="CUSIP")


class SecinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECID", "SECNAME"]
    optionalElements = ["TICKER", "FIID", "RATING", "UNITPRICE", "DTASOF", "CURRENCY"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECINFO")
        root.append(SecidTestCase.etree)
        SubElement(root, "SECNAME").text = "Acme Development, Inc."
        SubElement(root, "TICKER").text = "ACME"
        SubElement(root, "FIID").text = "AC.ME"
        SubElement(root, "RATING").text = "Aa"
        SubElement(root, "UNITPRICE").text = "94.5"
        SubElement(root, "DTASOF").text = "20130615000000.000[+0:UTC]"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "MEMO").text = "Foobar"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECINFO(
            secid=SecidTestCase.aggregate,
            secname="Acme Development, Inc.",
            ticker="ACME",
            fiid="AC.ME",
            rating="Aa",
            unitprice=Decimal("94.5"),
            dtasof=datetime(2013, 6, 15, tzinfo=UTC),
            currency=i18n.CurrencyTestCase.aggregate,
            memo="Foobar",
        )

    def testConvertSecnameTooLong(self):
        """Don't enforce length restriction on SECNAME; raise Warning"""
        # Issue #12
        root = self.etree
        root[
            1
        ].text = """
        There is a theory going around that the U.S.A. was and still is a
        gigantic Masonic plot under the ultimate control of the group known as
        the Illuminati. It is difficult to look for long at the strange single
        eye crowning the pyramid which is found on every dollar bill and not
        begin to believe the story, a little. Too many anarchists in
        19th-century Europe — Bakunin, Proudhon, Salverio Friscia — were Masons
        for it to be pure chance. Lovers of global conspiracy, not all of them
        Catholic, can count on the Masons for a few good shivers and voids when
        all else fails.
        """
        with self.assertWarns(Warning):
            instance = Aggregate.from_etree(root)
        self.assertEqual(
            instance.secname,
            """
        There is a theory going around that the U.S.A. was and still is a
        gigantic Masonic plot under the ultimate control of the group known as
        the Illuminati. It is difficult to look for long at the strange single
        eye crowning the pyramid which is found on every dollar bill and not
        begin to believe the story, a little. Too many anarchists in
        19th-century Europe — Bakunin, Proudhon, Salverio Friscia — were Masons
        for it to be pure chance. Lovers of global conspiracy, not all of them
        Catholic, can count on the Masons for a few good shivers and voids when
        all else fails.
        """,
        )

    def testConvertTickerTooLong(self):
        """Don't enforce length restriction on TICKER; raise Warning"""
        # Issue #12
        root = deepcopy(self.etree)
        root[
            2
        ].text = """
        Kekulé dreams the Great Serpent holding its own tail in its mouth, the
        dreaming Serpent which surrounds the World.  But the meanness, the
        cynicism with which this dream is to be used. The Serpent that
        announces, "The World is a closed thing, cyclical, resonant,
        eternally-returning," is to be delivered into a system whose only aim
        is to violate the Cycle. Taking and not giving back, demanding that
        "productivity" and "earnings" keep on increasing with time, the System
        removing from the rest of the World these vast quantities of energy to
        keep its own tiny desperate fraction showing a profit: and not only
        most of humanity — most of the World, animal, vegetable, and mineral,
        is laid waste in the process. The System may or may not understand that
        it's only buying time. And that time is an artificial resource to begin
        with, of no value to anyone or anything but the System, which must
        sooner or later crash to its death, when its addiction to energy has
        become more than the rest of the World can supply, dragging with it
        innocent souls all along the chain of life.
        """
        with self.assertWarns(Warning):
            instance = Aggregate.from_etree(root)
        self.assertEqual(
            instance.ticker,
            """
        Kekulé dreams the Great Serpent holding its own tail in its mouth, the
        dreaming Serpent which surrounds the World.  But the meanness, the
        cynicism with which this dream is to be used. The Serpent that
        announces, "The World is a closed thing, cyclical, resonant,
        eternally-returning," is to be delivered into a system whose only aim
        is to violate the Cycle. Taking and not giving back, demanding that
        "productivity" and "earnings" keep on increasing with time, the System
        removing from the rest of the World these vast quantities of energy to
        keep its own tiny desperate fraction showing a profit: and not only
        most of humanity — most of the World, animal, vegetable, and mineral,
        is laid waste in the process. The System may or may not understand that
        it's only buying time. And that time is an artificial resource to begin
        with, of no value to anyone or anything but the System, which must
        sooner or later crash to its death, when its addiction to energy has
        become more than the rest of the World can supply, dragging with it
        innocent souls all along the chain of life.
        """,
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secid.uniqueidtype)


class DebtinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECINFO", "PARVALUE", "DEBTTYPE"]
    optionalElements = [
        "DEBTCLASS",
        "COUPONRT",
        "DTCOUPON",
        "COUPONFREQ",
        "CALLPRICE",
        "YIELDTOCALL",
        "DTCALL",
        "CALLTYPE",
        "YIELDTOMAT",
        "DTMAT",
        "ASSETCLASS",
        "FIASSETCLASS",
    ]
    oneOfs = {
        "DEBTTYPE": ("COUPON", "ZERO"),
        "DEBTCLASS": ("TREASURY", "MUNICIPAL", "CORPORATE", "OTHER"),
        "COUPONFREQ": ("MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL", "OTHER"),
        "CALLTYPE": ("CALL", "PUT", "PREFUND", "MATURITY"),
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("DEBTINFO")
        secinfo = SecinfoTestCase.etree
        root.append(secinfo)
        SubElement(root, "PARVALUE").text = "1000"
        SubElement(root, "DEBTTYPE").text = "COUPON"
        SubElement(root, "DEBTCLASS").text = "CORPORATE"
        SubElement(root, "COUPONRT").text = "5.125"
        SubElement(root, "DTCOUPON").text = "20031201000000.000[+0:UTC]"
        SubElement(root, "COUPONFREQ").text = "QUARTERLY"
        SubElement(root, "CALLPRICE").text = "1000"
        SubElement(root, "YIELDTOCALL").text = "6.5"
        SubElement(root, "DTCALL").text = "20051215000000.000[+0:UTC]"
        SubElement(root, "CALLTYPE").text = "CALL"
        SubElement(root, "YIELDTOMAT").text = "6.0"
        SubElement(root, "DTMAT").text = "20061215000000.000[+0:UTC]"
        SubElement(root, "ASSETCLASS").text = "INTLBOND"
        SubElement(root, "FIASSETCLASS").text = "Fixed to floating bond"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return DEBTINFO(
            secinfo=SecinfoTestCase.aggregate,
            parvalue=Decimal("1000"),
            debttype="COUPON",
            debtclass="CORPORATE",
            couponrt=Decimal("5.125"),
            dtcoupon=datetime(2003, 12, 1, tzinfo=UTC),
            couponfreq="QUARTERLY",
            callprice=Decimal("1000"),
            yieldtocall=Decimal("6.5"),
            dtcall=datetime(2005, 12, 15, tzinfo=UTC),
            calltype="CALL",
            yieldtomat=Decimal("6.0"),
            dtmat=datetime(2006, 12, 15, tzinfo=UTC),
            assetclass="INTLBOND",
            fiassetclass="Fixed to floating bond",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secinfo.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secinfo.secid.uniqueidtype)


class PortionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True
    OneOfs = {"ASSETCLASS": ASSETCLASSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PORTION")
        SubElement(root, "ASSETCLASS").text = "DOMESTICBOND"
        SubElement(root, "PERCENT").text = "15"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PORTION(assetclass="DOMESTICBOND", percent=Decimal("15"))


class MfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFASSETCLASS")
        for i in range(4):
            portion = PortionTestCase.etree
            root.append(portion)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFASSETCLASS(
            PortionTestCase.aggregate,
            PortionTestCase.aggregate,
            PortionTestCase.aggregate,
            PortionTestCase.aggregate,
        )


class FiportionTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("FIPORTION")
        SubElement(root, "FIASSETCLASS").text = "Foobar"
        SubElement(root, "PERCENT").text = "50"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return FIPORTION(fiassetclass="Foobar", percent=Decimal("50"))


class FimfassetclassTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("FIMFASSETCLASS")
        for i in range(4):
            portion = FiportionTestCase.etree
            root.append(portion)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return FIMFASSETCLASS(
            FiportionTestCase.aggregate,
            FiportionTestCase.aggregate,
            FiportionTestCase.aggregate,
            FiportionTestCase.aggregate,
        )


class MfinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECINFO"]
    optionalElements = [
        "MFTYPE",
        "YIELD",
        "DTYIELDASOF",
        "MFASSETCLASS",
        "FIMFASSETCLASS",
    ]
    oneOfs = {"MFTYPE": ("OPENEND", "CLOSEEND", "OTHER")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MFINFO")
        root.append(SecinfoTestCase.etree)
        SubElement(root, "MFTYPE").text = "OPENEND"
        SubElement(root, "YIELD").text = "5.0"
        SubElement(root, "DTYIELDASOF").text = "20030501000000.000[+0:UTC]"
        root.append(MfassetclassTestCase.etree)
        root.append(FimfassetclassTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MFINFO(
            secinfo=SecinfoTestCase.aggregate,
            mftype="OPENEND",
            yld=Decimal("5.0"),
            dtyieldasof=datetime(2003, 5, 1, tzinfo=UTC),
            mfassetclass=MfassetclassTestCase.aggregate,
            fimfassetclass=FimfassetclassTestCase.aggregate,
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secinfo.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secinfo.secid.uniqueidtype)


class OptinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECINFO", "OPTTYPE", "STRIKEPRICE", "DTEXPIRE", "SHPERCTRCT"]
    optionalElements = ["SECID", "ASSETCLASS", "FIASSETCLASS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("OPTINFO")
        root.append(SecinfoTestCase.etree)
        SubElement(root, "OPTTYPE").text = "CALL"
        SubElement(root, "STRIKEPRICE").text = "25.5"
        SubElement(root, "DTEXPIRE").text = "20031215000000.000[+0:UTC]"
        SubElement(root, "SHPERCTRCT").text = "100"
        root.append(SecidTestCase.etree)
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OPTINFO(
            secinfo=SecinfoTestCase.aggregate,
            opttype="CALL",
            strikeprice=Decimal("25.5"),
            dtexpire=datetime(2003, 12, 15, tzinfo=UTC),
            shperctrct=100,
            secid=SecidTestCase.aggregate,
            assetclass="SMALLSTOCK",
            fiassetclass="FOO",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secinfo.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secinfo.secid.uniqueidtype)


class OtherinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECINFO"]
    optionalElements = ["TYPEDESC", "ASSETCLASS", "FIASSETCLASS"]
    oneOfs = {"ASSETCLASS": ASSETCLASSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("OTHERINFO")
        secinfo = SecinfoTestCase.etree
        root.append(secinfo)
        SubElement(root, "TYPEDESC").text = "Securitized baseball card pool"
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return OTHERINFO(
            secinfo=SecinfoTestCase.aggregate,
            typedesc="Securitized baseball card pool",
            assetclass="SMALLSTOCK",
            fiassetclass="FOO",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secinfo.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secinfo.secid.uniqueidtype)


class StockinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECINFO"]
    optionalElements = [
        "STOCKTYPE",
        "YIELD",
        "DTYIELDASOF",
        "ASSETCLASS",
        "FIASSETCLASS",
    ]
    oneOfs = {"ASSETCLASS": ASSETCLASSES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("STOCKINFO")
        secinfo = SecinfoTestCase.etree
        root.append(secinfo)
        SubElement(root, "STOCKTYPE").text = "CONVERTIBLE"
        SubElement(root, "YIELD").text = "5.0"
        SubElement(root, "DTYIELDASOF").text = "20030501000000.000[+0:UTC]"
        SubElement(root, "ASSETCLASS").text = "SMALLSTOCK"
        SubElement(root, "FIASSETCLASS").text = "FOO"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return STOCKINFO(
            secinfo=SecinfoTestCase.aggregate,
            stocktype="CONVERTIBLE",
            yld=Decimal("5.0"),
            dtyieldasof=datetime(2003, 5, 1, tzinfo=UTC),
            assetclass="SMALLSTOCK",
            fiassetclass="FOO",
        )

    def testPropertyAliases(self):
        instance = Aggregate.from_etree(self.etree)
        self.assertEqual(instance.uniqueid, instance.secinfo.secid.uniqueid)
        self.assertEqual(instance.uniqueidtype, instance.secinfo.secid.uniqueidtype)


class SeclistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLIST")
        root.append(DebtinfoTestCase.etree)
        root.append(MfinfoTestCase.etree)
        root.append(OptinfoTestCase.etree)
        root.append(OtherinfoTestCase.etree)
        root.append(StockinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLIST(
            DebtinfoTestCase.aggregate,
            MfinfoTestCase.aggregate,
            OptinfoTestCase.aggregate,
            OtherinfoTestCase.aggregate,
            StockinfoTestCase.aggregate,
        )


class SecrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        return next(cls.validSoup)

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECRQ(secid=SecidTestCase.aggregate)

    @classproperty
    @classmethod
    def validSoup(cls):
        secid = SecidTestCase.etree
        ticker = Element("TICKER")
        ticker.text = "ABCD"
        fiid = Element("FIID")
        fiid.text = "A1B2C3D4"

        for choice in secid, ticker, fiid:
            root = Element("SECRQ")
            root.append(choice)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        #  requiredMutexes = [('secid', 'ticker', 'fiid')]
        secid = SecidTestCase.etree
        ticker = Element("TICKER")
        ticker.text = "ABCD"
        fiid = Element("FIID")
        fiid.text = "A1B2C3D4"

        #  None
        root = Element("SECRQ")
        yield root

        #  Two
        for (choice0, choice1) in [(secid, ticker), (secid, fiid), (ticker, fiid)]:
            root = Element("SECRQ")
            root.append(choice0)
            root.append(choice1)
            yield root

        # All three
        root = Element("SECRQ")
        root.append(secid)
        root.append(ticker)
        root.append(fiid)
        yield root

        #  FIXME - Check out-of-order errors


class SeclistrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("SECLISTRQ")
        for i in range(2):
            root.append(SecrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTRQ(SecrqTestCase.aggregate, SecrqTestCase.aggregate)


class SeclistrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        return Element("SECLISTRS")

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTRS()


class SeclisttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = SeclistrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            seclistrq=SeclistrqTestCase.aggregate,
        )


class SeclisttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = SeclistrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return SECLISTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            seclistrs=SeclistrsTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
