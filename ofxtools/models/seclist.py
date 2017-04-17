# coding: utf-8
"""
Message set response aggregates (i.e. *MSGSRSV1) - OFX section 2.4.5
"""
# local imports
from ofxtools.Types import (
    String,
    NagString,
    Integer,
    Decimal,
    DateTime,
    OneOf,
)
from ofxtools.models.base import (
    Aggregate,
    SubAggregate,
    List,
)
from ofxtools.models.i18n import CURRENCY


ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


class SECID(Aggregate):
    """ OFX section 13.8.1 """
    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class Secid(object):
    """ Mixin """
    secid = SubAggregate(SECID, required=True)

    @property
    def uniqueid(self):
        return self.secid.uniqueid

    @property
    def uniqueidtype(self):
        return self.secid.uniqueidtype


class SECINFO(Aggregate, Secid):
    """ OFX Section 13.8.5.1 """
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
    currency = SubAggregate(CURRENCY)
    memo = String(255)


class Secinfo(object):
    """ Mixin """
    secinfo = SubAggregate(SECINFO, required=True)

    @property
    def uniqueid(self):
        return self.secinfo.secid.uniqueid

    @property
    def uniqueidtype(self):
        return self.secinfo.secid.uniqueidtype


class DEBTINFO(Aggregate, Secinfo):
    """ OFX Section 13.8.5.2 """
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


class PORTION(Aggregate):
    """ OFX section 13.8.5.3 """
    assetclass = OneOf(*ASSETCLASSES, required=True)
    percent = Decimal(required=True)


class MFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    memberTags = ['PORTION', ]


class FIPORTION(Aggregate):
    """ OFX section 13.8.5.3 """
    fiassetclass = String(32, required=True)
    percent = Decimal(required=True)


class FIMFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    memberTags = ['FIPORTION', ]


class MFINFO(Aggregate, Secinfo):
    """ OFX section 13.8.5.3 """
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    mfassetclass = SubAggregate(MFASSETCLASS)
    fimfassetclass = SubAggregate(FIMFASSETCLASS)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(MFINFO, MFINFO).groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'


class OPTINFO(Aggregate, Secinfo):
    """ OFX Section 13.8.5.4 """
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    secid = SubAggregate(SECID)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class OTHERINFO(Aggregate, Secinfo):
    """ OFX Section 13.8.5.5 """
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class STOCKINFO(Aggregate, Secinfo):
    """ OFX Section 13.8.5.6 """
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal(4)
    dtyieldasof = DateTime()
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        super(STOCKINFO, STOCKINFO).groom(elem)

        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'


class SECLIST(List):
    """ OFX section 13.8.4.4 """
    memberTags = ['DEBTINFO', 'MFINFO', 'OPTINFO', 'OTHERINFO', 'STOCKINFO', ]


class SECLISTMSGSRSV1(Aggregate):
    """ """
    seclist = SubAggregate(SECLIST)
