# coding: utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""


__all__ = ["OFX"]


# local imports
from ofxtools.Types import SubAggregate, Unsupported
from ofxtools.models.base import Aggregate
from ofxtools.models.signon import SIGNONMSGSRQV1, SIGNONMSGSRSV1
from ofxtools.models.profile import PROFMSGSRQV1, PROFMSGSRSV1
from ofxtools.models.signup import SIGNUPMSGSRQV1, SIGNUPMSGSRSV1
from ofxtools.models.email import EMAILMSGSRQV1, EMAILMSGSRSV1
from ofxtools.models.bank.msgsets import (
    BANKMSGSRQV1,
    BANKMSGSRSV1,
    CREDITCARDMSGSRQV1,
    CREDITCARDMSGSRSV1,
    INTERXFERMSGSRQV1,
    INTERXFERMSGSRSV1,
    WIREXFERMSGSRQV1,
    WIREXFERMSGSRSV1,
)
from ofxtools.models.billpay.msgsets import BILLPAYMSGSRQV1, BILLPAYMSGSRSV1
from ofxtools.models.invest.msgsets import (
    INVSTMTMSGSRQV1,
    INVSTMTMSGSRSV1,
    SECLISTMSGSRQV1,
    SECLISTMSGSRSV1,
)
from ofxtools.models.tax1099 import TAX1099MSGSRQV1, TAX1099MSGSRSV1
from ofxtools.utils import all_equal


class OFX(Aggregate):
    """OFX Section 2.4.3"""

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
    billpaymsgsrqv1 = SubAggregate(BILLPAYMSGSRQV1)
    billpaymsgsrsv1 = SubAggregate(BILLPAYMSGSRSV1)
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
    tax1099msgsrqv1 = SubAggregate(TAX1099MSGSRQV1)
    tax1099msgsrsv1 = SubAggregate(TAX1099MSGSRSV1)
    taxw2msgsrqv1 = Unsupported()
    taxw2msgsrsv1 = Unsupported()
    tax1095msgsrqv1 = Unsupported()
    tax1095msgsrsv1 = Unsupported()

    requiredMutexes = [["signonmsgsrqv1", "signonmsgsrsv1"]]

    @classmethod
    def validate_args(cls, *args, **kwargs):
        # Don't allow mixed *RQ and *RS in the same OFX
        if not all_equal(key[-7:] for key in kwargs):
            msg = f"{cls.__name__}: mixed *MSGRQV1 and *MSGSRSV1 are invalid"
            raise ValueError(msg)

        super().validate_args(*args, **kwargs)

    def __repr__(self):
        s = "<{} ".format(self.__class__.__name__)
        signon = self.signon
        if signon.fi is not None:
            s += f"fid='{signon.fi.fid}' org='{signon.fi.org}' "
        s += f"len(statements)={len(self.statements)} "
        s += f"len(securities)={len(self.securities)}>"
        return s

    # Human-friendly attribute aliases
    @property
    def signon(self):
        if self.signonmsgsrqv1 is not None:
            return self.signonmsgsrqv1.sonrq
        else:
            assert self.signonmsgsrsv1 is not None
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
        for msgs in (
            "bankmsgsrqv1",
            "creditcardmsgsrqv1",
            "invstmtmsgsrqv1",
            "bankmsgsrsv1",
            "creditcardmsgsrsv1",
            "invstmtmsgsrsv1",
        ):
            msg = getattr(self, msgs, None)
            if msg:
                stmts.extend(msg.statements)
        return stmts
