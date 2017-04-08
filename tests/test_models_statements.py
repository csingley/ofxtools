# coding: utf-8

# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
)


# local imports
from . import test_models_base
from . import test_models_accounts
from . import test_models_balances
from . import test_models_lists
from . import test_models_banktransactions

from ofxtools.models import (
    Aggregate,
    STMTTRNRS,
    STATUS,
    BANKACCTFROM,
    BANKTRANLIST, BALLIST,
    LEDGERBAL, AVAILBAL,
)


class StmttrnrsTestCase(test_models_banktransactions.StmttrnTestCase):
    """
    """
    requiredElements = ('TRNUID', 'CODE', 'SEVERITY', 'CURDEF',
                        'BANKACCTFROM', 'LEDGERBAL',)
    optionalElements = ('BANKTRANLIST', 'AVAILBAL', 'CASHADVBALAMT', 'INTRATE',
                        'BALLIST', 'MKTGINFO',)

    @property
    def root(self):
        root = Element('STMTTRNRS')
        SubElement(root, 'TRNUID').text = '1001'
        status = test_models_base.StatusTestCase().root
        root.append(status)
        stmtrs = SubElement(root, 'STMTRS')
        SubElement(stmtrs, 'CURDEF').text = 'USD'
        acctfrom = test_models_accounts.BankacctfromTestCase().root
        stmtrs.append(acctfrom)
        tranlist = test_models_lists.BanktranlistTestCase().root
        stmtrs.append(tranlist)
        ledgerbal = test_models_balances.LedgerbalTestCase().root
        availbal = test_models_balances.AvailbalTestCase().root
        stmtrs.append(ledgerbal)
        stmtrs.append(availbal)
        SubElement(stmtrs, 'CASHADVBALAMT').text = '10000.00'
        SubElement(stmtrs, 'INTRATE').text = '20.99'
        ballist = test_models_lists.BallistTestCase().root
        stmtrs.append(ballist)
        SubElement(stmtrs, 'MKTGINFO').text = 'Get Free Stuff NOW!!'

        return root

    def testConvert(self):
        # Test *TRNRS wrapper and **RS Aggregate.
        # Everything below that is tested elsewhere.
        root = Aggregate.from_etree(self.root)
        self.assertIsInstance(root, STMTTRNRS)
        self.assertEqual(root.trnuid, '1001')
        self.assertIsInstance(root.status, STATUS)
        self.assertEqual(root.curdef, 'USD')
        self.assertIsInstance(root.bankacctfrom, BANKACCTFROM)
        self.assertIsInstance(root.banktranlist, BANKTRANLIST)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertIsInstance(root.ballist, BALLIST)

        # Unsupported
        for tag in STMTTRNRS._unsupported:
            self.assertIsNone(getattr(root, tag, None))

    def testPropertyAliases(self):
        root = Aggregate.from_etree(self.root)
        self.assertIs(root.currency, root.curdef)
        self.assertIs(root.account, root.bankacctfrom)
        self.assertIs(root.transactions, root.banktranlist)


if __name__ == '__main__':
    unittest.main()
