# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# local imports
from ofxtools.models import Aggregate
from ofxtools.Types import (
    String,
    OneOf,
    DateTime,
)
from ofxtools.lib import CURRENCY_CODES


class TRNRS(Aggregate):
    """ Base class for *TRNRS (not in OFX spec) """
    trnuid = String(36, required=True)
    curdef = OneOf(*CURRENCY_CODES, required=True)

    _subaggregates = ()

    _rsTag = None
    _acctTag = None
    _tranList = None
    _unsupported = ()

    @classmethod
    def _preflatten(cls, elem):
        """ """
        # Don't call super() - start with a clean sheet
        # For statements we want to interpret cls._subaggregates
        # differently than Aggregate._preflatten()
        subaggs = {}

        status = elem.find('STATUS')
        subaggs['STATUS'] = status
        elem.remove(status)

        stmtrs = elem.find(cls._rsTag)

        acctfrom = stmtrs.find(cls._acctTag)
        if acctfrom is None:
            msg = "Can't find {}".format(cls._acctTag)
            raise ValueError(msg)
        subaggs[cls._acctTag] = acctfrom
        stmtrs.remove(acctfrom)

        tranlist = stmtrs.find(cls._tranList)
        if tranlist is not None:
            subaggs[cls._tranList] = tranlist
            stmtrs.remove(tranlist)

        # N.B. as opposed to Aggregate._preflatten(), TRNRS._preflatten()
        # searches for _subaggregates in the *RS child, not the *TRNRS itself.
        for tag in cls._subaggregates:
            subagg = stmtrs.find(tag)
            if subagg is not None:
                stmtrs.remove(subagg)
                subaggs[tag] = subagg

        # Unsupported subaggregates
        for tag in cls._unsupported:
            child = stmtrs.find(tag)
            if child is not None:
                stmtrs.remove(child)

        return subaggs

    # Human-friendly attribute aliases
    @property
    def currency(self):
        return self.curdef

    @property
    def account(self):
        attr = getattr(self, self._acctTag.lower())
        return attr

    @property
    def transactions(self):
        attr = getattr(self, self._tranList.lower())
        return attr


class STMTTRNRS(TRNRS):
    """ OFX section 11.4.2.2 """
    _subaggregates = ('LEDGERBAL', 'AVAILBAL', 'BALLIST')

    _rsTag = 'STMTRS'
    _acctTag = 'BANKACCTFROM'
    _tranList = 'BANKTRANLIST'
    _unsupported = ('BANKTRANLISTP', 'CASHADVBALAMT', 'INTRATE', 'MKTGINFO')

    @classmethod
    def _preflatten(cls, elem):
        """
        LEDGERBAL is a required subaggregate for STMTTRNRS, CCSTMTTRNS
        """
        subaggs = super(STMTTRNRS, cls)._preflatten(elem)
        if 'LEDGERBAL' not in subaggs:
            msg = "Can't find {}".format('LEDGERBAL')
            raise ValueError(msg)

        return subaggs


class CCSTMTTRNRS(STMTTRNRS):
    """ OFX section 11.4.3.2 """
    _rsTag = 'CCSTMTRS'
    _acctTag = 'CCACCTFROM'
    _unsupported = ('BANKTRANLISTP', 'CASHADVBALAMT', 'INTRATEPURCH',
                    'INTRATECASH', 'INTRATEXFER', 'REWARDINFO', 'MKTGINFO')


class INVSTMTTRNRS(TRNRS):
    """ OFX section 13.9.2.1 """
    dtasof = DateTime(required=True)

    _subaggregates = ('INVPOSLIST', 'INVBAL')

    _rsTag = 'INVSTMTRS'
    _acctTag = 'INVACCTFROM'
    _tranList = 'INVTRANLIST'
    _unsupported = ('INVOOLIST', 'MKTGINFO', 'INV401K', 'INV401KBAL')

    # Human-friendly attribute aliases
    @property
    def datetime(self):
        return self.dtasof

    @property
    def positions(self):
        return self.invposlist
