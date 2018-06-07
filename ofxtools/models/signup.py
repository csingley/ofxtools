# coding: utf-8
# local imports
from ofxtools.Types import (
    Bool, DateTime, String, OneOf
)
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
           'ACCTINFO', 'ACCTINFORS', 'ACCTINFOTRNRS', 'SIGNUPMSGSRSV1'
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
    memberTags = ['ACCTINFOTRNRQ', ]


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
    inacctfrom = SubAggregate(INVACCTFROM)
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
    memberTags = ['ACCTINFOTRNRS', ]
