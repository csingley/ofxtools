# coding: utf-8
""" Unit tests for ofxtools.ofxget """

# stdlib imports
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from io import BytesIO
import argparse
import configparser
import collections
import urllib
from configparser import ConfigParser


# local imports
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
from ofxtools import models
from ofxtools import Parser

# test imports
import test_models_msgsets
import test_models_signup


class MakeArgParserTestCase(unittest.TestCase):
    def testMakeArgparser(self):
        # This is the lamest test ever
        argparser = ofxget.make_argparser()
        self.assertGreater(len(argparser._actions), 0)


class CliTestCase(unittest.TestCase):
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
        }

    def testScanProfile(self):
        with patch("ofxtools.scripts.ofxget._scan_profile") as mock_scan_prof:
            with patch("builtins.print") as mock_print:
                ofxv1 = collections.OrderedDict([
                    ("versions", [102, 103]),
                    ("formats", [{"pretty": False, "unclosedelements": True},
                                 {"pretty": True, "unclosedelements": False}])])

                ofxv2 = collections.OrderedDict([
                    ("versions", [203]),
                    ("formats", [{"pretty": False},
                                 {"pretty": True}])])

                mock_scan_prof.return_value = (ofxv1, ofxv2)
                result = ofxget.scan_profile(self.args)
                self.assertIsNone(result, None)

                args, kwargs = mock_scan_prof.call_args
                self.assertEqual(len(args), 3)
                url, org, fid = args
                self.assertEqual(url, self.args["url"])
                self.assertEqual(org, self.args["org"])
                self.assertEqual(fid, self.args["fid"])
                self.assertEqual(len(kwargs), 0)

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)

                # FIXME - the string output of dicts in json.dumps() appears
                # not to be stable; below is for Py 3.5 - 3.7, whereas 
                # Py 3.4 looks like this:
                #[{"versions": [102, 103], "formats": [{"unclosedelements": true, "pretty": false}, {"unclosedelements": false, "pretty": true}]}, {"versions": [203], "formats": [{"pretty": false}, {"pretty": true}]}]

                #  self.maxDiff = None
                #  self.assertEqual(
                    #  args[0],
                    #  ('[{"versions": [102, 103], '
                     #  '"formats": [{"pretty": false, "unclosedelements": true},'
                     #  ' {"pretty": true, "unclosedelements": false}]}, '
                     #  '{"versions": [203], "formats": [{"pretty": false}, '
                     #  '{"pretty": true}]}]'))

    def testRequestProfile(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as fake_rqprof:
            with patch("builtins.print") as mock_print:
                fake_rqprof.return_value = BytesIO(
                    b"th-th-th-that's all folks!")

                output = ofxget.request_profile(self.args)
                self.assertEqual(output, None)

                args, kwargs = fake_rqprof.call_args
                self.assertEqual(len(args), 0)

                self.assertEqual(kwargs,
                                 {"dryrun": self.args["dryrun"],
                                  "verify_ssl": not self.args["unsafe"]})

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)
                self.assertEqual(args[0], "th-th-th-that's all folks!")
                self.assertEqual(len(kwargs), 0)

    def testRequestAcctinfo(self):
        """ Unit test for ofxtools.scripts.ofxget.request_acctinfo() """
        args = self.args
        args["dryrun"] = False

        with patch("ofxtools.scripts.ofxget._request_acctinfo") as fake_rq_acctinfo:
            with patch("getpass.getpass") as fake_getpass:
                with patch("builtins.print") as mock_print:
                    fake_getpass.return_value = "t0ps3kr1t"
                    fake_rq_acctinfo.return_value = BytesIO(b"th-th-th-that's all folks!")

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
        """ Unit test for ofxtools.scripts.ofxget._request_acctinfo() """
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
            self.assertEqual(dtacctup,
                             datetime(1999, 12, 31, tzinfo=UTC))

            self.assertEqual(kwargs,
                             {"dryrun": self.args["dryrun"],
                          "verify_ssl": not self.args["unsafe"]})

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
                    self.assertEqual(kwargs, {"dryrun": False,"verify_ssl": True})

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
                self.assertEqual(kwargs, {"dryrun": True, "verify_ssl": True})

                args, kwargs = mock_print.call_args
                self.assertEqual(len(args), 1)
                self.assertEqual(args[0], "th-th-th-that's all folks!")
                self.assertEqual(len(kwargs), 0)

    def testRequestStmtend(self):
        args = self.args
        args["dryrun"] = False

        with patch("getpass.getpass") as fake_getpass:
            with patch("builtins.print") as mock_print:
                fake_getpass.return_value = "t0ps3kr1t"
                with patch("ofxtools.Client.OFXClient.request_statements") as fake_rq_stmtend:
                    fake_rq_stmtend.return_value = BytesIO(b"th-th-th-that's all folks!")
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
                    self.assertEqual(kwargs, {"dryrun": False,"verify_ssl": True})

                    args, kwargs = mock_print.call_args
                    self.assertEqual(len(args), 1)
                    self.assertEqual(args[0], "th-th-th-that's all folks!")
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


class _ScanProfileTestCase(unittest.TestCase):
    """ Unit tests for ofxtools.scripts.ofxget._scan_profile() """
    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        profmsgsrsv1=test_models_msgsets.Profmsgsrsv1TestCase.aggregate)

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    errcount = 0

    def prof_result(self, version, prettyprint, close_elements, **kwargs):
        # Sequence of errors caught for futures.result() in _scan_profile()
        errors = (urllib.error.URLError(None, None),
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
            (203, True, True)
        ]
        if (version, prettyprint, close_elements) in accept:
            ofx = self.client.serialize(self.ofx,
                                        version,
                                        prettyprint,
                                        close_elements)
            return BytesIO(ofx)
        else:
            error = errors[self.errcount % len(errors)]
            self.errcount += 1
            raise error

    def test_scanProfile(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as mock_profrq:
            mock_profrq.side_effect = self.prof_result
            results = ofxget._scan_profile(None, None, None)

        ofxv1 = collections.OrderedDict([
            ("versions", [102, 103]),
            ("formats", [{"pretty": False, "unclosedelements": True},
                         {"pretty": True, "unclosedelements": False}])])

        ofxv2 = collections.OrderedDict([
            ("versions", [203]),
            ("formats", [{"pretty": False},
                         {"pretty": True}])])

        self.assertEqual(results, (ofxv1, ofxv2))


class ExtractAcctInfosTestCase(unittest.TestCase):
    """ Unit tests for ofxtools.scripts.ofxget.extract_acctinfos() """
    ofx = models.OFX(
        signonmsgsrsv1=test_models_msgsets.Signonmsgsrsv1TestCase.aggregate,
        signupmsgsrsv1=models.SIGNUPMSGSRSV1(
            test_models_signup.AcctinfotrnrsTestCase.aggregate))

    @property
    def client(self):
        return OFXClient("https://ofx.test.com")

    def test_extract_acctinfos(self):
        ofx = self.client.serialize(self.ofx)
        results = ofxget.extract_acctinfos(BytesIO(ofx))
        self.assertEqual(len(results), 5)
        self.assertEqual(results["bankid"], "111000614")
        self.assertEqual(results["brokerid"], "111000614")
        self.assertEqual(results["checking"], ["123456789123456789"])
        self.assertEqual(results["creditcard"], ["123456789123456789"])
        self.assertEqual(results["investment"], ["123456789123456789"])


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
        # Monkey-patch ofxget.UserConfig, ofxget.DefaultConfig
        user_cfg = configparser.ConfigParser()
        user_cfg["2big2fail"] = {}
        user_cfg["2big2fail"]["fid"] = "33"
        user_cfg["2big2fail"]["user"] = "porkypig"
        user_cfg["2big2fail"]["savings"] = "111"
        user_cfg["2big2fail"]["checking"] = "222, 333"
        user_cfg["2big2fail"]["creditcard"] = "444, 555"

        default_cfg = configparser.ConfigParser()
        default_cfg["2big2fail"] = {}
        default_cfg["2big2fail"]["ofxhome"] = "417"
        default_cfg["2big2fail"]["version"] = "203"
        default_cfg["2big2fail"]["pretty"] = "true"
        default_cfg["2big2fail"]["fid"] = "44"
        default_cfg["2big2fail"]["org"] = "2big2fail"

        cls._UserConfig = ofxget.UserConfig
        ofxget.UserConfig = user_cfg

        cls._DefaultConfig = ofxget.DefaultConfig
        ofxget.DefaultConfig = default_cfg

    @classmethod
    def tearDownClass(cls):
        # Undo monkey patches for ofxget.UserConfig, ofxget.DefaultConfig
        ofxget.UserConfig = cls._UserConfig
        ofxget.DefaultConfig = cls._DefaultConfig

    def testMergeConfig(self):
        args = argparse.Namespace(
            server="2big2fail",
            user="daffyduck",
            creditcard=["666"],
        )

        with patch("ofxtools.ofxhome.lookup") as ofxhome_lookup:
            ofxhome_lookup.return_value = OFXServer(
                id="1", name="Two Big Two Fail", fid="22", org="2BIG2FAIL",
                url="https://ofx.test.com", brokerid="2big2fail.com")

            merged = ofxget.merge_config(args)

        # None of args/usercfg/defaultcfg has the URL,
        # so there should have been an OFX Home lookup
        ofxhome_lookup.assert_called_once_with("417")

        # ChainMap(args, user_cfg, default_cfg, ofxhome_lookup, DEFAULTS)
        self.assertIsInstance(merged, collections.ChainMap)
        maps = merged.maps
        self.assertEqual(len(maps), 5)
        self.assertEqual(maps[0]["user"], "daffyduck")
        self.assertEqual(maps[1]["user"], "porkypig")
        self.assertEqual(maps[2]["org"], "2big2fail")
        self.assertEqual(maps[3]["org"], "2BIG2FAIL")
        self.assertEqual(maps[4], ofxget.DEFAULTS)

        # Args passed from the CLI trump everything
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
        self.assertEqual(maps[2]["version"], 203)

        # We have proper types for all lists, even absent configuration
        for lst in ("checking", "savings", "moneymrkt", "creditline",
                    "creditcard", "investment", "years", ):
            self.assertIsInstance(merged[lst], list)

        # We have proper types for all bools, even absent configuration
        for boole in ("dryrun", "unsafe", "unclosedelements", "pretty",
                      "inctran", "incbal", "incpos", "incoo", "all", "write"):
            self.assertIsInstance(merged[boole], bool)

        # We have default empty string for all unset string configs
        for string in ("appid", "appver", "bankid", "clientuid", "language",
                       "acctnum", "recid"):
            self.assertEqual(merged[string], "")

    def testMergeConfigUnknownFiArg(self):
        args = argparse.Namespace(server="3big4fail")
        with self.assertRaises(ValueError):
            ofxget.merge_config(args)


class ArgConfigTestCase(unittest.TestCase):
    """
    Unit tests for ofxtools.scripts.ofxget.config2arg() and
    ofxtools.scripts.ofxget.arg2config()
    """
    def testList2arg(self):
        for cfg in ("checking", "savings", "moneymrkt", "creditline",
                    "creditcard", "investment", "years"):
            self.assertEqual(ofxget.config2arg(cfg, "123"), ["123"])
            self.assertEqual(ofxget.config2arg(cfg, "123,456"), ["123", "456"])

            # Surrounding whitespace is stripped
            self.assertEqual(ofxget.config2arg(cfg, " 123 "), ["123"])
            self.assertEqual(ofxget.config2arg(cfg, "123, 456"), ["123", "456"])

    def testList2config(self):
        for cfg in ("checking", "savings", "moneymrkt", "creditline",
                    "creditcard", "investment", "years"):
            self.assertEqual(ofxget.arg2config(cfg, ["123"]), "123")
            self.assertEqual(ofxget.arg2config(cfg, ["123", "456"]), "123, 456")

    def testListRoundtrip(self):
        for cfg in ("checking", "savings", "moneymrkt", "creditline",
                    "creditcard", "investment", "years"):
            self.assertEqual(
                ofxget.config2arg(cfg, ofxget.arg2config(cfg, ["123", "456"])),
                ["123", "456"])
            self.assertEqual(
                ofxget.arg2config(cfg, ofxget.config2arg(cfg, "123, 456")),
                "123, 456")

    def testBool2arg(self):
        for cfg in ("dryrun", "unsafe", "unclosedelements", "pretty",
                    "inctran", "incbal", "incpos", "incoo", "all", "write"):
            self.assertEqual(ofxget.config2arg(cfg, "true"), True)
            self.assertEqual(ofxget.config2arg(cfg, "false"), False)
            self.assertEqual(ofxget.config2arg(cfg, "yes"), True)
            self.assertEqual(ofxget.config2arg(cfg, "no"), False)
            self.assertEqual(ofxget.config2arg(cfg, "on"), True)
            self.assertEqual(ofxget.config2arg(cfg, "off"), False)
            self.assertEqual(ofxget.config2arg(cfg, "1"), True)
            self.assertEqual(ofxget.config2arg(cfg, "0"), False)

    def testBool2config(self):
        for cfg in ("dryrun", "unsafe", "unclosedelements", "pretty",
                    "inctran", "incbal", "incpos", "incoo", "all", "write"):
            self.assertEqual(ofxget.arg2config(cfg, True), "true")
            self.assertEqual(ofxget.arg2config(cfg, False), "false")

    def testBoolRoundtrip(self):
        for cfg in ("dryrun", "unsafe", "unclosedelements", "pretty",
                    "inctran", "incbal", "incpos", "incoo", "all", "write"):
            self.assertEqual(
                ofxget.config2arg(cfg, ofxget.arg2config(cfg, True)),
                True)
            self.assertEqual(
                ofxget.config2arg(cfg, ofxget.arg2config(cfg, False)),
                False)
            self.assertEqual(
                ofxget.arg2config(cfg, ofxget.config2arg(cfg, "true")),
                "true")
            self.assertEqual(
                ofxget.arg2config(cfg, ofxget.config2arg(cfg, "false")),
                "false")

    def testInt2arg(self):
        for cfg in ("version", ):
            self.assertEqual(ofxget.config2arg(cfg, "1"), 1)

    def testInt2config(self):
        for cfg in ("version", ):
            self.assertEqual(ofxget.arg2config(cfg, 1), "1")

    def testIntRoundtrip(self):
        for cfg in ("version", ):
            self.assertEqual(
                ofxget.config2arg(cfg, ofxget.arg2config(cfg, 1)),
                1)
            self.assertEqual(
                ofxget.arg2config(cfg, ofxget.config2arg(cfg, "1")),
                "1")

    def testString2arg(self):
        for cfg in ("url", "org", "fid", "appid", "appver", "bankid",
                    "brokerid", "user", "clientuid", "language", "acctnum",
                    "recid"):
            self.assertEqual(ofxget.config2arg(cfg, "Something"), "Something")

    def testString2config(self):
        for cfg in ("url", "org", "fid", "appid", "appver", "bankid",
                    "brokerid", "user", "clientuid", "language", "acctnum",
                    "recid"):
            self.assertEqual(ofxget.arg2config(cfg, "Something"), "Something")

    def testStringRoundtrip(self):
        for cfg in ("url", "org", "fid", "appid", "appver", "bankid",
                    "brokerid", "user", "clientuid", "language", "acctnum",
                    "recid"):
            self.assertEqual(
                ofxget.config2arg(cfg, ofxget.arg2config(cfg, "Something")),
                "Something")
            self.assertEqual(
                ofxget.arg2config(cfg, ofxget.config2arg(cfg, "Something")),
                "Something")


class MkServerCfgTestCase(unittest.TestCase):
    """ Unit tests for ofxtools.script.ofxget.mk_server_cfg() """
    def testMkservercfg(self):
        with patch("ofxtools.scripts.ofxget.UserConfig", new=ConfigParser()):
            # Must have "server" arg
            with self.assertRaises(ValueError):
                ofxget.mk_server_cfg({"foo": "bar"})

            # "server" arg can't have been sourced from "url" arg
            with self.assertRaises(ValueError):
                ofxget.mk_server_cfg({"server": "foo", "url": "foo"})

            results = ofxget.mk_server_cfg(
                {"server": "myserver", "url": "https://ofxget.test.com",
                 "version": 203, "ofxhome": "123", "org": "TEST", "fid": "321",
                 "brokerid": "test.com", "bankid": "11235813",
                 "user": "porkypig", "pretty": True,
                 "unclosedelements": False})

            # args equal to defaults are omitted from the results
            predicted = {
                "url": "https://ofxget.test.com", "ofxhome": "123",
                "org": "TEST", "fid": "321", "brokerid": "test.com",
                "bankid": "11235813", "user": "porkypig", "pretty": "true"}

            self.assertEqual(dict(results), predicted)

            for opt, val in predicted.items():
                self.assertEqual(ofxget.UserConfig["myserver"][opt], val)


if __name__ == "__main__":
    unittest.main()
