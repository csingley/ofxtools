import os.path
import re
import datetime
import calendar
import time
from decimal import Decimal
import itertools
import string

from xml.dom import minidom


def prettify(xmlstring):
    """ """
    return minidom.parseString(xmlstring).toprettyxml(indent=' '*2)


def _(path):
    """Makes paths do the right thing."""
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = os.path.abspath(path)
    return path


OFXv1 = ('102', '103')
OFXv2 = ('203', '211')

APPIDS = ('QWIN', # Quicken for Windows
            'QMOFX', # Quicken for Mac
            'QBW', # QuickBooks for Windows
            'QBM', # QuickBooks for Mac
            'Money', # MSFT Money
            'Money Plus', # MSFT Money Plus
            'PyOFX', # Custom
)
APPVERS = ('1500', # Quicken 2006/ Money 2006
            '1600', # Quicken 2007/ Money 2007/ QuickBooks 2006
            '1700', # Quicken 2008/ Money Plus/ QuickBooks 2007
            '1800', # Quicken 2009/ QuickBooks 2008
            '1900', # Quicken 2010/ QuickBooks 2009
            '2000', # QuickBooks 2010
            '9999', # Custom
)

# Currency codes
ISO4217 = ('AE', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG',
            'AZN', 'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND',
            'BOB', 'BOV', 'BRL', 'BSD', 'BTN', 'BWP', 'BYR', 'BZD', 'CAD',
            'CDF', 'CHE', 'CHF', 'CHW', 'CLF', 'CLP', 'CNY', 'COP', 'COU',
            'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD',
            'EEK', 'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL',
            'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK',
            'HTG', 'HUF', 'IDR', 'ILS', 'INR', 'IQD', 'IRR', 'ISK', 'JMD',
            'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD',
            'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL',
            'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRO',
            'MUR', 'MVR', 'MWK', 'MXN', 'MXV', 'MYR', 'MZN', 'NAD', 'NGN',
            'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP',
            'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR',
            'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD',
            'STD', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP',
            'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'USN', 'USS',
            'UYI', 'UYU', 'UZS', 'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XAG',
            'XAU', 'XBA', 'XBB', 'XBC', 'XBD', 'XCD', 'XDR', 'XFU', 'XOF',
            'XPD', 'XPF', 'XPT', 'XTS', 'XXX', 'YER', 'ZAR', 'ZMK', 'ZWL')


# Country codes
ISO3166_1a3 = ('ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ANT', 'ARE',
                'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE',
                'BDI', 'BEL', 'BEN', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH',
                'BLM', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN',
                'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV',
                'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB',
                'CXR', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM',
                'DZA', 'ECU', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN',
                'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY',
                'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD',
                'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV',
                'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ',
                'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'JPN', 'KAZ', 'KEN',
                'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR',
                'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAC',
                'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD',
                'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR',
                'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK',
                'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN',
                'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI',
                'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU', 'RUS',
                'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB',
                'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'STP', 'SUR', 'SVK',
                'SVN', 'SWE', 'SWZ', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA',
                'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV',
                'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT',
                'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM',
                'ZAF', 'ZMB', 'ZWE')

# ISO3166_1a2 country codes and numbering agencies
# Swiped from
# http://code.activestate.com/recipes/498277-isin-validator/
numberingAgencies = {'BE': (u'Euronext - Brussels', u'Belgium'),
'FR': (u'Euroclear France', u'France'),
'BG': (u'Central Depository of Bulgaria', u'Bulgaria'),
'VE': (u'Bolsa de Valores de Caracas, C.A.', u'Venezuela'),
'DK': (u'VP Securities Services', u'Denmark'),
'HR': (u'SDA - Central Depository Agency of Croatia', u'Croatia'),
'DE': (u'Wertpapier-Mitteilungen', u'Germany'),
'JP': (u'Tokyo Stock Exchange', u'Japan'),
'HU': (u'KELER', u'Hungary'),
'HK': (u'Hong Kong Exchanges and Clearing Ltd', u'Hong Kong'),
'JO': (u'Securities Depository Center of Jordan', u'Jordan'),
'BR': (u'Bolsa de Valores de Sao Paulo - BOVESPA', u'Brazil'),
'XS': (u'Clearstream Banking', u'Clearstream'),
'FI': (u'Finnish Central Securities Depository Ltd', u'Finland'),
'GR': (u'Central Securities Depository S.A.', u'Greece'),
'IS': (u'Icelandic Securities Depository', u'Iceland'),
'RU': (u'The National Depository Center, Russia', u'Russia'),
'LB': (u'Midclear S.A.L.', u'Lebanon'),
'PT': (u'Interbolsa - Sociedade Gestora de Sistemas de Liquida\xc3\xa7\xc3\xa3o e Sistemas Centralizados de Valores', u'Portugal'),
'NO': (u'Verdipapirsentralen (VPS) ASA', u'Norway'),
'TW': (u'Taiwan Stock Exchange Corporation', u'Taiwan, Province of China'),
'UA': (u'National Depository of Ukraine', u'Ukraine'),
'TR': (u'Takasbank', u'Turkey'),
'LK': (u'Colombo Stock Exchange', u'Sri Lanka'),
'LV': (u'OMX - Latvian Central Depository', u'Latvia'),
'LU': (u'Clearstream Banking', u'Luxembourg'),
'TH': (u'Thailand Securities Depository Co., Ltd', u'Thailand'),
'NL': (u'Euronext Netherlands', u'Netherlands'),
'PK': (u'Central Depository Company of Pakistan Ltd', u'Pakistan'),
'PH': (u'Philippine Stock Exchange, Inc.', u'Philippines'),
'RO': (u'The National Securities Clearing Settlement and Depository Corporation', u'Romania'),
'EG': (u'Misr for Central Clearing, Depository and Registry (MCDR)', u'Egypt'),
'PL': (u'National Depository for Securities', u'Poland'),
'AA': (u'ANNA Secretariat', u'ANNAland'),
'CH': (u'Telekurs Financial Ltd.', u'Switzerland'),
'CN': (u'China Securities Regulatory Commission', u'China'),
'CL': (u'Deposito Central de Valores', u'Chile'),
'EE': (u'Estonian Central Depository for Securities', u'Estonia'),
'CA': (u'The Canadian Depository for Securities Ltd', u'Canada'),
'IR': (u'Tehran Stock Exchange Services Company', u'Iran'),
'IT': (u'Ufficio Italiano dei Cambi', u'Italy'),
'ZA': (u'JSE Securities Exchange of South Africa', u'South Africa'),
'CZ': (u'Czech National Bank', u'Czech Republic'),
'CY': (u'Cyprus Stock Exchange', u'Cyprus'),
'AR': (u'Caja de Valores S.A.', u'Argentina'),
'AU': (u'Australian Stock Exchange Limited', u'Australia'),
'AT': (u'Oesterreichische Kontrollbank AG', u'Austria'),
'IN': (u'Securities and Exchange Board of India', u'India'),
'CS': (u'Central Securities Depository A.D. Beograd', u'Serbia & Montenegro'),
'CR': (u'Central de Valores - CEVAL', u'Costa Rica'),
'IE': (u'The Irish Stock Exchange', u'Ireland'),
'ID': (u'PT. Kustodian Sentral Efek Indonesia (Indonesian Central Securities Depository (ICSD))', u'Indonesia'),
'ES': (u'Comision Nacional del Mercado de Valores (CNMV)', u'Spain'),
'PE': (u'Bolsa de Valores de Lima', u'Peru'),
'TN': (u'Sticodevam', u'Tunisia'),
'PA': (u'Bolsa de Valores de Panama S.A.', u'Panama'),
'SG': (u'Singapore Exchange Limited', u'Singapore'),
'IL': (u'The Tel Aviv Stock Exchange', u'Israel'),
'US': (u'Standard & Poor\xb4s - CUSIP Service Bureau', u'USA'),
'MX': (u'S.D. Indeval SA de CV', u'Mexico'),
'SK': (u'Central Securities Depository SR, Inc.', u'Slovakia'),
'KR': (u'Korea Exchange - KRX', u'Korea'),
'SI': (u'KDD Central Securities Clearing Corporation', u'Slovenia'),
'KW': (u'Kuwait Clearing Company', u'Kuwait'),
'MY': (u'Bursa Malaysia', u'Malaysia'),
'MO': (u'MAROCLEAR S.A.', u'Morocco'),
'SE': (u'VPC AB', u'Sweden'),
'GB': (u'London Stock Exchange', u'United Kingdom')}

# 3-letter language codes
ISO639_2 = ('AAR', 'ABK', 'ACE', 'ACH', 'ADA', 'ADY', 'AFA', 'AFH', 'AFR', 'AIN', 'AKA', 'AKK', 'SQI', 'ALE', 'ALG', 'ALT', 'AMH', 'ANG', 'ANP', 'APA', 'ARA', 'ARC', 'ARG', 'HYE', 'ARN', 'ARP', 'ART', 'ARW', 'ASM', 'AST', 'ATH', 'AUS', 'AVA', 'AVE', 'AWA', 'AYM', 'AZE', 'BAD', 'BAI', 'BAK', 'BAL', 'BAM', 'BAN', 'EUS', 'BAS', 'BAT', 'BEJ', 'BEL', 'BEM', 'BEN', 'BER', 'BHO', 'BIH', 'BIK', 'BIN', 'BIS', 'BLA', 'BNT', 'BOS', 'BRA', 'BRE', 'BTK', 'BUA', 'BUG', 'BUL', 'MYA', 'BYN', 'CAD', 'CAI', 'CAR', 'CAT', 'CAU', 'CEB', 'CEL', 'CHA', 'CHB', 'CHE', 'CHG', 'ZHO', 'CHK', 'CHM', 'CHN', 'CHO', 'CHP', 'CHR', 'CHU', 'CHV', 'CHY', 'CMC', 'COP', 'COR', 'COS', 'CPE', 'CPF', 'CPP', 'CRE', 'CRH', 'CRP', 'CSB', 'CUS', 'CES', 'DAK', 'DAN', 'DAR', 'DAY', 'DEL', 'DEN', 'DGR', 'DIN', 'DIV', 'DOI', 'DRA', 'DSB', 'DUA', 'DUM', 'NLD', 'DYU', 'DZO', 'EFI', 'EGY', 'EKA', 'ELX', 'ENG', 'ENM', 'EPO', 'EST', 'EWE', 'EWO', 'FAN', 'FAO', 'FAT', 'FIJ', 'FIL', 'FIN', 'FIU', 'FON', 'FRA', 'FRM', 'FRO', 'FRR', 'FRS', 'FRY', 'FUL', 'FUR', 'GAA', 'GAY', 'GBA', 'GEM', 'KAT', 'DEU', 'GEZ', 'GIL', 'GLA', 'GLE', 'GLG', 'GLV', 'GMH', 'GOH', 'GON', 'GOR', 'GOT', 'GRB', 'GRC', 'ELL', 'GRN', 'GSW', 'GUJ', 'GWI', 'HAI', 'HAT', 'HAU', 'HAW', 'HEB', 'HER', 'HIL', 'HIM', 'HIN', 'HIT', 'HMN', 'HMO', 'HRV', 'HSB', 'HUN', 'HUP', 'IBA', 'IBO', 'ISL', 'IDO', 'III', 'IJO', 'IKU', 'ILE', 'ILO', 'INA', 'INC', 'IND', 'INE', 'INH', 'IPK', 'IRA', 'IRO', 'ITA', 'JAV', 'JBO', 'JPN', 'JPR', 'JRB', 'KAA', 'KAB', 'KAC', 'KAL', 'KAM', 'KAN', 'KAR', 'KAS', 'KAU', 'KAW', 'KAZ', 'KBD', 'KHA', 'KHI', 'KHM', 'KHO', 'KIK', 'KIN', 'KIR', 'KMB', 'KOK', 'KOM', 'KON', 'KOR', 'KOS', 'KPE', 'KRC', 'KRL', 'KRO', 'KRU', 'KUA', 'KUM', 'KUR', 'KUT', 'LAD', 'LAH', 'LAM', 'LAO', 'LAT', 'LAV', 'LEZ', 'LIM', 'LIN', 'LIT', 'LOL', 'LOZ', 'LTZ', 'LUA', 'LUB', 'LUG', 'LUI', 'LUN', 'LUO', 'LUS', 'MKD', 'MAD', 'MAG', 'MAH', 'MAI', 'MAK', 'MAL', 'MAN', 'MRI', 'MAP', 'MAR', 'MAS', 'MSA', 'MDF', 'MDR', 'MEN', 'MGA', 'MIC', 'MIN', 'MIS', 'MKH', 'MLG', 'MLT', 'MNC', 'MNI', 'MNO', 'MOH', 'MON', 'MOS', 'MUL', 'MUN', 'MUS', 'MWL', 'MWR', 'MYN', 'MYV', 'NAH', 'NAI', 'NAP', 'NAU', 'NAV', 'NBL', 'NDE', 'NDO', 'NDS', 'NEP', 'NEW', 'NIA', 'NIC', 'NIU', 'NNO', 'NOB', 'NOG', 'NON', 'NOR', 'NQO', 'NSO', 'NUB', 'NWC', 'NYA', 'NYM', 'NYN', 'NYO', 'NZI', 'OCI', 'OJI', 'ORI', 'ORM', 'OSA', 'OSS', 'OTA', 'OTO', 'PAA', 'PAG', 'PAL', 'PAM', 'PAN', 'PAP', 'PAU', 'PEO', 'FAS', 'PHI', 'PHN', 'PLI', 'POL', 'PON', 'POR', 'PRA', 'PRO', 'PUS', 'QAA-QTZ', 'QUE', 'RAJ', 'RAP', 'RAR', 'ROA', 'ROH', 'ROM', 'RON', 'RUN', 'RUP', 'RUS', 'SAD', 'SAG', 'SAH', 'SAI', 'SAL', 'SAM', 'SAN', 'SAS', 'SAT', 'SCN', 'SCO', 'SEL', 'SEM', 'SGA', 'SGN', 'SHN', 'SID', 'SIN', 'SIO', 'SIT', 'SLA', 'SLO', 'SLV', 'SMA', 'SME', 'SMI', 'SMJ', 'SMN', 'SMO', 'SMS', 'SNA', 'SND', 'SNK', 'SOG', 'SOM', 'SON', 'SOT', 'SPA', 'SRD', 'SRN', 'SRP', 'SRR', 'SSA', 'SSW', 'SUK', 'SUN', 'SUS', 'SUX', 'SWA', 'SWE', 'SYC', 'SYR', 'TAH', 'TAI', 'TAM', 'TAT', 'TEL', 'TEM', 'TER', 'TET', 'TGK', 'TGL', 'THA', 'BOD', 'TIG', 'TIR', 'TIV', 'TKL', 'TLH', 'TLI', 'TMH', 'TOG', 'TON', 'TPI', 'TSI', 'TSN', 'TSO', 'TUK', 'TUM', 'TUP', 'TUR', 'TUT', 'TVL', 'TWI', 'TYV', 'UDM', 'UGA', 'UIG', 'UKR', 'UMB', 'UND', 'URD', 'UZB', 'VAI', 'VEN', 'VIE', 'VOL', 'VOT', 'WAK', 'WAL', 'WAR', 'WAS', 'CYM', 'WEN', 'WLN', 'WOL', 'XAL', 'XHO', 'YAO', 'YAP', 'YID', 'YOR', 'YPK', 'ZAP', 'ZBL', 'ZEN', 'ZHA', 'ZND', 'ZUL', 'ZUN', 'ZXX', 'ZZA')

def cusipChecksum(base):
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
    for badLetter in 'IO':
        assert badLetter not in base
    check = ''.join([encode(index, char) for index, char in enumerate(base)])
    check = sum([int(digit) for digit in check])
    return str((10 - (check % 10)) % 10)

def sedolChecksum(base):
    """
    Stock Exchange Daily Official List (SEDOL)
    http://goo.gl/HxFWL
    """
    weights = (1, 3, 1, 7, 3, 9)

    assert len(base) == 6
    for badLetter in 'AEIOU':
        assert badLetter not in base
    check = sum([int(char, 36) * weights[n] for n, char in enumerate(base)])
    return str((10 - (check % 10)) % 10)

def isinChecksum(base):
    """
    Compute the check digit for a base International Securities Identification
    Number (ISIN).  Input an 11-char alphanum str, output a single-char str.

    http://goo.gl/8kPzD
    """
    assert len(base) == 11
    assert alphanum[:2] in numberingAgencies.keys()
    check = ''.join([int(char, 36) for char in base])
    check = check[::-1] # string reversal
    check = ''.join([d if n%2 else str(int(d)*2) for n, d in enumerate(check)])
    return str((10 - sum([int(d) for d in check]) % 10) % 10)

def cusip2isin(cusip, nation=None):
    nation = nation or 'US'
    assert len(cusip) == 9
    assert CUSIPchecksum(cusip[:8]) == cusip[9]
    base = nation + cusip
    return base + ISINchecksum(base)

def sedol2isin(sedol, nation=None):
    nation = nation or 'GB'
    assert len(sedol) == 7
    assert SEDOLchecksum(sedol[:6]) == sedol[6]
    base = nation + sedol.zfill(9)
    return base + ISINchecksum(base)

#def isin2cusip(isin):
    #assert len(isin) == 12
    #assert isinChecksum(isin[:11]) == isin[12]
    #assert isin[:2] in ('US', 'CA') # FIXME
    #return isin[2:11]

#def isin2sedol(isin):
    #assert len(isin) == 12
    #assert isinChecksum(isin[:11]) == isin[12]
    #assert isin[:2] in ('GB', 'CA') # FIXME

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

    #print dt
    for n in range(3):
        dt = nextBizDay(dt)
    #print dt
    return dt


class NYSEcalendar(object):
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

    Edited by csingley to "de-modulize" the function to fit into PMS,
    and to remove Easter calculation methods unused by our application.

    This method was ported from the work done by GM Arts,
    on top of the algorithm by Claus Tondering, which was
    based in part on the algorithm of Ouding (1940), as
    quoted in "Explanatory Supplement to the Astronomical
    Almanac", P.  Kenneth Seidelmann, editor.

    This algorithm (as edited by csingley) implements the
    revised method of easter calculation, in Gregorian calendar,
    valid in years 1583 to 4099.

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



# Validators/converters implemented here so that
# client.py needn't depend on FormEncode or SQLAlchemy
class OFXDtConverter(object):
    # Valid datetime formats given by OFX 3.2.8.2
    tz_re = re.compile(r'\[([-+]?\d{0,2}\.?\d*):?(\w*)\]')
    # strftime formats keyed by the length of the corresponding string
    formats = {18: '%Y%m%d%H%M%S.%f', 14: '%Y%m%d%H%M%S', 8: '%Y%m%d'}

    @classmethod
    def to_python(cls, value):
        # If it's a datetime or None, don't touch it.
        if isinstance(value, datetime.datetime) or value==None:
            return value

        # Pristine copy of input for error reporting
        orig_value = value

        # Strip out timezone, on which strptime() chokes
        chunks = cls.tz_re.split(value)
        value = chunks.pop(0)
        if chunks:
            gmt_offset, tz_name = chunks[:2]
            # Some FIs *cough* IBKR *cough* write crap for the TZ offset
            if gmt_offset == '-':
                gmt_offset = '0'
            gmt_offset = int(Decimal(gmt_offset)*3600) # hours -> seconds
        else:
            gmt_offset = 0
        format = cls.formats[len(value)]
        try:
            value = datetime.datetime.strptime(value, format)
        except ValueError:
            raise ValueError("Datetime '%s' does not match OFX formats %s" %
                            (orig_value, str(cls.formats.values())))

        # Adjust timezone to GMT
        value -= datetime.timedelta(seconds=gmt_offset)
        return value

    @classmethod
    def from_python(cls, value):
        """ Input datetime.datetime in local time; output str in GMT. """
        # Pristine copy of input for error reporting
        orig_value = value

        try:
            # Transform to GMT
            value = time.gmtime(time.mktime(value.timetuple()))
            # timetuples don't have usec precision
            #value = time.strftime('%s[0:GMT]' % cls.formats[14], value)
            value = time.strftime(cls.formats[14], value)
        except:
            raise # FIXME
        return value


class OFXStringBool(object):
    values = {True: 'Y', False: 'N'}

    @classmethod
    def from_python(cls, value):
        return cls.values[value]


class BankAcctTypeValidator(object):
    values = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')

    @classmethod
    def to_python(cls, value):
        assert value in cls.values
        return value
