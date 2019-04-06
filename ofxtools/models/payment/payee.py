# coding: utf-8
"""
PAYEE aggregate - OFX Section 12.5.2.1

This class is defined in its own module to avoid circular imports
"""
from ofxtools.Types import String, NagString, OneOf
from ofxtools.models.base import Aggregate
from ofxtools.models.i18n import COUNTRY_CODES


class PAYEE(Aggregate):
    """ OFX section 12.5.2.1 """

    name = NagString(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32, required=True)
