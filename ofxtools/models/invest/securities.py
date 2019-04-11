# coding: utf-8
"""
Security information - OFX section 13.7.2
"""
# stdlib imports
from copy import deepcopy


# local imports
from ofxtools.Types import String, NagString, OneOf, Integer, Decimal, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.i18n import CURRENCY


__all__ = [
    "SECID",
    "SECRQ",
    "SECLISTRQ",
    "SECINFO",
    "DEBTINFO",
    "PORTION",
    "MFASSETCLASS",
    "FIPORTION",
    "FIMFASSETCLASS",
    "MFINFO",
    "OPTINFO",
    "OTHERINFO",
    "STOCKINFO",
    "SECLIST",
    "SECLISTRS",
    "SECLISTTRNRQ",
    "SECLISTTRNRS",
]


ASSETCLASSES = (
    "DOMESTICBOND",
    "INTLBOND",
    "LARGESTOCK",
    "SMALLSTOCK",
    "INTLSTOCK",
    "MONEYMRKT",
    "OTHER",
)


class SECID(Aggregate):
    """ OFX section 13.8.1 """

    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class SECRQ(Aggregate):
    """ OFX section 13.8.2.2 """

    secid = SubAggregate(SECID)
    ticker = String(32)
    fiid = String(32)

    requiredMutexes = [("secid", "ticker", "fiid")]


class SECLISTRQ(Aggregate):
    """ OFX section 13.8.2.2 """
    secrq = ListItem(SECRQ)


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
    debttype = OneOf("COUPON", "ZERO", required=True)
    debtclass = OneOf("TREASURY", "MUNICIPAL", "CORPORATE", "OTHER")
    couponrt = Decimal()
    dtcoupon = DateTime()
    couponfreq = OneOf("MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL", "OTHER")
    callprice = Decimal()
    yieldtocall = Decimal()
    dtcall = DateTime()
    calltype = OneOf("CALL", "PUT", "PREFUND", "MATURITY")
    yieldtomat = Decimal()
    dtmat = DateTime()
    assetclass = OneOf(*ASSETCLASSES)
    fiassetclass = String(32)


class PORTION(Aggregate):
    """ OFX section 13.8.5.3 """

    assetclass = OneOf(*ASSETCLASSES, required=True)
    percent = Decimal(required=True)


class MFASSETCLASS(Aggregate):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    portion = ListItem(PORTION)


class FIPORTION(Aggregate):
    """ OFX section 13.8.5.3 """

    fiassetclass = String(32, required=True)
    percent = Decimal(required=True)


class FIMFASSETCLASS(Aggregate):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """

    fiportion = ListItem(FIPORTION)


class MFINFO(Aggregate):
    """ OFX section 13.8.5.3 """

    secinfo = SubAggregate(SECINFO, required=True)
    mftype = OneOf("OPENEND", "CLOSEEND", "OTHER")
    yld = Decimal()
    dtyieldasof = DateTime()
    mfassetclass = SubAggregate(MFASSETCLASS)
    fimfassetclass = SubAggregate(FIMFASSETCLASS)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged YIELD (reserved Python keyword) to YLD
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        yld = elem.find("./YIELD")
        if yld is not None:
            yld.tag = "YLD"

        return super(MFINFO, MFINFO).groom(elem)

    @staticmethod
    def ungroom(elem):
        """
        Rename YLD back to YIELD
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        yld = elem.find("./YLD")
        if yld is not None:
            yld.tag = "YIELD"

        return super(MFINFO, MFINFO).ungroom(elem)


class OPTINFO(Aggregate):
    """ OFX Section 13.8.5.4 """

    secinfo = SubAggregate(SECINFO, required=True)
    opttype = OneOf("CALL", "PUT", required=True)
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
    stocktype = OneOf("COMMON", "PREFERRED", "CONVERTIBLE", "OTHER")
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
        # Keep input free of side effects
        elem = deepcopy(elem)

        yld = elem.find("./YIELD")
        if yld is not None:
            yld.tag = "YLD"

        return super(STOCKINFO, STOCKINFO).groom(elem)

    @staticmethod
    def ungroom(elem):
        """
        Rename YLD back to YLD
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        yld = elem.find("./YLD")
        if yld is not None:
            yld.tag = "YIELD"

        return super(STOCKINFO, STOCKINFO).ungroom(elem)


class SECLIST(Aggregate):
    """ OFX section 13.8.4.4 """

    debtinfo = ListItem(DEBTINFO)
    mfinfo = ListItem(MFINFO)
    optinfo = ListItem(OPTINFO)
    otherinfo = ListItem(OTHERINFO)
    stockinfo = ListItem(STOCKINFO)


class SECLISTTRNRQ(TrnRq):
    """ OFX section 13.8.2.1 """

    seclistrq = SubAggregate(SECLISTRQ, required=True)


class SECLISTRS(Aggregate):
    """
    The only empty aggregate in OFX.

    OFX section 13.8.2.2
    """


class SECLISTTRNRS(TrnRs):
    """ OFX section 13.8.2.1 """

    seclistrs = SubAggregate(SECLISTRS)
