# coding: utf-8

import os
import sys
import unittest

from sqlalchemy import create_engine

from ofxtools.ofxalchemy import Base, DBSession, OFXParser


def ofx_to_database(filename):
    parser = OFXParser()
    parser.parse(filename)
    parser.instantiate()
    DBSession.commit()


class AlchemyTestCase(unittest.TestCase):

    def setUp(self):
        verbose = '-v' in sys.argv
        engine = create_engine('sqlite:///test.db', echo=verbose)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        try:
            os.unlink('test.db')
        except OSError:  # file not created by test -- probably an error
            pass

    def assert_result(self, result):
        expected_attributes = ['securities', 'sonrs', 'statements', 'tree']
        result_attributes = dir(result)
        for attribute in expected_attributes:
            self.assertIn(attribute, result_attributes)

    def test_account_type_checking(self):
        filename = 'tests/data/stmtrs.ofx'
        ofx_to_database(filename)
        # TODO: test the created database

    def test_euro_decimal_separator(self):
        filename = 'tests/data/stmtrs_euro.ofx'
        ofx_to_database(filename)
        # TODO: test the created database

    def test_account_type_investment(self):
        filename = 'tests/data/invstmtrs.ofx'
        ofx_to_database(filename)
        # TODO: test the created database


if __name__=='__main__':
    unittest.main()
