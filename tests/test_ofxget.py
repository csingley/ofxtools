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


class CliTestCase(unittest.TestCase):
    @property
    def args(self):
        return {
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
        }

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

    def testRequestStmt(self):
        args = self.args
        args["dryrun"] = False

        with patch("getpass.getpass") as fake_getpass:
            fake_getpass.return_value = "t0ps3kr1t"
            with patch("ofxtools.Client.OFXClient.request_statements") as fake_rq_stmt:
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

    def testRequestStmtDryrun(self):
        with patch("ofxtools.Client.OFXClient.request_statements") as fake_rq_stmt:
            fake_rq_stmt.return_value = BytesIO(b"th-th-th-that's all folks!")
            output = ofxget.request_stmt(self.args)

            self.assertEqual(output, None)

            args, kwargs = fake_rq_stmt.call_args
            password, *stmtrqs = args
            self.assertEqual(password, "{:0<32}".format("anonymous"))
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

    def testRequestProfile(self):
        with patch("ofxtools.Client.OFXClient.request_profile") as fake_rq_prof:
            fake_rq_prof.return_value = BytesIO(b"th-th-th-that's all folks!")

            output = ofxget.request_profile(self.args)

            self.assertEqual(output, None)

            args, kwargs = fake_rq_prof.call_args
            self.assertEqual(len(args), 0)

            self.assertEqual(kwargs,
                             {"dryrun": self.args["dryrun"],
                              "verify_ssl": not self.args["unsafe"],
                              "version": self.args["version"],
                              "prettyprint": self.args["pretty"],
                              "close_elements": not self.args["unclosedelements"]})


class MakeArgParserTestCase(unittest.TestCase):
    def testMakeArgparser(self):
        # This is the lamest test ever
        argparser = ofxget.make_argparser()
        self.assertGreater(len(argparser._actions), 0)


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
        default_cfg["2big2fail"]["ofxhome_id"] = "417"
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

        # We have default value of None for all unset string configs
        for string in ("appid", "appver", "bankid", "clientuid", "language",
                       "acctnum", "recid"):
            self.assertIsNone(merged[string])

    def testMergeConfigUnknownFiArg(self):
        args = argparse.Namespace(server="3big4fail")
        with self.assertRaises(ValueError):
            ofxget.merge_config(args)


if __name__ == "__main__":
    unittest.main()
