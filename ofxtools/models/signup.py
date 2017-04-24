# coding: utf-8
# local imports
from ofxtools.Types import (
    Bool, String,
)
from ofxtools.models.base import (
    Aggregate, SubAggregate,
)
from ofxtools.models.common import MSGSETCORE


__all__ = ['SIGNUPMSGSET', 'SIGNUPMSGSETV1', 'CLIENTENROLL', 'WEBENROLL',
           'OTHERENROLL', ]


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
