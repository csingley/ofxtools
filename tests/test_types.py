# coding: utf-8

import unittest
import decimal
import datetime

import ofxtools


class Base:
    def test_required(self):
        t = self.type_(required=True)
        # If required, missing value (i.e. None) is illegal
        with self.assertRaises(ValueError):
            t.convert(None)

    def test_optional(self):
        t = self.type_(required=False)
        # If not required, missing value (i.e. None) returns None
        self.assertEqual(t.convert(None), None)


class BoolTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.Bool

    def test_convert(self):
        t = self.type_()
        # Per OFX spec, 'Y' converts to True
        self.assertTrue(t.convert('Y'))
        # Per OFX spec, 'N' converts to False
        self.assertFalse(t.convert('N'))
        # All other inputs (except None) are illegal
        for illegal in (True, False, 0, 1):
            with self.assertRaises(ValueError):
                t.convert(illegal)

    def test_unconvert(self):
        t = self.type_()
        # Per OFX spec, 'Y' converts to True
        self.assertEqual(t.unconvert(True), 'Y')
        # Per OFX spec, 'N' converts to False
        self.assertEqual(t.unconvert(False), 'N')
        # All other inputs (except None) are illegal
        for illegal in ('Y', 'N', 0, 1):
            with self.assertRaises(ValueError):
                t.unconvert(illegal)


class StringTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.String

    def test_convert(self):
        t = self.type_()
        self.assertEqual('foo', t.convert('foo'))
        self.assertEqual('123', t.convert(123))

    def test_max_length(self):
        t = self.type_(5)
        self.assertEqual('foo', t.convert('foo'))
        with self.assertRaises(ValueError):
            t.convert('foobar')

    def test_empty_string(self):
        # Empty string interpreted as None
        t = self.type_(required=True)
        with self.assertRaises(ValueError):
            t.convert('')
        t = self.type_(required=False)
        self.assertEqual(t.convert(''), None)


class OneOfTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.OneOf

    def test_convert(self):
        t = self.type_('A', 'B')
        self.assertEqual('A', t.convert('A'))
        self.assertEqual('B', t.convert('B'))
        with self.assertRaises(ValueError):
            t.convert('C')


class IntegerTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.Integer

    def test_convert(self):
        t = self.type_()
        self.assertEqual(1, t.convert(1))
        self.assertEqual(1, t.convert('1'))
        self.assertEqual(1, t.convert(decimal.Decimal('1.00')))

    def test_max_length(self):
        t = self.type_(2)
        self.assertEqual(1, t.convert('1'))
        with self.assertRaises(ValueError):
            t.convert('100')


class DecimalTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.Decimal

    def test_convert(self):
        t = self.type_()
        self.assertEqual(1, t.convert(1))
        self.assertEqual(1, t.convert('1'))
        self.assertEqual(1, t.convert(decimal.Decimal('1.00')))

    def test_precision(self):
        # Default precision is 2
        t = self.type_()
        cmp = decimal.Decimal('100.00').compare_total(t.convert('100'))
        self.assertEqual(cmp, 0)
        # Test nondefault precision
        t = self.type_(4)
        cmp = decimal.Decimal('100.0000').compare_total(t.convert('100'))
        self.assertEqual(cmp, 0)

    def test_euro_decimal_separator(self):
        t = self.type_()
        self.assertEqual(decimal.Decimal('1.23'), t.convert('1,23'))


class DateTimeTestCase(unittest.TestCase, Base):
    type_ = ofxtools.types.DateTime

    def test_convert(self):
        t = self.type_()
        # Accept datetime
        dt = datetime.datetime(2011, 11, 17, 3, 30, 45, 150)
        self.assertEqual(dt, t.convert(dt))
        # Accept date
        d = datetime.date(2011, 11, 17)
        check = datetime.datetime(2011, 11, 17, 0, 0, 0, 0)
        self.assertEqual(check, t.convert(d))
        # Accept YYYYMMDD
        check = datetime.datetime(2011, 11, 17, 0, 0, 0, 0)
        self.assertEqual(check, t.convert('20111117'))
        # Accept YYYYMMDDHHMM
        check = datetime.datetime(2011, 11, 17, 3, 30, 0, 0)
        self.assertEqual(check, t.convert('201111170330'))
        # Accept YYYYMMDDHHMMSS
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 0)
        self.assertEqual(check, t.convert('20111117033045'))
        # Accept YYYYMMDDHHMMSS.XXX
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 150)
        self.assertEqual(check, t.convert('20111117033045.150'))


