# coding: utf-8
""" Unit tests for ofxtools.Types """
# stdlib imports
import unittest
import decimal
import datetime
import warnings
from typing import Optional


# local imports
import ofxtools
from ofxtools.Types import OFXTypeWarning, OFXSpecError
from ofxtools.utils import UTC


class ElementTestCase(unittest.TestCase):
    def testInit(self):
        """
        Element base class __init__() accepts only single ``required`` kwarg
        """
        ofxtools.Types.Element(required=False)  # Succeeds

        with self.assertRaises(TypeError):
            ofxtools.Types.Element(1, required=False)

        with self.assertRaises(TypeError):
            ofxtools.Types.Element(required=False, otherarg=5)

    def testConvert(self):
        with self.assertRaises(NotImplementedError):
            instance = ofxtools.Types.Element(required=True)
            instance.convert(None)

    def testRepr(self):
        instance = ofxtools.Types.Element(required=True)
        rep = repr(instance)
        self.assertEqual(rep, "<Element required=True>")


class Base:
    """Common tests for Element subclasses"""

    def test_required(self):
        t = self.type_(required=True)
        # If required, missing value (i.e. None) is illegal
        with self.assertRaises(OFXSpecError):
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
        self.assertTrue(t.convert("Y"))
        self.assertFalse(t.convert("N"))

        # To allow creating Aggregates directly via Aggregate.__init__()
        # rather than forcing them to be parsed via Aggregate.from_etree(),
        # we pass Python types True/False/none
        self.assertEqual(t.convert(True), True)
        self.assertEqual(t.convert(False), False)
        self.assertEqual(t.convert(None), None)

        # All other inputs are illegal
        for illegal in (0, 1, "y", "n"):
            with self.assertRaises(OFXSpecError):
                t.convert(illegal)
        for illegal in (
            0,
            1,
            "y",
            "n",
            123,
            decimal.Decimal("1"),
            datetime.datetime(1999, 9, 9),
            datetime.time(12, 12, 12),
        ):
            with self.assertRaises(OFXSpecError):
                t.convert(illegal)

    def test_unconvert(self):
        t = self.type_()
        # Per OFX spec, 'Y' converts to True; 'N' converts to False
        self.assertEqual(t.unconvert(True), "Y")
        self.assertEqual(t.unconvert(False), "N")

        # Pass None
        self.assertEqual(t.unconvert(None), None)

        # All other inputs are illegal
        for illegal in ("Y", "N", 0, 1):
            with self.assertRaises(OFXSpecError):
                t.unconvert(illegal)

    def test_convert_roundtrip(self):
        t = self.type_()
        value = "N"
        self.assertEqual(t.unconvert(t.convert(value)), value)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        value = True
        self.assertEqual(t.convert(t.unconvert(value)), value)


class StringTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.String

    def test_convert(self):
        t = self.type_()
        # Pass string
        self.assertEqual("foo", t.convert("foo"))
        # Pass None
        self.assertEqual(None, t.convert(None))
        # Interpret empty string as None
        self.assertEqual(None, t.convert(""))
        # Don't pass non-string
        for illegal in (
            True,
            123,
            decimal.Decimal("1"),
            datetime.datetime(1999, 9, 9),
            datetime.time(12, 12, 12),
        ):
            with self.assertRaises(TypeError):
                t.convert(illegal)

    def test_unescape(self):
        # Issue # 28

        # Unescape '&amp;' '&lt;' '&gt;' '&nbsp;' per OFX section 2.3
        t = self.type_()
        self.assertEqual("rock&roll", t.convert("rock&amp;roll"))
        self.assertEqual("<3", t.convert("&lt;3"))
        self.assertEqual("->", t.convert("-&gt;"))
        self.assertEqual("splish splash", t.convert("splish&nbsp;splash"))

        # Also unescape the other XML control characters, ie. '&apos;' '&quot;'
        # because FIs don't read the spec
        self.assertEqual(
            "We didn't read the OFX spec", t.convert("We didn&apos;t read the OFX spec")
        )
        self.assertEqual(
            '"No soup for you!"', t.convert("&quot;No soup for you!&quot;")
        )

    def test_max_length(self):
        t = self.type_(5)
        self.assertEqual("foo", t.convert("foo"))
        with self.assertRaises(OFXSpecError):
            t.convert("foobar")

    def test_empty_string(self):
        # Empty string interpreted as None
        t = self.type_(required=True)
        with self.assertRaises(OFXSpecError):
            t.convert("")
        t = self.type_(required=False)
        self.assertEqual(t.convert(""), None)

    def test_unconvert(self):
        t = self.type_()
        # Pass string
        s = "漢字"
        self.assertEqual(s, t.unconvert(s))
        # Pass None
        self.assertEqual(None, t.unconvert(None))

        # Validator behavior for ``unconvert()``
        t = self.type_(10, required=True)
        # required=True + value=None -> OFXSpecError
        with self.assertRaises(OFXSpecError):
            t.unconvert(None)
        # value > length constraint -> OFXSpecError
        with self.assertRaises(OFXSpecError):
            t.unconvert("My car is fast, my teeth are shiny")

        # Don't pass non-string
        for illegal in (
            True,
            123,
            decimal.Decimal("1"),
            datetime.datetime(1999, 9, 9),
            datetime.time(12, 12, 12),
        ):
            with self.assertRaises(TypeError):
                t.unconvert(illegal)

    def test_convert_roundtrip(self):
        t = self.type_()
        value = "漢字"
        self.assertEqual(t.unconvert(t.convert(value)), value)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        value = "漢字"
        self.assertEqual(t.convert(t.unconvert(value)), value)


class NagstringTestCase(StringTestCase):
    type_ = ofxtools.Types.NagString

    def test_max_length(self):
        t = self.type_(5)
        self.assertEqual("foo", t.convert("foo"))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t.convert("foobar")
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, OFXTypeWarning)

    def test_unconvert(self):
        t = self.type_()
        # Pass string
        s = "漢字"
        self.assertEqual(s, t.unconvert(s))
        # Pass None
        self.assertEqual(None, t.unconvert(None))

        # Validator behavior for ``unconvert()``
        t = self.type_(10, required=True)
        # required=True + value=None -> OFXSpecError
        with self.assertRaises(OFXSpecError):
            t.unconvert(None)
        # value > length constraint -> OFXTypeWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t.unconvert("My car is fast, my teeth are shiny")
            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, OFXTypeWarning)


class OneOfTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.OneOf

    def test_convert(self):
        t = self.type_("1", "2")
        self.assertEqual("1", t.convert("1"))
        self.assertEqual("2", t.convert("2"))
        self.assertEqual(None, t.convert(""))
        with self.assertRaises(OFXSpecError):
            t.convert("3")
        with self.assertRaises(OFXSpecError):
            t.convert(1)

    def test_unconvert(self):
        t = self.type_("1", "2")
        # Pass enum
        self.assertEqual("1", t.unconvert("1"))
        self.assertEqual("2", t.unconvert("2"))
        # Pass None
        self.assertEqual(None, t.unconvert(None))

        # Validator behavior for ``unconvert()``
        t = self.type_("1", "2", required=True)
        # required=True + value=None -> OFXSpecError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(OFXSpecError):
            t.unconvert(None)
        # value not in enum -> OFXSpecError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(OFXSpecError):
            t.unconvert("3")

    def test_convert_roundtrip(self):
        t = self.type_("1", "2")
        value = "1"
        self.assertEqual(t.unconvert(t.convert(value)), value)

    def test_unconvert_roundtrip(self):
        t = self.type_("1", "2")
        value = "1"
        self.assertEqual(t.convert(t.unconvert(value)), value)


class IntegerTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.Integer

    def test_convert(self):
        t = self.type_()
        self.assertEqual(None, t.convert(None))
        self.assertEqual(None, t.convert(""))
        self.assertEqual(1, t.convert(1))
        self.assertEqual(1, t.convert("1"))
        self.assertEqual(1, t.convert(decimal.Decimal("1.00")))

        # Don't accept strings that can't be converted to int
        with self.assertRaises(ValueError):
            t.convert("foobar")

    def test_max_length(self):
        t = self.type_(2)
        self.assertEqual(1, t.convert("1"))
        with self.assertRaises(OFXSpecError):
            t.convert("100")

    def test_unconvert(self):
        t = self.type_()
        # integer -> string
        self.assertEqual(t.unconvert(1), "1")
        self.assertEqual(t.unconvert(999999), "999999")
        # Pass None
        self.assertEqual(None, t.unconvert(None))

        # Validator behavior for ``unconvert()``
        t = self.type_(2, required=True)
        # type(value) is not int -> TypeError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(TypeError):
            t.unconvert(decimal.Decimal("1"))
        # required=True + value=None -> OFXSpecError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(OFXSpecError):
            t.unconvert(None)
        # value has more digits than length constraint -> OFXSpecError
        # (never should have been allowed by ``__set__()`` in the first place)
        with self.assertRaises(OFXSpecError):
            t.unconvert(123)

    def test_convert_roundtrip(self):
        t = self.type_()
        value = "2152"
        self.assertEqual(t.unconvert(t.convert(value)), value)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        value = 2152
        self.assertEqual(t.convert(t.unconvert(value)), value)


class DecimalTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.Decimal

    def test_convert(self):
        t = self.type_()
        self.assertEqual(1, t.convert(1))
        self.assertEqual(1, t.convert("1"))
        self.assertEqual(1, t.convert(decimal.Decimal("1.00")))

    def test_scale(self):
        # By default (no scale specified), convert() doesn't quantize
        t = self.type_()
        cmp = decimal.Decimal("100.00").compare_total(t.convert("100"))
        self.assertNotEqual(cmp, 0)
        # Test nondefault scale
        t = self.type_(4)
        cmp = decimal.Decimal("100.0000").compare_total(t.convert("100"))
        self.assertEqual(cmp, 0)
        cmp = decimal.Decimal("100.0000").compare_total(
            t.convert(decimal.Decimal("100"))
        )
        self.assertEqual(cmp, 0)

    def test_euro_decimal_separator(self):
        # Issue #4
        t = self.type_()
        self.assertEqual(decimal.Decimal("1.23"), t.convert("1,23"))
        # Separators other than . and , are illegal
        with self.assertRaises(decimal.InvalidOperation):
            t.convert("1:23")

    def test_illegal(self):
        t = self.type_()
        # Don't accept strings that can't be converted to Decimal
        with self.assertRaises(decimal.InvalidOperation):
            t.convert("foobar")
        # Don't accept random types
        with self.assertRaises(TypeError):
            t.convert(object)

    def test_unconvert(self):
        t = self.type_()
        # decimal -> string
        check = decimal.Decimal("21.52")
        self.assertEqual(t.unconvert(check), "21.52")
        # Pass None
        self.assertEqual(None, t.unconvert(None))

        # Validator behavior for ``unconvert()``
        t = self.type_(2, required=True)
        # type(value) is not decimal -> TypeError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(TypeError):
            t.unconvert(1)
        # required=True + value=None -> OFXSpecError (never should have been
        # allowed by ``__set__()`` in the first place)
        with self.assertRaises(OFXSpecError):
            t.unconvert(None)
        # value doesn't match scale constraint -> ValueError
        # (never should have been allowed by ``__set__()`` in the first place)
        with self.assertRaises(ValueError):
            t.unconvert(decimal.Decimal("0.123"))

    def test_convert_roundtrip(self):
        t = self.type_()
        value = "21.52"
        self.assertEqual(t.unconvert(t.convert(value)), value)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        value = decimal.Decimal("21.52")
        self.assertEqual(t.convert(t.unconvert(value)), value)


class TestingTimezone(datetime.tzinfo):
    """Timezone info class for testing purposes"""

    def __init__(self, name: str, offset: datetime.timedelta):
        self.name = name
        self.offset = offset

    def utcoffset(self, dst: Optional[datetime.datetime]) -> datetime.timedelta:
        return self.offset

    def dst(self, dst: Optional[datetime.datetime]) -> Optional[datetime.timedelta]:
        return None

    def tzname(self, dst: Optional[datetime.datetime]) -> Optional[str]:
        return self.name


CST = TestingTimezone("CST", datetime.timedelta(hours=-6))
IST = TestingTimezone("IST", datetime.timedelta(hours=5, minutes=30))
NST = TestingTimezone("NST", datetime.timedelta(hours=-3.5))


class DateTimeTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.DateTime

    def test_convert(self):
        t = self.type_()
        # Accept timezone-aware datetime
        dt = datetime.datetime(2011, 11, 17, 3, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(dt, t.convert(dt))
        # Accept YYYYMMDD
        check = datetime.datetime(2011, 11, 17, 0, 0, 0, 0, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117"))
        # Accept YYYYMMDDHHMMSS
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 0, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045"))
        # Accept YYYYMMDDHHMMSS.XXX
        check = datetime.datetime(2011, 11, 17, 3, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045.150"))
        # Accept YYYYMMDDHHMMSS.XXX[offset]
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045.150[-6]"))
        # Accept YYYYMMDDHHMMSS[offset] - workaround for Chase Bank
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045[-6]"))
        # Accept YYYYMMDDHHMMSS.XXX[offset:TZ]
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045.150[-6:CST]"))
        # Accept YYYYMMDDHHMMSS.XXX[-:TZ] for TZs defined in the kludge
        check = datetime.datetime(2011, 11, 17, 9, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("20111117033045.150[-:CST]"))

    def test_convert_illegal(self):
        t = self.type_()
        # Don't accept timezone-naive datetime
        with self.assertRaises(ValueError):
            t.convert(datetime.datetime(2011, 11, 17, 3, 30, 45, 150))
        # Don't accept date
        with self.assertRaises(TypeError):
            t.convert(datetime.date(2011, 11, 17))
        # Don't accept strings of the wrong length
        with self.assertRaises(ValueError):
            t.convert("2015129")
        # Don't accept strings of the wrong format
        with self.assertRaises(ValueError):
            t.convert("20151A29")
        # Don't accept integer
        with self.assertRaises(TypeError):
            t.convert(123)
        # Don't accept YYYYMMDDHHMM
        with self.assertRaises(ValueError):
            t.convert("201111170330")
        # Don't accept YYYYMMDD.XXX
        with self.assertRaises(ValueError):
            t.convert("20111117.150")
        # Don't accept YYYYMMDDHHMMSS.XXX[-:TZ] for TZs not defined in kludge
        with self.assertRaises(ValueError):
            t.convert("20111117033045.150[-:GMT]")

    def test_unconvert(self):
        t = self.type_()
        check = datetime.datetime(2007, 1, 1, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "20070101000000.000[+0:UTC]")

        check = datetime.datetime(2007, 1, 1, tzinfo=CST)
        self.assertEqual(t.unconvert(check), "20070101000000.000[-6:CST]")

        check = datetime.datetime(2007, 1, 1, tzinfo=IST)
        self.assertEqual(t.unconvert(check), "20070101000000.000[+5.30:IST]")

        check = datetime.datetime(2007, 1, 1, tzinfo=NST)
        self.assertEqual(t.unconvert(check), "20070101000000.000[-3.30:NST]")

    def test_unconvert_round_microseconds(self):
        # Round up microseconds above 999499; increment seconds (Issue #80)
        t = self.type_()
        check = datetime.datetime(2020, 1, 1, 1, 1, 1, 999499, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "20200101010101.999[+0:UTC]")
        check = datetime.datetime(2020, 1, 1, 1, 1, 1, 999500, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "20200101010102.000[+0:UTC]")
        check = datetime.datetime(2020, 1, 1, 1, 1, 1, 999999, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "20200101010102.000[+0:UTC]")
        # Check that bumping seconds correctly propagates to bump all higher dials
        check = datetime.datetime(2020, 12, 31, 23, 59, 59, 999500, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "20210101000000.000[+0:UTC]")

    def test_unconvert_illegal(self):
        t = self.type_()
        # Don't accept timezone-naive datetime
        with self.assertRaises(ValueError):
            t.unconvert(datetime.datetime(2011, 11, 17, 3, 30, 45, 150))
        # Don't accept date
        with self.assertRaises(TypeError):
            t.unconvert(datetime.date(2011, 11, 17))
        # Don't accept string
        with self.assertRaises(TypeError):
            t.unconvert("20070101")

    def test_convert_roundtrip(self):
        t = self.type_()
        original = "20070101122030.567[+0:UTC]"
        result = original
        self.assertEqual(t.unconvert(t.convert(original)), result)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        original = datetime.datetime(2007, 1, 1, tzinfo=UTC)
        result = original
        self.assertEqual(t.convert(t.unconvert(original)), result)


class TimeTestCase(unittest.TestCase, Base):
    type_ = ofxtools.Types.Time

    def test_convert(self):
        t = self.type_()
        # Accept timezone-aware time
        tm = datetime.time(3, 30, 45, 150, tzinfo=UTC)
        self.assertEqual(tm, t.convert(tm))

        # Accept HHMMSS
        check = datetime.time(2, 4, 6, tzinfo=UTC)
        self.assertEqual(check, t.convert("020406"))

        # Accept HHMMSS.XXX
        check = datetime.time(3, 30, 0, 20000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033000.020"))

        # Accept HHMMSS.XXX[gmt offset]
        check = datetime.time(4, 30, 45, 20000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.020[-1]"))

        check = datetime.time(3, 30, 45, 20000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.020[0]"))

        check = datetime.time(2, 30, 45, 20000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.020[1]"))

        # Accept + prefixed GMT offsets
        check = datetime.time(2, 30, 45, 20000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.020[+1]"))

        # Accept HHMMSS[offset:TZ]
        check = datetime.time(9, 30, 45, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045[-6:CST]"))

        # Accept HHMMSS.XXX[offset:TZ]
        check = datetime.time(9, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.150[-6:CST]"))

        # Accept HHMMSS.XXX[-:TZ] for TZs defined in the kludge
        check = datetime.time(9, 30, 45, 150000, tzinfo=UTC)
        self.assertEqual(check, t.convert("033045.150[-:CST]"))

    def test_convert_illegal(self):
        t = self.type_()

        # Don't accept timezone-naive time
        with self.assertRaises(ValueError):
            t.convert(datetime.time(3, 30, 45, 150))

        # Don't accept datetime
        with self.assertRaises(TypeError):
            t.convert(datetime.datetime(2011, 11, 17, 3, 30, 45, 150, tzinfo=UTC))

        # Don't accept strings of the wrong length
        with self.assertRaises(ValueError):
            t.convert("03304")

        # Don't accept strings of the wrong format
        with self.assertRaises(ValueError):
            t.convert("033045,150[-:CST]")

        with self.assertRaises(ValueError):
            t.convert("033045.-150[-:CST]")

        # Don't accept strings with values out of legal range
        with self.assertRaises(ValueError):
            t.convert("243045.150[-:CST]")

        with self.assertRaises(ValueError):
            t.convert("036045.150[-:CST]")

        with self.assertRaises(ValueError):
            t.convert("033060.150[-:CST]")

        # Don't accept integer
        with self.assertRaises(TypeError):
            t.convert(123)

        # Don't accept HHMMSS.XXX[-:TZ] for TZs not defined in kludge
        with self.assertRaises(ValueError):
            t.convert("033045.150[-:GMT]")

    def test_unconvert(self):
        t = self.type_()
        check = datetime.time(1, 2, 3, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "010203.000[+0:UTC]")

        check = datetime.time(1, 2, 3, tzinfo=CST)
        self.assertEqual(t.unconvert(check), "010203.000[-6:CST]")

        check = datetime.time(1, 2, 3, tzinfo=IST)
        self.assertEqual(t.unconvert(check), "010203.000[+5.30:IST]")

    def test_unconvert_round_microseconds(self):
        # Round up microseconds above 999499; increment seconds (Issue #80)
        t = self.type_()
        check = datetime.time(1, 1, 1, 999499, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "010101.999[+0:UTC]")
        check = datetime.time(1, 1, 1, 999500, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "010102.000[+0:UTC]")
        check = datetime.time(1, 1, 1, 999999, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "010102.000[+0:UTC]")
        # Check that bumping seconds correctly propagates to bump all higher dials
        check = datetime.time(23, 59, 59, 999500, tzinfo=UTC)
        self.assertEqual(t.unconvert(check), "000000.000[+0:UTC]")

    def test_unconvert_illegal(self):
        t = self.type_()
        # Don't accept timezone-naive datetime
        with self.assertRaises(ValueError):
            t.unconvert(datetime.time(3, 30, 45, 150))

        # Don't accept datetime
        with self.assertRaises(TypeError):
            t.unconvert(datetime.datetime(2011, 11, 17, 6, 8, 10, tzinfo=UTC))

        # Don't accept string
        with self.assertRaises(TypeError):
            t.unconvert("033045")

    def test_convert_roundtrip(self):
        t = self.type_()
        original = "122030.567[+0:UTC]"
        result = original
        self.assertEqual(t.unconvert(t.convert(original)), result)

    def test_unconvert_roundtrip(self):
        t = self.type_()
        original = datetime.time(23, 3, 1, tzinfo=UTC)
        result = original
        self.assertEqual(t.convert(t.unconvert(original)), result)


if __name__ == "__main__":
    unittest.main()
