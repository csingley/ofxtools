# coding: utf-8

# stdlib imports
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring,
)


# local imports
from . import test_models_banktransactions
from ofxtools.models import (
    Aggregate,
    INVSUBACCTS,
)


class InvbanktranTestCase(test_models_banktransactions.StmttrnTestCase):
    """ """
    requiredElements = ('DTPOSTED', 'TRNAMT', 'FITID', 'TRNTYPE',
                        'SUBACCTFUND')

    @property
    def root(self):
        root = Element('INVBANKTRAN')
        stmttrn = super(InvbanktranTestCase, self).root
        root.append(stmttrn)
        SubElement(root, 'SUBACCTFUND').text = 'MARGIN'
        return root

    def testConvert(self):
        # Test only INVBANKTRAN wrapper; STMTTRN tested elsewhere
        root = super(InvbanktranTestCase, self).testConvert()
        self.assertEqual(root.subacctfund, 'MARGIN')

    def testOneOf(self):
        self.oneOfTest('SUBACCTFUND', INVSUBACCTS)
