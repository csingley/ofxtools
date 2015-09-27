# coding: utf-8

import unittest

from ofxtools.Parser import OFXTree


def ofx_parse(filename):
    tree = OFXTree()
    tree.parse(filename)
    return tree.convert()


class ParserTestCase(unittest.TestCase):

    def assert_result(self, result):
        expected_attributes = ['securities', 'sonrs', 'statements', 'tree']
        result_attributes = dir(result)
        for attribute in expected_attributes:
            self.assertIn(attribute, result_attributes)

    def test_account_type_checking(self):
        filename = 'tests/data/stmtrs.ofx'
        result = ofx_parse(filename)
        self.assert_result(result)
        # TODO: do something with 'result'

    def test_euro_decimal_separator(self):
        filename = 'tests/data/stmtrs_euro.ofx'
        result = ofx_parse(filename)
        self.assert_result(result)
        # TODO: do something with 'result'

    def test_account_type_investment(self):
        filename = 'tests/data/invstmtrs.ofx'
        result = ofx_parse(filename)
        self.assert_result(result)
        # TODO: do something with 'result'
