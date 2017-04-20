# coding: utf-8
# local imports
from ofxtools.Types import (
    String, Integer, OneOf, DateTime, Bool,
)
from ofxtools.models.base import (
    Aggregate, SubAggregate, List, Unsupported,
)
from ofxtools.models.common import (STATUS, MSGSETCORE,)
from ofxtools.models.i18n import LANG_CODES


__all__ = ['SIGNONMSGSRQV1', 'SIGNONMSGSRSV1', 'SONRQ', 'SONRS', 'FI', ]


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


class SIGNONINFO(Aggregate):
    """ OFX section 7.2.2 """
    signonrealm = String(32, required=True)
    min = Integer(required=True)
    max = Integer(required=True)
    chartype = OneOf('ALPHAONLY', 'NUMERICONLY', 'ALPHAORNUMERIC',
                     'ALPHAANDNUMERIC', required=True)
    casesen = Bool(required=True)
    special = Bool(required=True)
    spaces = Bool(required=True)
    pinch = Bool(required=True)
    chpinfirst = Bool(required=True)
    usercred1label = String(64)
    usercred2label = String(64)
    clientuidreq = Bool()
    authtokenfirst = Bool()
    authtokenlabel = String(64)
    authtokeninfourl = String(255)
    mfachallengesupt = Bool()
    mfachallengefirst = Bool()
    accesstokenreq = Bool()


class SIGNONINFOLIST(List):
    """ OFX section 7.2 """
    memberTags = ['SIGNONINFO', ]


class SIGNONMSGSRQV1(Aggregate):
    """ """
    sonrq = SubAggregate(SONRQ)


class SIGNONMSGSRSV1(Aggregate):
    """ """
    sonrs = SubAggregate(SONRS)


class SIGNONMSGSETV1(Aggregate):
    """ OFX section 2.5.5 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class SIGNONMSGSET(Aggregate):
    """ OFX section 2.5.5 """
    signonmsgsetv1 = SubAggregate(SIGNONMSGSETV1, required=True)
