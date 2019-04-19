# coding: utf-8
"""
Client signon - OFX Section 2.5
"""
# stdlib imports
from copy import deepcopy

# local imports
from ofxtools.Types import String, OneOf, DateTime, Bool, ListItem
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.wrapperbases import TrnRq, TrnRs
from ofxtools.models.common import STATUS, MSGSETCORE
from ofxtools.models.i18n import LANG_CODES


__all__ = [
    "FI",
    "MFACHALLENGE",
    "MFACHALLENGEA",
    "SONRQ",
    "SONRS",
    "PINCHRQ",
    "PINCHRS",
    "PINCHTRNRQ",
    "PINCHTRNRS",
    "CHALLENGERQ",
    "CHALLENGERS",
    "CHALLENGETRNRQ",
    "CHALLENGETRNRS",
    "MFACHALLENGERQ",
    "MFACHALLENGERS",
    "MFACHALLENGETRNRQ",
    "MFACHALLENGETRNRS",
    "SIGNONMSGSRQV1",
    "SIGNONMSGSRSV1",
    "SIGNONMSGSETV1",
    "SIGNONMSGSET",
]


MFAPHRASEIDS = {
    "MFA1": "City of birth",
    "MFA2": "Date of birth, formatted MM/DD/YYYY",
    "MFA3": "Debit card number",
    "MFA4": "Father’s middle name",
    "MFA5": "Favorite color",
    "MFA6": "First pet’s name",
    "MFA7": "Five digit ZIP code",
    "MFA8": "Grandmother’s maiden name on your father’s side",
    "MFA9": "Grandmother’s maiden name on your mother’s side",
    "MFA10": "Last four digits of your cell phone number",
    "MFA11": "Last four digits of your daytime phone number",
    "MFA12": "Last four digits of your home phone number",
    "MFA13": "Last four digits of your social sescurity number",
    "MFA14": "Last four digits of your tax ID",
    "MFA15": "Month of birth of youngest sibling, do not abbreviate",
    "MFA16": "Mother’s maiden name",
    "MFA17": "Mother’s middle name",
    "MFA18": "Name of the company where you had your first job",
    "MFA19": "Name of the manufacturer of your first car",
    "MFA20": "Name of the street you grew up on",
    "MFA21": "Name of your high school football team, do not include high school name, e.g. 'Beavers' rather than 'Central High Beavers'",
    "MFA22": "Recent deposit or recent withdrawal amount",
    "MFA23": "Year of birth, formatted YYYY",
    "MFA24": "",
    "MFA25": "",
    "MFA26": "",
    "MFA27": "",
    "MFA28": "",
    "MFA29": "",
    "MFA30": "",
    "MFA101": "Datetime, formatted YYYYMMDDHHMMSS",
    "MFA102": "Host name",
    "MFA103": "IP Address",
    "MFA104": "MAC Address",
    "MFA105": "Operating System version",
    "MFA106": "Processor architecture, e.g. I386",
    "MFA107": " UserAgent",
    "MFA108": "",
    "MFA109": "",
    "MFA110": "",
}


class FI(Aggregate):
    """ OFX section 2.5.1.8 """

    org = String(32, required=True)
    fid = String(32)


class MFACHALLENGE(Aggregate):
    """ OFX Section 2.5.4.2 """
    mfaphraseid = String(32, required=True)
    mfaphraselabel = String(64)


class MFACHALLENGEA(Aggregate):
    """ OFX Section 2.5.4.5 """

    mfaphraseid = String(32, required=True)
    mfaphrasea = String(64, required=True)


class SONRQ(Aggregate):
    """ OFX section 2.5.1.2 """

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
    mfachallengea = ListItem(MFACHALLENGEA)
    ofxextension = Unsupported()

    @classmethod
    def validate_args(cls, *args, **kwargs):
        #  "Either <USERID> and <USERPASS> or <USERKEY>, but not both"
        userid = kwargs.get("userid", None)
        userpass = kwargs.get("userpass", None)
        userkey = kwargs.get("userkey", None)
        try:
            assert (userid and userpass) or userkey
            assert not ((userid or userpass) and userkey)
        except AssertionError:
            msg = ("{} must contain either <USERID> and <USERPASS> "
                   "or <USERKEY>, but not both")
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class SONRS(Aggregate):
    """ OFX section 2.5.1.3 """

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


class PINCHRQ(Aggregate):
    """ OFX Section 2.5.2.1 """

    userid = String(32, required=True)
    newuserpass = String(32, required=True)


class PINCHRS(Aggregate):
    """ OFX Section 2.5.2.2 """

    userid = String(32, required=True)
    dtchanged = DateTime()


class PINCHTRNRQ(TrnRq):
    """ OFX Section 2.5.2.1 """

    pinchrq = SubAggregate(PINCHRQ, required=True)


class PINCHTRNRS(TrnRs):
    """ OFX Section 2.5.2.2 """

    pinchrs = SubAggregate(PINCHRS, required=True)


class CHALLENGERQ(Aggregate):
    """ OFX Section 2.5.3.1 """

    userid = String(32, required=True)
    ficertid = String(64)


class CHALLENGERS(Aggregate):
    """ OFX Section 2.5.3.2 """

    userid = String(32, required=True)
    nonce = String(16, required=True)
    ficertid = String(64, required=True)


class CHALLENGETRNRQ(TrnRq):
    """ OFX Section 2.5.3.1 """

    challengerq = SubAggregate(CHALLENGERQ, required=True)


class CHALLENGETRNRS(TrnRs):
    """ OFX Section 2.5.3.2 """

    challengers = SubAggregate(CHALLENGERS, required=True)


class MFACHALLENGERQ(Aggregate):
    """ OFX Section 2.5.4.1 """

    dtclient = DateTime(required=True)


class MFACHALLENGERS(Aggregate):
    """ OFX Section 2.5.4.2 """

    mfachallenge = ListItem(MFACHALLENGE)

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # "Challenge question aggregate (1 or more)"
        if len(args) == 0:
            msg = "{} must contain at least one item"
            raise ValueError(msg.format(cls.__name__))

        super().validate_args(*args, **kwargs)


class MFACHALLENGETRNRQ(TrnRq):
    """ OFX Section 2.5.4.1 """

    mfachallengerq = SubAggregate(MFACHALLENGERQ, required=True)


class MFACHALLENGETRNRS(TrnRs):
    """ OFX Section 2.5.4.2 """

    mfachallengers = SubAggregate(MFACHALLENGERS, required=True)


class SIGNONMSGSRQV1(Aggregate):
    """ OFX Section 2.5 """
    sonrq = SubAggregate(SONRQ, required=True)
    pinchtrnrq = SubAggregate(PINCHTRNRQ)
    challengetrnrq = SubAggregate(CHALLENGETRNRQ)
    mfachallengetrnrq = SubAggregate(MFACHALLENGETRNRQ)


class SIGNONMSGSRSV1(Aggregate):
    """ OFX Section 2.5 """
    sonrs = SubAggregate(SONRS, required=True)
    pinchtrnrs = SubAggregate(PINCHTRNRS)
    challengetrnrs = SubAggregate(CHALLENGETRNRS)
    mfachallengetrnrs = SubAggregate(MFACHALLENGETRNRS)


class SIGNONMSGSETV1(Aggregate):
    """ OFX section 2.5.5 """

    msgsetcore = SubAggregate(MSGSETCORE, required=True)


class SIGNONMSGSET(Aggregate):
    """ OFX section 2.5.5 """

    signonmsgsetv1 = SubAggregate(SIGNONMSGSETV1, required=True)
