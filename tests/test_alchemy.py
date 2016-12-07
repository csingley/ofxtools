# coding: utf-8
# stdlib imports
import unittest
from contextlib import contextmanager
import os
import sys


# 3rd part imports
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)

# local imports
from ofxtools.ofxalchemy import Base, OFXParser


### DB SETUP
verbose = '-v' in sys.argv
engine = create_engine('sqlite:///test.db', echo=verbose)
DBSession = scoped_session(sessionmaker())
DBSession.configure(bind=engine)


def ofx_to_database(filename):
    parser = OFXParser()
    parser.parse(filename)
    parser.instantiate(DBSession)


class AlchemyTestCase(unittest.TestCase):
    def setUp(self):
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
