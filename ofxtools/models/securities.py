# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import (
    Aggregate,
    SECID,
    CURRENCY,
    ASSETCLASSES,
)
from ofxtools.Types import (
    String,
    OneOf,
    Integer,
    Decimal,
    DateTime,
    NagString,
)


class SECINFO(CURRENCY, SECID):
    """ """
    # FIs abuse SECNAME/TICKER
    # Relaxing the length constraints from the OFX spec does little harm
    # secname = String(120, required=True)
    secname = NagString(120, required=True)
    # ticker = String(32)
    ticker = NagString(32)
    fiid = String(32)
    rating = String(10)
    unitprice = Decimal()
    dtasof = DateTime()
    memo = String(255)


class DEBTINFO(SECINFO):
    """ """
    parvalue = Decimal(required=True)
    debttype = OneOf('COUPON', 'ZERO', required=True)
    debtclass = OneOf('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
    couponrt = Decimal(4)
    dtcoupon = DateTime()
    couponfreq = OneOf('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                       'OTHER')
    callprice = Decimal(4)
    yieldtocall = Decimal(4)
    dtcall = DateTime()
    calltype = OneOf('CALL', 'PUT', 'PREFUND', 'MATURITY')
    yieldtomat = Decimal(4)
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class MFINFO(SECINFO):
    """ OFX section 13.8.5.3 """
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()

    mfassetclass = []
    fimfassetclass = []

    _subaggregates = ('MFASSETCLASS', 'FIMFASSETCLASS')

    @staticmethod
    def _groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(MFINFO, MFINFO)._groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'


class PORTION(Aggregate):
    """ """
    assetclass = OneOf(*ASSETCLASSES, required=True)
    percent = Decimal(required=True)


class FIPORTION(Aggregate):
    """ """
    fiassetclass = String(32, required=True)
    percent = Decimal(required=True)


class OPTINFO(SECINFO):
    """ """
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    _subaggregates = ('SECID',)


class OTHERINFO(SECINFO):
    """ """
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class STOCKINFO(SECINFO):
    """ """
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    @staticmethod
    def _groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(STOCKINFO, STOCKINFO)._groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'
