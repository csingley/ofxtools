# coding: utf-8
from ofxtools.Types import (
    String,
    OneOf,
    DateTime,
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


class SIGNONMSGSRSV1(Aggregate):
    """ """
    sonrs = SubAggregate(SONRS)
