# coding: utf-8
"""
Message set response aggregates (i.e. *MSGSRSV1) - OFX section 2.4.5
"""
# local imports
from ofxtools.Types import (
    String, NagString, Integer, Decimal, DateTime, OneOf, Bool,
)
from ofxtools.models.base import (
    Aggregate, SubAggregate, List, Unsupported,
)
from ofxtools.models.common import MSGSETCORE
from ofxtools.models.i18n import CURRENCY


__all__ = ['SECLISTMSGSETV1', 'SECLISTMSGSET', 'SECLISTMSGSRSV1', 'SECLIST',
           'MFASSETCLASS', 'PORTION', 'FIMFASSETCLASS', 'FIPORTION', 'SECID',
           'SECINFO', 'DEBTINFO', 'MFINFO', 'OPTINFO', 'OTHERINFO',
           'STOCKINFO', 'SECRQ', 'SECLISTRQ', 'SECLISTTRNRQ',
           'SECLISTMSGSRQV1', 'SECLISTMSGSRSV1', 'SECLISTMSGSETV1',
           'SECLISTMSGSET', ]


ASSETCLASSES = ('DOMESTICBOND', 'INTLBOND', 'LARGESTOCK', 'SMALLSTOCK',
                'INTLSTOCK', 'MONEYMRKT', 'OTHER')


class SECID(Aggregate):
    """ OFX section 13.8.1 """
    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class SECINFO(Aggregate):
    """ OFX Section 13.8.5.1 """
    secid = SubAggregate(SECID, required=True)
    # FIs abuse SECNAME/TICKER
    # Relaxing the length constraints from the OFX spec does little harm
    secname = NagString(120, required=True)
    ticker = NagString(32)
    fiid = String(32)
    rating = String(10)
    unitprice = Decimal()
    dtasof = DateTime()
    currency = SubAggregate(CURRENCY)
    memo = String(255)


class DEBTINFO(Aggregate):
    """ OFX Section 13.8.5.2 """
    secinfo = SubAggregate(SECINFO, required=True)
    parvalue = Decimal(required=True)
    debttype = OneOf('COUPON', 'ZERO', required=True)
    debtclass = OneOf('TREASURY', 'MUNICIPAL', 'CORPORATE', 'OTHER')
    couponrt = Decimal()
    dtcoupon = DateTime()
    couponfreq = OneOf('MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL',
                       'OTHER')
    callprice = Decimal()
    yieldtocall = Decimal()
    dtcall = DateTime()
    calltype = OneOf('CALL', 'PUT', 'PREFUND', 'MATURITY')
    yieldtomat = Decimal()
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class PORTION(Aggregate):
    """ OFX section 13.8.5.3 """
    assetclass = OneOf(*ASSETCLASSES, required=True)
    percent = Decimal(required=True)


class MFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    dataTags = ['PORTION']


class FIPORTION(Aggregate):
    """ OFX section 13.8.5.3 """
    fiassetclass = String(32, required=True)
    percent = Decimal(required=True)


class FIMFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    dataTags = ['FIPORTION']


class MFINFO(Aggregate):
    """ OFX section 13.8.5.3 """
    secinfo = SubAggregate(SECINFO, required=True)
    mftype = OneOf('OPENEND', 'CLOSEEND', 'OTHER')
    yld = Decimal()
    dtyieldasof = DateTime()
    mfassetclass = SubAggregate(MFASSETCLASS)
    fimfassetclass = SubAggregate(FIMFASSETCLASS)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'

        return super(MFINFO, MFINFO).groom(elem)

    @staticmethod
    def ungroom(elem):
        """
        Rename YLD back to YLD
        """
        yld = elem.find('./YLD')
        if yld is not None:
            yld.tag = 'YIELD'

        return super(MFINFO, MFINFO).ungroom(elem)


class OPTINFO(Aggregate):
    """ OFX Section 13.8.5.4 """
    secinfo = SubAggregate(SECINFO, required=True)
    opttype = OneOf('CALL', 'PUT', required=True)
    strikeprice = Decimal(required=True)
    dtexpire = DateTime(required=True)
    shperctrct = Integer(required=True)
    secid = SubAggregate(SECID)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class OTHERINFO(Aggregate):
    """ OFX Section 13.8.5.5 """
    secinfo = SubAggregate(SECINFO, required=True)
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class STOCKINFO(Aggregate):
    """ OFX Section 13.8.5.6 """
    secinfo = SubAggregate(SECINFO, required=True)
    stocktype = OneOf('COMMON', 'PREFERRED', 'CONVERTIBLE', 'OTHER')
    yld = Decimal()
    dtyieldasof = DateTime()
    typedesc = String(32)
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        yld = elem.find('./YIELD')
        if yld is not None:
            yld.tag = 'YLD'

        return super(STOCKINFO, STOCKINFO).groom(elem)

    @staticmethod
    def ungroom(elem):
        """
        Rename YLD back to YLD
        """
        yld = elem.find('./YLD')
        if yld is not None:
            yld.tag = 'YIELD'

        return super(STOCKINFO, STOCKINFO).ungroom(elem)


class SECLIST(List):
    """ OFX section 13.8.4.4 """
    dataTags = ['DEBTINFO', 'MFINFO', 'OPTINFO', 'OTHERINFO', 'STOCKINFO']


class SECRQ(Aggregate):
    """ OFX section 13.8.2.2 """
    secid = SubAggregate(SECID)
    ticker = String(32)
    fiid = String(32)


class SECLISTRQ(List):
    """ OFX section 13.8.2.2 """
    dataTags = ['SECRQ']


class SECLISTTRNRQ(Aggregate):
    """ OFX section 13.8.2.1 """
    trnuid = String(36, required=True)
    cltcookie = String(32)
    tan = String(80)
    ofxextension = Unsupported()
    seclisttrq = SubAggregate(SECLISTRQ)


class SECLISTMSGSRQV1(Aggregate):
    """ OFX section 13.7.2.2.1 """
    seclisttrnrq = SubAggregate(SECLISTTRNRQ)


class SECLISTMSGSRSV1(Aggregate):
    """ """
    seclist = SubAggregate(SECLIST)


class SECLISTMSGSETV1(Aggregate):
    """ OFX section 13.7.2.1 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    seclistrqdnld = Bool(required=True)


class SECLISTMSGSET(Aggregate):
    """ OFX section 13.7.2.1 """
    seclistmsgsetv1 = SubAggregate(SECLISTMSGSETV1, required=True)
