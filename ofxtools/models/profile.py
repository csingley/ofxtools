# coding: utf-8
# local imports
from ofxtools.Types import (
    String, OneOf, DateTime,
)
from ofxtools.models.base import (
    Aggregate, SubAggregate, List,
)
from ofxtools.models.common import (STATUS, MSGSETCORE)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.signon import SIGNONINFOLIST


__all__ = ['PROFMSGSRQV1', 'PROFMSGSRSV1', 'PROFTRNRQ', 'PROFTRNRS', 'PROFRQ',
           'PROFRS', 'MSGSETLIST', 'PROFMSGSETV1', 'PROFMSGSET', ]


class PROFRQ(Aggregate):
    """ OFX section 7.1.5 """
    clientrouting = OneOf('NONE', 'SERVICE', 'MSGSET', required=True)
    dtprofup = DateTime(required=True)


class MSGSETLIST(List):
    dataTags = ['SIGNONMSGSET', 'SIGNUPMSGSET', 'PROFMSGSET',
                'BANKMSGSET', 'CREDITCARDMSGSET', 'INVSTMTMSGSET',
                'SECLISTMSGSET', 'TAX1099MSGSET']


class PROFRS(Aggregate):
    """ OFX section 7.2 """
    msgsetlist = SubAggregate(MSGSETLIST, required=True)
    signoninfolist = SubAggregate(SIGNONINFOLIST, required=True)
    dtprofup = DateTime(required=True)
    finame = String(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES, required=True)
    csphone = String(32)
    tsphone = String(32)
    faxphone = String(32)
    url = String(255)
    email = String(80)

    @staticmethod
    def groom(elem):
        """
        Remove proprietary tags e.g. INTU.XXX
        """
        for child in set(elem):
            if '.' in child.tag:
                elem.remove(child)

        return super(PROFRS, PROFRS).groom(elem)


class PROFTRNRQ(Aggregate):
    trnuid = String(36, required=True)
    profrq = SubAggregate(PROFRQ)


class PROFTRNRS(Aggregate):
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS)
    profrs = SubAggregate(PROFRS)

    @property
    def profile(self):
        return self.profrs


class PROFMSGSRQV1(List):
    dataTags = ['PROFTRNRQ']


class PROFMSGSRSV1(List):
    dataTags = ['PROFTRNRS']


class PROFMSGSETV1(Aggregate):
    """ OFX section 7.3 """
    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class PROFMSGSET(Aggregate):
    """ OFX section 7.3 """
    profmsgsetv1 = SubAggregate(PROFMSGSETV1, required=True)
