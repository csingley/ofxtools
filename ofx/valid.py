import re
import datetime
import time
from decimal import Decimal

from formencode import api, validators, Schema

import utilities

OFXv1 = ('102', '103')
OFXv2 = ('203', '211')
VERSIONS = OFXv1 + OFXv2
APPIDS = ('QWIN', # Quicken for Windows
            'QMOFX', # Quicken for Mac
            'QBW', # QuickBooks for Windows
            'QBM', # QuickBooks for Mac
            'Money', # MSFT Money
            'Money Plus', # MSFT Money Plus
)
APPVERS = ('1500', # Quicken 2006/ Money 2006
            '1600', # Quicken 2007/ Money 2007/ QuickBooks 2006
            '1700', # Quicken 2008/ Money Plus/ QuickBooks 2007
            '1800', # Quicken 2009/ QuickBooks 2008
            '1900', # Quicken 2010/ QuickBooks 2009
            '2000', # QuickBooks 2010
)
HEADER_FIELDS = {'100': ('DATA', 'VERSION', 'SECURITY', 'ENCODING', 'CHARSET',
                        'COMPRESSION', 'OLDFILEUID', 'NEWFILEUID'),}

# Custom formencode validators
class OFXStringBool(validators.StringBool):
    true_values = ['y',]
    false_values = ['n',]

    def _from_python(self, value, state):
        return super(OFXStringBool, self)._from_python(value, state).upper()

class DecimalConverter(validators.Number):
    """ FIXME This is pretty rough """
    def _to_python(self, value, state):
        try:
            value = str(value)
            value = Decimal(value)
            return value
        except (InvalidOperation, ValueError):
            raise Invalid(self.message('number', state),
                                value, state)

#class OFXDatetimeConverter(api.FancyValidator):
    ## Valid datetime formats given by OFX 3.2.8.2
    #tz_re = re.compile(r'\[[-+.\d]*:\w*\]')
    #formats = ('%Y%m%d%H%M%S.%f', '%Y%m%d%H%M%S', '%Y%m%d')

    #def _to_python(self, value, state):
        ## If it's already there, don't push it.
        #if isinstance(value, datetime.datetime):
            #return value
        ## Pristine copy of input for error reporting
        #orig_value = value
        ## Strip out timezone, on which strptime() chokes
        #match = self.tz_re.search(value)
        #if match:
            #tz_delta = match.group().split(':')[0].lstrip('[')
            #tz_delta = int(Decimal(tz_delta)*3600) # in seconds
            #value = value[:match.start()]
        #else:
            #tz_delta = 0

        ## Try each supported format
        #for format in self.formats:
            #try:
                #value = datetime.datetime.strptime(value, format)
                #error = False
                #break
            #except ValueError:
                #error = True
                #continue
        #if error:
            #raise ValueError("Datetime '%s' does not match OFX formats %s" % (orig_value, str(self.formats)))

        ## Adjust timezone to GMT
        #value -= datetime.timedelta(seconds=tz_delta)
        #return value

    #def _from_python(self, value, state):
        #""" Input datetime.datetime in local time; output str in GMT. """
        ## Pristine copy of input for error reporting
        #orig_value = value

        #try:
            ## Transform to GMT
            #value = time.gmtime(time.mktime(value.timetuple()))
            ## timetuples don't have usec precision
            ##value = time.strftime('%s[0:GMT]' % self.formats[1], value)
            #value = time.strftime(self.formats[1], value)
        #except:
            #raise ValueError # FIXME
        #return value

class OFXDatetimeConverter(api.FancyValidator):
    _converter = utilities.OFXDtConverter

    def _to_python(self, value, state):
        return self._converter.to_python(value)

    def _from_python(self, value, state):
        return self._converter.from_python(value)

# Validators specifying allowed item types in the XXXLIST aggregates
BANKTRANLISTitem = validators.OneOf(('STMTTRN',))

SECLISTitem = validators.OneOf(('DEBTINFO', 'MFINFO', 'OPTINFO',
                                'OTHERINFO', 'STOCKINFO'))

INVTRANLISTitem = validators.OneOf(('BUYDEBT', 'BUYMF', 'BUYOPT', 'BUYOTHER',
                        'BUYSTOCK', 'CLOSUREOPT', 'INCOME', 'INVEXPENSE', 'JRNLFND',
                        'JRNLSEC', 'MARGININTEREST', 'REINVEST', 'RETOFCAP',
                        'SELLDEBT', 'SELLMF', 'SELLOPT', 'SELLOTHER', 'SELLSTOCK',
                        'SPLIT', 'TRANSFER', 'INVBANKTRAN'))

POSLISTitem = validators.OneOf(('POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK'))

# Country codes
COUNTRY_CODES = ('ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ANT', 'ARE', 'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH', 'BLM', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN', 'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CXR', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN', 'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'JPN', 'KAZ', 'KEN', 'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAC', 'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD', 'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR', 'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK', 'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI', 'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU', 'RUS', 'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB', 'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'STP', 'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA', 'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV', 'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT', 'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM', 'ZAF', 'ZMB', 'ZWE')

# Currency aggregates
ISO4217codes = ('AE', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG',
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

class CURRENCY(Schema):
    currate = DecimalConverter()
    cursym = validators.OneOf(ISO4217codes)

class ORIGCURRENCY(Schema):
    currate = DecimalConverter()
    cursym = validators.OneOf(ISO4217codes)

# SONRS
class SONRS(Schema):
    dtserver = OFXDatetimeConverter()
    userkey = validators.String(max=64, if_missing=None)
    tskeyexpire = OFXDatetimeConverter(if_missing=None)
    language = validators.OneOf(('ENG',)) # FIXME
    dtprofup = OFXDatetimeConverter(if_missing=None)
    dtacctup = OFXDatetimeConverter(if_missing=None)
    sesscookie = validators.String(max=1000, if_missing=None)
    accesskey = validators.String(max=1000, if_missing=None)


class STATUS(Schema):
    code = validators.Int()
    severity = validators.OneOf(('INFO', 'WARN', 'ERROR'))
    message = validators.String(max=255, if_missing=None)


class FI(Schema):
    org = validators.String(max=32)
    fid = validators.String(max=32, if_missing=None)


# STMTRS preamble
class STMTRS(Schema):
    curdef = validators.OneOf(ISO4217codes)

# BANKTRANLIST preamble
class BANKTRANLIST(Schema):
    dtstart = OFXDatetimeConverter()
    dtend = OFXDatetimeConverter()

# Banking transaction aggregates
ACCOUNT_TYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
TRANSACTION_TYPES = ('CREDIT', 'DEBIT', 'INT', 'DIV', 'FEE', 'SRVCHG', 'DEP', 'ATM', 'POS', 'XFER', 'CHECK', 'PAYMENT', 'CASH', 'DIRECTDEP', 'DIRECTDEBIT', 'REPEATPMT', 'OTHER')
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING', 'ROLLOVER',
'OTHERVEST', 'OTHERNONVEST')

class STMTTRN(Schema):
    trntype = validators.OneOf(TRANSACTION_TYPES)
    dtposted = OFXDatetimeConverter()
    dtuser = OFXDatetimeConverter(if_missing=None)
    dtavail = OFXDatetimeConverter(if_missing=None)
    trnamt = DecimalConverter()
    fitid = validators.String(max=255)
    correctfitid = validators.String(max=255, if_missing=None)
    correctaction = validators.OneOf(('REPLACE', 'DELETE'), if_missing=None)
    srvrtid = validators.String(max=10, if_missing=None)
    checknum = validators.String(max=12, if_missing=None)
    refnum = validators.String(max=32, if_missing=None)
    sic = validators.String(max=6, if_missing=None)
    payeeid = validators.String(max=12, if_missing=None)
    name = validators.String(max=32, if_missing=None)
    memo = validators.String(max=255, if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class LEDGERBAL(Schema):
    balamt = DecimalConverter()
    dtasof = OFXDatetimeConverter()

class AVAILBAL(Schema):
    balamt = DecimalConverter()
    dtasof = OFXDatetimeConverter()

class PAYEE(Schema):
    name = validators.String(max=32)
    addr1 = validators.String(max=32)
    addr2 = validators.String(max=32, if_missing=None)
    addr3 = validators.String(max=32, if_missing=None)
    city = validators.String(max=32)
    state = validators.String(max=5)
    postalcode = validators.String(max=11)
    country = validators.OneOf(COUNTRY_CODES)
    phone = validators.String(max=32)

class BANKACCTFROM(Schema):
    bankid = validators.String(max=9)
    branchid = validators.String(max=22, if_missing=None)
    acctid = validators.String(max=22)
    accttype = validators.OneOf(ACCOUNT_TYPES)
    acctkey = validators.String(max=22, if_missing=None)

class BANKACCTTO(BANKACCTFROM):
    pass

class BAL(Schema):
    name = validators.String(max=32)
    desc = validators.String(max=80)
    baltype = validators.OneOf(('DOLLAR', 'PERCENT', 'NUMBER'))
    value = DecimalConverter()
    dtasof = OFXDatetimeConverter(if_missing=None)

# CCSTMTRS preamble
class CCSTMTRS(Schema):
    curdef = validators.OneOf(ISO4217codes)

class CCACCTFROM(Schema):
    acctid = validators.String(max=22)
    acctkey = validators.String(max=22, if_missing=None)

# Security aggregates
ASSET_CLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK', 'INTLSTOCK', 'MONEYMRKT', 'OTHER')

class SECID(Schema):
    uniqueid = validators.String(max=32)
    uniqueidtype = validators.OneOf(('CUSIP', 'ISIN'))

class SECINFO(Schema):
    secname = validators.String(max=120)
    ticker = validators.String(max=32, if_missing=None)
    fiid = validators.String(max=32, if_missing=None)
    rating = validators.String(max=10, if_missing=None)
    unitprice = DecimalConverter(if_missing=None)
    dtasof = OFXDatetimeConverter(if_missing=None)
    memo = validators.String(max=255, if_missing=None)

class DEBTINFO(Schema):
    parvalue = DecimalConverter()
    debttype = validators.OneOf(('COUPON', 'ZERO'))
    debtclass = validators.OneOf(('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER'), if_missing=None)
    couponrt = DecimalConverter(if_missing=None)
    dtcoupon = OFXDatetimeConverter(if_missing=None)
    couponfreq = validators.OneOf(('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL', 'OTHER'), if_missing=None)
    callprice = DecimalConverter(if_missing=None)
    yieldtocall = DecimalConverter(if_missing=None)
    dtcall = OFXDatetimeConverter(if_missing=None)
    calltype = validators.OneOf(('CALL', 'PUT', 'PREFUND', 'MATURITY'), if_missing=None)
    yieldtomat = DecimalConverter(if_missing=None)
    dtmat = OFXDatetimeConverter(if_missing=None)
    assetclass = validators.OneOf(ASSET_CLASSES, if_missing=None)
    fiassetclass = validators.String(max=32, if_missing=None)

class MFINFO(Schema):
    # FIXME this assetclass jazz with repeated <PORTION> aggregates
    # breaks parsing assumptions
    pass

class OPTINFO(Schema):
    opttype = validators.OneOf(('CALL', 'PUT'))
    strikeprice = DecimalConverter()
    dtexpire = OFXDatetimeConverter()
    shperctrct = validators.Int()
    assetclass = validators.OneOf(ASSET_CLASSES, if_missing=None)
    fiassetclass = validators.String(max=32, if_missing=None)

class OTHERINFO(Schema):
    typedesc = validators.String(max=32, if_missing=None)
    assetclass = validators.OneOf(ASSET_CLASSES, if_missing=None)
    fiassetclass = validators.String(max=32, if_missing=None)

class STOCKINFO(Schema):
    stocktype = validators.OneOf(('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER'), if_missing=None)
    # FIXME 'yield' (from OFX spec) is a reserved word in Python => SyntaxError
    #yield = DecimalConverter(if_missing=None)
    dtyieldasof = OFXDatetimeConverter(if_missing=None)
    typedesc = validators.String(max=32, if_missing=None)
    assetclass = validators.OneOf(ASSET_CLASSES, if_missing=None)
    fiassetclass = validators.String(max=32, if_missing=None)

# INVSTMTRS preamble
class INVSTMTRS(Schema):
    dtasof = OFXDatetimeConverter()
    curdef = validators.OneOf(ISO4217codes)

class INVACCTFROM(Schema):
    brokerid = validators.String(max=22)
    acctid = validators.String(max=22)

# INVTRANLIST preamble
class INVTRANLIST(Schema):
    dtstart = OFXDatetimeConverter()
    dtend = OFXDatetimeConverter()

# Investment Transaction aggregates
SUBACCOUNTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')
BUYTYPES = ('BUY', 'BUYTOCOVER')
SELLTYPES = ('SELL', 'SELLSHORT')
OPTBUYTYPES = ('BUYTOOPEN', 'BUYTOCLOSE')
OPTSELLTYPES = ('SELLTOOPEN', 'SELLTOCLOSE')
INCOMETYPES = ('CGLONG', 'CGSHORT', 'DIV', 'INTEREST', 'MISC')
SECURED_TYPES = ('NAKED', 'COVERED')
POSITIONTYPES = ('SHORT', 'LONG')

class INVTRAN(Schema):
    fitid = validators.String(max=255)
    srvrtid = validators.String(max=10, if_missing=None)
    dttrade = OFXDatetimeConverter()
    dtsettle = OFXDatetimeConverter(if_missing=None)
    reversalfitid = validators.String(max=255, if_missing=None)
    memo = validators.String(max=255, if_missing=None)

class INVBUY(Schema):
    units = DecimalConverter()
    unitprice = DecimalConverter()
    markup = DecimalConverter(if_missing=None)
    commission = DecimalConverter(if_missing=None)
    taxes = DecimalConverter(if_missing=None)
    fees = DecimalConverter(if_missing=None)
    load = DecimalConverter(if_missing=None)
    total = DecimalConverter()
    subacctsec = validators.OneOf(SUBACCOUNTS)
    subacctfund = validators.OneOf(SUBACCOUNTS)
    loanid = validators.String(max=32, if_missing=None)
    loanprincipal = DecimalConverter(if_missing=None)
    loaninterest = DecimalConverter(if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)
    dtpayroll = OFXDatetimeConverter(if_missing=None)
    prioryearcontrib = OFXStringBool(if_missing=None)

class INVSELL(Schema):
    units = DecimalConverter()
    unitprice = DecimalConverter()
    markdown = DecimalConverter(if_missing=None)
    commission = DecimalConverter(if_missing=None)
    taxes = DecimalConverter(if_missing=None)
    fees = DecimalConverter(if_missing=None)
    load = DecimalConverter(if_missing=None)
    withholding = DecimalConverter(if_missing=None)
    taxexempt = OFXStringBool(if_missing=None)
    total = DecimalConverter()
    gain = DecimalConverter(if_missing=None)
    subacctsec = validators.OneOf(SUBACCOUNTS)
    subacctfund = validators.OneOf(SUBACCOUNTS)
    loanid = validators.String(max=32, if_missing=None)
    statewithholding = DecimalConverter(if_missing=None)
    penalty = DecimalConverter(if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class BUYDEBT(Schema):
    accrdint = DecimalConverter(if_missing=None)

class BUYMF(Schema):
    buytype = validators.OneOf(BUYTYPES)
    relfitid = validators.String(max=255, if_missing=None)

class BUYOPT(Schema):
    optbuytype = validators.OneOf(OPTBUYTYPES)
    shperctrct = validators.Int()

class BUYOTHER(Schema):
    pass

class BUYSTOCK(Schema):
    buytype = validators.OneOf(BUYTYPES)

class INCOME(Schema):
    incometype = validators.OneOf(INCOMETYPES)
    total = DecimalConverter()
    subacctsec = validators.OneOf(SUBACCOUNTS)
    subacctfund = validators.OneOf(SUBACCOUNTS)
    withholding = DecimalConverter(if_missing=None)
    taxexempt = OFXStringBool(if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class INVEXPENSE(Schema):
    total = DecimalConverter()
    subacctsec = validators.OneOf(SUBACCOUNTS)
    subacctfund = validators.OneOf(SUBACCOUNTS)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class SELLDEBT(Schema):
    sellreason = validators.OneOf(('CALL','SELL', 'MATURITY'))
    accrdint = DecimalConverter(if_missing=None)

class SELLMF(Schema):
    selltype = validators.OneOf(SELLTYPES)
    avgcostbasis = DecimalConverter(if_missing=None)
    relfitid = validators.String(max=255, if_missing=None)

class SELLOPT(Schema):
    optselltype = validators.OneOf(OPTSELLTYPES)
    shperctrct = validators.Int()
    relfitid = validators.String(max=255, if_missing=None)
    reltype = validators.OneOf(('SPREAD', 'STRADDLE', 'NONE', 'OTHER'), if_missing=None)
    secured = validators.OneOf(SECURED_TYPES, if_missing=None)

class SELLOTHER(Schema):
    pass

class SELLSTOCK(Schema):
    selltype = validators.OneOf(SELLTYPES)

class SPLIT(Schema):
    subacctsec = validators.OneOf(SUBACCOUNTS)
    oldunits = DecimalConverter()
    newunits = DecimalConverter()
    numerator = DecimalConverter()
    denominator = DecimalConverter()
    fraccash = DecimalConverter(if_missing=None)
    subacctfund = validators.OneOf(SUBACCOUNTS, if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class TRANSFER(Schema):
    subacctsec = validators.OneOf(SUBACCOUNTS)
    units = DecimalConverter()
    tferaction = validators.OneOf(('IN', 'OUT'))
    postype = validators.OneOf(POSITIONTYPES)
    avgcostbasis = DecimalConverter(if_missing=None)
    unitprice = DecimalConverter(if_missing=None)
    dtpurchase = OFXDatetimeConverter(if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class JRNLFUND(Schema):
    subacctto = validators.OneOf(SUBACCOUNTS)
    subacctfrom = validators.OneOf(SUBACCOUNTS)
    total = DecimalConverter()

class JRNLSEC(Schema):
    subacctto = validators.OneOf(SUBACCOUNTS)
    subacctfrom = validators.OneOf(SUBACCOUNTS)
    units = DecimalConverter()

class INVBANKTRAN(Schema):
    subacctfund = validators.OneOf(SUBACCOUNTS)

# Investment positions
class INVPOS(Schema):
    heldinacct = validators.OneOf(SUBACCOUNTS)
    postype = validators.OneOf(POSITIONTYPES)
    units = DecimalConverter()
    unitprice = DecimalConverter()
    mktval = DecimalConverter()
    dtpriceasof = OFXDatetimeConverter()
    memo = validators.String(max=255, if_missing=None)
    inv401ksource = validators.OneOf(INV401KSOURCES, if_missing=None)

class POSMF(Schema):
    unitsstreet = DecimalConverter(if_missing=None)
    unitsuser = DecimalConverter(if_missing=None)
    reinvdiv = OFXStringBool(if_missing=None)
    reinvcg = OFXStringBool(if_missing=None)

class POSOPT(Schema):
    secured = validators.OneOf(SECURED_TYPES, if_missing=None)

class POSSTOCK(Schema):
    unitsstreet = DecimalConverter(if_missing=None)
    unitsuser = DecimalConverter(if_missing=None)
    reinvdiv = OFXStringBool(if_missing=None)

# Investment balances
class INVBAL(Schema):
    availcash = DecimalConverter()
    marginbalance = DecimalConverter()
    shortbalance = DecimalConverter()
    buypower = DecimalConverter(if_missing=None)
