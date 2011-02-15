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
ISO4217 = (u'AE', u'AFN', u'ALL', u'AMD', u'ANG', u'AOA', u'ARS', u'AUD',
            u'AWG', u'AZN', u'BAM', u'BBD', u'BDT', u'BGN', u'BHD', u'BIF',
            u'BMD', u'BND', u'BOB', u'BOV', u'BRL', u'BSD', u'BTN', u'BWP',
            u'BYR', u'BZD', u'CAD', u'CDF', u'CHE', u'CHF', u'CHW', u'CLF',
            u'CLP', u'CNY', u'COP', u'COU', u'CRC', u'CUC', u'CUP', u'CVE',
            u'CZK', u'DJF', u'DKK', u'DOP', u'DZD', u'EEK', u'EGP', u'ERN',
            u'ETB', u'EUR', u'FJD', u'FKP', u'GBP', u'GEL', u'GHS', u'GIP',
            u'GMD', u'GNF', u'GTQ', u'GYD', u'HKD', u'HNL', u'HRK', u'HTG',
            u'HUF', u'IDR', u'ILS', u'INR', u'IQD', u'IRR', u'ISK', u'JMD',
            u'JOD', u'JPY', u'KES', u'KGS', u'KHR', u'KMF', u'KPW', u'KRW',
            u'KWD', u'KYD', u'KZT', u'LAK', u'LBP', u'LKR', u'LRD', u'LSL',
            u'LTL', u'LVL', u'LYD', u'MAD', u'MDL', u'MGA', u'MKD', u'MMK',
            u'MNT', u'MOP', u'MRO', u'MUR', u'MVR', u'MWK', u'MXN', u'MXV',
            u'MYR', u'MZN', u'NAD', u'NGN', u'NIO', u'NOK', u'NPR', u'NZD',
            u'OMR', u'PAB', u'PEN', u'PGK', u'PHP', u'PKR', u'PLN', u'PYG',
            u'QAR', u'RON', u'RSD', u'RUB', u'RWF', u'SAR', u'SBD', u'SCR',
            u'SDG', u'SEK', u'SGD', u'SHP', u'SLL', u'SOS', u'SRD', u'STD',
            u'SVC', u'SYP', u'SZL', u'THB', u'TJS', u'TMT', u'TND', u'TOP',
            u'TRY', u'TTD', u'TWD', u'TZS', u'UAH', u'UGX', u'USD', u'USN',
            u'USS', u'UYI', u'UYU', u'UZS', u'VEF', u'VND', u'VUV', u'WST',
            u'XAF', u'XAG', u'XAU', u'XBA', u'XBB', u'XBC', u'XBD', u'XCD',
            u'XDR', u'XFU', u'XOF', u'XPD', u'XPF', u'XPT', u'XTS', u'XXX',
            u'YER', u'ZAR', u'ZMK', u'ZWL')


# Country codes
ISO3166_1a3 = (u'ABW', u'AFG', u'AGO', u'AIA', u'ALA', u'ALB', u'AND', u'ANT',
                u'ARE', u'ARG', u'ARM', u'ASM', u'ATA', u'ATF', u'ATG', u'AUS',
                u'AUT', u'AZE', u'BDI', u'BEL', u'BEN', u'BFA', u'BGD', u'BGR',
                u'BHR', u'BHS', u'BIH', u'BLM', u'BLR', u'BLZ', u'BMU', u'BOL',
                u'BRA', u'BRB', u'BRN', u'BTN', u'BVT', u'BWA', u'CAF', u'CAN',
                u'CCK', u'CHE', u'CHL', u'CHN', u'CIV', u'CMR', u'COD', u'COG',
                u'COK', u'COL', u'COM', u'CPV', u'CRI', u'CUB', u'CXR', u'CYM',
                u'CYP', u'CZE', u'DEU', u'DJI', u'DMA', u'DNK', u'DOM', u'DZA',
                u'ECU', u'EGY', u'ERI', u'ESH', u'ESP', u'EST', u'ETH', u'FIN',
                u'FJI', u'FLK', u'FRA', u'FRO', u'FSM', u'GAB', u'GBR', u'GEO',
                u'GGY', u'GHA', u'GIB', u'GIN', u'GLP', u'GMB', u'GNB', u'GNQ',
                u'GRC', u'GRD', u'GRL', u'GTM', u'GUF', u'GUM', u'GUY', u'HKG',
                u'HMD', u'HND', u'HRV', u'HTI', u'HUN', u'IDN', u'IMN', u'IND',
                u'IOT', u'IRL', u'IRN', u'IRQ', u'ISL', u'ISR', u'ITA', u'JAM',
                u'JEY', u'JOR', u'JPN', u'KAZ', u'KEN', u'KGZ', u'KHM', u'KIR',
                u'KNA', u'KOR', u'KWT', u'LAO', u'LBN', u'LBR', u'LBY', u'LCA',
                u'LIE', u'LKA', u'LSO', u'LTU', u'LUX', u'LVA', u'MAC', u'MAF',
                u'MAR', u'MCO', u'MDA', u'MDG', u'MDV', u'MEX', u'MHL', u'MKD',
                u'MLI', u'MLT', u'MMR', u'MNE', u'MNG', u'MNP', u'MOZ', u'MRT',
                u'MSR', u'MTQ', u'MUS', u'MWI', u'MYS', u'MYT', u'NAM', u'NCL',
                u'NER', u'NFK', u'NGA', u'NIC', u'NIU', u'NLD', u'NOR', u'NPL',
                u'NRU', u'NZL', u'OMN', u'PAK', u'PAN', u'PCN', u'PER', u'PHL',
                u'PLW', u'PNG', u'POL', u'PRI', u'PRK', u'PRT', u'PRY', u'PSE',
                u'PYF', u'QAT', u'REU', u'ROU', u'RUS', u'RWA', u'SAU', u'SDN',
                u'SEN', u'SGP', u'SGS', u'SHN', u'SJM', u'SLB', u'SLE', u'SLV',
                u'SMR', u'SOM', u'SPM', u'SRB', u'STP', u'SUR', u'SVK', u'SVN',
                u'SWE', u'SWZ', u'SYC', u'SYR', u'TCA', u'TCD', u'TGO', u'THA',
                u'TJK', u'TKL', u'TKM', u'TLS', u'TON', u'TTO', u'TUN', u'TUR',
                u'TUV', u'TWN', u'TZA', u'UGA', u'UKR', u'UMI', u'URY', u'USA',
                u'UZB', u'VAT', u'VCT', u'VEN', u'VGB', u'VIR', u'VNM', u'VUT',
                u'WLF', u'WSM', u'YEM', u'ZAF', u'ZMB', u'ZWE')

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
ISO639_2 = (u'AAR', u'ABK', u'ACE', u'ACH', u'ADA', u'ADY', u'AFA', u'AFH',
            u'AFR', u'AIN', u'AKA', u'AKK', u'SQI', u'ALE', u'ALG', u'ALT',
            u'AMH', u'ANG', u'ANP', u'APA', u'ARA', u'ARC', u'ARG', u'HYE',
            u'ARN', u'ARP', u'ART', u'ARW', u'ASM', u'AST', u'ATH', u'AUS',
            u'AVA', u'AVE', u'AWA', u'AYM', u'AZE', u'BAD', u'BAI', u'BAK',
            u'BAL', u'BAM', u'BAN', u'EUS', u'BAS', u'BAT', u'BEJ', u'BEL',
            u'BEM', u'BEN', u'BER', u'BHO', u'BIH', u'BIK', u'BIN', u'BIS',
            u'BLA', u'BNT', u'BOS', u'BRA', u'BRE', u'BTK', u'BUA', u'BUG',
            u'BUL', u'MYA', u'BYN', u'CAD', u'CAI', u'CAR', u'CAT', u'CAU',
            u'CEB', u'CEL', u'CHA', u'CHB', u'CHE', u'CHG', u'ZHO', u'CHK',
            u'CHM', u'CHN', u'CHO', u'CHP', u'CHR', u'CHU', u'CHV', u'CHY',
            u'CMC', u'COP', u'COR', u'COS', u'CPE', u'CPF', u'CPP', u'CRE',
            u'CRH', u'CRP', u'CSB', u'CUS', u'CES', u'DAK', u'DAN', u'DAR',
            u'DAY', u'DEL', u'DEN', u'DGR', u'DIN', u'DIV', u'DOI', u'DRA',
            u'DSB', u'DUA', u'DUM', u'NLD', u'DYU', u'DZO', u'EFI', u'EGY',
            u'EKA', u'ELX', u'ENG', u'ENM', u'EPO', u'EST', u'EWE', u'EWO',
            u'FAN', u'FAO', u'FAT', u'FIJ', u'FIL', u'FIN', u'FIU', u'FON',
            u'FRA', u'FRM', u'FRO', u'FRR', u'FRS', u'FRY', u'FUL', u'FUR',
            u'GAA', u'GAY', u'GBA', u'GEM', u'KAT', u'DEU', u'GEZ', u'GIL',
            u'GLA', u'GLE', u'GLG', u'GLV', u'GMH', u'GOH', u'GON', u'GOR',
            u'GOT', u'GRB', u'GRC', u'ELL', u'GRN', u'GSW', u'GUJ', u'GWI',
            u'HAI', u'HAT', u'HAU', u'HAW', u'HEB', u'HER', u'HIL', u'HIM',
            u'HIN', u'HIT', u'HMN', u'HMO', u'HRV', u'HSB', u'HUN', u'HUP',
            u'IBA', u'IBO', u'ISL', u'IDO', u'III', u'IJO', u'IKU', u'ILE',
            u'ILO', u'INA', u'INC', u'IND', u'INE', u'INH', u'IPK', u'IRA',
            u'IRO', u'ITA', u'JAV', u'JBO', u'JPN', u'JPR', u'JRB', u'KAA',
            u'KAB', u'KAC', u'KAL', u'KAM', u'KAN', u'KAR', u'KAS', u'KAU',
            u'KAW', u'KAZ', u'KBD', u'KHA', u'KHI', u'KHM', u'KHO', u'KIK',
            u'KIN', u'KIR', u'KMB', u'KOK', u'KOM', u'KON', u'KOR', u'KOS',
            u'KPE', u'KRC', u'KRL', u'KRO', u'KRU', u'KUA', u'KUM', u'KUR',
            u'KUT', u'LAD', u'LAH', u'LAM', u'LAO', u'LAT', u'LAV', u'LEZ',
            u'LIM', u'LIN', u'LIT', u'LOL', u'LOZ', u'LTZ', u'LUA', u'LUB',
            u'LUG', u'LUI', u'LUN', u'LUO', u'LUS', u'MKD', u'MAD', u'MAG',
            u'MAH', u'MAI', u'MAK', u'MAL', u'MAN', u'MRI', u'MAP', u'MAR',
            u'MAS', u'MSA', u'MDF', u'MDR', u'MEN', u'MGA', u'MIC', u'MIN',
            u'MIS', u'MKH', u'MLG', u'MLT', u'MNC', u'MNI', u'MNO', u'MOH',
            u'MON', u'MOS', u'MUL', u'MUN', u'MUS', u'MWL', u'MWR', u'MYN',
            u'MYV', u'NAH', u'NAI', u'NAP', u'NAU', u'NAV', u'NBL', u'NDE',
            u'NDO', u'NDS', u'NEP', u'NEW', u'NIA', u'NIC', u'NIU', u'NNO',
            u'NOB', u'NOG', u'NON', u'NOR', u'NQO', u'NSO', u'NUB', u'NWC',
            u'NYA', u'NYM', u'NYN', u'NYO', u'NZI', u'OCI', u'OJI', u'ORI',
            u'ORM', u'OSA', u'OSS', u'OTA', u'OTO', u'PAA', u'PAG', u'PAL',
            u'PAM', u'PAN', u'PAP', u'PAU', u'PEO', u'FAS', u'PHI', u'PHN',
            u'PLI', u'POL', u'PON', u'POR', u'PRA', u'PRO', u'PUS', u'QUE',
            u'RAJ', u'RAP', u'RAR', u'ROA', u'ROH', u'ROM', u'RON', u'RUN',
            u'RUP', u'RUS', u'SAD', u'SAG', u'SAH', u'SAI', u'SAL', u'SAM',
            u'SAN', u'SAS', u'SAT', u'SCN', u'SCO', u'SEL', u'SEM', u'SGA',
            u'SGN', u'SHN', u'SID', u'SIN', u'SIO', u'SIT', u'SLA', u'SLO',
            u'SLV', u'SMA', u'SME', u'SMI', u'SMJ', u'SMN', u'SMO', u'SMS',
            u'SNA', u'SND', u'SNK', u'SOG', u'SOM', u'SON', u'SOT', u'SPA',
            u'SRD', u'SRN', u'SRP', u'SRR', u'SSA', u'SSW', u'SUK', u'SUN',
            u'SUS', u'SUX', u'SWA', u'SWE', u'SYC', u'SYR', u'TAH', u'TAI',
            u'TAM', u'TAT', u'TEL', u'TEM', u'TER', u'TET', u'TGK', u'TGL',
            u'THA', u'BOD', u'TIG', u'TIR', u'TIV', u'TKL', u'TLH', u'TLI',
            u'TMH', u'TOG', u'TON', u'TPI', u'TSI', u'TSN', u'TSO', u'TUK',
            u'TUM', u'TUP', u'TUR', u'TUT', u'TVL', u'TWI', u'TYV', u'UDM',
            u'UGA', u'UIG', u'UKR', u'UMB', u'UND', u'URD', u'UZB', u'VAI',
            u'VEN', u'VIE', u'VOL', u'VOT', u'WAK', u'WAL', u'WAR', u'WAS',
            u'CYM', u'WEN', u'WLN', u'WOL', u'XAL', u'XHO', u'YAO', u'YAP',
            u'YID', u'YOR', u'YPK', u'ZAP', u'ZBL', u'ZEN', u'ZHA', u'ZND',
            u'ZUL', u'ZUN', u'ZXX', u'ZZA')

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
