"""Unit tests for models/common.py"""

# stdlib imports
import unittest
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement

# test imports
import base

# local imports
from ofxtools.models.i18n import CURRENCY, CURRENCY_CODES, ORIGCURRENCY
from ofxtools.utils import classproperty


class CurrencyTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["CURRATE", "CURSYM"]
    oneOfs = {"CURSYM": CURRENCY_CODES}

    @classproperty
    @classmethod
    def etree(cls):
        etree = Element("CURRENCY")
        SubElement(etree, "CURRATE").text = "59.773"
        SubElement(etree, "CURSYM").text = "EUR"
        return etree

    @classproperty
    @classmethod
    def aggregate(cls):
        return CURRENCY(currate=Decimal("59.773"), cursym="EUR")


class OrigcurrencyTestCase(CurrencyTestCase):
    @classproperty
    @classmethod
    def etree(cls):
        etree = Element("ORIGCURRENCY")
        SubElement(etree, "CURRATE").text = "59.773"
        SubElement(etree, "CURSYM").text = "EUR"
        return etree

    @classproperty
    @classmethod
    def aggregate(cls):
        return ORIGCURRENCY(currate=Decimal("59.773"), cursym="EUR")


class OrigcurrencyMixinTestCase(unittest.TestCase):
    """Test Origcurrency mixin property fallback via ORIGCURRENCY (not CURRENCY)."""

    def _make_stmttrn(self, use_origcurrency=False):
        from ofxtools.models.bank.stmt import STMTTRN
        from ofxtools.utils import UTC

        kwargs = dict(
            trntype="CHECK",
            dtposted=__import__("datetime").datetime(2013, 6, 15, tzinfo=UTC),
            trnamt=Decimal("-433.25"),
            fitid="DEADBEEF",
        )
        if use_origcurrency:
            kwargs["origcurrency"] = ORIGCURRENCY(
                currate=Decimal("59.773"), cursym="EUR"
            )
        else:
            kwargs["currency"] = CURRENCY(currate=Decimal("59.773"), cursym="EUR")
        return STMTTRN(**kwargs)

    def test_curtype_via_origcurrency(self):
        trn = self._make_stmttrn(use_origcurrency=True)
        self.assertEqual(trn.curtype, "ORIGCURRENCY")

    def test_cursym_via_origcurrency(self):
        trn = self._make_stmttrn(use_origcurrency=True)
        self.assertEqual(trn.cursym, "EUR")

    def test_currate_via_origcurrency(self):
        trn = self._make_stmttrn(use_origcurrency=True)
        self.assertEqual(trn.currate, Decimal("59.773"))

    def test_curtype_none_when_no_currency(self):
        from ofxtools.models.bank.stmt import STMTTRN
        from ofxtools.utils import UTC

        trn = STMTTRN(
            trntype="CHECK",
            dtposted=__import__("datetime").datetime(2013, 6, 15, tzinfo=UTC),
            trnamt=Decimal("-433.25"),
            fitid="DEADBEEF",
        )
        self.assertIsNone(trn.curtype)
        self.assertIsNone(trn.cursym)
        self.assertIsNone(trn.currate)


if __name__ == "__main__":
    unittest.main()
