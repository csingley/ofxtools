"""Unit tests for ofxtools.utils"""

# stdlib imports
import datetime
import os
import unittest
import xml.etree.ElementTree as ET

# local imports
import ofxtools.utils
from ofxtools.utils import (
    NYSEcalendar,
    collapseToSingle,
    cusip2isin,
    cusip_checksum,
    findEaster,
    fixpath,
    gmt_offset,
    indent,
    isin_checksum,
    nextBizDay,
    pairwise,
    sedol2isin,
    sedol_checksum,
    settleDate,
    tostring_unclosed_elements,
    validate_cusip,
    validate_isin,
)


class TostringUnclosedElementsTestCase(unittest.TestCase):
    def _make_tree(self):
        # <OFX><STMTRQ><ACCTID>12345</STMTRQ></OFX>
        root = ET.Element("OFX")
        stmtrq = ET.SubElement(root, "STMTRQ")
        acctid = ET.SubElement(stmtrq, "ACCTID")
        acctid.text = "12345"
        return root

    def test_leaf_no_closing_tag(self):
        root = self._make_tree()
        result = tostring_unclosed_elements(root).decode("utf_8")
        self.assertIn("<ACCTID>12345", result)
        self.assertNotIn("</ACCTID>", result)

    def test_container_has_closing_tag(self):
        root = self._make_tree()
        result = tostring_unclosed_elements(root).decode("utf_8")
        self.assertIn("<STMTRQ>", result)
        self.assertIn("</STMTRQ>", result)
        self.assertIn("<OFX>", result)
        self.assertIn("</OFX>", result)

    def test_value_preserved(self):
        root = self._make_tree()
        result = tostring_unclosed_elements(root).decode("utf_8")
        self.assertIn("12345", result)

    def test_structure(self):
        root = self._make_tree()
        result = tostring_unclosed_elements(root).decode("utf_8")
        self.assertEqual(result, "<OFX><STMTRQ><ACCTID>12345</STMTRQ></OFX>")

    def test_prettyprint(self):
        root = self._make_tree()
        indent(root)
        result = tostring_unclosed_elements(root).decode("utf_8")
        self.assertEqual(
            result, "<OFX>\n  <STMTRQ>\n    <ACCTID>12345\n  </STMTRQ>\n</OFX>"
        )


class CollapseToSingleTestCase(unittest.TestCase):
    def test_single(self):
        self.assertEqual(collapseToSingle([42, 42, 42], "values"), 42)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            collapseToSingle([], "values")

    def test_multiple_raises(self):
        with self.assertRaises(ValueError):
            collapseToSingle([1, 2], "values")


class GmtOffsetTestCase(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(gmt_offset(-5, 0), datetime.timedelta(hours=-5))

    def test_invalid_hours(self):
        with self.assertRaises(ValueError):
            gmt_offset(15, 0)

    def test_negative_minutes(self):
        with self.assertRaises(ValueError):
            gmt_offset(0, -1)


class PairwiseTestCase(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(list(pairwise([1, 2, 3])), [(1, 2), (2, 3)])

    def test_empty(self):
        self.assertEqual(list(pairwise([])), [])

    def test_single(self):
        self.assertEqual(list(pairwise([1])), [])


class FixpathTestCase(unittest.TestCase):
    def test_all(self):
        """
        utils.fixpath() calls os.path.{expanduser, normpath, normcase, abspath}
        """
        test_path = "~/foo/../bar"
        home = os.environ["HOME"]
        self.assertEqual(fixpath(test_path), f"{home}/bar")


class CusipTestCase(unittest.TestCase):
    def test_cusip_checksum(self):
        self.assertEqual(cusip_checksum("08467010"), "8")

    def test_cusip_checksum_wrong_length(self):
        with self.assertRaises(ValueError):
            cusip_checksum("0846701")  # 7 chars, needs 8

    def test_validate_cusip(self):
        self.assertTrue(validate_cusip("084670207"))
        self.assertFalse(validate_cusip("084670208"))
        self.assertFalse(validate_cusip("08467020"))
        self.assertFalse(validate_cusip("0846702077"))

    def test_cusip2isin(self):
        self.assertEqual(cusip2isin("084670108"), "US0846701086")

    def test_cusip2isin_invalid_isin(self):
        with self.assertRaises(ValueError):
            cusip2isin("084670208")

    def test_cusip2isin_invalid_nation(self):
        with self.assertRaises(ValueError):
            cusip2isin("084670108", nation="MOON")


class IsinTestCase(unittest.TestCase):
    def test_isin_checksum(self):
        self.assertEqual(isin_checksum("US084670108"), "6")

    def test_isin_checksum_wrong_length(self):
        with self.assertRaises(ValueError):
            isin_checksum("US08467010")  # 10 chars, needs 11

    def test_isin_checksum_bad_country(self):
        with self.assertRaises(ValueError):
            isin_checksum("XX08467010X")  # XX not a valid country code

    def test_validate_isin(self):
        self.assertTrue(validate_isin("US0846701086"))
        self.assertFalse(validate_isin("US0846701087"))
        self.assertFalse(validate_isin("US084670108"))
        self.assertFalse(validate_isin("US08467010866"))

    def test_validate_isin_bad_country(self):
        self.assertFalse(validate_isin("XX0846701086"))


class SedolTestCase(unittest.TestCase):
    def test_sedol_checksum(self):
        self.assertEqual(sedol_checksum("011100"), "9")

    def test_sedol_checksum_wrong_length(self):
        with self.assertRaises(ValueError):
            sedol_checksum("01110")  # 5 chars, needs 6

    def test_sedol_checksum_vowel(self):
        with self.assertRaises(ValueError):
            sedol_checksum("A11100")  # contains vowel A

    def test_sedol2isin(self):
        self.assertEqual(sedol2isin("0111009"), "GB0001110096")

    def test_sedol2isin_wrong_length(self):
        with self.assertRaises(ValueError):
            sedol2isin("011100")  # 6 chars, needs 7

    def test_sedol2isin_bad_check_digit(self):
        with self.assertRaises(ValueError):
            sedol2isin("0111008")  # correct is 0111009


class FindEasterTestCase(unittest.TestCase):
    # Known Easter dates sourced from https://www.timeanddate.com/holidays/us/easter
    def test_2020(self):
        self.assertEqual(findEaster(2020), datetime.date(2020, 4, 12))

    def test_2021(self):
        self.assertEqual(findEaster(2021), datetime.date(2021, 4, 4))

    def test_2022(self):
        self.assertEqual(findEaster(2022), datetime.date(2022, 4, 17))

    def test_2023(self):
        self.assertEqual(findEaster(2023), datetime.date(2023, 4, 9))

    def test_2024(self):
        self.assertEqual(findEaster(2024), datetime.date(2024, 3, 31))

    def test_2025(self):
        self.assertEqual(findEaster(2025), datetime.date(2025, 4, 20))

    def test_early_april(self):
        # Easter can fall as early as March 22
        self.assertEqual(findEaster(1954), datetime.date(1954, 4, 18))

    def test_late_april(self):
        self.assertEqual(findEaster(2019), datetime.date(2019, 4, 21))


class NYSEcalendarTestCase(unittest.TestCase):
    def test_mondays(self):
        # January 2024 starts on Monday; mondays are 1, 8, 15, 22, 29
        mondays = NYSEcalendar.mondays(2024, 1)
        self.assertEqual(mondays[0], datetime.date(2024, 1, 1))
        self.assertEqual(mondays[2], datetime.date(2024, 1, 15))  # MLK Day 2024
        self.assertEqual(len(mondays), 5)

    def test_thursdays(self):
        # November 2018 starts on Thursday; thursdays are 1, 8, 15, 22, 29
        thursdays = NYSEcalendar.thursdays(2018, 11)
        self.assertEqual(len(thursdays), 5)
        self.assertEqual(thursdays[3], datetime.date(2018, 11, 22))  # Thanksgiving
        self.assertEqual(thursdays[4], datetime.date(2018, 11, 29))  # NOT Thanksgiving

    def test_observed_weekday(self):
        # Regular weekday: date unchanged
        thursday = datetime.date(2024, 7, 4)
        self.assertEqual(NYSEcalendar._observed(thursday), thursday)

    def test_observed_saturday(self):
        # Saturday → preceding Friday
        sat = datetime.date(2020, 7, 4)
        self.assertEqual(NYSEcalendar._observed(sat), datetime.date(2020, 7, 3))

    def test_observed_sunday(self):
        # Sunday → following Monday
        sun = datetime.date(2021, 7, 4)
        self.assertEqual(NYSEcalendar._observed(sun), datetime.date(2021, 7, 5))

    def test_nyd_weekday(self):
        # NYD on a weekday: Jan 1 is in holidays
        # 2024: Jan 1 is Monday
        hols = NYSEcalendar.holidays(2024)
        self.assertIn(datetime.date(2024, 1, 1), hols)

    def test_nyd_saturday_skipped(self):
        # NYD on Saturday: skipped entirely (Dec 31 is year-end close)
        # 2022: Jan 1 is Saturday
        hols = NYSEcalendar.holidays(2022)
        self.assertNotIn(datetime.date(2022, 1, 1), hols)
        self.assertNotIn(datetime.date(2021, 12, 31), hols)

    def test_nyd_sunday_observed_monday(self):
        # NYD on Sunday: observed Monday Jan 2
        # 2023: Jan 1 is Sunday
        hols = NYSEcalendar.holidays(2023)
        self.assertNotIn(datetime.date(2023, 1, 1), hols)
        self.assertIn(datetime.date(2023, 1, 2), hols)

    def test_thanksgiving_4th_thursday(self):
        # 2018: November has 5 Thursdays; Thanksgiving is the 4th (Nov 22), not last (Nov 29)
        hols = NYSEcalendar.holidays(2018)
        self.assertIn(datetime.date(2018, 11, 22), hols)
        self.assertNotIn(datetime.date(2018, 11, 29), hols)

    def test_thanksgiving_4th_thursday_normal(self):
        # 2024: November has 4 Thursdays; 4th == last, Nov 28
        hols = NYSEcalendar.holidays(2024)
        self.assertIn(datetime.date(2024, 11, 28), hols)

    def test_independence_day_saturday_observed_friday(self):
        # 2020: July 4 is Saturday → observed July 3
        hols = NYSEcalendar.holidays(2020)
        self.assertIn(datetime.date(2020, 7, 3), hols)
        self.assertNotIn(datetime.date(2020, 7, 4), hols)

    def test_independence_day_sunday_observed_monday(self):
        # 2021: July 4 is Sunday → observed July 5
        hols = NYSEcalendar.holidays(2021)
        self.assertIn(datetime.date(2021, 7, 5), hols)
        self.assertNotIn(datetime.date(2021, 7, 4), hols)

    def test_christmas_saturday_observed_friday(self):
        # 2021: Dec 25 is Saturday → observed Dec 24
        hols = NYSEcalendar.holidays(2021)
        self.assertIn(datetime.date(2021, 12, 24), hols)
        self.assertNotIn(datetime.date(2021, 12, 25), hols)

    def test_christmas_sunday_observed_monday(self):
        # 2022: Dec 25 is Sunday → observed Dec 26
        hols = NYSEcalendar.holidays(2022)
        self.assertIn(datetime.date(2022, 12, 26), hols)
        self.assertNotIn(datetime.date(2022, 12, 25), hols)

    def test_good_friday(self):
        # 2024: Easter is March 31, Good Friday is March 29
        hols = NYSEcalendar.holidays(2024)
        self.assertIn(datetime.date(2024, 3, 29), hols)

    def test_holidays_sorted(self):
        hols = NYSEcalendar.holidays(2024)
        self.assertEqual(hols, sorted(hols))

    def test_holidays_count(self):
        # Should be 9 holidays in a typical year (NYD + 8 others)
        # 2024 has all 9 (NYD is Monday)
        self.assertEqual(len(NYSEcalendar.holidays(2024)), 9)
        # 2022 has 8 (NYD Saturday is skipped)
        self.assertEqual(len(NYSEcalendar.holidays(2022)), 8)


class NextBizDayTestCase(unittest.TestCase):
    def test_monday_to_tuesday(self):
        mon = datetime.date(2024, 6, 3)  # Monday, no holiday
        self.assertEqual(nextBizDay(mon), datetime.date(2024, 6, 4))

    def test_friday_skips_weekend(self):
        fri = datetime.date(2024, 6, 7)
        self.assertEqual(nextBizDay(fri), datetime.date(2024, 6, 10))

    def test_skips_holiday(self):
        # Dec 24 2021 is observed Christmas; nextBizDay(Dec 23) → Dec 27
        self.assertEqual(
            nextBizDay(datetime.date(2021, 12, 23)), datetime.date(2021, 12, 27)
        )

    def test_skips_holiday_and_weekend(self):
        # Good Friday 2024 is March 29 (Friday); nextBizDay(Mar 28 Thu) → Apr 1 Mon
        self.assertEqual(
            nextBizDay(datetime.date(2024, 3, 28)), datetime.date(2024, 4, 1)
        )


class SettleDateTestCase(unittest.TestCase):
    def test_t1_default(self):
        # T+1 default: Monday → Tuesday
        mon = datetime.date(2024, 6, 3)
        self.assertEqual(settleDate(mon), datetime.date(2024, 6, 4))

    def test_t1_over_weekend(self):
        # T+1: Friday → Monday
        fri = datetime.date(2024, 6, 7)
        self.assertEqual(settleDate(fri), datetime.date(2024, 6, 10))

    def test_t2(self):
        # T+2: Monday → Wednesday
        mon = datetime.date(2024, 6, 3)
        self.assertEqual(settleDate(mon, n=2), datetime.date(2024, 6, 5))

    def test_t2_over_weekend(self):
        # T+2: Thursday → Monday
        thu = datetime.date(2024, 6, 6)
        self.assertEqual(settleDate(thu, n=2), datetime.date(2024, 6, 10))

    def test_t2_over_holiday(self):
        # T+2 from Wed Mar 27 2024, skipping Good Friday Mar 29: Wed→Thu→Mon
        self.assertEqual(
            settleDate(datetime.date(2024, 3, 27), n=2), datetime.date(2024, 4, 1)
        )


class UtcTestCase(unittest.TestCase):
    @property
    def datetime(self):
        return datetime.datetime.now()

    def testUTC(self):
        self.assertEqual(ofxtools.utils.UTC.tzname(self.datetime), "UTC")
        self.assertEqual(
            ofxtools.utils.UTC.utcoffset(self.datetime), datetime.timedelta(0)
        )
        self.assertEqual(ofxtools.utils.UTC.dst(self.datetime), datetime.timedelta(0))
        self.assertEqual(repr(ofxtools.utils.UTC), "<UTC>")


if __name__ == "__main__":
    unittest.main()
