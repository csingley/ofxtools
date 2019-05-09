# coding: utf-8
""" Unit tests for models/common.py """
# stdlib imports
import unittest
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.i18n import CURRENCY, ORIGCURRENCY, CURRENCY_CODES
from ofxtools.utils import classproperty


# test imports
import base


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


if __name__ == "__main__":
    unittest.main()
