# coding: utf-8
"""
Client signon - OFX Section 2.5
"""
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import String, OneOf, DateTime, Bool
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.common import STATUS, MSGSETCORE
from ofxtools.models.i18n import LANG_CODES


__all__ = [
    "FI",
    "SONRQ",
    "SONRS",
    "SIGNONMSGSRQV1",
    "SIGNONMSGSRSV1",
    "SIGNONMSGSETV1",
    "SIGNONMSGSET",
]


class FI(Aggregate):
    """ OFX section 2.5.1.8 """

    org = String(32, required=True)
    fid = String(32)


class SONRQ(Aggregate):
    """ OFX section 2.5.1.5 """

    dtclient = DateTime(required=True)
    userid = String(32)
    userpass = String(171)
    userkey = String(64)
    accesstoken = String(1000)
    genuserkey = Bool()
    language = OneOf(*LANG_CODES, required=True)
    fi = SubAggregate(FI)
    sesscookie = String(1000)
    appid = String(5, required=True)
    appver = String(4, required=True)
    appkey = String(10000)
    clientuid = String(36)
    usercred1 = String(171)
    usercred2 = String(171)
    authtoken = String(171)
    accesskey = String(1000)
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

    @staticmethod
    def groom(elem):
        """ Remove proprietary tags e.g. INTU.XXX """
        # Keep input free of side effects
        elem = deepcopy(elem)

        for child in set(elem):
            if "." in child.tag:
                elem.remove(child)

        return super(SONRS, SONRS).groom(elem)

    # Human-friendly attribute aliases
    @property
    def org(self):
        return self.fi.org

    @property
    def fid(self):
        return self.fi.fid


class SIGNONMSGSRQV1(Aggregate):
    sonrq = SubAggregate(SONRQ)


class SIGNONMSGSRSV1(Aggregate):
    sonrs = SubAggregate(SONRS)


class SIGNONMSGSETV1(Aggregate):
    """ OFX section 2.5.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class SIGNONMSGSET(Aggregate):
    """ OFX section 2.5.5 """

    signonmsgsetv1 = SubAggregate(SIGNONMSGSETV1, required=True)
