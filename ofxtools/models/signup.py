# coding: utf-8
# local imports
from ofxtools.Types import (
    Bool, DateTime, String, OneOf
)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.bank import (
    BANKACCTFROM, CCACCTFROM,
)
from ofxtools.models.base import (
    Aggregate, SubAggregate, List, Unsupported
)
from ofxtools.models.common import (
    MSGSETCORE, STATUS,
)
from ofxtools.models.investment import INVACCTFROM


__all__ = ['SIGNUPMSGSET', 'SIGNUPMSGSETV1', 'CLIENTENROLL', 'WEBENROLL',
           'OTHERENROLL', 'ACCTINFORQ', 'ACCTINFOTRNRQ', 'SIGNUPMSGSRQV1',
           'SVCSTATUSES', 'BANKACCTINFO', 'CCACCTINFO', 'INVACCTINFO',
           'ACCTINFO', 'ACCTINFORS', 'ACCTINFOTRNRS', 'SIGNUPMSGSRSV1',
           'ENROLLRQ', 'ENROLLRS', 'ENROLLTRNRQ', 'ENROLLTRNRS',
           ]


class CLIENTENROLL(Aggregate):
    """ OFX section 8.8 """
    acctrequired = Bool(required=True)


class WEBENROLL(Aggregate):
    """ OFX section 8.8 """
    url = String(255, required=True)


class OTHERENROLL(Aggregate):
    """ OFX section 8.8 """
    message = String(80, required=True)


class SIGNUPMSGSETV1(Aggregate):
    """ OFX section 8.8 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    clientenroll = SubAggregate(CLIENTENROLL)
    webenroll = SubAggregate(WEBENROLL)
    otherenroll = SubAggregate(OTHERENROLL)
    chguserinfo = Bool(required=True)
    availaccts = Bool(required=True)
    clientactreq = Bool(required=True)


class SIGNUPMSGSET(Aggregate):
    """ OFX section 8.8 """
    signupmsgsetv1 = SubAggregate(SIGNUPMSGSETV1, required=True)


class ACCTINFORQ(Aggregate):
    """ OFX section 8.5.1 """
    dtacctup = DateTime(required=True)


class ACCTINFOTRNRQ(Aggregate):
    """ OFX section 8.5"""
    trnuid = String(36, required=True)
    acctinforq = SubAggregate(ACCTINFORQ, required=True)


class SIGNUPMSGSRQV1(List):
    """ OFX section 8.1 """
    memberTags = ['ENROLLTRNRQ', ]


SVCSTATUSES = ['AVAIL', 'PEND', 'ACTIVE']


class BANKACCTINFO(Aggregate):
    """ OFX section 8.5.3 """
    bankacctfrom = SubAggregate(BANKACCTFROM)
    svcstatus = OneOf(*SVCSTATUSES)
    suptxdl = Unsupported()
    xfersrc = Unsupported()
    xferdest = Unsupported()


class CCACCTINFO(Aggregate):
    """ OFX section 8.5.3 """
    ccacctfrom = SubAggregate(CCACCTFROM)
    svcstatus = OneOf(*SVCSTATUSES)


class INVACCTINFO(Aggregate):
    """ OFX section 8.5.3 """
    invacctfrom = SubAggregate(INVACCTFROM)
    svcstatus = OneOf(*SVCSTATUSES)


class ACCTINFO(Aggregate):
    """ OFX section 8.5.3 """
    desc = String(80)
    phone = String(32)
    bankacctinfo = SubAggregate(BANKACCTINFO)
    ccacctinfo = SubAggregate(CCACCTINFO)
    invacctinfo = SubAggregate(INVACCTINFO)


class ACCTINFORS(Aggregate):
    """ OFX section 8.5.1 """
    dtacctup = DateTime(required=True)
    acctinfo = SubAggregate(ACCTINFO)


class ACCTINFOTRNRS(Aggregate):
    """ OFX section 8.5.1 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    acctinfors = SubAggregate(ACCTINFORS)


class SIGNUPMSGSRSV1(List):
    """ OFX section 8.1 """
    memberTags = ['ENROLLTRNRS', ]


class ENROLLRQ(Aggregate):
    """ OFX section 8.4.2 """
    firstname = String(32, required=True)
    middlename = String(32)
    lastname = String(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    dayphone = String(32)
    evephone = String(32)
    email = String(80, required=True)
    userid = String(32)
    taxid = String(32)
    securityname = String(32)
    datebirth = DateTime()
    bankacctFrom = SubAggregate(BANKACCTFROM)
    ccacctFrom = SubAggregate(CCACCTFROM)
    invacctFrom = SubAggregate(INVACCTFROM)

    mutexes = [('BANKACCTFROM', 'CCACCTFROM'), ('BANKACCTFROM', 'INVACCTFROM'),
               ('CCACCTFROM', 'INVACCTFROM')]


class ENROLLTRNRQ(Aggregate):
    """ OFX section 8.4.2 """
    trnuid = String(36, required=True)
    enrollrq = SubAggregate(ENROLLRQ, required=True)


class ENROLLRS(Aggregate):
    """ OFX section 8.4.3 """
    temppass = String(32)
    userid = String(32)
    dtexpire = DateTime()


class ENROLLTRNRS(Aggregate):
    """ OFX section 8.4.3 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    enrollrs = SubAggregate(ENROLLRS, required=True)
