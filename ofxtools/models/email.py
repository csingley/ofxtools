# coding: utf-8
"""
email - OFX Section 9
"""


__all__ = [
    "MAIL",
    "MAILRQ",
    "MAILRS",
    "MAILTRNRQ",
    "MAILTRNRS",
    "MAILSYNCRQ",
    "MAILSYNCRS",
    "GETMIMERQ",
    "GETMIMERS",
    "GETMIMETRNRQ",
    "GETMIMETRNRS",
    "EMAILMSGSRQV1",
    "EMAILMSGSRSV1",
    "EMAILMSGSETV1",
    "EMAILMSGSET",
]


# stdlib imports
from copy import deepcopy
import logging


# local imports
from ofxtools.Types import Bool, String, DateTime, SubAggregate, ListAggregate
from ofxtools.models.base import Aggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.common import MSGSETCORE


logger = logging.getLogger(__name__)


class MAIL(Aggregate):
    """OFX section 9.2.2"""

    userid = String(32, required=True)
    dtcreated = DateTime(required=True)
    frm = String(32, required=True)
    to = String(32, required=True)
    subject = String(60, required=True)
    msgbody = String(10000, required=True)
    incimages = Bool(required=True)
    usehtml = Bool(required=True)

    @staticmethod
    def groom(elem):
        """
        Rename all Elements tagged FROM (reserved Python keyword) to FROM
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        frm = elem.find("./FROM")
        if frm is not None:
            logger.debug("Renaming <FROM> to <FRM>")
            frm.tag = "FRM"

        return super(MAIL, MAIL).groom(elem)

    @staticmethod
    def ungroom(elem):
        """
        Rename FRM back to FROM
        """
        # Keep input free of side effects
        elem = deepcopy(elem)

        frm = elem.find("./FRM")
        if frm is not None:
            logger.debug("Renaming <FRM> to <FROM>")
            frm.tag = "FROM"

        return super(MAIL, MAIL).ungroom(elem)


class MAILRQ(Aggregate):
    """OFX section 9.2.3"""

    mail = SubAggregate(MAIL, required=True)


class MAILRS(Aggregate):
    """OFX section 9.2.3"""

    mail = SubAggregate(MAIL, required=True)


class MAILTRNRQ(TrnRq):
    """OFX section 9.2.3"""

    mailrq = SubAggregate(MAILRQ, required=True)


class MAILTRNRS(TrnRs):
    """OFX section 9.2.3"""

    mailrs = SubAggregate(MAILRS)


class MAILSYNCRQ(SyncRqList):
    """OFX section 9.2.4"""

    incimages = Bool(required=True)
    usehtml = Bool(required=True)
    mailtrnrq = ListAggregate(MAILTRNRQ)


class MAILSYNCRS(SyncRsList):
    """OFX section 9.2.4"""

    mailtrnrs = ListAggregate(MAILTRNRS)


class GETMIMERQ(Aggregate):
    """OFX section 9.3.1"""

    url = String(255, required=True)


class GETMIMERS(Aggregate):
    """OFX section 9.3.1"""

    url = String(255, required=True)


class GETMIMETRNRQ(TrnRq):
    """OFX section 9.3.2"""

    getmimerq = SubAggregate(GETMIMERQ, required=True)


class GETMIMETRNRS(TrnRs):
    """OFX section 9.3.2"""

    getmimers = SubAggregate(GETMIMERS)


class EMAILMSGSRQV1(Aggregate):
    """OFX section 9.4.1.1"""

    mailtrnrq = ListAggregate(MAILTRNRQ)
    getmimetrnrq = ListAggregate(GETMIMETRNRQ)
    mailsyncrq = ListAggregate(MAILSYNCRQ)


class EMAILMSGSRSV1(Aggregate):
    """OFX section 9.4.1.2"""

    mailtrnrs = ListAggregate(MAILTRNRS)
    getmimetrnrs = ListAggregate(GETMIMETRNRS)
    mailsyncrs = ListAggregate(MAILSYNCRS)


class EMAILMSGSETV1(Aggregate):
    """OFX section 9.4.2"""

    msgsetcore = SubAggregate(MSGSETCORE, required=True)
    mailsup = Bool(required=True)
    getmimesup = Bool(required=True)


class EMAILMSGSET(Aggregate):
    """OFX section 9.4.2"""

    emailmsgsetv1 = SubAggregate(EMAILMSGSETV1, required=True)
