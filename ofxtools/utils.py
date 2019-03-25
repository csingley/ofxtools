# vim: set fileencoding=utf-8
""" Utility functions and classes """

# stdlib imports
import datetime
import calendar
import os

# local imports
from ofxtools.lib import NUMBERING_AGENCIES


def fixpath(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path


def cusip_checksum(base):
    """
    Compute the check digit for a base Committee on Uniform Security
    Identification Procedures (CUSIP) securities identifier.
    Input an 8-digit alphanum str, output a single-char str.

    http://goo.gl/4TeWl
    """
    def encode(index, char):
        num = {'*': 36, '@': 37, '#': 38}.get(char, int(char, 36))
        return str(num * 2) if index % 2 else str(num)

    assert len(base) == 8
    check = ''.join([encode(index, char) for index, char in enumerate(base)])
    check = sum([int(digit) for digit in check])
    return str((10 - (check % 10)) % 10)


def validate_cusip(cusip):
    """
    Validate a CUSIP
    """
    if len(cusip) == 9 and cusip_checksum(cusip[:8]) == cusip[8]:
        return True
    else:
        return False


def sedol_checksum(base):
    """
    Stock Exchange Daily Official List (SEDOL)
    http://goo.gl/HxFWL
    """
    weights = (1, 3, 1, 7, 3, 9)

    assert len(base) == 6
    for badLetter in 'AEIO':
        assert badLetter not in base
    check = sum([int(char, 36) * weights[n] for n, char in enumerate(base)])
    return str((10 - (check % 10)) % 10)


def isin_checksum(base):
    """
    Compute the check digit for a base International Securities Identification
    Number (ISIN).  Input an 11-char alphanum str, output a single-char str.

    http://goo.gl/8kPzD
    """
    assert len(base) == 11
    assert base[:2] in NUMBERING_AGENCIES.keys()
    check = ''.join([str(int(char, 36)) for char in base])
    check = check[::-1]  # string reversal
    check = ''.join([d if n % 2 else str(int(d)*2) for n, d in enumerate(check)])
    return str((10 - sum([int(d) for d in check]) % 10) % 10)


def validate_isin(isin):
    """
    Validate an ISIN
    """
    if len(isin) == 12 \
       and isin[:2] in NUMBERING_AGENCIES.keys() \
       and isin_checksum(isin[:11]) == isin[11]:
        return True
    else:
        return False


def cusip2isin(cusip, nation=None):
    # Validate inputs
    if not validate_cusip(cusip):
        raise ValueError("'%s' is not a valid CUSIP" % cusip)

    nation = nation or 'US'
    if nation not in NUMBERING_AGENCIES.keys():
        raise ValueError("'%s' is not a valid country code" % nation)

    # Construct ISIN
    base = nation + cusip
    return base + isin_checksum(base)


def sedol2isin(sedol, nation=None):
    nation = nation or 'GB'
    assert len(sedol) == 7
    assert sedol_checksum(sedol[:6]) == sedol[6]
    base = nation + sedol.zfill(9)
    return base + isin_checksum(base)


def settleDate(dt):
    """
    Given a trade date (or datetime), return the trade settlement date(time)
    """
    def nextBizDay(dt):
        stop = False
        while not stop:
            dt += datetime.timedelta(days=1)
            if dt.weekday() in (5, 6) or dt in NYSEcalendar.holidays(dt.year):
                stop = False
            else:
                stop = True
        return dt

    for n in range(3):
        dt = nextBizDay(dt)
    return dt


class NYSEcalendar:
    """
    The Board has determined that the Exchange will not be open for business on
        New Year's Day,
        Martin Luther King, Jr. Day,
        Washington's Birthday,
        Good Friday,
        Memorial Day,
        Independence Day,
        Labor Day,
        Thanksgiving Day
        and Christmas Day.
    Martin Luther King, Jr. Day, Washington's Birthday and Memorial Day will be
    celebrated on the third Monday in January, the third Monday in February
    and the last Monday in May, respectively

    The Exchange Board has also determined that, when any holiday observed by
    the Exchange falls on a Saturday, the Exchange will not be open for
    business on the preceding Friday and when any holiday observed by the
    Exchange falls on a Sunday, the Exchange will not be open for business on
    the succeeding Monday, unless unusual business conditions exist,
    such as the ending of a monthly or the yearly accounting period.
    """
    _cal = calendar.Calendar()

    @classmethod
    def _weekdays(cls, year, month, weekday):
        """
        Filter datetime.dates in (year, month) for a given weekday.
        """
        def weekdayTest(days):
            return (days[0] > 0) and (days[1] == weekday)
        return [datetime.date(year, month, day) \
                for (day, wkday) in itertools.ifilter(weekdayTest,
                                        cls._cal.itermonthdays2(year, month))]

    @classmethod
    def mondays(cls, year, month):
        return cls._weekdays(year, month, weekday=0)

    @classmethod
    def thursdays(cls, year, month):
        return cls._weekdays(year, month, weekday=3)

    @classmethod
    def holidays(cls, year):
        hols = [datetime.date(year, 7, 4), # Independence Day
                datetime.date(year, 12, 25), # Christmas
                cls.mondays(year, 1)[2], # MLK Day
                findEaster(year) - datetime.timedelta(days=2), # Good Friday
                cls.mondays(year, 2)[2], # Washington's Birthday
                cls.mondays(year, 5)[-1], # Memorial Day
                cls.mondays(year, 9)[0], # Labor Day
                cls.thursdays(year, 11)[-1], # Thanksgiving
        ]
        newYearsDay = datetime.date(year, 1, 1)
        if newYearsDay.weekday() != 5:
            # If New Year's Day falls on a Saturday, then it would get moved
            # back to the preceding Friday, except that would be 12/31, which
            # is the close of the monthly and annual accounting cycle... so
            # in that case, the holiday just gets skipped instead.
            hols.append(newYearsDay)
        hols.sort()
        return hols


def findEaster(year):
    """
    Copyright (c) 2003  Gustavo Niemeyer <niemeyer@conectiva.com>
    The code is licensed under the PSF license.

    This method was ported from the work done by GM Arts,
    on top of the algorithm by Claus Tondering, which was
    based in part on the algorithm of Ouding (1940), as
    quoted in "Explanatory Supplement to the Astronomical
    Almanac", P.  Kenneth Seidelmann, editor.

    Edited by csingley to "de-modulize" the function to fit into pyofx,
    and to remove unused Easter calculation methods.

    This algorithm implements the revised method of easter calculation,
    in Gregorian calendar, valid in years 1583 to 4099.

    More about the algorithm may be found at:
    http://users.chariot.net.au/~gmarts/eastalg.htm
    and
    http://www.tondering.dk/claus/calendar.html
    """
    # g - Golden year - 1
    # c - Century
    # h - (23 - Epact) mod 30
    # i - Number of days from March 21 to Paschal Full Moon
    # j - Weekday for PFM (0=Sunday, etc)
    # p - Number of days from March 21 to Sunday on or before PFM
    #     (-6 to 28)

    y = year
    g = y % 19
    e = 0

    # New method (i.e. EASTER_WESTERN)
    c = y/100
    h = (c-c/4-(8*c+13)/25+19*g+15)%30
    i = h-(h/28)*(1-(h/28)*(29/(h+1))*((21-g)/11))
    j = (y+y/4+i+2-c+c/4)%7

    # p can be from -6 to 56 corresponding to dates 22 March to 23 May
    # (later dates apply to method 2, although 23 May never actually occurs)
    p = i-j+e
    d = 1+(p+27+(p+6)/40)%31
    m = 3+(p+26)/30
    return datetime.date(y,m,d)


try:
    # If pytz is installed then use that.
    import pytz
    UTC = pytz.UTC
except ImportError:
    # Otherwise create our own UTC tzinfo.
    class _UTC(datetime.tzinfo):
        def tzname(self, dt):
            """datetime -> string name of time zone."""
            return "UTC"

        def utcoffset(self, dt):
            """datetime -> minutes east of UTC (negative for west of UTC)"""
            return datetime.timedelta(0)

        def dst(self, dt):
            """datetime -> DST offset in minutes east of UTC.

            Return 0 if DST not in effect.  utcoffset() must include the DST
            offset.
            """
            return datetime.timedelta(0)

        def __repr__(self):
            return "<UTC>"

    UTC = _UTC()
