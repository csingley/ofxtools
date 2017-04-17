# coding: utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models.base import (
    Aggregate,
    SubAggregate,
    Unsupported,
)
from ofxtools.models.signon import SIGNONMSGSRSV1
from ofxtools.models.bank import BANKMSGSRSV1
from ofxtools.models.investment import INVSTMTMSGSRSV1
from ofxtools.models.creditcard import CREDITCARDMSGSRSV1
from ofxtools.models.seclist import SECLISTMSGSRSV1


class OFX(Aggregate):
    """ """
    signonmsgsrsv1 = SubAggregate(SIGNONMSGSRSV1, required=True)
    bankmsgsrsv1 = SubAggregate(BANKMSGSRSV1)
    creditcardmsgsrsv1 = SubAggregate(CREDITCARDMSGSRSV1)
    invstmtmsgsrsv1 = SubAggregate(INVSTMTMSGSRSV1)
    seclistmsgsrsv1 = SubAggregate(SECLISTMSGSRSV1)

    signupmsgsrsv1 = Unsupported()
    emailmsgsrsv1 = Unsupported()
    loanmsgsrsv1 = Unsupported()
    presdirmsgsrsv1 = Unsupported()
    presdlvmsgsrsv1 = Unsupported()
    profmsgsrsv1 = Unsupported()
    tax1098msgsrsv1 = Unsupported()
    tax1099msgsrsv1 = Unsupported()
    taxw2msgsrsv1 = Unsupported()
    tax1095msgsrsv1 = Unsupported()

    # Human-friendly attribute aliases
    @property
    def sonrs(self):
        return self.signonmsgsrsv1.sonrs

    @property
    def securities(self):
        seclist = []
        attr = getattr(self, 'seclistmsgsrsv1', None)
        if attr:
            seclist = self.seclistmsgsrsv1.seclist
        return seclist

    @property
    def statements(self):
        """ """
        stmts = []
        for msgs in ('bankmsgsrsv1', 'creditcardmsgsrsv1', 'invstmtmsgsrsv1'):
            msg = getattr(self, msgs, None)
            if msg:
                stmts.extend(msg.statements)
        return stmts

    # def __repr__(self):
        # s = "<%s fid='%s' org='%s' dtserver='%s' len(statements)=%d len(securities)=%d>"
        # return s % (self.__class__.__name__,
                    # self.sonrs.fid,
                    # self.sonrs.org,
                    # str(self.sonrs.dtserver),
                    # len(self.statements),
                    # len(self.securities),)

