# coding: utf-8
"""
Python object model for Aggregate containers (the OFX response, statements,
transaction lists, etc.)
"""

# local imports
from ofxtools.models import (Aggregate, STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS)
from ofxtools.Types import String, DateTime


class OFXResponse(object):
    """
    Top-level object representing an OFX response converted into Python
    data types, with attributes for convenient access to statements (i.e.
    OFX *STMT aggregates), security descriptions (i.e. OFX SECLIST aggregate),
    and SONRS (server response to signon request).

    After conversion, each of these convenience attributes holds instances
    of various Aggregate subclasses.
    """
    def __init__(self, tree):
        """
        Initialize with ofx.ElementTree instance containing parsed OFX.
        """
        # Keep a copy of the parse tree
        self.tree = tree

        # SONRS - server response to signon request
        sonrs = self.tree.find('SIGNONMSGSRSV1/SONRS')
        self.sonrs = Aggregate.from_etree(sonrs)

        # TRNRS - transaction response, which is the main section
        # containing account statements
        self.statements = []

        # N.B. This iteration method doesn't preserve the original
        # ordering of the statements within the OFX response
        for stmtClass in (STMTTRNRS, CCSTMTTRNRS, INVSTMTTRNRS):
            tagname = stmtClass.__name__
            for trnrs in self.tree.findall('*/%s' % tagname):
                # *STMTTRNRS may have no *STMTRS (in case of error).
                # Don't blow up; skip silently.
                stmtrs = trnrs.find(stmtClass._rsTag)
                if stmtrs is not None:
                    stmt = Aggregate.from_etree(trnrs)
                    self.statements.append(stmt)

        # SECLIST - list of description of securities referenced by
        # INVSTMT (investment account statement)
        self.securities = []
        seclist = self.tree.find('SECLISTMSGSRSV1/SECLIST')
        if seclist is not None:
            self.securities = Aggregate.from_etree(seclist)

    def __repr__(self):
        s = "<%s fid='%s' org='%s' dtserver='%s' len(statements)=%d len(securities)=%d>"
        return s % (self.__class__.__name__,
                    self.sonrs.fid,
                    self.sonrs.org,
                    str(self.sonrs.dtserver),
                    len(self.statements),
                    len(self.securities),
                   )
