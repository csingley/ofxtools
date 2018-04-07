# coding: utf-8
""" Unit tests for ofxtools.utils """
# stdlib imports
import unittest
import os
import datetime


# local imports
from ofxtools.utils import (
    fixpath, cusip_checksum, validate_cusip, sedol_checksum, isin_checksum,
    validate_isin, cusip2isin, sedol2isin, settleDate, NYSEcalendar,
)


class FixpathTestCase(unittest.TestCase):
    def test_all(self):
        """
        utils.fixpath() calls os.path.{expanduser, normpath, normcase, abspath}
        """
        test_path = '~/foo/../bar'
        home = os.environ['HOME']
        self.assertEqual(fixpath(test_path), '{}/bar'.format(home))


class CusipTestCase(unittest.TestCase):
    def test_cusip_checksum(self):
        self.assertEqual(cusip_checksum('08467010'), '8')

    def test_validate_cusip(self):
        self.assertTrue(validate_cusip('084670207'))
        self.assertFalse(validate_cusip('084670208'))
        self.assertFalse(validate_cusip('08467020'))
        self.assertFalse(validate_cusip('0846702077'))

    def test_cusip2isin(self):
        self.assertEqual(cusip2isin('084670108'), 'US0846701086')


class IsinTestCase(unittest.TestCase):
    def test_isin_checksum(self):
        self.assertEqual(isin_checksum('US084670108'), '6')

    def test_validate_isin(self):
        self.assertTrue(validate_isin('US0846701086'))
        self.assertFalse(validate_isin('US0846701087'))
        self.assertFalse(validate_isin('US084670108'))
        self.assertFalse(validate_isin('US08467010866'))


class SedolTestCase(unittest.TestCase):
    def test_sedol_checksum(self):
        self.assertEqual(sedol_checksum('011100'), '9')

    def test_sedol2isin(self):
        self.assertEqual(sedol2isin('0111009'), 'GB0001110096')


class SettledateTestCase(unittest.TestCase):
    pass


class NYSEcalendarTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
