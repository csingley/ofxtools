# coding: utf-8
""" Utility functions and classes """

# stdlib imports
import datetime
import os
import itertools
import xml.etree.ElementTree as ET
from typing import Any, Optional, Tuple, Callable, Iterable, Sequence
import math


# local imports
from ofxtools.lib import NUMBERING_AGENCIES


class classproperty(property):
    """Decorator that turns a classmethod into a property"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def fixpath(path: str) -> str:
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path


def collapseToSingle(items: Sequence, label: str):
    """
    Given a sequence of repeated items, return the item that's repeated.
    Throw an error if sequence is empty or contains >1 distinct item.

    ``label`` is the name used in error reporting.
    """
    items_ = set(items)
    if len(items_) == 0:
        raise ValueError("{label} is empty")
    if len(items_) > 1:
        raise ValueError(
            (f"Multiple {label} {list(items)}; " "can't configure automatically")
        )
    return items_.pop()


###############################################################################
#  date/time utilities
###############################################################################
def gmt_offset(hours: int, minutes: int) -> datetime.timedelta:
    assert hours in range(-12, 15)
    assert minutes >= 0
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


###############################################################################
#  itertools recipes
#  https://docs.python.org/2/library/itertools.html#recipes
###############################################################################
def pairwise(iterable: Iterable) -> Iterable[Tuple[Any, Any]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def all_equal(iterable):
    """Returns True if all the elements are equal to each other"""
    g = itertools.groupby(iterable)
    return next(g, True) and not next(g, False)


def partition(pred: Callable, iterable: Iterable) -> Tuple[Iterable, Iterable]:
    """
    Use a predicate to partition entries into false entries and true entries
    """
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)


###############################################################################
#  ElementTree utilities
###############################################################################
def indent(elem: ET.Element, level: int = 0) -> None:
    """
    Indent xml.etree.ElementTree.Element.text by nesting level.

    http://effbot.org/zone/element-lib.htm#prettyprint
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# FIXME - this doesn't work quite right
def tostring_unclosed_elements(elem: ET.Element) -> bytes:
    """
    SGML-style string representation of xml.etree.ElementTree, without
    closing tags.

    Drop-in replacement for xml.etree.ElementTree.tostring().
    """
    if len(elem) == 0:
        text = "<{}>{}{}".format(elem.tag, elem.text or "", elem.tail or "")
        output = bytes(text, "utf_8")
    else:
        output = bytes("<{}>{}".format(elem.tag, elem.tail or ""), "utf_8")
        for child in elem:
            output += tostring_unclosed_elements(child)
        output += bytes("</{}>{}".format(elem.tag, elem.tail or ""), "utf_8")
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

    def encode(index, char):
        num = {"*": 36, "@": 37, "#": 38}.get(char, int(char, 36))
        return str(num * 2) if index % 2 else str(num)

    assert len(base) == 8
    check = "".join([encode(index, char) for index, char in enumerate(base)])
    check_ = sum([int(digit) for digit in check])
    return str((10 - (check_ % 10)) % 10)


def validate_cusip(cusip: str) -> bool:
    """
    Validate a CUSIP
    """
    if len(cusip) == 9 and cusip_checksum(cusip[:8]) == cusip[8]:
        return True
    else:
        return False


def sedol_checksum(base: str) -> str:
    """
    Stock Exchange Daily Official List (SEDOL)
    http://goo.gl/HxFWL
    """
    weights = (1, 3, 1, 7, 3, 9)

    assert len(base) == 6
    for badLetter in "AEIO":
        assert badLetter not in base
    check = sum([int(char, 36) * weights[n] for n, char in enumerate(base)])
    return str((10 - (check % 10)) % 10)


def isin_checksum(base: str) -> str:
    """
    Compute the check digit for a base International Securities Identification
    Number (ISIN).  Input an 11-char alphanum str, output a single-char str.

    http://goo.gl/8kPzD
    """
    assert len(base) == 11
    assert base[:2] in NUMBERING_AGENCIES.keys()
    check = "".join([str(int(char, 36)) for char in base])
    check = check[::-1]  # string reversal
    check = "".join([d if n % 2 else str(int(d) * 2) for n, d in enumerate(check)])
    return str((10 - sum([int(d) for d in check]) % 10) % 10)


def validate_isin(isin: str) -> bool:
    """
    Validate an ISIN
    """
    if (
        len(isin) == 12
        and isin[:2] in NUMBERING_AGENCIES.keys()
        and isin_checksum(isin[:11]) == isin[11]
    ):
        return True
    else:
        return False


def cusip2isin(cusip: str, nation: Optional[str] = None) -> str:
    # Validate inputs
    if not validate_cusip(cusip):
        raise ValueError("'%s' is not a valid CUSIP" % cusip)

    nation = nation or "US"
    if nation not in NUMBERING_AGENCIES.keys():
        raise ValueError("'%s' is not a valid country code" % nation)

    # Construct ISIN
    base = nation + cusip
    return base + isin_checksum(base)


def sedol2isin(sedol, nation=None) -> str:
    nation = nation or "GB"
    assert len(sedol) == 7
    assert sedol_checksum(sedol[:6]) == sedol[6]
    base = nation + sedol.zfill(9)
    return base + isin_checksum(base)


# TESTME
try:
    # If pytz is installed then use that.
    import pytz

    UTC = pytz.UTC  # type: ignore
except ImportError:
    # Otherwise create our own UTC tzinfo.
    class _UTC(datetime.tzinfo):
        def tzname(self, dt: Optional[datetime.datetime]) -> Optional[str]:
            """datetime -> string name of time zone."""
            return "UTC"

        def utcoffset(
            self, dt: Optional[datetime.datetime]
        ) -> Optional[datetime.timedelta]:
            """datetime -> minutes east of UTC (negative for west of UTC)"""
            return datetime.timedelta(0)

        def dst(self, dt: Optional[datetime.datetime]) -> Optional[datetime.timedelta]:
            """datetime -> DST offset in minutes east of UTC.

            Return 0 if DST not in effect.  utcoffset() must include the DST
            offset.
            """
            return datetime.timedelta(0)

        def __repr__(self) -> str:
            return "<UTC>"

    UTC = _UTC()  # type: ignore


#  def settleDate(dt):
#  """
#  Given a trade date (or datetime), return the trade settlement date(time)
#  """

#  def nextBizDay(dt):
#  stop = False
#  while not stop:
#  dt += datetime.timedelta(days=1)
#  if dt.weekday() in (5, 6) or dt in NYSEcalendar.holidays(dt.year):
#  stop = False
#  else:
#  stop = True
#  return dt

#  for n in range(3):
#  dt = nextBizDay(dt)
#  return dt


#  class NYSEcalendar:
#  """
#  The Board has determined that the Exchange will not be open for business on
#  New Year's Day,
#  Martin Luther King, Jr. Day,
#  Washington's Birthday,
#  Good Friday,
#  Memorial Day,
#  Independence Day,
#  Labor Day,
#  Thanksgiving Day
#  and Christmas Day.
#  Martin Luther King, Jr. Day, Washington's Birthday and Memorial Day will be
#  celebrated on the third Monday in January, the third Monday in February
#  and the last Monday in May, respectively

#  The Exchange Board has also determined that, when any holiday observed by
#  the Exchange falls on a Saturday, the Exchange will not be open for
#  business on the preceding Friday and when any holiday observed by the
#  Exchange falls on a Sunday, the Exchange will not be open for business on
#  the succeeding Monday, unless unusual business conditions exist,
#  such as the ending of a monthly or the yearly accounting period.
#  """

#  _cal = calendar.Calendar()

#  @classmethod
#  def _weekdays(cls, year, month, weekday):
#  """
#  Filter datetime.dates in (year, month) for a given weekday.
#  """

#  def weekdayTest(days):
#  return (days[0] > 0) and (days[1] == weekday)

#  return [
#  datetime.date(year, month, day)
#  for (day, wkday) in itertools.ifilter(
#  weekdayTest, cls._cal.itermonthdays2(year, month)
#  )
#  ]

#  @classmethod
#  def mondays(cls, year, month):
#  return cls._weekdays(year, month, weekday=0)

#  @classmethod
#  def thursdays(cls, year, month):
#  return cls._weekdays(year, month, weekday=3)

#  @classmethod
#  def holidays(cls, year):
#  hols = [
#  datetime.date(year, 7, 4),  # Independence Day
#  datetime.date(year, 12, 25),  # Christmas
#  cls.mondays(year, 1)[2],  # MLK Day
#  findEaster(year) - datetime.timedelta(days=2),  # Good Friday
#  cls.mondays(year, 2)[2],  # Washington's Birthday
#  cls.mondays(year, 5)[-1],  # Memorial Day
#  cls.mondays(year, 9)[0],  # Labor Day
#  cls.thursdays(year, 11)[-1],  # Thanksgiving
#  ]
#  newYearsDay = datetime.date(year, 1, 1)
#  if newYearsDay.weekday() != 5:
#  # If New Year's Day falls on a Saturday, then it would get moved
#  # back to the preceding Friday, except that would be 12/31, which
#  # is the close of the monthly and annual accounting cycle... so
#  # in that case, the holiday just gets skipped instead.
#  hols.append(newYearsDay)
#  hols.sort()
#  return hols


#  def findEaster(year):
#  """
#  Copyright (c) 2003  Gustavo Niemeyer <niemeyer@conectiva.com>
#  The code is licensed under the PSF license.

#  This method was ported from the work done by GM Arts,
#  on top of the algorithm by Claus Tondering, which was
#  based in part on the algorithm of Ouding (1940), as
#  quoted in "Explanatory Supplement to the Astronomical
#  Almanac", P.  Kenneth Seidelmann, editor.

#  Edited by csingley to "de-modulize" the function to fit into ofxtools,
#  and to remove unused Easter calculation methods.

#  This algorithm implements the revised method of easter calculation,
#  in Gregorian calendar, valid in years 1583 to 4099.

#  More about the algorithm may be found at:
#  http://users.chariot.net.au/~gmarts/eastalg.htm
#  and
#  http://www.tondering.dk/claus/calendar.html
#  """
#  # g - Golden year - 1
#  # c - Century
#  # h - (23 - Epact) mod 30
#  # i - Number of days from March 21 to Paschal Full Moon
#  # j - Weekday for PFM (0=Sunday, etc)
#  # p - Number of days from March 21 to Sunday on or before PFM
#  #     (-6 to 28)

#  y = year
#  g = y % 19
#  e = 0

#  # New method (i.e. EASTER_WESTERN)
#  c = y / 100
#  h = (c - c / 4 - (8 * c + 13) / 25 + 19 * g + 15) % 30
#  i = h - (h / 28) * (1 - (h / 28) * (29 / (h + 1)) * ((21 - g) / 11))
#  j = (y + y / 4 + i + 2 - c + c / 4) % 7

#  # p can be from -6 to 56 corresponding to dates 22 March to 23 May
#  # (later dates apply to method 2, although 23 May never actually occurs)
#  p = i - j + e
#  d = 1 + (p + 27 + (p + 6) / 40) % 31
#  m = 3 + (p + 26) / 30
#  return datetime.date(y, m, d)
