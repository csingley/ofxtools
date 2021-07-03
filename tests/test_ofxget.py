# coding: utf-8
""" Unit tests for ofxtools.ofxget """

# stdlib imports
import unittest
from unittest.mock import Mock, patch, DEFAULT
from datetime import datetime
from io import BytesIO
import argparse
import collections
import urllib
from configparser import ConfigParser
import xml.etree.ElementTree as ET
import concurrent.futures
from urllib.error import HTTPError, URLError
import socket


# local imports
from ofxtools import models, header, Parser, utils
from ofxtools.Client import (
    OFXClient,
    StmtRq,
    CcStmtRq,
    InvStmtRq,
    StmtEndRq,
    CcStmtEndRq,
)
from ofxtools.utils import UTC
from ofxtools.scripts import ofxget
from ofxtools.ofxhome import OFXServer

# test imports
import base
import test_models_msgsets
import test_models_signup
import test_models_bank_stmt
import test_models_invest
import test_models_billpay_common


class MakeArgParserTestCase(unittest.TestCase):
    def testMakeArgparser(self):
        # This is the lamest test ever
        argparser = ofxget.make_argparser()
        self.assertGreater(len(argparser._actions), 0)

    ###############################################################################
    # CLI METHODS
    ###############################################################################
    #  class CliTestCase(unittest.TestCase):
    @property
    def args(self):
        return {
            "server": "2big2fail",
            "url": "http://example.com",
            "org": "Example",
            "fid": "666",
            "version": "103",
            "appid": "ofxtools",
            "appver": "0.7.0",
            "language": "ENG",
            "bankid": "1234567890",
            "brokerid": "example.com",
            "dtstart": "20070101000000",
            "dtend": "20071231000000",
            "dtasof": "20071231000000",
            "dtacctup": "",
            "checking": ["123", "234"],
            "savings": ["345", "456"],
            "moneymrkt": ["567", "678"],
            "creditline": ["789", "890"],
            "creditcard": ["111", "222"],
            "investment": ["333", "444"],
            "inctran": True,
            "incoo": False,
            "incpos": True,
            "incbal": True,
            "dryrun": True,
            "user": "porkypig",
            "clientuid": None,
            "unclosedelements": False,
            "pretty": False,
            "unsafe": False,
            "all": False,
            "write": False,
            "savepass": False,
            "nonewfileuid": False,
            "useragent": "",
            "gen_newfileuid": True,
            "timeout": 2.0,
            "password": "",
        }

    def testScanProfile(self):
        with patch("ofxtools.scripts.ofxget._scan_profile") as mock_scan_prof:
            with patch("builtins.print") as mock_print:
                ofxv1 = {
                    "versions": [102, 103],
                    "formats": [
                        {"pretty": False, "unclosedelements": True},
                        {"pretty": True, "unclosedelements": False},
                    ],
                }

                ofxv2 = {
                    "versions": [203],
                    "formats": [{"pretty": False}, {"pretty": True}],
                }

                signoninfo = {
                    "chgpinfirst": False,
                    "clientuidreq": False,
                    "authtokenfirst": False,
                    "mfachallengefirst": False,
                }

                mock_scan_prof.return_value = (ofxv1, ofxv2, signoninfo)
                args = self.args
                args["dryrun"] = False
                result = ofxget.scan_profile(args)
                self.assertIsNone(result, None)

                args, kwargs = mock_scan_prof.call_args

                self.assertEqual(len(args), 0)
                self.assertEqual(len(kwargs), 6)
                for arg in (
                    "url",
                    "org",
                    "fid",
                    "useragent",
                    "gen_newfileuid",
                    "timeout",
                ):
                    self.assertEqual(kwargs[arg], self.args[arg])

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)

                # FIXME - json.dumps output for dicts isn't stable
                #  self.maxDiff = None
                #  self.assertEqual(
                #  args[0],
                #  ('[{"versions": [102, 103], '
                #  '"formats": [{"pretty": false, "unclosedelements": true},'
                #  ' {"pretty": true, "unclosedelements": false}]}, '
                #  '{"versions": [203], "formats": [{"pretty": false}, '
                #  '{"pretty": true}]}]'))

    def testScanProfileNoResult(self):
        with patch("ofxtools.scripts.ofxget._scan_profile") as mock_scan_prof:
            with patch("builtins.print") as mock_print:
                mock_scan_prof.return_value = ({"versions": []}, {"versions": []}, {})
                args = self.args
                args["dryrun"] = False
                result = ofxget.scan_profile(args)
                self.assertIsNone(result, None)

                args, kwargs = mock_scan_prof.call_args

                self.assertEqual(len(args), 0)
                self.assertEqual(len(kwargs), 6)
                for arg in (
                    "url",
                    "org",
                    "fid",
                    "useragent",
                    "gen_newfileuid",
                    "timeout",
                ):
                    self.assertEqual(kwargs[arg], self.args[arg])

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)

                self.maxDiff = None
                self.assertEqual(
                    args[0], f"Scan found no working formats for {self.args['url']}"
                )

    def testScanProfileWrite(self):
        with patch.multiple(
            "ofxtools.scripts.ofxget", _scan_profile=DEFAULT, write_config=DEFAULT
        ) as MOCKS:
            mock_scan_prof = MOCKS["_scan_profile"]
            mock_write_config = MOCKS["write_config"]

            ofxv1 = {
                "versions": [102, 103],
                "formats": [
                    {"pretty": False, "unclosedelements": True},
                    {"pretty": True, "unclosedelements": False},
                ],
            }

            ofxv2 = {
                "versions": [203],
                "formats": [{"pretty": False}, {"pretty": True}],
            }

            signoninfo = {
                "chgpinfirst": False,
                "clientuidreq": False,
                "authtokenfirst": False,
                "mfachallengefirst": False,
            }

            mock_scan_prof.return_value = (ofxv1, ofxv2, signoninfo)

            ARGS = collections.ChainMap({"write": True, "dryrun": False}, self.args)

            with patch("builtins.print"):
                result = ofxget.scan_profile(ARGS)

            self.assertEqual(result, None)

            args, kwargs = mock_scan_prof.call_args

            self.assertEqual(len(args), 0)
            self.assertEqual(len(kwargs), 6)
            for arg in ("url", "org", "fid", "useragent", "gen_newfileuid", "timeout"):
                self.assertEqual(kwargs[arg], self.args[arg])

            args, kwargs = mock_write_config.call_args
            self.assertEqual(len(args), 1)
            args = args[0]

            ARGS["version"] = 203  # best version
            self.assertEqual(dict(args), dict(ARGS))
            self.assertEqual(len(kwargs), 0)

    def testInitClient(self):
        args = self.args
        client = ofxget.init_client(args)
        self.assertIsInstance(client, OFXClient)
        self.assertEqual(str(client.version), args["version"])
        for arg in [
            "url",
            "org",
            "fid",
            "appid",
            "appver",
            "language",
            "bankid",
            "brokerid",
        ]:
            self.assertEqual(getattr(client, arg), args[arg])

    def testRequestProfile(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as fake_rqprof:
            with patch("builtins.print") as mock_print:
                fake_rqprof.return_value = BytesIO(b"th-th-th-that's all folks!")

                output = ofxget.request_profile(self.args)
                self.assertEqual(output, None)

                args, kwargs = fake_rqprof.call_args
                self.assertEqual(len(args), 0)

                self.assertEqual(
                    kwargs,
                    {
                        "dryrun": self.args["dryrun"],
                        "gen_newfileuid": not self.args["nonewfileuid"],
                    },
                )

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)
                self.assertEqual(args[0], "th-th-th-that's all folks!")
                self.assertEqual(len(kwargs), 0)

    def testRequestAcctinfo(self):
        """Unit test for ofxtools.scripts.ofxget.request_acctinfo()"""
        args = self.args
        args["dryrun"] = False

        with patch("ofxtools.scripts.ofxget._request_acctinfo") as fake_rq_acctinfo:
            with patch("getpass.getpass") as fake_getpass:
                with patch("builtins.print") as mock_print:
                    fake_getpass.return_value = "t0ps3kr1t"
                    fake_rq_acctinfo.return_value = BytesIO(
                        b"th-th-th-that's all folks!"
                    )

                    output = ofxget.request_acctinfo(self.args)
                    self.assertIsNone(output)

                    args, kwargs = fake_rq_acctinfo.call_args
                    self.assertEqual(len(args), 2)
                    args, passwd = args
                    self.assertEqual(args, self.args)
                    self.assertEqual(passwd, "anonymous00000000000000000000000")

                    self.assertEqual(len(kwargs), 0)

                    args, kwargs = mock_print.call_args
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], "th-th-th-that's all folks!")
                    self.assertEqual(len(kwargs), 0)

    def test_RequestAcctinfo(self):
        """Unit test for ofxtools.scripts.ofxget._request_acctinfo()"""
        args = self.args
        args["dryrun"] = False

        with patch("ofxtools.Client.OFXClient.request_accounts") as fake_rq_acctinfo:
            fake_rq_acctinfo.return_value = BytesIO(b"th-th-th-that's all folks!")

            output = ofxget._request_acctinfo(self.args, password="t0ps3kr1t")
            self.assertEqual(output.read(), (b"th-th-th-that's all folks!"))

            args, kwargs = fake_rq_acctinfo.call_args
            self.assertEqual(len(args), 2)
            passwd, dtacctup = args
            self.assertEqual(passwd, "t0ps3kr1t")
            self.assertEqual(dtacctup, datetime(1990, 1, 1, tzinfo=UTC))

            self.assertEqual(
                kwargs,
                {
                    "dryrun": self.args["dryrun"],
                    "gen_newfileuid": not self.args["nonewfileuid"],
                },
            )

    def test_RequestAcctinfoOverrideDtacctup(self):
        """Nondefault `dtacctup` arg for ofxtools.scripts.ofxget._request_acctinfo()"""
        args = self.args
        args["dryrun"] = False
        args["dtacctup"] = "17760704"

        with patch("ofxtools.Client.OFXClient.request_accounts") as fake_rq_acctinfo:
            fake_rq_acctinfo.return_value = BytesIO(b"th-th-th-that's all folks!")

            output = ofxget._request_acctinfo(self.args, password="t0ps3kr1t")
            self.assertEqual(output.read(), (b"th-th-th-that's all folks!"))

            args, kwargs = fake_rq_acctinfo.call_args
            self.assertEqual(len(args), 2)
            passwd, dtacctup = args
            self.assertEqual(passwd, "t0ps3kr1t")
            self.assertEqual(dtacctup, datetime(1990, 1, 1, tzinfo=UTC))

            self.assertEqual(
                kwargs,
                {
                    "dryrun": self.args["dryrun"],
                    "gen_newfileuid": not self.args["nonewfileuid"],
                },
            )

    def testMergeAcctinfo(self):
        """Unit test for ofxtools.scripts.ofxget._merge_acctinfo()"""
        cli = {"dryrun": True}
        config = {"pretty": False}
        args = collections.ChainMap(cli, config)

        markup = OFXClient("").serialize(ExtractAcctInfosTestCase.ofx)

        ofxget._merge_acctinfo(args, BytesIO(markup))

        # Have extracted bankid, brokerid, checking, creditcard, investment
        self.assertEqual(len(args), 7)
        self.assertEqual(args["dryrun"], True)
        self.assertEqual(args["pretty"], False)
        self.assertEqual(args["bankid"], "111000614")
        self.assertEqual(args["brokerid"], "111000614")
        self.assertEqual(args["checking"], ["123456789123456789"])
        self.assertEqual(args["creditcard"], ["123456789123456789"])
        self.assertEqual(args["investment"], ["123456789123456789"])

    def testRequestStmt(self):
        args = self.args
        args["dryrun"] = False

        with patch("getpass.getpass") as fake_getpass:
            fake_getpass.return_value = "t0ps3kr1t"
            with patch("ofxtools.Client.OFXClient.request_statements") as fake_rq_stmt:
                with patch("builtins.print") as mock_print:
                    fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
                    output = ofxget.request_stmt(args)

                    self.assertEqual(output, None)

                    args, kwargs = fake_rq_stmt.call_args
                    password, *stmtrqs = args
                    self.assertEqual(password, "t0ps3kr1t")
                    self.assertEqual(
                        stmtrqs,
                        [
                            StmtRq(
                                acctid="123",
                                accttype="CHECKING",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="234",
                                accttype="CHECKING",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="345",
                                accttype="SAVINGS",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="456",
                                accttype="SAVINGS",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="567",
                                accttype="MONEYMRKT",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="678",
                                accttype="MONEYMRKT",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="789",
                                accttype="CREDITLINE",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            StmtRq(
                                acctid="890",
                                accttype="CREDITLINE",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            CcStmtRq(
                                acctid="111",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            CcStmtRq(
                                acctid="222",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                            ),
                            InvStmtRq(
                                acctid="333",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                dtasof=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                                incoo=False,
                                incpos=True,
                                incbal=True,
                            ),
                            InvStmtRq(
                                acctid="444",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                                dtasof=datetime(2007, 12, 31, tzinfo=UTC),
                                inctran=True,
                                incoo=False,
                                incpos=True,
                                incbal=True,
                            ),
                        ],
                    )
                    self.assertEqual(
                        kwargs,
                        {
                            "dryrun": False,
                            "gen_newfileuid": True,
                        },
                    )

                    args, kwargs = mock_print.call_args
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], "th-th-th-that's all folks!")
                    self.assertEqual(len(kwargs), 0)

    def testRequestStmtDryrun(self):
        with patch("ofxtools.Client.OFXClient.request_statements") as fake_rq_stmt:
            with patch("builtins.print") as mock_print:
                fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
                output = ofxget.request_stmt(self.args)

                self.assertEqual(output, None)

                args, kwargs = fake_rq_stmt.call_args
                password, *stmtrqs = args
                self.assertEqual(password, "anonymous00000000000000000000000")
                self.assertEqual(
                    stmtrqs,
                    [
                        StmtRq(
                            acctid="123",
                            accttype="CHECKING",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="234",
                            accttype="CHECKING",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="345",
                            accttype="SAVINGS",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="456",
                            accttype="SAVINGS",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="567",
                            accttype="MONEYMRKT",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="678",
                            accttype="MONEYMRKT",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="789",
                            accttype="CREDITLINE",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        StmtRq(
                            acctid="890",
                            accttype="CREDITLINE",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        CcStmtRq(
                            acctid="111",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        CcStmtRq(
                            acctid="222",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                        ),
                        InvStmtRq(
                            acctid="333",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            dtasof=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                            incoo=False,
                            incpos=True,
                            incbal=True,
                        ),
                        InvStmtRq(
                            acctid="444",
                            dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                            dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            dtasof=datetime(2007, 12, 31, tzinfo=UTC),
                            inctran=True,
                            incoo=False,
                            incpos=True,
                            incbal=True,
                        ),
                    ],
                )
                self.assertEqual(
                    kwargs,
                    {
                        "dryrun": True,
                        "gen_newfileuid": True,
                    },
                )

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)
                self.assertEqual(args[0], "th-th-th-that's all folks!")
                self.assertEqual(len(kwargs), 0)

    def testRequestStmtEmpty(self):
        args = self.args
        args["dryrun"] = False
        for accttype in (
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
        ):
            args[accttype] = []

        with patch("getpass.getpass") as fake_getpass:
            with patch("builtins.print"):
                fake_getpass.return_value = "t0ps3kr1t"
                with patch(
                    "ofxtools.Client.OFXClient.request_statements"
                ) as fake_rq_stmt:
                    fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
                    with self.assertWarns(SyntaxWarning):
                        ofxget.request_stmt(args)

    def testRequestStmtend(self):
        args = self.args
        args["dryrun"] = False

        with patch("getpass.getpass") as fake_getpass:
            with patch("builtins.print") as mock_print:
                fake_getpass.return_value = "t0ps3kr1t"
                with patch(
                    "ofxtools.Client.OFXClient.request_statements"
                ) as fake_rq_stmtend:
                    fake_rq_stmtend.return_value = BytesIO(
                        b"th-th-th-that's all folks!"
                    )
                    output = ofxget.request_stmtend(args)

                    self.assertEqual(output, None)

                    args, kwargs = fake_rq_stmtend.call_args
                    password, *stmtrqs = args
                    self.assertEqual(password, "t0ps3kr1t")
                    self.assertEqual(
                        stmtrqs,
                        [
                            StmtEndRq(
                                acctid="123",
                                accttype="CHECKING",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="234",
                                accttype="CHECKING",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="345",
                                accttype="SAVINGS",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="456",
                                accttype="SAVINGS",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="567",
                                accttype="MONEYMRKT",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="678",
                                accttype="MONEYMRKT",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="789",
                                accttype="CREDITLINE",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            StmtEndRq(
                                acctid="890",
                                accttype="CREDITLINE",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            CcStmtEndRq(
                                acctid="111",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                            CcStmtEndRq(
                                acctid="222",
                                dtstart=datetime(2007, 1, 1, tzinfo=UTC),
                                dtend=datetime(2007, 12, 31, tzinfo=UTC),
                            ),
                        ],
                    )
                    self.assertEqual(
                        kwargs,
                        {
                            "dryrun": False,
                            "gen_newfileuid": True,
                        },
                    )

                    args, kwargs = mock_print.call_args
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], "th-th-th-that's all folks!")
                    self.assertEqual(len(kwargs), 0)

    def testRequestTax1099(self):
        args = self.args
        args["dryrun"] = False
        args["years"] = [2017, 2018]
        args["acctnum"] = "12345"
        args["recid"] = "67890"

        with patch("getpass.getpass") as fake_getpass:
            with patch("builtins.print") as mock_print:
                fake_getpass.return_value = "t0ps3kr1t"
                with patch(
                    "ofxtools.Client.OFXClient.request_tax1099"
                ) as fake_rq_tax1099:
                    fake_rq_tax1099.return_value = BytesIO(
                        b"th-th-th-that's all folks!"
                    )
                    output = ofxget.request_tax1099(args)

                    self.assertEqual(output, None)

                    args, kwargs = fake_rq_tax1099.call_args
                    password, *years = args
                    self.assertEqual(password, "t0ps3kr1t")
                    self.assertEqual(years, [2017, 2018])
                    self.assertEqual(
                        kwargs,
                        {
                            "acctnum": "12345",
                            "recid": "67890",
                            "dryrun": False,
                            "gen_newfileuid": True,
                        },
                    )

                    args, kwargs = mock_print.call_args
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], "th-th-th-that's all folks!")
                    self.assertEqual(len(kwargs), 0)


###############################################################################
# ARGUMENT/CONFIG HANDLERS
###############################################################################
class MkServerCfgTestCase(unittest.TestCase):
    """Unit tests for ofxtools.script.ofxget.mk_server_cfg()"""

    def testMkservercfg(self):
        with patch("ofxtools.scripts.ofxget.USERCFG", new=ConfigParser()):
            # FIXME - patching the classproperty isn't working
            #  with patch("ofxtools.Client.OFXClient.uuid", new="DEADBEEF"):

            # Must have "server" arg
            with self.assertRaises(ValueError):
                ofxget.mk_server_cfg({"foo": "bar"})

            # "server" arg can't have been sourced from "url" arg
            with self.assertRaises(ValueError):
                ofxget.mk_server_cfg({"server": "foo", "url": "foo"})

            results = dict(
                ofxget.mk_server_cfg(
                    {
                        "server": "myserver",
                        "url": "https://ofxget.test.com",
                        "version": 203,
                        "ofxhome": "123",
                        "org": "TEST",
                        "fid": "321",
                        "brokerid": "test.com",
                        "bankid": "11235813",
                        "user": "porkypig",
                        "pretty": True,
                        "unclosedelements": False,
                    }
                )
            )

            self.assertIn("clientuid", results)

            # FIXME - patching the classproperty isn't working
            del results["clientuid"]

            # args equal to defaults are omitted from the results
            predicted = {
                "url": "https://ofxget.test.com",
                "ofxhome": "123",
                "org": "TEST",
                "fid": "321",
                "brokerid": "test.com",
                "bankid": "11235813",
                "user": "porkypig",
                "pretty": "true",
            }

            self.assertEqual(dict(results), predicted)

            for opt, val in predicted.items():
                self.assertEqual(ofxget.USERCFG["myserver"][opt], val)


class ArgConfigTestCase(unittest.TestCase):
    """
    Unit tests for ofxtools.scripts.ofxget.config2arg() and
    ofxtools.scripts.ofxget.arg2config()
    """

    def testList2config(self):
        for cfg in (
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
            "years",
        ):
            self.assertEqual(ofxget.arg2config(cfg, list, ["123"]), "123")
            self.assertEqual(ofxget.arg2config(cfg, list, ["123", "456"]), "123, 456")

    def testBool2config(self):
        for cfg in (
            "dryrun",
            "unsafe",
            "unclosedelements",
            "pretty",
            "inctran",
            "incbal",
            "incpos",
            "incoo",
            "all",
            "write",
        ):
            self.assertEqual(ofxget.arg2config(cfg, bool, True), "true")
            self.assertEqual(ofxget.arg2config(cfg, bool, False), "false")

    def testInt2config(self):
        for cfg in ("version",):
            self.assertEqual(ofxget.arg2config(cfg, int, 1), "1")

    def testString2config(self):
        for cfg in (
            "url",
            "org",
            "fid",
            "appid",
            "appver",
            "bankid",
            "brokerid",
            "user",
            "clientuid",
            "language",
            "acctnum",
            "recid",
        ):
            self.assertEqual(ofxget.arg2config(cfg, str, "Something"), "Something")


class MergeConfigTestCase(unittest.TestCase):
    @property
    def args(self):
        return argparse.Namespace(
            server="2big2fail",
            dtstart="20070101000000",
            dtend="20071231000000",
            dtasof="20071231000000",
            checking=None,
            savings=["444"],
            moneymrkt=None,
            creditline=None,
            creditcard=["555"],
            investment=["666"],
            inctran=True,
            incoo=False,
            incpos=True,
            incbal=True,
            dryrun=True,
            user=None,
            clientuid=None,
            unclosedelements=False,
        )

    @classmethod
    def setUpClass(cls):
        # Monkey-patch ofxget.USERCFG
        default_cfg = """
        [2big2fail]
        ofxhome = 417
        version = 203
        pretty = true
        fid = 44
        org = 2big2fail
        """

        user_cfg = """
        [2big2fail]
        fid = 33
        user = porkypig
        savings = 111
        checking = 222, 333
        creditcard = 444, 555
        """

        cfg = ofxget.UserConfig()
        cfg.read_string(default_cfg)
        cfg.read_string(user_cfg)

        cls._USERCFG = ofxget.USERCFG
        ofxget.USERCFG = cfg

    @classmethod
    def tearDownClass(cls):
        # Undo monkey patches for ofxget.USERCFG
        #  ofxget.UserConfig = cls._UserConfig
        ofxget.USERCFG = cls._USERCFG

    def testMergeConfig(self):
        args = argparse.Namespace(
            server="2big2fail", user="daffyduck", creditcard=["666"]
        )

        with patch("ofxtools.ofxhome.lookup") as ofxhome_lookup:
            ofxhome_lookup.return_value = OFXServer(
                id="1",
                name="Two Big Two Fail",
                fid="22",
                org="2BIG2FAIL",
                url="https://ofx.test.com",
                brokerid="2big2fail.com",
            )

            merged = ofxget.merge_config(args, ofxget.USERCFG)

        # None of args/usercfg/defaultcfg has the URL,
        # so there should have been an OFX Home lookup
        ofxhome_lookup.assert_called_once_with("417")

        # ChainMap(args, user_cfg, ofxhome_lookup, DEFAULTS)
        self.assertIsInstance(merged, collections.ChainMap)
        maps = merged.maps
        self.assertEqual(len(maps), 4)
        self.assertEqual(maps[0]["user"], "daffyduck")
        self.assertEqual(maps[1]["user"], "porkypig")
        self.assertEqual(maps[2]["org"], "2BIG2FAIL")
        self.assertEqual(maps[3], ofxget.DEFAULTS)

        # Any arg from the the CLI should be available in the merged map.
        self.assertEqual(merged["server"], "2big2fail")

        # Args passed from the CLI trump the same args from any other source.
        self.assertEqual(merged["user"], "daffyduck")

        # For list-type configs, higher-priority config overrides
        # lower-priority config (i.e. it's not appended).
        self.assertEqual(merged["creditcard"], ["666"])

        # Args missing from CLI fall back to user config...
        self.assertEqual(merged["savings"], ["111"])

        # ...or, failing that, fall back to library default config...
        self.assertEqual(merged["org"], "2big2fail")

        # ...or, failing that, fall back to ofxhome lookup
        self.assertEqual(merged["brokerid"], "2big2fail.com")

        # ...or, failing THAT, fall back to ofxget.DEFAULTS
        self.assertEqual(merged["unsafe"], False)

        # User config trumps library default config and ofxhome lookup
        self.assertEqual(merged["fid"], "33")

        # Library default config trumps ofxhome lookup
        self.assertEqual(merged["org"], "2big2fail")

        # Library default config drumps ofxget.DEFAULTS
        # Also, INI bool conversion works
        self.assertEqual(merged["pretty"], True)

        # INI list chunking works
        self.assertEqual(maps[1]["checking"], ["222", "333"])

        # INI int conversion works
        self.assertEqual(maps[1]["version"], 203)

        # We have proper types for all lists, even absent configuration
        for lst in (
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
            "years",
        ):
            self.assertIsInstance(merged[lst], list)

        # We have proper types for all bools, even absent configuration
        for boole in (
            "dryrun",
            "unsafe",
            "unclosedelements",
            "pretty",
            "inctran",
            "incbal",
            "incpos",
            "incoo",
            "all",
            "write",
        ):
            self.assertIsInstance(merged[boole], bool)

        # We have default empty string for all unset string configs
        for string in (
            "appid",
            "appver",
            "bankid",
            "clientuid",
            "language",
            "acctnum",
            "recid",
        ):
            self.assertEqual(merged[string], "")

    def testMergeConfigUnknownFiArg(self):
        args = argparse.Namespace(server="3big4fail")
        with self.assertRaises(ValueError):
            ofxget.merge_config(args, ofxget.USERCFG)


###############################################################################
# PROFILE SCAN
###############################################################################
class ScanProfileTestCase(unittest.TestCase):
    """Unit tests for ofxtools.scripts.ofxget._scan_profile() and helpers"""

    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        profmsgsrsv1=test_models_msgsets.Profmsgsrsv1TestCase.aggregate,
    )

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    errcount = 0

    def prof_result(self, version, prettyprint, close_elements, **kwargs):
        # Sequence of errors caught for futures.result() in _scan_profile()
        errors = (
            urllib.error.URLError(None, None),
            urllib.error.HTTPError(None, None, None, None, None),
            ConnectionError(),
            OSError(),
        )
        accept = [
            (102, False, False),
            (102, True, True),
            (103, False, False),
            (103, True, True),
            (203, False, True),
            (203, True, True),
        ]
        if (version, prettyprint, close_elements) in accept:
            ofx = self.client.serialize(
                ofx=self.ofx,
                version=version,
                prettyprint=prettyprint,
                close_elements=close_elements,
            )
            return BytesIO(ofx)
        else:
            error = errors[self.errcount % len(errors)]
            self.errcount += 1
            raise error

    def test_scanProfile(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as mock_profrq:
            mock_profrq.side_effect = self.prof_result
            results = ofxget._scan_profile(None, None, None, None, None)

        ofxv1 = {
            "versions": [102, 103],
            "formats": [
                {"pretty": False, "unclosedelements": True},
                {"pretty": True, "unclosedelements": False},
            ],
        }

        ofxv2 = {"versions": [203], "formats": [{"pretty": False}, {"pretty": True}]}

        signoninfo = {
            "chgpinfirst": False,
            "clientuidreq": False,
            "authtokenfirst": False,
            "mfachallengefirst": False,
        }

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], ofxv1)
        self.assertEqual(results[1], ofxv2)
        self.assertEqual(results[2], signoninfo)

    def test_scanProfileNoResult(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as mock_profrq:
            mock_profrq.side_effect = urllib.error.URLError(None, None)
            results = ofxget._scan_profile(None, None, None, None, None)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], {"versions": [], "formats": []})
        self.assertEqual(results[1], {"versions": [], "formats": []})
        self.assertEqual(results[2], {})

    def testQueueScanResponse(self):
        """Test ofxget._queue_scans()"""
        with patch("ofxtools.Client.OFXClient.request_profile") as mock_profrq:
            mock_profrq.side_effect = self.prof_result

            futures = ofxget._queue_scans(
                self.client, gen_newfileuid=True, max_workers=1, timeout=1.0
            )

        # OFXv1: pretty, unclosed True/False for 6 versions; 4 * 4 = 16
        # OFXv2: pretty True/False for 7 versions ; 7 * 2 = 12
        self.assertEqual(len(futures), 30)

        for future, format in futures.items():
            self.assertIsInstance(future, concurrent.futures.Future)
            self.assertEqual(len(format), 2)
            version, format = format
            self.assertIn(
                version, [102, 103, 151, 160, 200, 201, 202, 203, 210, 211, 220]
            )
            self.assertEqual(len(format), 2)
            self.assertIsInstance(format["pretty"], bool)
            self.assertIsInstance(format["unclosedelements"], bool)


class ReadScanResponseTestCase(unittest.TestCase):
    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        profmsgsrsv1=test_models_msgsets.Profmsgsrsv1TestCase.aggregate,
    )

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    def testReadScanResponse(self):
        markup = self.client.serialize(self.ofx)

        # Connection error: return False, empty SIGNONINFO parameters
        rq_errors = [
            URLError(""),
            HTTPError(None, None, None, None, None),
            ConnectionError(""),
            OSError(""),
            socket.timeout,
        ]

        for error in rq_errors:
            with patch("concurrent.futures.Future.result") as mock_result:
                mock_result.side_effect = error

                future = concurrent.futures.Future()
                result = ofxget._read_scan_response(future)

            self.assertEqual(len(result), 2)
            self.assertFalse(result[0])
            self.assertEqual(result[1], {})

        # No valid OFX: return False, empty SIGNONINFO parameters
        ofx_errors = [
            socket.timeout,
            ET.ParseError(),
            Parser.ParseError(),
            header.OFXHeaderError(),
        ]
        for error in ofx_errors:
            with patch("concurrent.futures.Future.result") as mock_result:
                mock_result.return_value = BytesIO(markup)
                with patch(
                    "ofxtools.scripts.ofxget.extract_signoninfos"
                ) as mock_extract_signoninfos:
                    mock_extract_signoninfos.side_effect = error

                    future = concurrent.futures.Future()
                    result = ofxget._read_scan_response(future, read_signoninfo=True)

            self.assertEqual(len(result), 2)
            self.assertFalse(result[0])
            self.assertEqual(result[1], {})

        # Valid OFX with no good SIGNONINFO: return True, empty SIGNONINFO
        with patch("concurrent.futures.Future.result") as mock_result:
            mock_result.return_value = BytesIO(markup)
            with patch(
                "ofxtools.scripts.ofxget.extract_signoninfos"
            ) as mock_extract_signoninfos:
                mock_extract_signoninfos.side_effect = ValueError()

                future = concurrent.futures.Future()
                result = ofxget._read_scan_response(future, read_signoninfo=True)

            self.assertEqual(len(result), 2)
            self.assertTrue(result[0])
            self.assertEqual(result[1], {})

        # Valid OFX with good SIGNONINFO: return True, SIGNONINFO parameters
        with patch("concurrent.futures.Future.result") as mock_result:
            mock_result.return_value = BytesIO(markup)

            future = concurrent.futures.Future()
            result = ofxget._read_scan_response(future, read_signoninfo=True)

            self.assertEqual(len(result), 2)
            self.assertTrue(result[0])
            signoninfo = result[1]
            self.assertEqual(len(signoninfo), 4)
            self.assertEqual(
                set(signoninfo.keys()),
                set(
                    [
                        "chgpinfirst",
                        "clientuidreq",
                        "authtokenfirst",
                        "mfachallengefirst",
                    ]
                ),
            )


class CollateScanResultsTestCase(unittest.TestCase):
    def testCollateScanResults(self):
        formats_in = [
            {"pretty": True, "unclosedelements": True},
            {"pretty": False, "unclosedelements": True},
            {"pretty": False, "unclosedelements": False},
        ]

        v1 = [(160, formats_in), (102, formats_in), (103, formats_in)]
        v1_result = ofxget.collate_scan_results(v1)
        self.assertEqual(list(v1_result.keys()), ["versions", "formats"])
        self.assertEqual(v1_result["versions"], [102, 103, 160])

        self.assertEqual(
            v1_result["formats"],
            [
                {"pretty": False, "unclosedelements": False},
                {"pretty": False, "unclosedelements": True},
                {"pretty": True, "unclosedelements": True},
            ],
        )


###############################################################################
# OFX PARSING
###############################################################################
class VerifyStatusTestCase(unittest.TestCase):
    """Unit tests for ofxtools.scripts.ofxget.verify_status()"""

    status_good = models.STATUS(code=0, severity="INFO")
    status_bad = models.STATUS(code=1500, severity="ERROR")
    dtserver = datetime(2012, 5, 31, tzinfo=UTC)

    def test_verify_status(self):
        sonrs_good = models.SONRS(
            status=self.status_good, dtserver=self.dtserver, language="ENG"
        )

        ofxget.verify_status(sonrs_good)
        sonrs_bad = models.SONRS(
            status=self.status_bad, dtserver=self.dtserver, language="ENG"
        )
        with self.assertRaises(ValueError):
            ofxget.verify_status(sonrs_bad)


class AcctIsActiveTestCase(unittest.TestCase):
    """Unit tests for ofxtools.scripts.ofxget._acctIsActive()"""

    bankacctinfo = test_models_bank_stmt.BankacctinfoTestCase.aggregate
    ccacctinfo = test_models_bank_stmt.CcacctinfoTestCase.aggregate
    invacctinfo = test_models_invest.InvacctinfoTestCase.aggregate
    bpacctinfo = test_models_billpay_common.BpacctinfoTestCase.aggregate

    def testAcctIsActive(self):
        for acctinfo in (
            self.bankacctinfo,
            self.ccacctinfo,
            self.invacctinfo,
            self.bpacctinfo,
        ):
            acctinfo.svcstatus = "ACTIVE"
            self.assertTrue(ofxget._acctIsActive(acctinfo))
            for svcstatus in "PEND", "AVAIL":
                acctinfo.svcstatus = svcstatus
                self.assertFalse(ofxget._acctIsActive(acctinfo))


class ExtractSignonInfosTestCase(unittest.TestCase):
    """Unit tests for ofxtools.scripts.ofxget.extract_signoninfos()"""

    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        profmsgsrsv1=test_models_msgsets.Profmsgsrsv1TestCase.aggregate,
    )

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    def testExtractSignonInfos(self):
        markup = BytesIO(self.client.serialize(self.ofx))
        signoninfos = list(ofxget.extract_signoninfos(markup))
        self.assertEqual(len(signoninfos), 4)
        self.assertTrue(utils.all_equal(signoninfos))
        info = signoninfos[0]
        self.assertEqual(info.signonrealm, "AMERITRADE")
        self.assertEqual(info.min, 4)
        self.assertEqual(info.max, 32)
        self.assertEqual(info.chartype, "ALPHAORNUMERIC")
        self.assertTrue(info.casesen)
        self.assertFalse(info.special)
        self.assertFalse(info.spaces)
        self.assertFalse(info.pinch)
        self.assertFalse(info.chgpinfirst)


class ExtractAcctInfosTestCase(unittest.TestCase):
    """Unit tests for ofxtools.scripts.ofxget.extract_acctinfos()"""

    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        signupmsgsrsv1=models.SIGNUPMSGSRSV1(
            test_models_signup.AcctinfotrnrsTestCase.aggregate
        ),
    )

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    def test_extract_acctinfos(self):
        ofx = self.client.serialize(self.ofx)
        results = ofxget.extract_acctinfos(BytesIO(ofx))
        # results is an iterator - sorted by *ACCTINFO classname
        results = list(results)

        acctinfo = test_models_signup.AcctinfoTestCase.aggregate

        # HACK - Reuse base.OfxTestCase._eqAggregate to determine that
        # our results are the same as the children of
        # test_models_signup.AcctinfoTestCase, which was used to construct
        # self.ofx
        class Foo(unittest.TestCase, base.OfxTestCase):
            ...

        tc = Foo()

        for n in range(3):
            tc._eqAggregate(results[n], acctinfo[n])


###############################################################################
# CLI UTILITIES
###############################################################################
class FiIndexTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = ConfigParser()
        parser["NAMES"] = {"0": "0th Server", "1": "1st Server"}
        parser["server0"] = {"ofxhome": "0", "url": "https://ofx.test.com"}
        parser["server1"] = {"ofxhome": "1", "url": "https://ofx.test.com"}

        cls.USERCFG = parser

    def testFiIndex(self):
        with patch("ofxtools.scripts.ofxget.USERCFG", new=self.USERCFG):
            servers = ofxget.fi_index()

        self.assertEqual(
            servers, [("0th Server", "server0", "0"), ("1st Server", "server1", "1")]
        )

    def testListFisNoServer(self):
        with patch("ofxtools.scripts.ofxget.USERCFG", new=self.USERCFG):
            with patch("pydoc.pager") as mock_pager:
                ofxget.list_fis({"server": ""})

        # FIXME

    def testListFisWithUnknownServer(self):
        with patch("ofxtools.scripts.ofxget.USERCFG", new=self.USERCFG):
            with self.assertRaises(ValueError):
                ofxget.list_fis({"server": "server2"})

    def testListFisWithKnownServer(self):
        with patch("ofxtools.scripts.ofxget.USERCFG", new=self.USERCFG):
            with patch("builtins.print") as mock_print:
                ofxget.list_fis({"server": "server0"})

        # FIXME


class SavePasswdTestCase(unittest.TestCase):
    def testSavePasswdDryRun(self):
        with self.assertWarns(SyntaxWarning):
            ofxget.save_passwd({"dryrun": True}, "t0ps3kr1t")

    def testSavePasswdEmptyPassword(self):
        with self.assertWarns(SyntaxWarning):
            ofxget.save_passwd({"dryrun": False, "nokeyring": False}, "")

    def testSavePasswdNoKeyring(self):
        HAS_KEYRING = ofxget.HAS_KEYRING
        try:
            ofxget.HAS_KEYRING = False
            with self.assertRaises(RuntimeError):
                ofxget.save_passwd({"dryrun": False, "nokeyring": False}, "t0ps3kr1t")
        finally:
            ofxget.HAS_KEYRING = HAS_KEYRING

    #  def testSavePasswdSuccess(self):
    #  assert ofxget.HAS_KEYRING is True
    #  with patch("keyring.set_password") as set_password:
    #  ofxget.save_passwd({"dryrun": False, "server": "myserver"}, "t0ps3kr1t")
    #  set_password.assert_called_once_with("ofxtools", "myserver", "t0ps3kr1t")


class MainTestCase(unittest.TestCase):
    def testMain(self):
        args = argparse.Namespace(verbose=1, request="list")
        mock_parser = Mock()
        mock_parser.parse_args.return_value = args

        def _merge_config(*args):
            return {"verbose": 1, "request": "list", "server": "server0"}

        _USERCFG = ConfigParser()
        _USERCFG["NAMES"] = {"0": "0th server"}
        _USERCFG["server0"] = {"ofxhome": "0", "url": "https://ofx.test.com"}

        with patch.multiple(
            "ofxtools.scripts.ofxget",
            make_argparser=mock_parser,
            merge_config=_merge_config,
            list_fis=DEFAULT,
            USERCFG=_USERCFG,
        ) as MOCKS:
            ofxget.main()


if __name__ == "__main__":
    unittest.main()
