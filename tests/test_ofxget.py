# coding: utf-8
""" Unit tests for ofxtools.ofxget """

# stdlib imports
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from io import BytesIO
import argparse


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


class MainTestCase(unittest.TestCase):
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

    def testMakeArgparser(self):
        fi_index = ["bank0", "broker0"]
        argparser = ofxget.make_argparser(fi_index)
        self.assertEqual(len(argparser._actions), 34)

    def testMergeConfig(self):
        config = MagicMock()
        config.fi_index = ["2big2fail"]
        self.assertEqual(config.fi_index, ["2big2fail"])
        config.items.return_value = [
            ("user", "porkypig"),
            ("checking", "111"),
            ("creditcard", "222, 333"),
        ]

        args = ofxget.merge_config(config, self.args)
        # Entries in self.args that are not None and aren't specified in
        # config.items() remain unchanged.
        attrs = ["server", "dtstart", "dtend", "dtasof", "savings",
                 "investment", "inctran", "incoo", "incpos", "incbal",
                 "dryrun", "unclosedelements"]
        for attr in attrs:
            self.assertEqual(args[attr], getattr(self.args, attr))

        # Entries in self.args that are missing or None fall back to
        # entries from config
        self.assertEqual(args["user"], "porkypig")
        self.assertEqual(args["checking"], ["111"])
        # CLI args override config completely (not append)
        self.assertEqual(args["creditcard"], ["555"])

        # Entries that are are missing or None in both self.args and config
        # fall back to ARG_DEFAULTS
        attrs = ["moneymrkt", "creditline", "clientuid", "unsafe", "pretty",
                 "all", "years", "acctnum", "recid"]

        for atttr in attrs:
            self.assertEqual(args[attr], ofxget.ARG_DEFAULTS[attr])

    def testMergeConfigUnknownFiArg(self):
        config = MagicMock()
        config.fi_index = []
        with self.assertRaises(ValueError):
            ofxget.merge_config(config, self.args)


if __name__ == "__main__":
    unittest.main()
