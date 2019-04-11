# coding: utf-8
"""
Base classes for OFX message wrappers

These can't be defined in models.base because models.common.STATUS would
create circular imports.
"""
# local imports
from ofxtools.Types import Bool, String, DateTime
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.common import STATUS, OFXEXTENSION


__all__ = ["TrnRq", "TrnRs", "SyncRqList", "SyncRsList"]


class TrnRq(Aggregate):
    """
    Base class for *TRNRQ wrappers.

    OFX section 2.4.6.1
    """

    trnuid = String(36, required=True)
    cltcookie = String(32)
    tan = String(80)
    ofxextension = SubAggregate(OFXEXTENSION)


class TrnRs(Aggregate):
    """
    Base class for *TRNRS wrappers.

    OFX section 2.4.6.1
    """

    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    cltcookie = String(32)
    ofxextension = SubAggregate(OFXEXTENSION)


class TranList(Aggregate):
    """
    Base class for OFX *TRANLIST

    Cf. OFX section 3.2.7
    """

    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)

    def __repr__(self):
        return "<{} dtstart='{}' dtend='{}' len={}>".format(
            self.__class__.__name__, self.dtstart, self.dtend, len(self)
        )


class SyncRqList(Aggregate):
    """ Base class for *SYNCRQ """

    token = String(10)
    tokenonly = Bool()
    refresh = Bool()
    rejectifmissing = Bool(required=True)

    requiredMutexes = [("token", "tokenonly", "refresh")]


class SyncRsList(Aggregate):
    """ Base class for *SYNCRS """

    token = String(10, required=True)
    lostsync = Bool()
