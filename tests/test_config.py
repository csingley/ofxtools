# coding: utf-8
""" Unit tests for ofxtools.config """

# stdlib imports
import unittest
from unittest.mock import MagicMock, patch, DEFAULT, sentinel, ANY
from datetime import datetime
from collections import namedtuple
from io import BytesIO


# local imports
from ofxtools.config import OfxgetConfigParser


class OfxgetConfigParserTestCase(unittest.TestCase):
    @property
    def parser(self):
        parser = OfxgetConfigParser()
        return parser

    def testRead(self):
        with patch("configparser.ConfigParser.read") as fake_read:
            filenames = ["/fake/path"]
            self.parser.read(filenames)
            args, kwargs = fake_read.call_args
            self.assertEqual(len(args), 2)
            parser = args[0]
            self.assertIsInstance(parser, OfxgetConfigParser)
            self.assertEqual(args[1], filenames)
            self.assertEqual(len(kwargs), 0)

    def testFiIndex(self):
        pass


if __name__ == "__main__":
    unittest.main()
