# coding: utf-8
""" Unit tests for ofxtools.Types """
# stdlib imports
import unittest
import decimal
import datetime
import warnings


# local imports
import ofxtools
from ofxtools.Types import OFXTypeWarning
from ofxtools.utils import UTC


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
    type_ = ofxtools.Types.Bool

    def test_convert(self):
        t = self.type_()
        # Per OFX spec, 'Y' converts to True; 'N' converts to False
        self.assertTrue(t.convert('Y'))
        self.assertFalse(t.convert('N'))

        # To allow creating Aggregates directly via Aggregate.__init__()
        # rather than forcing them to be parsed via Aggregate.from_etree(),
        # we pass Python types True/False/none
        self.assertEqual(t.convert(True), True)
        self.assertEqual(t.convert(False), False)
        self.assertEqual(t.convert(None), None)

        # All other inputs are illegal
        for illegal in (0, 1, 'y', 'n'):
            with self.assertRaises(ValueError):
                t.convert(illegal)

    def test_unconvert(self):
        t = self.type_()
        # Per OFX spec, 'Y' converts to True; 'N' converts to False
        self.assertEqual(t.unconvert(True), 'Y')
        self.assertEqual(t.unconvert(False), 'N')

        # Pass None
        self.assertEqual(t.unconvert(None), None)

        # All other inputs are illegal
        for illegal in ('Y', 'N', 0, 1):
            with self.assertRaises(ValueError):
                t.unconvert(illegal)


class StringTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.String

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


class NagstringTestCase(StringTestCase):
    type_ = ofxtools.Types.NagString

    def test_max_length(self):
        t = self.type_(5)
        self.assertEqual('foo', t.convert('foo'))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            t.convert('foobar')
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, OFXTypeWarning)


class OneOfTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.OneOf

    def test_convert(self):
        t = self.type_('1', '2')
        self.assertEqual('1', t.convert('1'))
        self.assertEqual('2', t.convert('2'))
        self.assertEqual(None, t.convert(''))
        with self.assertRaises(ValueError):
            t.convert('3')
        with self.assertRaises(ValueError):
            t.convert(1)


class IntegerTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.Integer

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

    def test_illegal(self):
        t = self.type_()
        # Don't accept strings that can't be converted to int
        with self.assertRaises(ValueError):
            t.convert('foobar')


class DecimalTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.Decimal

    def test_convert(self):
        t = self.type_()
        self.assertEqual(1, t.convert(1))
        self.assertEqual(1, t.convert('1'))
        self.assertEqual(1, t.convert(decimal.Decimal('1.00')))

    def test_precision(self):
        # By default (no precision specified), convert() doesn't quantize
        t = self.type_()
        cmp = decimal.Decimal('100.00').compare_total(t.convert('100'))
        self.assertNotEqual(cmp, 0)
        # Test nondefault precision
        t = self.type_(4)
        cmp = decimal.Decimal('100.0000').compare_total(t.convert('100'))
        self.assertEqual(cmp, 0)

    def test_euro_decimal_separator(self):
        t = self.type_()
        self.assertEqual(decimal.Decimal('1.23'), t.convert('1,23'))
        # Separators other than . and , are illegal
        with self.assertRaises(decimal.InvalidOperation):
            t.convert('1:23')

    def test_illegal(self):
        t = self.type_()
        # Don't accept strings that can't be converted to Decimal
        with self.assertRaises(decimal.InvalidOperation):
            t.convert('foobar')
        # Don't accept random types
        with self.assertRaises(TypeError):
            t.convert(object)


class DateTimeTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.DateTime

    def test_convert(self):
        t = self.type_()
        # Accept timezone-aware datetime
        dt = datetime.datetime(2011, 11, 17, 3, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(dt, t.convert(dt))
        # Accept YYYYMMDD
        check = datetime.datetime(2011, 11, 17, 0, 0, 0, 0, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117'))
        # Accept YYYYMMDDHHMM
        check = datetime.datetime(2011, 11, 17, 3, 30, 0, 0, tzinfo=UTC)
        self.assertEqual(check, t.convert('201111170330'))
        # Accept YYYYMMDDHHMMSS
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 0, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117033045'))
        # Accept YYYYMMDDHHMMSS.XXX
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117033045.150'))

        # Accept YYYYMMDDHHMMSS.XXX[offset]
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117033045.150[-6]'))
        # Accept YYYYMMDDHHMMSS.XXX[offset:TZ]
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117033045.150[-6:CST]'))
        # Accept YYYYMMDDHHMMSS.XXX[-:TZ] for TZs defined in the kludge
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(check, t.convert('20111117033045.150[-:CST]'))

    def test_convert_illegal(self):
        t = self.type_()
        # Don't accept timezone-naive datetime
        with self.assertRaises(ValueError):
            t.convert(datetime.datetime(2011, 11, 17, 3, 30, 45, 150))
        # Don't accept date
        with self.assertRaises(ValueError):
            t.convert(datetime.date(2011, 11, 17))
        # Don't accept strings of the wrong length
        with self.assertRaises(ValueError):
            t.convert('2015129')
        # Don't accept strings of the wrong format
        with self.assertRaises(ValueError):
            t.convert('20151A29')
        # Don't accept integer
        with self.assertRaises(ValueError):
            t.convert(123)
        # Don't accept YYYYMMDDHHMMSS.XXX[-:TZ] for TZs not defined in kludge
        with self.assertRaises(ValueError):
            t.convert('20111117033045.150[-:GMT]')

    def test_unconvert(self):
        t = self.type_()
        check = datetime.datetime(2007, 1, 1, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), '20070101000000')

    def test_unconvert_illegal(self):
        t = self.type_()
        # Don't accept timezone-naive datetime
        with self.assertRaises(ValueError):
            t.convert(datetime.datetime(2011, 11, 17, 3, 30, 45, 150))
        # Don't accept date
        with self.assertRaises(ValueError):
            t.convert(datetime.date(2011, 11, 17))
        # Don't accept string
        with self.assertRaises(ValueError):
            t.unconvert('20070101')

    def test_convert_roundtrip(self):
        t = self.type_()
        original = '20070101'
        result = '20070101000000'
        self.assertEqual(t.unconvert(t.convert(original)), result)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        original = datetime.datetime(2007, 1, 1, tzinfo=UTC)
        result = original
        self.assertEqual(t.convert(t.unconvert(original)), result)


if __name__ == '__main__':
    unittest.main()
