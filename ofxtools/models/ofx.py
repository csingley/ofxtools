# coding: utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models.base import Aggregate, SubAggregate, Unsupported
from ofxtools.models.signon import SIGNONMSGSRQV1, SIGNONMSGSRSV1
from ofxtools.models.signup import SIGNUPMSGSRQV1, SIGNUPMSGSRSV1
from ofxtools.models.bank import BANKMSGSRQV1, BANKMSGSRSV1
from ofxtools.models.interxfer import INTERXFERMSGSRQV1, INTERXFERMSGSRSV1
from ofxtools.models.wire import WIREXFERMSGSRQV1, WIREXFERMSGSRSV1
from ofxtools.models.creditcard import CREDITCARDMSGSRQV1, CREDITCARDMSGSRSV1
from ofxtools.models.investment import INVSTMTMSGSRQV1, INVSTMTMSGSRSV1
from ofxtools.models.email import EMAILMSGSRQV1, EMAILMSGSRSV1
from ofxtools.models.seclist import SECLISTMSGSRQV1, SECLISTMSGSRSV1
from ofxtools.models.profile import PROFMSGSRQV1, PROFMSGSRSV1


__all__ = ["OFX"]


class OFX(Aggregate):
    """ OFX Section 2.4.3 """

    signonmsgsrqv1 = SubAggregate(SIGNONMSGSRQV1)
    signonmsgsrsv1 = SubAggregate(SIGNONMSGSRSV1)
    signupmsgsrqv1 = SubAggregate(SIGNUPMSGSRQV1)
    signupmsgsrsv1 = SubAggregate(SIGNUPMSGSRSV1)
    bankmsgsrqv1 = SubAggregate(BANKMSGSRQV1)
    bankmsgsrsv1 = SubAggregate(BANKMSGSRSV1)
    creditcardmsgsrqv1 = SubAggregate(CREDITCARDMSGSRQV1)
    creditcardmsgsrsv1 = SubAggregate(CREDITCARDMSGSRSV1)
    invstmtmsgsrqv1 = SubAggregate(INVSTMTMSGSRQV1)
    invstmtmsgsrsv1 = SubAggregate(INVSTMTMSGSRSV1)
    interxfermsgsrqv1 = SubAggregate(INTERXFERMSGSRQV1)
    interxfermsgsrsv1 = SubAggregate(INTERXFERMSGSRSV1)
    wirexfermsgsrqv1 = SubAggregate(WIREXFERMSGSRQV1)
    wirexfermsgsrsv1 = SubAggregate(WIREXFERMSGSRSV1)
    billpaymsgsrqv1 = Unsupported()
    billpaymsgsrsv1 = Unsupported()
    emailmsgsrqv1 = SubAggregate(EMAILMSGSRQV1)
    emailmsgsrsv1 = SubAggregate(EMAILMSGSRSV1)
    seclistmsgsrqv1 = SubAggregate(SECLISTMSGSRQV1)
    seclistmsgsrsv1 = SubAggregate(SECLISTMSGSRSV1)
    presdirmsgsrqv1 = Unsupported()
    presdirmsgsrsv1 = Unsupported()
    presdlvmsgsrqv1 = Unsupported()
    presdlvmsgsrsv1 = Unsupported()
    profmsgsrqv1 = SubAggregate(PROFMSGSRQV1)
    profmsgsrsv1 = SubAggregate(PROFMSGSRSV1)

    loanmsgsrqv1 = Unsupported()
    loanmsgsrsv1 = Unsupported()
    tax1098msgsrqv1 = Unsupported()
    tax1098msgsrsv1 = Unsupported()
    tax1099msgsrqv1 = Unsupported()
    tax1099msgsrsv1 = Unsupported()
    taxw2msgsrqv1 = Unsupported()
    taxw2msgsrsv1 = Unsupported()
    tax1095msgsrqv1 = Unsupported()
    tax1095msgsrsv1 = Unsupported()

    requiredMutexes = [("signonmsgsrqv1", "signonmsgsrsv1")]
    optionalMutexes = [
        ("signupmsgsrqv1", "signupmsgsrsv1"),
        ("bankmsgsrqv1", "bankmsgsrsv1"),
        ("creditcardmsgsrqv1", "creditcardmsgsrsv1"),
        ("invstmtmsgsrqv1", "invstmtmsgsrsv1"),
        ("interxfermsgsrqv1", "interxfermsgsrsv1"),
        ("wirexfermsgsrqv1", "wirexfermsgsrsv1"),
        #  ("billpaymsgsrqv1", "billpaymsgsrsv1"),
        ("emailmsgsrqv1", "emailmsgsrsv1"),
        ("seclistmsgsrqv1", "seclistmsgsrsv1"),
        #  ("presdirmsgsrqv1", "presdirmsgsrsv1"),
        #  ("presdlmsgsrqv1", "presdlmsgsrsv1"),
        ("profmsgsrqv1", "profmsgsrsv1"),
        #  ("loanmsgsrqv1", "loanmsgsrsv1"),
        #  ("tax1098msgsrqv1", "tax1098msgsrsv1"),
        #  ("tax1099msgsrqv1", "tax1099msgsrsv1"),
        #  ("taxw2msgsrqv1", "taxw2msgsrsv1"),
        #  ("tax1095msgsrqv1", "tax1095msgsrsv1"),
        # Don't allow mixed *RQ and *RS in the same OFX
        ("signupmsgsrqv1", "bankmsgsrsv1"),
        ("signupmsgsrqv1", "creditcardmsgsrsv1"),
        ("signupmsgsrqv1", "invstmtmsgsrsv1"),
        ("signupmsgsrqv1", "interxfermsgsrsv1"),
        ("signupmsgsrqv1", "wirexfermsgsrsv1"),
        ("signupmsgsrqv1", "billpaymsgsrsv1"),
        ("signupmsgsrqv1", "emailmsgsrsv1"),
        ("signupmsgsrqv1", "seclistmsgsrsv1"),
        ("signupmsgsrqv1", "presdirmsgsrsv1"),
        ("signupmsgsrqv1", "presdlmsgsrsv1"),
        ("signupmsgsrqv1", "profmsgsrsv1"),
        ("signupmsgsrqv1", "loanmsgsrsv1"),
        ("signupmsgsrqv1", "tax1098msgsrsv1"),
        ("signupmsgsrqv1", "tax1099msgsrsv1"),
        ("signupmsgsrqv1", "taxw2msgsrsv1"),
        ("signupmsgsrqv1", "tax1095msgsrsv1"),
        ("signupmsgsrsv1", "bankmsgsrqv1"),
        ("signupmsgsrsv1", "creditcardmsgsrqv1"),
        ("signupmsgsrsv1", "invstmtmsgsrqv1"),
        ("signupmsgsrsv1", "interxfermsgsrqv1"),
        ("signupmsgsrsv1", "wirexfermsgsrqv1"),
        ("signupmsgsrsv1", "billpaymsgsrqv1"),
        ("signupmsgsrsv1", "emailmsgsrqv1"),
        ("signupmsgsrsv1", "seclistmsgsrqv1"),
        ("signupmsgsrsv1", "presdirmsgsrqv1"),
        ("signupmsgsrsv1", "presdlmsgsrqv1"),
        ("signupmsgsrsv1", "profmsgsrqv1"),
        ("signupmsgsrsv1", "loanmsgsrqv1"),
        ("signupmsgsrsv1", "tax1098msgsrqv1"),
        ("signupmsgsrsv1", "tax1099msgsrqv1"),
        ("signupmsgsrsv1", "taxw2msgsrqv1"),
        ("signupmsgsrsv1", "tax1095msgsrqv1")
    ]

    def __repr__(self):
        s = "<{} ".format(self.__class__.__name__)
        if self.sonrs.fi is not None:
            s += "fid='{}' org='{}' ".format(
                self.sonrs.fi.fid or "", self.sonrs.fi.org or ""
            )
        s += "dtserver='{}' len(statements)={} len(securities)={}>".format(
            str(self.sonrs.dtserver), len(self.statements), len(self.securities)
        )
        return s

    # Human-friendly attribute aliases
    @property
    def sonrs(self):
        return self.signonmsgsrsv1.sonrs

    @property
    def securities(self):
        seclist = []
        msgs = getattr(self, "seclistmsgsrsv1", None)
        if msgs:
            seclist = msgs.securities
        return seclist

    @property
    def statements(self):
        stmts = []
        for msgs in ("bankmsgsrsv1", "creditcardmsgsrsv1", "invstmtmsgsrsv1"):
            msg = getattr(self, msgs, None)
            if msg:
                stmts.extend(msg.statements)
        return stmts
