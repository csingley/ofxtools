.. _utils:

Utility Functions
=================

``ofxtools.utils`` provides several utility functions and classes useful for
working with financial data, particularly for investment account processing.


Securities Identifier Utilities
--------------------------------

``ofxtools`` can validate and convert between the three most common securities
identifier formats: CUSIP (US), SEDOL (UK), and ISIN (international).

.. code-block:: python

    from ofxtools.utils import cusip2isin, sedol2isin, validate_cusip, validate_isin

    # Validate a CUSIP
    validate_cusip('084670207')   # True
    validate_cusip('084670208')   # False (bad check digit)

    # Convert CUSIP to ISIN (defaults to US country code)
    cusip2isin('084670108')       # 'US0846701086'
    cusip2isin('084670108', nation='CA')  # Canadian ISIN

    # Convert SEDOL to ISIN (defaults to GB country code)
    sedol2isin('0111009')         # 'GB0001110096'

    # Validate an ISIN
    validate_isin('US0846701086')  # True


NYSE Holiday Calendar
---------------------

``NYSEcalendar`` provides the official NYSE holiday schedule for a given year.
The NYSE is closed on New Year's Day, Martin Luther King Jr. Day, Washington's
Birthday, Good Friday, Memorial Day, Independence Day, Labor Day, Thanksgiving,
and Christmas.

Weekend-shifted holidays follow NYSE convention: Saturday holidays are observed
on the preceding Friday, Sunday holidays on the following Monday — except New
Year's Day falling on Saturday, which is simply skipped (December 31 is the
year-end accounting close).

.. code-block:: python

    import datetime
    from ofxtools.utils import NYSEcalendar

    # Get all NYSE holidays for a year
    NYSEcalendar.holidays(2024)
    # [datetime.date(2024, 1, 1),   # New Year's Day (Monday)
    #  datetime.date(2024, 1, 15),  # MLK Day
    #  datetime.date(2024, 2, 19),  # Washington's Birthday
    #  datetime.date(2024, 3, 29),  # Good Friday
    #  datetime.date(2024, 5, 27),  # Memorial Day
    #  datetime.date(2024, 7, 4),   # Independence Day (Thursday)
    #  datetime.date(2024, 9, 2),   # Labor Day
    #  datetime.date(2024, 11, 28), # Thanksgiving (4th Thursday)
    #  datetime.date(2024, 12, 25)] # Christmas (Wednesday)

    # Get all Mondays in a given month (useful for computing floating holidays)
    NYSEcalendar.mondays(2024, 1)
    # [datetime.date(2024, 1, 1), datetime.date(2024, 1, 8), ...]

    # Get all Thursdays in November (for Thanksgiving)
    NYSEcalendar.thursdays(2024, 11)
    # [datetime.date(2024, 11, 7), ..., datetime.date(2024, 11, 28)]

``findEaster`` computes Easter Sunday for any Gregorian calendar year
(valid 1583–4099), which is needed to derive Good Friday:

.. code-block:: python

    from ofxtools.utils import findEaster

    findEaster(2024)  # datetime.date(2024, 3, 31)
    findEaster(2025)  # datetime.date(2025, 4, 20)


Settlement Date Utilities
--------------------------

US equity settlement moved to T+1 (trade date plus one business day) in
May 2024.  Most bonds and many international markets still settle T+2.
``settleDate`` and ``nextBizDay`` handle both, skipping weekends and NYSE
holidays.

.. code-block:: python

    import datetime
    from ofxtools.utils import nextBizDay, settleDate

    trade_date = datetime.date(2024, 3, 28)  # Thursday before Good Friday

    # Next NYSE business day (skips Good Friday 3/29 and weekend)
    nextBizDay(trade_date)   # datetime.date(2024, 4, 1)

    # T+1 settlement (US equity default since May 2024)
    settleDate(trade_date)          # datetime.date(2024, 4, 1)

    # T+2 settlement (bonds, some international markets)
    settleDate(trade_date, n=2)     # datetime.date(2024, 4, 2)

    # Friday trade: T+1 settles Monday (skips weekend)
    settleDate(datetime.date(2024, 6, 7))  # datetime.date(2024, 6, 10)
