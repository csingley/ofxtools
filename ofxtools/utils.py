"""Utility functions and classes"""

from __future__ import annotations

# stdlib imports
import calendar
import datetime
import math
import os
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Iterator, Sequence
from itertools import filterfalse, groupby, tee
from itertools import pairwise as pairwise
from typing import Any
from xml.etree.ElementTree import indent as indent

# local imports
from ofxtools.lib import NUMBERING_AGENCIES


class classproperty(property):
    """Descriptor that makes a classmethod behave like a property."""

    def __get__(self, cls: Any, owner: type) -> Any:  # type: ignore[override]
        return self.fget.__get__(None, owner)()  # type: ignore[union-attr]


def fixpath(path: str) -> str:
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path


def collapseToSingle(items: Sequence[Any], label: str) -> Any:
    """
    Given a sequence of repeated items, return the item that's repeated.
    Throw an error if sequence is empty or contains >1 distinct item.

    ``label`` is the name used in error reporting.
    """
    items_ = set(items)
    if len(items_) == 0:
        raise ValueError(f"{label} is empty")
    if len(items_) > 1:
        raise ValueError(
            f"Multiple {label} {list(items)}; can't configure automatically"
        )
    return items_.pop()


###############################################################################
#  date/time utilities
###############################################################################
def gmt_offset(hours: int, minutes: int) -> datetime.timedelta:
    if hours not in range(-12, 15):
        raise ValueError(f"Invalid UTC offset hours: {hours}")
    if minutes < 0:
        raise ValueError(f"Invalid UTC offset minutes: {minutes}")
    offset_minutes = math.copysign(60 * abs(hours) + minutes, hours)
    return datetime.timedelta(minutes=offset_minutes)


TZS = {
    "EST": -5,
    "EDT": -4,
    "CST": -6,
    "CDT": -5,
    "MST": -7,
    "MDT": -6,
    "PST": -8,
    "PDT": -7,
}


def all_equal(iterable: Iterable[Any]) -> bool:
    """Returns True if all the elements are equal to each other"""
    g = groupby(iterable)
    next(g, None)  # consume first group (if any)
    return next(g, None) is None  # True iff no second group exists


def partition(
    pred: Callable[..., Any], iterable: Iterable[Any]
) -> tuple[Iterator[Any], Iterator[Any]]:
    """
    Use a predicate to partition entries into false entries and true entries
    """
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


###############################################################################
#  ElementTree utilities
###############################################################################
def tostring_unclosed_elements(elem: ET.Element) -> bytes:
    """
    SGML-style string representation of xml.etree.ElementTree, without
    closing tags on leaf elements.

    In OFX v1 (SGML), aggregate elements retain closing tags but leaf
    (data-bearing) elements do not: <ACCTID>12345 rather than
    <ACCTID>12345</ACCTID>.

    Drop-in replacement for xml.etree.ElementTree.tostring().
    """
    if len(elem) == 0:
        # Leaf element: emit value, no closing tag
        text = f"<{elem.tag}>{elem.text or ''}{elem.tail or ''}"
        return bytes(text, "utf_8")
    else:
        # Container element: emit children between opening/closing tags.
        # elem.text is whitespace between the start tag and the first child
        # (set by ET.indent() when prettyprint=True).
        # elem.tail is whitespace after the closing tag (between siblings).
        output = bytes(f"<{elem.tag}>{elem.text or ''}", "utf_8")
        for child in elem:
            output += tostring_unclosed_elements(child)
        output += bytes(f"</{elem.tag}>{elem.tail or ''}", "utf_8")
        return output


###############################################################################
#  Securities identifier utilities (CUSIP, ISIN, etc.)
###############################################################################
def cusip_checksum(base: str) -> str:
    """
    Compute the check digit for a base Committee on Uniform Security
    Identification Procedures (CUSIP) securities identifier.
    Input an 8-digit alphanum str, output a single-char str.

    http://goo.gl/4TeWl
    """

    def encode(index: int, char: str) -> str:
        num = {"*": 36, "@": 37, "#": 38}.get(char, int(char, 36))
        return str(num * 2) if index % 2 else str(num)

    if len(base) != 8:
        raise ValueError(f"CUSIP base must be 8 characters, got {len(base)}")
    check = "".join(encode(index, char) for index, char in enumerate(base))
    check_ = sum(int(digit) for digit in check)
    return str((10 - (check_ % 10)) % 10)


def validate_cusip(cusip: str) -> bool:
    """
    Validate a CUSIP
    """
    return len(cusip) == 9 and cusip_checksum(cusip[:8]) == cusip[8]


def sedol_checksum(base: str) -> str:
    """
    Stock Exchange Daily Official List (SEDOL)
    http://goo.gl/HxFWL
    """
    weights = (1, 3, 1, 7, 3, 9)

    if len(base) != 6:
        raise ValueError(f"SEDOL base must be 6 characters, got {len(base)}")
    for badLetter in "AEIO":
        if badLetter in base:
            raise ValueError(f"SEDOL base must not contain vowel '{badLetter}'")
    check = sum(int(char, 36) * weights[n] for n, char in enumerate(base))
    return str((10 - (check % 10)) % 10)


def isin_checksum(base: str) -> str:
    """
    Compute the check digit for a base International Securities Identification
    Number (ISIN).  Input an 11-char alphanum str, output a single-char str.

    http://goo.gl/8kPzD
    """
    if len(base) != 11:
        raise ValueError(f"ISIN base must be 11 characters, got {len(base)}")
    if base[:2] not in NUMBERING_AGENCIES:
        raise ValueError(f"ISIN country code '{base[:2]}' not recognized")
    check = "".join(str(int(char, 36)) for char in base)
    check = check[::-1]  # string reversal
    check = "".join(d if n % 2 else str(int(d) * 2) for n, d in enumerate(check))
    return str((10 - sum(int(d) for d in check) % 10) % 10)


def validate_isin(isin: str) -> bool:
    """
    Validate an ISIN
    """
    return (
        len(isin) == 12
        and isin[:2] in NUMBERING_AGENCIES
        and isin_checksum(isin[:11]) == isin[11]
    )


def cusip2isin(cusip: str, nation: str | None = None) -> str:
    # Validate inputs
    if not validate_cusip(cusip):
        raise ValueError(f"'{cusip}' is not a valid CUSIP")

    nation = nation or "US"
    if nation not in NUMBERING_AGENCIES:
        raise ValueError(f"'{nation}' is not a valid country code")

    # Construct ISIN
    base = nation + cusip
    return base + isin_checksum(base)


def sedol2isin(sedol: str, nation: str | None = None) -> str:
    nation = nation or "GB"
    if len(sedol) != 7:
        raise ValueError(f"SEDOL must be 7 characters, got {len(sedol)}")
    if sedol_checksum(sedol[:6]) != sedol[6]:
        raise ValueError(f"Invalid SEDOL check digit in '{sedol}'")
    base = nation + sedol.zfill(9)
    return base + isin_checksum(base)


UTC: datetime.tzinfo
try:
    # If pytz is installed then use that.
    import pytz

    UTC = pytz.UTC
except ImportError:
    # Otherwise create our own UTC tzinfo.
    class _UTC(datetime.tzinfo):
        def tzname(self, dt: datetime.datetime | None) -> str | None:
            """datetime -> string name of time zone."""
            return "UTC"

        def utcoffset(self, dt: datetime.datetime | None) -> datetime.timedelta | None:
            """datetime -> minutes east of UTC (negative for west of UTC)"""
            return datetime.timedelta(0)

        def dst(self, dt: datetime.datetime | None) -> datetime.timedelta | None:
            """datetime -> DST offset in minutes east of UTC.

            Return 0 if DST not in effect.  utcoffset() must include the DST
            offset.
            """
            return datetime.timedelta(0)

        def __repr__(self) -> str:
            return "<UTC>"

    UTC = _UTC()


def findEaster(year: int) -> datetime.date:
    """
    Compute the date of Easter Sunday for the given Gregorian calendar year
    (valid 1583–4099).

    Copyright (c) 2003  Gustavo Niemeyer <niemeyer@conectiva.com>
    Licensed under the PSF license.
    Ported from GM Arts / Claus Tondering algorithm (Ouding 1940), as quoted
    in "Explanatory Supplement to the Astronomical Almanac", P. Kenneth
    Seidelmann, editor.
    """
    # g - Golden year - 1
    # c - Century
    # h - (23 - Epact) mod 30
    # i - Number of days from March 21 to Paschal Full Moon
    # j - Weekday for PFM (0=Sunday, etc)
    # p - Number of days from March 21 to Sunday on or before PFM (-6 to 28)
    y = year
    g = y % 19
    c = y // 100
    h = (c - c // 4 - (8 * c + 13) // 25 + 19 * g + 15) % 30
    i = h - (h // 28) * (1 - (h // 28) * (29 // (h + 1)) * ((21 - g) // 11))
    j = (y + y // 4 + i + 2 - c + c // 4) % 7
    p = i - j
    d = 1 + (p + 27 + (p + 6) // 40) % 31
    m = 3 + (p + 26) // 30
    return datetime.date(y, m, d)


class NYSEcalendar:
    """
    NYSE holiday calendar.

    The Exchange is closed on: New Year's Day, Martin Luther King Jr. Day,
    Washington's Birthday, Good Friday, Memorial Day, Independence Day,
    Labor Day, Thanksgiving Day, and Christmas Day.

    When a fixed-date holiday falls on Saturday, the preceding Friday is
    observed — except New Year's Day, where Dec 31 is the year-end accounting
    close and the holiday is simply skipped that year.  When a fixed-date
    holiday falls on Sunday, the following Monday is observed.
    """

    _cal = calendar.Calendar()

    @classmethod
    def _weekdays(cls, year: int, month: int, weekday: int) -> list[datetime.date]:
        """Return all dates in (year, month) falling on the given weekday (0=Mon)."""
        return [
            datetime.date(year, month, day)
            for day, wkday in cls._cal.itermonthdays2(year, month)
            if day > 0 and wkday == weekday
        ]

    @classmethod
    def mondays(cls, year: int, month: int) -> list[datetime.date]:
        return cls._weekdays(year, month, weekday=0)

    @classmethod
    def thursdays(cls, year: int, month: int) -> list[datetime.date]:
        return cls._weekdays(year, month, weekday=3)

    @classmethod
    def _observed(cls, date: datetime.date) -> datetime.date:
        """Return the NYSE-observed date for a fixed holiday falling on a weekend."""
        if date.weekday() == 5:  # Saturday → preceding Friday
            return date - datetime.timedelta(days=1)
        if date.weekday() == 6:  # Sunday → following Monday
            return date + datetime.timedelta(days=1)
        return date

    @classmethod
    def holidays(cls, year: int) -> list[datetime.date]:
        hols = [
            cls._observed(datetime.date(year, 7, 4)),  # Independence Day
            cls._observed(datetime.date(year, 12, 25)),  # Christmas
            cls.mondays(year, 1)[2],  # MLK Day (3rd Mon in Jan)
            findEaster(year) - datetime.timedelta(days=2),  # Good Friday
            cls.mondays(year, 2)[2],  # Washington's Birthday (3rd Mon in Feb)
            cls.mondays(year, 5)[-1],  # Memorial Day (last Mon in May)
            cls.mondays(year, 9)[0],  # Labor Day (1st Mon in Sep)
            cls.thursdays(year, 11)[3],  # Thanksgiving (4th Thu in Nov)
        ]
        # New Year's Day: Saturday → skipped (Dec 31 is year-end accounting close)
        #                 Sunday   → observed Monday Jan 2
        #                 weekday  → Jan 1 itself
        nyd = datetime.date(year, 1, 1)
        if nyd.weekday() == 6:
            hols.append(nyd + datetime.timedelta(days=1))
        elif nyd.weekday() != 5:
            hols.append(nyd)
        hols.sort()
        return hols


def nextBizDay(dt: datetime.date) -> datetime.date:
    """Return the next NYSE business day after dt."""
    dt += datetime.timedelta(days=1)
    while dt.weekday() in (5, 6) or dt in NYSEcalendar.holidays(dt.year):
        dt += datetime.timedelta(days=1)
    return dt


def settleDate(dt: datetime.date, n: int = 1) -> datetime.date:
    """
    Return the settlement date for a trade on dt.

    n is the number of business days to add (T+n).  Defaults to 1 (T+1),
    the US equity standard since May 2024.  Pass n=2 for instruments still
    settling T+2 (e.g. most bonds, some international markets).
    """
    for _ in range(n):
        dt = nextBizDay(dt)
    return dt
