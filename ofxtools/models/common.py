# coding: utf-8
"""
"""
# local imports
from ofxtools.Types import (
    String,
    NagString,
    OneOf,
    Integer,
    Decimal,
    DateTime,
)
from ofxtools.models.base import (
    Aggregate,
    List,
    SubAggregate,
    Unsupported,
)
from ofxtools.models.i18n import (
    CURRENCY, 
    COUNTRY_CODES,
)


# class OFX(Aggregate):
    # """ """
    # signonmsgsrsv1 = SubAggregate(SIGNONMSGSRSV1, required=True)
    # bankmsgsrsv1 = SubAggregate(BANKMSGSRSV1)
    # creditcardmsgsrsv1 = SubAggregate(CREDITCARDMSGSRSV1)
    # invstmtmsgsrsv1 = SubAggregate(INVSTMTMSGSRSV1)
    # seclistmsgsrsv1 = SubAggregate(SECLISTMSGSRSV1)

    # signupmsgsrsv1 = Unsupported()
    # emailmsgsrsv1 = Unsupported()
    # loanmsgsrsv1 = Unsupported()
    # presdirmsgsrsv1 = Unsupported()
    # presdlvmsgsrsv1 = Unsupported()
    # profmsgsrsv1 = Unsupported()
    # tax1098msgsrsv1 = Unsupported()
    # tax1099msgsrsv1 = Unsupported()
    # taxw2msgsrsv1 = Unsupported()
    # tax1095msgsrsv1 = Unsupported()

    # # Human-friendly attribute aliases
    # @property
    # def sonrs(self):
        # sonrs = None
        # attr = getattr(self, 'signonmsgsrsv1', None)
        # if attr:
            # sonrs = getattr(attr, 'sonrs')
        # return sonrs

    # @property
    # def securities(self):
        # seclist = []
        # attr = getattr(self, 'seclistmsgsrsv1', None)
        # if attr:
            # seclist = getattr(attr, 'seclist')
        # return seclist

    # @property
    # def statements(self):
        # """ """
        # stmts = []
        # for msgs in ('bankmsgsrsv1', 'creditcardmsgsrsv1', 'invstmtmsgsrsv1'):
            # attr = getattr(self, msgs, None)
            # if attr:
                # stmts.extend(attr)
        # return stmts

    # def __repr__(self):
        # s = "<%s fid='%s' org='%s' dtserver='%s' len(statements)=%d len(securities)=%d>"
        # return s % (self.__class__.__name__,
                    # self.sonrs.fid,
                    # self.sonrs.org,
                    # str(self.sonrs.dtserver),
                    # len(self.statements),
                    # len(self.securities),)


class OFXELEMENT(Aggregate):
    """ OFX section 2.7.2 """
    tagname = String(32, required=True)
    name = String(32)
    tagtype = String(20)
    tagvalue = String(1000, required=True)


class OFXEXTENSION(List):
    """ OFX section 2.7.2 """
    memberTags = ('OFXELEMENT', )


class STATUS(Aggregate):
    """ OFX section 3.1.5 """
    code = Integer(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = String(255)


class BAL(Aggregate):
    """ OFX section 3.1.4 """
    name = String(32, required=True)
    desc = String(80, required=True)
    baltype = OneOf('DOLLAR', 'PERCENT', 'NUMBER', required=True)
    value = Decimal(required=True)
    dtasof = DateTime()
    currency = SubAggregate(CURRENCY)
