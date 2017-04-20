# coding: utf-8
from ofxtools.Types import (
    String,
    OneOf,
    DateTime,
    Bool,
)
from ofxtools.models.base import (
    Aggregate,
    SubAggregate,
    Unsupported,
)
from ofxtools.models.common import STATUS
from ofxtools.models.i18n import LANG_CODES


__all__ = ['SIGNONMSGSRSV1', 'SONRS', 'FI', ]


class FI(Aggregate):
    """ OFX section 2.5.1.8 """
    org = String(32, required=True)
    fid = String(32)


class SONRQ(Aggregate):
    """ OFX section 2.5.1.5 """
    dtclient = DateTime(required=True)
    userid = String(32)
    userpass = String(171)
    # userkey = String(64)
    userkey = Unsupported()
    # accesstoken = String(10000)
    accesstoken = Unsupported()
    # genuserkey = Bool()
    genuserkey = Unsupported()
    language = OneOf(*LANG_CODES, required=True)
    fi = SubAggregate(FI)
    sesscookie = String(1000)
    appid = String(5, required=True)
    appver = String(4, required=True)
    # appkey = String(10000)
    appkey = Unsupported()
    clientuid = String(36)
    # usercred1 = String(171)
    usercred1 = Unsupported()
    # usercred2 = String(171)
    usercred2 = Unsupported()
    # authtoken = String(171)
    authtoken = Unsupported()
    # accesskey = String(1000)
    accesskey = Unsupported()
    mfachallengeanswer = Unsupported()
    ofxextension = Unsupported()


class SONRS(Aggregate):
    """ OFX section 2.5.1.6 """
    status = SubAggregate(STATUS, required=True)
    dtserver = DateTime(required=True)
    userkey = String(64)
    tskeyexpire = DateTime()
    language = OneOf(*LANG_CODES, required=True)
    dtprofup = DateTime()
    dtacctup = DateTime()
    fi = SubAggregate(FI)
    sesscookie = String(1000)
    accesskey = String(1000)
    ofxextension = Unsupported()


class SIGNONMSGSRQV1(Aggregate):
    """ """
    sonrq = SubAggregate(SONRQ)


class SIGNONMSGSRSV1(Aggregate):
    """ """
    sonrs = SubAggregate(SONRS)
