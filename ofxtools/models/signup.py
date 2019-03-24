# coding: utf-8
# stdlib imports
import operator
import itertools

# local imports
from ofxtools.Types import (
    Bool, DateTime, String, OneOf
)
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.bank import (
    BANKACCTFROM, CCACCTFROM, BANKACCTTO, CCACCTTO, BANKACCTINFO, CCACCTINFO
)
from ofxtools.models.base import (
    Aggregate, SubAggregate, Unsupported,
    List, SyncRqList, SyncRsList,
)
from ofxtools.models.common import (MSGSETCORE, STATUS, SVCSTATUSES)
from ofxtools.models.investment import (INVACCTFROM, INVACCTTO, INVACCTINFO)


__all__ = ['SIGNUPMSGSET', 'SIGNUPMSGSETV1', 'SIGNUPMSGSRQV1', 'SIGNUPMSGSRSV1',
           'ENROLLTRNRQ', 'ENROLLTRNRS', 'ENROLLRQ', 'ENROLLRS',
           'CLIENTENROLL', 'WEBENROLL', 'OTHERENROLL',
           'ACCTINFOTRNRQ', 'ACCTINFOTRNRS', 'ACCTINFORQ', 'ACCTINFORS',
           'ACCTINFO', 'ACCTTRNRQ', 'ACCTTRNRS', 'ACCTRQ', 'ACCTRS',
           'SVCADD', 'SVCCHG', 'SVCDEL', 'ACCTSYNCRQ', 'ACCTSYNCRS',
           'CHGUSERINFOTRNRQ', 'CHGUSERINFOTRNRS', 'CHGUSERINFORQ',
           'CHGUSERINFORS', 'CHGUSERINFOSYNCRQ', 'CHGUSERINFOSYNCRS',
           ]

# Enums used in aggregate validation
SVCS = ('BANKSVC', 'BPSVC', 'INVSVC', 'PRESSVC')


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

    optionalMutexes = [
        ('clientenroll', 'webenroll'),
        ('clientenroll', 'otherenroll'),
        ('webenroll', 'otherenroll')]


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
    dataTags = ['ENROLLTRNRQ']


class ACCTINFO(List):
    """
    OFX section 8.5.3

    The text description is a little ambiguous.  Here's what the DTD says:
    <xsd:sequence>
        <xsd:element name="DESC" type="ofx:ShortMessageType" minOccurs="0"/>
        <xsd:element name="PHONE" type="ofx:PhoneType" minOccurs="0"/>
        <xsd:sequence maxOccurs="unbounded">
            <xsd:choice>
                <xsd:element name="BANKACCTINFO" type="ofx:BankAccountInfo"/>
                <xsd:element name="CCACCTINFO" type="ofx:CreditCardAccountInfo"/>
                <xsd:element name="BPACCTINFO" type="ofx:BillPaymentAccountInfo"/>
                <xsd:element name="INVACCTINFO" type="ofx:InvestmentAccountInfo"/>
                <xsd:element name="PRESACCTINFO" type="ofx:PresentmentAccountInfo"/>
            </xsd:choice>
        </xsd:sequence>
    </xsd:sequence>
    """
    desc = String(80)
    phone = String(32)

    metadataTags = ['DESC', 'PHONE']
    dataTags = ['BANKACCTINFO', 'CCACCTINFO', 'BPACCTINFO', 'INVACCTINFO',
                'PRESACCTINFO']

    def __init__(self, desc=None, phone=None, *members):
        self.desc = desc
        self.phone = phone

        # Must contain at least one <xxxACCTINFO>
        if not members:
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(self.__class__.__name__,
                                        self.dataTags))

        #  For a given service xxx, there can be at most one <xxxACCTINFO>
        #  returned. For example, you cannot return two <BANKACCTINFO>
        #  aggregates.
        sortKey = operator.attrgetter('__class__.__name__')
        members_copy = sorted(members, key=sortKey)
        for tag, group in itertools.groupby(members_copy, key=sortKey):
            if len(list(group)) > 1:
                msg = "{} contains multiple {} aggregates"
                raise ValueError(msg.format(self.__class__, tag))

        super().__init__(*members)

    def __repr__(self):
        return "<{} desc='{}' phone='{}' len={}>".format(
            self.__class__.__name__, self.desc, self.phone, len(self))


class ACCTINFORS(List):
    """ OFX section 8.5.2 """
    dtacctup = DateTime(required=True)

    metadataTags = ['DTACCTUP']

    dataTags = ['ACCTINFO']

    def __init__(self, dtacctup, *members):
        self.dtacctup = dtacctup
        super().__init__(*members)

    def __repr__(self):
        return "<{} dtacctup='{}' len={}>".format(
            self.__class__.__name__, self.dtacctup, len(self))


class ACCTINFOTRNRS(Aggregate):
    """ OFX section 8.5.2 """
    trnuid = String(36, required=True)
    status = SubAggregate(STATUS, required=True)
    acctinfors = SubAggregate(ACCTINFORS)


class SIGNUPMSGSRSV1(List):
    """ OFX section 8.1 """
    dataTags = ['ENROLLTRNRS']


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
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    invacctfrom = SubAggregate(INVACCTFROM)

    optionalMutexes = [
        ('bankacctfrom', 'ccacctfrom'),
        ('bankacctfrom', 'invacctfrom'),
        ('ccacctfrom', 'invacctfrom')]


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


class SVCADD(Aggregate):
    """ OFX section 8.6.1.1 """
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    invacctto = SubAggregate(INVACCTTO)

    requiredMutexes = [('bankacctto', 'ccacctto', 'invacctto'), ]


class SVCCHG(Aggregate):
    """ OFX section 8.6.1.2 """
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    invacctfrom = SubAggregate(INVACCTFROM)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    invacctto = SubAggregate(INVACCTTO)

    requiredMutexes = [
        ('bankacctfrom', 'ccacctfrom', 'invacctfrom'),
        ('bankacctto', 'ccacctto', 'invacctto'),
    ]


class SVCDEL(Aggregate):
    """ OFX section 8.6.1.1 """
    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    invacctfrom = SubAggregate(INVACCTFROM)

    requiredMutexes = [('bankacctfrom', 'ccacctfrom', 'invacctfrom'), ]


class ACCTRQ(Aggregate):
    """ OFX section 8.6.1 """
    svcadd = SubAggregate(SVCADD)
    svcchg = SubAggregate(SVCCHG)
    svcdel = SubAggregate(SVCDEL)
    svc = OneOf(*SVCS, required=True)

    requiredMutexes = [('svcadd', 'svcchg', 'svcdel'), ]


class ACCTRS(Aggregate):
    """ OFX section 8.6.2 """
    svcadd = SubAggregate(SVCADD)
    svcchg = SubAggregate(SVCCHG)
    svcdel = SubAggregate(SVCDEL)
    svc = OneOf(*SVCS, required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)

    requiredMutexes = [('svcadd', 'svcchg', 'svcdel'), ]


class ACCTTRNRQ(Aggregate):
    """ OFX section 8.6.1 """
    trnuid = String(36, required=True)
    acctrq = SubAggregate(ACCTRQ, required=True)


class ACCTTRNRS(Aggregate):
    """ OFX section 8.6.2 """
    trnuid = String(36, required=True)
    acctrs = SubAggregate(ACCTRS, required=True)


class ACCTSYNCRQ(SyncRqList):
    """ OFX section 8.6.4.1 """
    dataTags = ['ACCTTRNRQ']


class ACCTSYNCRS(SyncRsList):
    """ OFX section 8.6.4.2 """
    dataTags = ['ACCTTRNRS']


class CHGUSERINFORQ(Aggregate):
    """ OFX section 8.7.1 """
    firstname = String(32)
    middlename = String(32)
    lastname = String(32)
    addr1 = String(32)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32)
    state = String(5)
    postalcode = String(11)
    country = OneOf(*COUNTRY_CODES)
    dayphone = String(32)
    evephone = String(32)
    email = String(80)


class CHGUSERINFORS(Aggregate):
    """ OFX section 8.7.2 """
    firstname = String(32)
    middlename = String(32)
    lastname = String(32)
    addr1 = String(32)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32)
    state = String(5)
    postalcode = String(11)
    country = OneOf(*COUNTRY_CODES)
    dayphone = String(32)
    evephone = String(32)
    email = String(80)
    dtinfochg = DateTime(required=True)


class CHGUSERINFOTRNRQ(Aggregate):
    """ OFX section 8.7 """
    trnuid = String(36, required=True)
    chguserinforq = SubAggregate(CHGUSERINFORQ, required=True)


class CHGUSERINFOTRNRS(Aggregate):
    """ OFX section 8.7 """
    trnuid = String(36, required=True)
    chguserinfors = SubAggregate(CHGUSERINFORS, required=True)


class CHGUSERINFOSYNCRQ(SyncRqList):
    """ OFX section 8.7.4.1 """
    dataTags = ['CHGUSERINFOTRNRQ']


class CHGUSERINFOSYNCRS(SyncRsList):
    """ OFX section 8.7.4.2 """
    dataTags = ['CHGUSERINFOTRNRS']
