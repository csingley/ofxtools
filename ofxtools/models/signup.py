# coding: utf-8
"""
Activation and Account Information - OFX Section 8
"""
# stdlib imports
import operator
import itertools

# local imports
from ofxtools.Types import Bool, String, OneOf, DateTime, ListItem
from ofxtools.models.base import Aggregate, SubAggregate
from ofxtools.models.wrapperbases import TrnRq, TrnRs, SyncRqList, SyncRsList
from ofxtools.models.common import SVCSTATUSES, MSGSETCORE
from ofxtools.models.i18n import COUNTRY_CODES
from ofxtools.models.bank import (
    BANKACCTFROM, BANKACCTTO, BANKACCTINFO, CCACCTFROM, CCACCTTO, CCACCTINFO,
)
from ofxtools.models.billpay import BPACCTINFO
from ofxtools.models.invest import INVACCTFROM, INVACCTTO, INVACCTINFO


__all__ = [
    "ENROLLRQ",
    "ENROLLRS",
    "ENROLLTRNRQ",
    "ENROLLTRNRS",
    "ACCTINFO",
    "ACCTINFORQ",
    "ACCTINFORS",
    "ACCTINFOTRNRQ",
    "ACCTINFOTRNRS",
    "SVCADD",
    "SVCCHG",
    "SVCDEL",
    "ACCTRQ",
    "ACCTRS",
    "ACCTTRNRQ",
    "ACCTTRNRS",
    "ACCTSYNCRQ",
    "ACCTSYNCRS",
    "CHGUSERINFORQ",
    "CHGUSERINFORS",
    "CHGUSERINFOTRNRQ",
    "CHGUSERINFOTRNRS",
    "CHGUSERINFOSYNCRQ",
    "CHGUSERINFOSYNCRS",
    "SIGNUPMSGSRQV1",
    "SIGNUPMSGSRSV1",
    "CLIENTENROLL",
    "WEBENROLL",
    "OTHERENROLL",
    "SIGNUPMSGSETV1",
    "SIGNUPMSGSET",
]


# Enums used in aggregate validation
SVCS = ("BANKSVC", "BPSVC", "INVSVC", "PRESSVC")


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
        ("bankacctfrom", "ccacctfrom"),
        ("bankacctfrom", "invacctfrom"),
        ("ccacctfrom", "invacctfrom"),
    ]


class ENROLLRS(Aggregate):
    """ OFX section 8.4.3 """

    temppass = String(32)
    userid = String(32)
    dtexpire = DateTime()


class ENROLLTRNRQ(TrnRq):
    """ OFX section 8.4.2 """

    enrollrq = SubAggregate(ENROLLRQ, required=True)


class ENROLLTRNRS(TrnRs):
    """ OFX section 8.4.3 """

    enrollrs = SubAggregate(ENROLLRS)


class ACCTINFO(Aggregate):
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
    bankacctinfo = ListItem(BANKACCTINFO)
    ccacctinfo = ListItem(CCACCTINFO)
    bpacctinfo = ListItem(BPACCTINFO)
    invacctinfo = ListItem(INVACCTINFO)
    #  presacctinfo = ListItem(PRESACCTINFO)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Must contain at least one <xxxACCTINFO>
        if len(args) == 0:
            msg = "{} must contain at least one of {}"
            raise ValueError(msg.format(cls.__name__, cls.listitems.keys()))

        #  For a given service xxx, there can be at most one <xxxACCTINFO>
        #  returned. For example, you cannot return two <BANKACCTINFO>
        #  aggregates.
        sortKey = operator.attrgetter("__class__.__name__")
        args_copy = sorted(args, key=sortKey)
        for tag, group in itertools.groupby(args_copy, key=sortKey):
            if len(list(group)) > 1:
                msg = "{} contains multiple {} aggregates"
                raise ValueError(msg.format(cls.__name__, tag))

        super().validate_args(*args, **kwargs)

    def __repr__(self):
        return "<{} desc='{}' phone='{}' len={}>".format(
            self.__class__.__name__, self.desc, self.phone, len(self)
        )


class ACCTINFORQ(Aggregate):
    """ OFX section 8.5.1 """

    dtacctup = DateTime(required=True)


class ACCTINFORS(Aggregate):
    """ OFX section 8.5.2 """

    dtacctup = DateTime(required=True)
    acctinfo = ListItem(ACCTINFO)

    def __repr__(self):
        return "<{} dtacctup='{}' len={}>".format(
            self.__class__.__name__, self.dtacctup, len(self)
        )


class ACCTINFOTRNRQ(TrnRq):
    """ OFX section 8.5"""

    acctinforq = SubAggregate(ACCTINFORQ, required=True)


class ACCTINFOTRNRS(TrnRs):
    """ OFX section 8.5.2 """

    acctinfors = SubAggregate(ACCTINFORS)


class SVCADD(Aggregate):
    """ OFX section 8.6.1.1 """

    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    invacctto = SubAggregate(INVACCTTO)

    requiredMutexes = [("bankacctto", "ccacctto", "invacctto")]


class SVCCHG(Aggregate):
    """ OFX section 8.6.1.2 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    invacctfrom = SubAggregate(INVACCTFROM)
    bankacctto = SubAggregate(BANKACCTTO)
    ccacctto = SubAggregate(CCACCTTO)
    invacctto = SubAggregate(INVACCTTO)

    requiredMutexes = [
        ("bankacctfrom", "ccacctfrom", "invacctfrom"),
        ("bankacctto", "ccacctto", "invacctto"),
    ]


class SVCDEL(Aggregate):
    """ OFX section 8.6.1.1 """

    bankacctfrom = SubAggregate(BANKACCTFROM)
    ccacctfrom = SubAggregate(CCACCTFROM)
    invacctfrom = SubAggregate(INVACCTFROM)

    requiredMutexes = [("bankacctfrom", "ccacctfrom", "invacctfrom")]


class ACCTRQ(Aggregate):
    """ OFX section 8.6.1 """

    svcadd = SubAggregate(SVCADD)
    svcchg = SubAggregate(SVCCHG)
    svcdel = SubAggregate(SVCDEL)
    svc = OneOf(*SVCS, required=True)

    requiredMutexes = [("svcadd", "svcchg", "svcdel")]


class ACCTRS(Aggregate):
    """ OFX section 8.6.2 """

    svcadd = SubAggregate(SVCADD)
    svcchg = SubAggregate(SVCCHG)
    svcdel = SubAggregate(SVCDEL)
    svc = OneOf(*SVCS, required=True)
    svcstatus = OneOf(*SVCSTATUSES, required=True)

    requiredMutexes = [("svcadd", "svcchg", "svcdel")]


class ACCTTRNRQ(TrnRq):
    """ OFX section 8.6.1 """

    acctrq = SubAggregate(ACCTRQ, required=True)


class ACCTTRNRS(TrnRs):
    """ OFX section 8.6.2 """

    acctrs = SubAggregate(ACCTRS)


class ACCTSYNCRQ(SyncRqList):
    """ OFX section 8.6.4.1 """

    accttrnrq = ListItem(ACCTTRNRQ)


class ACCTSYNCRS(SyncRsList):
    """ OFX section 8.6.4.2 """

    accttrnrs = ListItem(ACCTTRNRS)


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


class CHGUSERINFOTRNRQ(TrnRq):
    """ OFX section 8.7 """

    chguserinforq = SubAggregate(CHGUSERINFORQ, required=True)


class CHGUSERINFOTRNRS(TrnRs):
    """ OFX section 8.7 """

    chguserinfors = SubAggregate(CHGUSERINFORS)


class CHGUSERINFOSYNCRQ(SyncRqList):
    """ OFX section 8.7.4.1 """

    chguserinfotrnrq = ListItem(CHGUSERINFOTRNRQ)


class CHGUSERINFOSYNCRS(SyncRsList):
    """ OFX section 8.7.4.2 """

    chguserinfotrnrs = ListItem(CHGUSERINFOTRNRS)


class SIGNUPMSGSRQV1(Aggregate):
    """ OFX section 8.1 """

    enrolltrnrq = ListItem(ENROLLTRNRQ)
    acctinfotrnrq = ListItem(ACCTINFOTRNRQ)
    accttrnrq = ListItem(ACCTTRNRQ)
    chguserinfotrnrq = ListItem(CHGUSERINFOTRNRQ)


class SIGNUPMSGSRSV1(Aggregate):
    """ OFX section 8.1 """

    enrolltrnrs = ListItem(ENROLLTRNRS)
    acctinfotrnrs = ListItem(ACCTINFOTRNRS)
    accttrnrs = ListItem(ACCTTRNRS)
    chguserinfotrnrs = ListItem(CHGUSERINFOTRNRS)


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
        ("clientenroll", "webenroll"),
        ("clientenroll", "otherenroll"),
        ("webenroll", "otherenroll"),
    ]


class SIGNUPMSGSET(Aggregate):
    """ OFX section 8.8 """

    signupmsgsetv1 = SubAggregate(SIGNUPMSGSETV1, required=True)
