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
        status = SubElement(root, 'STATUS')
        SubElement(status, 'CODE').text = '0'
        SubElement(status, 'SEVERITY').text = 'INFO'
        stmtrs = SubElement(root, 'STMTRS')
        SubElement(stmtrs, 'CURDEF').text = 'USD'
        acctfrom = SubElement(stmtrs, 'BANKACCTFROM')
        SubElement(acctfrom, 'BANKID').text = '111000614'
        SubElement(acctfrom, 'ACCTID').text = '3456789012'
        SubElement(acctfrom, 'ACCTTYPE').text = 'SAVINGS'
        tranlist = SubElement(stmtrs, 'BANKTRANLIST')
        SubElement(tranlist, 'DTSTART').text = '20010601'
        SubElement(tranlist, 'DTEND').text = '20010630'
        stmttrn = super(self.__class__, self).root
        tranlist.append(stmttrn)
        ledgerbal = SubElement(stmtrs, 'LEDGERBAL')
        SubElement(ledgerbal, 'BALAMT').text = '2350.51'
        SubElement(ledgerbal, 'DTASOF').text = '20010630'
        availbal = SubElement(stmtrs, 'AVAILBAL')
        SubElement(availbal, 'BALAMT').text = '13100.00'
        SubElement(availbal, 'DTASOF').text = '20010630'
        SubElement(stmtrs, 'CASHADVBALAMT').text = '10000.00'
        SubElement(stmtrs, 'INTRATE').text = '20.99'
        ballist = SubElement(stmtrs, 'BALLIST')
        bal1 = SubElement(ballist, 'BAL')
        SubElement(bal1, 'NAME').text = 'BAL1'
        SubElement(bal1, 'DESC').text = 'Balance 1'
        SubElement(bal1, 'BALTYPE').text = 'DOLLAR'
        SubElement(bal1, 'VALUE').text = '111.22'
        SubElement(bal1, 'DTASOF').text = '20010630'
        currency = SubElement(bal1, 'CURRENCY')
        SubElement(currency, 'CURRATE').text = '1.0'
        SubElement(currency, 'CURSYM').text = 'USD'
        bal2 = SubElement(ballist, 'BAL')
        SubElement(bal2, 'NAME').text = 'BAL2'
        SubElement(bal2, 'DESC').text = 'Balance 2'
        SubElement(bal2, 'BALTYPE').text = 'PERCENT'
        SubElement(bal2, 'VALUE').text = '1.39'
        SubElement(bal2, 'DTASOF').text = '20010630'
        currency = SubElement(bal2, 'CURRENCY')
        SubElement(currency, 'CURRATE').text = '8.00'
        SubElement(currency, 'CURSYM').text = 'CNY'
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
        self.assertEqual(len(root.banktranlist), 1)
        self.assertIsInstance(root.ledgerbal, LEDGERBAL)
        self.assertIsInstance(root.availbal, AVAILBAL)
        self.assertIsInstance(root.ballist, BALLIST)
        self.assertEqual(len(root.ballist), 2)

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
