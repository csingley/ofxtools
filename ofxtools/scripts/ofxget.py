#!/usr/bin/env python
# coding: utf-8
"""
Configurable CLI front end for ``ofxtools.Client``
"""
# stdlib imports
import os
import sys
from pathlib import Path
import argparse
import configparser
import datetime
from collections import defaultdict, OrderedDict, ChainMap
import getpass
from urllib import parse as urllib_parse
from urllib.error import HTTPError, URLError
import socket
import concurrent.futures
import json
import xml.etree.ElementTree as ET
from io import BytesIO
import itertools
from operator import attrgetter
import logging
import logging.config
import pydoc
import typing
from typing import (
    Union,
    Optional,
    Tuple,
    List,
    Any,
    Mapping,
    MutableMapping,
    Dict,
    Sequence,
    Iterable,
)

# 3rd party imports
try:
    # No library stub file for module 'keyring'
    import keyring  # type: ignore

    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


# local imports
from ofxtools import utils, ofxhome, config, models
from ofxtools.Client import (
    OFXClient,
    StmtRq,
    CcStmtRq,
    InvStmtRq,
    StmtEndRq,
    CcStmtEndRq,
)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools.header import OFXHeaderError
from ofxtools.Parser import OFXTree, ParseError


CONFIGPATH = config.CONFIGDIR / "fi.cfg"
USERCONFIGPATH = config.USERCONFIGDIR / "ofxget.cfg"
LOGCONFIGPATH = config.CONFIGDIR / "ofxget_log_cfg.json"
USERLOGCONFIGPATH = config.USERCONFIGDIR / "ofxget_log_cfg.json"


###############################################################################
# LOGGING
###############################################################################
def setup_logging(default_level=logging.INFO,):
    """
    Set up logging from user config file.
    Fall back to library default, and create user config file.
    """
    path = USERLOGCONFIGPATH
    value = os.getenv("OFXGET_LOG_CFG", None)
    if value:
        path = Path(value)
    if path.exists():
        with open(path, "r") as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        with open(LOGCONFIGPATH, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)
        with open(USERLOGCONFIGPATH, "w") as f:
            json.dump(config, f, indent=4)


setup_logging()
logger = logging.getLogger(__name__)


###############################################################################
# TYPE ALIASES
###############################################################################
# Parsed ArgParser arg
ArgType = Union[List[str], bool, int, str]

# Common data structure used for loading, combining, and converting between
# ArgParser and ConfigParser
ArgsType = typing.ChainMap[str, Any]

# OFX connection params (OFX version, prettyprint, unclosedelements) tagged
# onto the OFXClient.request_profile() job submitted to the ThreadPoolExecutor
# during a profile scan
OFXVersion = int
MarkupFormat = OrderedDict  # keys are "pretty", "unclosedelements"
ScanMetadata = Tuple[OFXVersion, MarkupFormat]

# All working FormatArgs for a given OFX version
FormatMap = Mapping[OFXVersion, List[MarkupFormat]]

# Scan result of a single OFX protocol version
ScanResult = Mapping[str, list]

# Auth information parsed out of SIGNONINFO during a profile scan -
# CLIENTUIDREQ et al.
SignoninfoReport = Mapping[str, bool]

# Full set of profile scan results
ScanResults = Tuple[ScanResult, ScanResult, SignoninfoReport]

AcctInfo = Union[models.BANKACCTINFO, models.CCACCTINFO, models.INVACCTINFO]
ParsedAcctinfo = Mapping[str, Union[str, list]]


###############################################################################
# DEFINE CLI
###############################################################################
class UuidAction(argparse.Action):
    """
    Generates a random UUID4 each time called
    """

    def __call__(self, parser, namespace, values, option_string=None):
        uuid = OFXClient.uuid
        setattr(namespace, self.dest, uuid)


def make_argparser() -> argparse.ArgumentParser:
    main_parser = argparse.ArgumentParser(
        description="Download OFX financial data", prog="ofxget"
    )
    subparsers_ = main_parser.add_subparsers(
        title="commands", description=None, help=None
    )
    subparsers = {}

    subparsers["list"] = add_subparser(
        subparsers_, "list", help="List known reachable OFX servers"
    )
    subparsers["scan"] = add_subparser(
        subparsers_,
        "scan",
        server=True,
        help=("Probe OFX server for working " "connection parameters"),
    )
    subparsers["prof"] = add_subparser(
        subparsers_,
        "prof",
        format=True,
        help=("Download OFX service profile " "for server"),
    )
    subparsers["acctinfo"] = add_subparser(
        subparsers_,
        "acctinfo",
        signon=True,
        help=("Download account information " "for a user login"),
    )
    subparsers["stmt"] = add_subparser(
        subparsers_,
        "stmt",
        stmt=True,
        help=("Download statement(s) for " "bank/CC/investment acct(s)"),
    )
    subparsers["stmtend"] = add_subparser(
        subparsers_,
        "stmtend",
        stmtend=True,
        help=("Download closing statement(s) " "for bank/CC account(s)"),
    )
    subparsers["tax1099"] = add_subparser(
        subparsers_,
        "tax1099",
        tax=True,
        help=("(EXPERIMENTAL) Download US " "income tax data on f1099"),
    )
    main_parser.subparsers = subparsers  # type: ignore
    return main_parser


def add_subparser(
    subparsers: argparse._SubParsersAction,
    cmd: str,
    server: bool = False,
    format: bool = False,
    signon: bool = False,
    stmtend: bool = False,
    stmt: bool = False,
    tax: bool = False,
    help: Optional[str] = None,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(cmd, help=help, description=help)
    parser.set_defaults(request=cmd)
    parser.add_argument("server", nargs="?", help="OFX server nickname")
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Give more output (option can be repeated)",
    )
    # Higher-level configs (e.g. account #s)
    # imply lower-level configs (e.g. username/passwd)
    if stmt:
        stmtend = True
    if stmtend or tax:
        signon = True
    if signon:
        format = True
    if format:
        server = True

    if server:
        parser.add_argument("--url", help="OFX server URL")
        parser.add_argument(
            "--ofxhome", metavar="ID#", help="FI id# on http://www.ofxhome.com/"
        )
        parser.add_argument(
            "-w",
            "--write",
            action="store_true",
            default=None,
            help="Write working parameters to config file",
        )
        parser.add_argument(
            "--unsafe",
            action="store_true",
            default=None,
            help="Skip SSL certificate verification",
        )

    if format:
        parser.add_argument(
            "-n",
            "--dryrun",
            action="store_true",
            default=None,
            help="Display OFX request and exit without sending",
        )
        add_format_group(parser)

    if signon:
        parser.add_argument(
            "--savepass",
            action="store_true",
            default=None,
            help="Store password in system keyring (requires python-keyring)",
        )
        add_signon_group(parser)

    if stmtend:
        add_bank_acct_group(parser)
        stmt_group = add_stmt_group(parser)
        if stmt:
            add_stmt_args(stmt_group)
            add_inv_acct_group(parser)
            add_inv_stmt_group(parser)

    if tax:
        add_tax_group(parser)

    return parser


def add_format_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="format options")
    group.add_argument("--version", help="OFX version")
    group.add_argument(
        "--unclosedelements",
        action="store_true",
        default=None,
        help="Omit end tags for elements (OFXv1 only)",
    )
    group.add_argument(
        "--pretty",
        action="store_true",
        default=None,
        help="Insert newlines and whitespace indentation",
    )

    return group


def add_signon_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="signon options")
    group.add_argument("-u", "--user", help="FI login username")
    group.add_argument(
        "--clientuid",
        nargs=0,
        action=UuidAction,
        metavar="UUID4",
        help="Override default CLIENTUID with random number",
    )
    group.add_argument("--org", help="FI.ORG")
    group.add_argument("--fid", help="FI.FID")
    group.add_argument("--appid", help="OFX client app identifier")
    group.add_argument("--appver", help="OFX client app version")
    group.add_argument("--language", help="OFX language")

    return group


def add_bank_acct_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="bank/CC account options")
    group.add_argument("--bankid", help="ABA routing#")
    group.add_argument(
        "-C",
        "--checking",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    group.add_argument(
        "-S",
        "--savings",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    group.add_argument(
        "-M",
        "--moneymrkt",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    group.add_argument(
        "-L",
        "--creditline",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    group.add_argument(
        "-c",
        "--creditcard",
        "--cc",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    group.add_argument(
        "--all",
        dest="all",
        action="store_true",
        default=None,
        help="Request ACCTINFO; download statements for all",
    )

    return group


def add_stmt_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(
        title="general statement options (both bank and investment)"
    )
    group.add_argument(
        "-s",
        "--start",
        metavar="DATE",
        dest="dtstart",
        help="(YYYYmmdd) Transactions list start date",
    )
    group.add_argument(
        "-e",
        "--end",
        metavar="DATE",
        dest="dtend",
        help="(YYYYmmdd) Transactions list end date",
    )
    return group


def add_stmt_args(group: argparse._ArgumentGroup) -> argparse._ArgumentGroup:
    group.add_argument(
        "-a",
        "--asof",
        metavar="DATE",
        dest="dtasof",
        help="(YYYYmmdd) As-of date for balances and investment positions",
    )
    group.add_argument(
        "--no-transactions",
        dest="inctran",
        action="store_false",
        default=None,
        help="Omit transactions (config 'inctran: false')",
    )
    group.add_argument(
        "--no-balances",
        dest="incbal",
        action="store_false",
        default=None,
        help="Omit balances (config 'incbal: false')",
    )

    return group


def add_inv_acct_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="investment account options")
    group.add_argument("--brokerid", help="Broker ID string")
    group.add_argument(
        "-i",
        "--investment",
        metavar="#",
        action="append",
        help="Account number (option can be repeated)",
    )
    return group


def add_inv_stmt_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="investment statement options")
    group.add_argument(
        "--no-positions",
        dest="incpos",
        action="store_false",
        default=None,
        help="Omit investment positions (config 'incpos: false')",
    )
    group.add_argument(
        "--open-orders",
        dest="incoo",
        action="store_true",
        default=None,
        help="Include open orders (config 'incoo: true')",
    )
    return group


def add_tax_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    group = parser.add_argument_group(title="tax form options")
    group.add_argument(
        "-y",
        "--year",
        metavar="YEAR",
        dest="years",
        type=int,
        action="append",
        help="(YYYY) Tax year (option can be repeated)",
    )
    group.add_argument(
        "--acctnum",
        dest="acctnum",
        help="Account # of recipient, if different than tax ID",
    )
    group.add_argument("--recid", dest="recid", help="ID of recipient")

    return group


###############################################################################
# CLI METHODS
###############################################################################
def scan_profile(args: ArgsType) -> None:
    """
    Report working connection parameters
    """
    url = args["url"]
    org = args["org"]
    fid = args["fid"]

    scan_results = _scan_profile(url, org, fid)

    v1, v2, signoninfo = scan_results
    if (not v2["versions"]) and (not v1["versions"]):
        msg = f"Scan found no working formats for {url}"
        print(msg)
    else:
        print(json.dumps(scan_results))

        if args["write"] and not args["dryrun"]:
            extra_args = _best_scan_format(scan_results)
            write_config(ChainMap(extra_args, dict(args)))


def _best_scan_format(scan_results: ScanResults) -> MutableMapping:
    """
    Given the results of _scan_profile(), choose the best parameters;
    return as dict (compatible with ArgParser/ ChainMap).

    "Best" here means highest working version with the minimal configuration
    delta, i.e. we prefer formats with "pretty"/"unclosedelements" given as
    False (the default) over True.
    """
    logger.info(f"Choosing best scan result from {scan_results}")
    v1, v2, signoninfo = scan_results
    if v2["versions"]:
        logger.debug("Found working OFX version 2")
        result = v2
    elif v1["versions"]:
        logger.debug("Found working OFX version 1")
        result = v1
    else:
        logger.info("Found no working OFX versions; returning")
        return {}

    formats = sorted(result["formats"], key=lambda f: sum(f.values()))
    logger.debug(f"Choose best format {formats[0]} from {formats}")
    args = {k: v for k, v in formats[0].items() if v}

    versions = result["versions"]
    args["version"] = versions[-1]
    logger.debug(f"Choose best version{versions[-1]} from {versions}")
    logger.info(f"Best scan result: {args}")
    return args


def request_profile(args: ArgsType) -> None:
    """
    Send PROFRQ
    """
    client = init_client(args)

    with client.request_profile(
        dryrun=args["dryrun"], verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)


def request_acctinfo(args: ArgsType) -> None:
    """
    Send ACCTINFORQ
    """

    if not args["user"]:
        msg = "'user' not configured"
        logger.error(msg)
        raise ValueError(msg)

    password = get_passwd(args)
    acctinfo = _request_acctinfo(args, password)

    print(acctinfo.read().decode())
    acctinfo.seek(0)

    if args["write"] and not args["dryrun"]:
        _merge_acctinfo(args, acctinfo)

        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def _request_acctinfo(args: ArgsType, password: str) -> BytesIO:
    client = init_client(args)
    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(
        password, dtacctup, dryrun=args["dryrun"], verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    return BytesIO(response)


def _merge_acctinfo(args: ArgsType, markup: BytesIO) -> None:
    # *ACCTINFO classes don't have rich comparison methods;
    # can't sort by class
    sortKey = attrgetter("__class__.__name__")
    acctinfos: List[AcctInfo] = sorted(extract_acctinfos(markup), key=sortKey)

    def parse_acctinfos(clsName, acctinfos):
        dispatcher = {
            "BANKACCTINFO": parse_bankacctinfos,
            "CCACCTINFO": parse_ccacctinfos,
            "INVACCTINFO": parse_invacctinfos,
        }
        parser = dispatcher.get(clsName, lambda x: {})
        return parser(acctinfos)

    parsed_args: List[ParsedAcctinfo] = [
        parse_acctinfos(clsnm, infos)
        for clsnm, infos in itertools.groupby(acctinfos, key=sortKey)
    ]

    # Insert extracted ACCTINFO after CLI commands, but before config files
    args.maps.insert(1, ChainMap(*parsed_args))


def request_stmt(args: ArgsType) -> None:
    """
    Send *STMTRQ
    """
    dt = convert_datetime(args)
    password = get_passwd(args)

    if args["all"]:
        acctinfo = _request_acctinfo(args, password)
        _merge_acctinfo(args, acctinfo)

    stmtrqs: List[Union[StmtRq, CcStmtRq, InvStmtRq]] = []
    for accttype in ("checking", "savings", "moneymrkt", "creditline"):
        stmtrqs.extend(
            [
                StmtRq(
                    acctid=acctid,
                    accttype=accttype.upper(),
                    dtstart=dt["start"],
                    dtend=dt["end"],
                    inctran=args["inctran"],
                )
                for acctid in args[accttype]
            ]
        )

    for acctid in args["creditcard"]:
        stmtrqs.append(
            CcStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                inctran=args["inctran"],
            )
        )

    for acctid in args["investment"]:
        stmtrqs.append(
            InvStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                dtasof=dt["asof"],
                inctran=args["inctran"],
                incoo=args["incoo"],
                incpos=args["incpos"],
                incbal=args["incbal"],
            )
        )

    if not stmtrqs:
        accttypes = [
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
        ]
        logger.warn(f"No accounts specified; configure at least one of {accttypes}")

    client = init_client(args)
    with client.request_statements(
        password, *stmtrqs, dryrun=args["dryrun"], verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def request_stmtend(args: ArgsType) -> None:
    """
    Send *STMTENDRQ
    """
    dt = convert_datetime(args)
    password = get_passwd(args)

    if args["all"]:
        acctinfo = _request_acctinfo(args, password)
        _merge_acctinfo(args, acctinfo)

    stmtendrqs: List[Union[StmtEndRq, CcStmtEndRq]] = []
    for accttype in ("checking", "savings", "moneymrkt", "creditline"):
        acctids = args[accttype]
        stmtendrqs.extend(
            [
                StmtEndRq(
                    acctid=acctid,
                    accttype=accttype.upper(),
                    dtstart=dt["start"],
                    dtend=dt["end"],
                )
                for acctid in acctids
            ]
        )

    for acctid in args["creditcard"]:
        stmtendrqs.append(
            CcStmtEndRq(acctid=acctid, dtstart=dt["start"], dtend=dt["end"])
        )

    if not stmtendrqs:
        accttypes = ["checking", "savings", "moneymrkt", "creditline", "creditcard"]
        logger.warn(f"No accounts specified; configure at least one of {accttypes}")

    client = init_client(args)
    with client.request_statements(
        password, *stmtendrqs, dryrun=args["dryrun"], verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def request_tax1099(args: ArgsType) -> None:
    """
    Send TAX1099RQ
    """
    client = init_client(args)

    password = get_passwd(args)

    with client.request_tax1099(
        password,
        *args["years"],
        acctnum=args["acctnum"],
        recid=args["recid"],
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"],
    ) as f:
        response = f.read()

    print(response.decode())


###############################################################################
# ARGUMENT/CONFIG HANDLERS
###############################################################################
def convert_list(string: str) -> List[str]:
    """
    Deserialize INI representation to a Python list
    """
    return [sub.strip() for sub in string.split(",")]


UserConfig = configparser.ConfigParser(converters={"list": convert_list})
UserConfig.read([CONFIGPATH, USERCONFIGPATH])


LibraryConfig = configparser.ConfigParser(converters={"list": convert_list})
LibraryConfig.read(CONFIGPATH)


DEFAULTS: Dict[str, ArgType] = {
    "verbose": 0,
    "server": "",
    "url": "",
    "ofxhome": "",
    "version": 203,
    "org": "",
    "fid": "",
    "appid": "",
    "appver": "",
    "language": "",
    "bankid": "",
    "brokerid": "",
    "unclosedelements": False,
    "pretty": False,
    "user": "",
    "clientuid": "",
    "checking": [],
    "savings": [],
    "moneymrkt": [],
    "creditline": [],
    "creditcard": [],
    "investment": [],
    "dtstart": "",
    "dtend": "",
    "dtasof": "",
    "inctran": True,
    "incbal": True,
    "incpos": True,
    "incoo": False,
    "all": False,
    "years": [],
    "acctnum": "",
    "recid": "",
    "dryrun": False,
    "unsafe": False,
    "write": False,
    "savepass": False,
}


configurable_srvr = (
    "url",
    "ofxhome",
    "version",
    "pretty",
    "unclosedelements",
    "org",
    "fid",
    "brokerid",
    "bankid",
    "appid",
    "appver",
    "language",
)
CONFIGURABLE_SRVR = OrderedDict(
    [(k, type(v)) for k, v in DEFAULTS.items() if k in configurable_srvr]
)


configurable_user = (
    "user",
    "clientuid",
    "checking",
    "savings",
    "moneymrkt",
    "creditline",
    "creditcard",
    "investment",
)
CONFIGURABLE_USER = OrderedDict(
    [(k, type(v)) for k, v in DEFAULTS.items() if k in configurable_user]
)


CONFIGURABLE = CONFIGURABLE_SRVR
CONFIGURABLE.update(CONFIGURABLE_USER)


NULL_ARGS = [None, "", []]


def read_config(cfg: configparser.ConfigParser, section: str) -> Mapping[str, ArgType]:
    logger.info(f"Loading Python data structures from {cfg}")
    args: Mapping = {}
    if section not in cfg:
        return args

    proxy = cfg[section]
    handlers = {
        bool: proxy.getboolean,
        int: proxy.getint,
        list: proxy.getlist,
        str: proxy.get,
        None: lambda x: None,
    }

    args = {
        opt: handlers[CONFIGURABLE.get(opt, None)](opt)  # type: ignore
        for opt in proxy
        if opt in CONFIGURABLE
    }

    return args


def write_config(args: ArgsType) -> None:
    mk_server_cfg(args)

    logger.info(f"Writing user configs to {USERCONFIGPATH}")

    with open(USERCONFIGPATH, "w") as f:
        UserConfig.write(f)


def mk_server_cfg(args: ArgsType) -> configparser.SectionProxy:
    """
    Load user config from disk; apply key args to the section corresponding to
    the server nickname.
    """
    logger.info("Creating user config")
    logger.debug(f"Args to populate config: {args}")

    logger.debug(f"Reloading user config from {USERCONFIGPATH}")
    UserConfig.clear()
    UserConfig.read(USERCONFIGPATH)

    defaults = UserConfig[UserConfig.default_section]  # type: ignore
    if "clientuid" not in defaults:
        clientuid = OFXClient.uuid
        logger.debug(f"No global default CLIENTUID found; choosing {clientuid}")
        defaults["clientuid"] = clientuid

    server = args.get("server", None)
    # args.server might actually be a URL from CLI, not a nickname
    if (not server) or server == args["url"]:
        msg = "No server nickname provided; can't create config"
        logger.error(msg)
        raise ValueError(msg)
    logger.debug(f"Configuring {server}")

    if not UserConfig.has_section(server):
        UserConfig[server] = {}
    cfg = UserConfig[server]
    logger.debug(f"Existing user config section: {dict(cfg)}")

    lib_cfg = read_config(LibraryConfig, server)

    def test_cfg_val(opt: str, value: ArgType) -> bool:
        """ Select CLI args to write to config file """
        if value in NULL_ARGS:
            return False
        # Don't include CLIENTUID in the server section if it's sourced
        # from UserConfig.default_section
        if opt == "clientuid" and value == defaults["clientuid"]:
            return False
        # Don't include configs that are the same as defaults
        elif value == lib_cfg.get(opt, DEFAULTS[opt]):
            return False

        return True

    for opt, opt_type in CONFIGURABLE.items():
        if opt in args:
            value = args[opt]
            if test_cfg_val(opt, value):
                cfg[opt] = arg2config(opt, opt_type, value)

    return cfg


def arg2config(key: str, cfg_type: type, value: ArgType) -> str:
    """
    Transform a config value from ArgParser format to ConfigParser format
    """

    def write_string(value: str) -> str:
        return value

    def write_int(value: int) -> str:
        return str(value)

    def write_bool(value: bool) -> str:
        return {True: "true", False: "false"}[value]

    def write_list(value: list) -> str:
        # Serialized string representation of Python list type
        return str(value).strip("[]").replace("'", "")

    handlers = {str: write_string, bool: write_bool, list: write_list, int: write_int}

    if cfg_type not in handlers:
        msg = f"Don't know how to write config for {key} type={cfg_type}"
        logger.error(msg)
        raise ValueError(msg)

    return handlers[cfg_type](value)  # type: ignore


def merge_config(
    args: argparse.Namespace, config: configparser.ConfigParser
) -> ArgsType:
    """
    Merge CLI args > user config > OFX Home > defaults
    """
    logger.info("Merging CLI args with config files")
    # All ArgumentParser args that have a value set
    _args = {k: v for k, v in vars(args).items() if v is not None}
    logger.debug(f"Non-empty CLI args; {_args}")

    if "server" in _args:
        user_cfg = read_config(config, _args["server"])
    else:
        user_cfg = {}
    logger.debug(f"Existing user configs: {user_cfg}")
    merged: ArgsType = ChainMap(_args, user_cfg, DEFAULTS)
    logger.debug(f"CLI args merged with user configs and defaults: {merged}")

    # Try to perform an OFX Home lookup if:
    # - it's configured from the CLI
    # - it's configured in ofxget.cfg
    # - we don't have a URL
    if "ofxhome" in _args or "ofxhome" in user_cfg or (not merged["url"]):
        merge_from_ofxhome(merged)

    if not (
        merged.get("url", None)
        or merged.get("dryrun", False)
        or merged.get("request", None) == "list"
    ):
        err = "Missing URL"

        if "server" not in _args:
            logger.error(err)
            msg = (
                f"{err} - please provide a server nickname, "
                "or configure 'url' / 'ofxhome'\n"
            )
            print(msg)
            command = merged["request"]
            make_argparser().subparsers[command].print_help()  # type: ignore
            sys.exit()

        server = _args["server"]
        # Allow sloppy CLI args - passing URL as "server" positional arg
        if urllib_parse.urlparse(server).scheme:
            merged["url"] = server
            merged["server"] = None
        else:
            logger.error(err)
            msg = f"{err} - please configure 'url' or 'ofxhome' for server '{server}'"
            raise ValueError(msg)

    logger.info(f"Merged args: {merged}")
    return merged


def merge_from_ofxhome(args: ArgsType):
    ofxhome_id = args["ofxhome"]
    logger.info(f"Looking up OFX Home API for id#{ofxhome_id}")
    if ofxhome_id:
        lookup = ofxhome.lookup(ofxhome_id)
        if lookup:
            logger.info(f"OFX Home lookup found {lookup}")
            # Insert OFX Home lookup ahead of DEFAULTS but after
            # CLI args and user configss
            args.maps.insert(
                -1,
                {
                    "url": lookup.url,
                    "org": lookup.org,
                    "fid": lookup.fid,
                    "brokerid": lookup.brokerid,
                },
            )
            msg = "CLI args merged with user configs, OFX Home lookup, and defaults: {merged}"
            logger.debug(msg)


def init_client(args: ArgsType) -> OFXClient:
    """
    Initialize OFXClient with connection info from args
    """
    client = OFXClient(
        args["url"],
        userid=args["user"] or None,
        clientuid=args["clientuid"] or None,
        org=args["org"] or None,
        fid=args["fid"] or None,
        version=args["version"],
        appid=args["appid"] or None,
        appver=args["appver"] or None,
        language=args["language"] or None,
        prettyprint=args["pretty"],
        close_elements=not args["unclosedelements"],
        bankid=args["bankid"] or None,
        brokerid=args["brokerid"] or None,
    )
    logger.debug(f"Initialized {client}")
    return client


###############################################################################
# PROFILE SCAN
###############################################################################
def _scan_profile(
    url: str,
    org: Optional[str],
    fid: Optional[str],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
) -> ScanResults:
    """
    Report permutations of OFX version/prettyprint/unclosedelements that
    successfully download OFX profile from server.

    Returns a 3-tuple of (OFXv1 results, OFXv2 results, signoninfo), each
    type(dict).  OFX results provide ``ofxget`` configs that will work to
    make a basic OFX connection. SIGNONINFO reports further information
    that may be helpful to authenticate successfully.
    """
    logger.info(
        (
            f"Scanning url={url} org={org} fid={fid} "
            "max_workers={max_workers} timeout={timeout}"
        )
    )
    client = OFXClient(url, org=org, fid=fid)
    futures = _queue_scans(client, max_workers, timeout)

    # The primary data we keep is actually the metadata (i.e. connection
    # parameters - OFX version; prettyprint; unclosedelements) tagged on
    # the Future by _queue_scans() that gave us a successful OFX connection.
    success_params: FormatMap = defaultdict(list)
    # If possible, we also parse out some data from SIGNONINFO included in
    # the PROFRS.
    signoninfo: SignoninfoReport = {}

    # Assume that SIGNONINFO is the same for each successful OFX PROFRS.
    # Tell _read_scan_response() to stop parsing out SIGNONINFO once
    # it's successfully extracted one.
    for future in concurrent.futures.as_completed(futures):
        version, format = futures[future]
        valid, signoninfo_ = _read_scan_response(future, not signoninfo)

        if not valid:
            continue
        if not signoninfo and signoninfo_:
            signoninfo = signoninfo_

        logger.debug(
            (f"OFX connection success, version={version}, " f"format={format}")
        )
        success_params[version].append(format)

    v1_result, v2_result = [
        collate_scan_results(ver)
        for ver in utils.partition(lambda it: it[0] >= 200, success_params.items())
    ]

    # V2 always has closing tags for elements; just report prettyprint
    for fmt in v2_result["formats"]:
        assert not fmt["unclosedelements"]
        del fmt["unclosedelements"]

    results = (v1_result, v2_result, signoninfo)
    logger.info(f"Scan results: {results}")
    return results


def _queue_scans(
    client: OFXClient, max_workers: Optional[int], timeout: Optional[float]
) -> Dict[concurrent.futures.Future, ScanMetadata]:
    ofxv1 = [102, 103, 151, 160]
    ofxv2 = [200, 201, 202, 203, 210, 211, 220]

    BOOLS = (False, True)

    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
        for version, pretty, close in itertools.product(ofxv1, BOOLS, BOOLS):
            future = executor.submit(
                client.request_profile,
                version=version,
                prettyprint=pretty,
                close_elements=close,
                timeout=timeout,
            )
            #  futures[future] = (version, pretty, True)
            futures[future] = (
                version,
                OrderedDict([("pretty", pretty), ("unclosedelements", not close)]),
            )

        for version, pretty in itertools.product(ofxv2, BOOLS):
            future = executor.submit(
                client.request_profile,
                version=version,
                prettyprint=pretty,
                close_elements=True,
                timeout=timeout,
            )
            #  futures[future] = (version, pretty, True)
            futures[future] = (
                version,
                OrderedDict([("pretty", pretty), ("unclosedelements", not close)]),
            )

    return futures


def _read_scan_response(
    future: concurrent.futures.Future, read_signoninfo: bool = False
) -> Tuple[bool, SignoninfoReport]:
    valid: bool = False
    signoninfo: SignoninfoReport = {}

    try:
        # ``future.result()`` returns an http.client.HTTPResponse
        response = future.result()
    except (URLError, HTTPError, ConnectionError, OSError, socket.timeout) as exc:
        logger.debug(f"Didn't receive HTTP response: {exc}")
        future.cancel()
        return valid, signoninfo

    # ``response`` is an HTTPResponse; doesn't have seek() method used
    # by ``header.parse_header()``.  Repackage as BytesIO for parsing.
    if read_signoninfo:
        with response as f:
            response_ = f.read()
        try:
            if not response_:
                return valid, signoninfo

            signoninfos: List[models.SIGNONINFO] = extract_signoninfos(
                BytesIO(response_)
            )

            assert len(signoninfos) > 0
            valid = True
            info = signoninfos[0]
            bool_attrs = (
                "chgpinfirst",
                "clientuidreq",
                "authtokenfirst",
                "mfachallengefirst",
            )
            signoninfo = OrderedDict(
                [(attr, getattr(info, attr, None) or False) for attr in bool_attrs]
            )
            logger.debug(
                ("Received HTTP response with valid OFX; " f"signoninfo={signoninfo}")
            )
        except (socket.timeout,):
            # We didn't receive a response at all
            logger.debug("Didn't receive HTTP response: socket timeout")
            valid = False
        except (ParseError, ET.ParseError, OFXHeaderError):
            # We didn't receive valid OFX in the response
            logger.debug("Received HTTP response that didn't contain valid OFX")
            valid = False
        except (ValueError,):
            # We received OFX; can't find SIGNONIFO (probably no PROFRS)
            logger.debug(
                ("Received HTTP response with valid OFX; " "can't parse SIGNONINFO")
            )
            valid = True
    else:
        # IF we're not parsing the PROFRS, then we interpret receiving a good
        # HTTP response as valid.
        logger.debug("Received HTTP response; not parsing SIGNONINFO")
        valid = True

    logger.info(f"valid: {valid}, signoninfo: {signoninfo}")
    return valid, signoninfo


def collate_scan_results(
    scan_results: Iterable[Tuple[OFXVersion, MarkupFormat]]
) -> ScanResult:
    """
    Input ``scan_results`` needs to be a complete set for either OFXv1 or v2,
    with no results for the other version admixed.
    """
    results_ = list(scan_results)
    if not results_:
        return OrderedDict()
    versions, formats = zip(*results_)

    # Assumption: the same markup formatting requirements apply to all
    # versions (e.g. 1.0.2 and 1.0.3, or 2.0.3 and 2.2.0).
    # If markup format succeeds on some versions but fails on others,
    # we'll chalk it up to network transmission errors.
    #
    # Translation: just pick the longest sequence of successful
    # formats and assume it applies for all versions.
    formats = max(formats, key=len)
    formats.sort(key=lambda f: (f["pretty"], f["unclosedelements"]))
    return OrderedDict(zip(("versions", "formats"), (sorted(versions), formats)))


###############################################################################
# OFX PARSING
###############################################################################
def verify_status(trnrs: models.Aggregate) -> None:
    """
    Input a models.Aggregate instance representing a transaction wrapper.
    """
    status = trnrs.status
    if status.code != 0:
        cls = trnrs.__class__.__name__
        msg = (
            f"{cls}: Request failed, code={status.code}, "
            f"severity={status.severity}, message='{status.message}'"
        )
        logger.error(msg)
        raise ValueError(msg)


def _acctIsActive(acctinfo: AcctInfo) -> bool:
    return acctinfo.svcstatus == "ACTIVE"


def extract_signoninfos(markup: BytesIO) -> List[models.SIGNONINFO]:
    """
    Input seralized OFX containing PROFRS
    Output list of ofxtools.models.SIGNONINFO instances
    """
    parser = OFXTree()
    parser.parse(markup)
    ofx = parser.convert()

    sonrs = ofx.signonmsgsrsv1.sonrs
    assert isinstance(sonrs, models.SONRS)
    verify_status(sonrs)

    msgs = ofx.profmsgsrsv1
    assert msgs is not None

    def extract_signoninfo(trnrs: models.PROFTRNRS) -> List[models.SIGNONINFO]:
        verify_status(trnrs)
        rs = trnrs.profrs
        assert rs is not None

        list_ = rs.signoninfolist
        assert list_ is not None
        return list_[:]

    #  return list(itertools.chain.from_iterable(
    #  [extract_signoninfo(trnrs) for trnrs in msgs]))
    return list(
        itertools.chain.from_iterable(extract_signoninfo(trnrs) for trnrs in msgs)
    )


def extract_acctinfos(markup: BytesIO) -> Iterable[AcctInfo]:
    """
    Input seralized OFX containing ACCTINFORS
    Output dict-like object containing parsed *ACCTINFOs
    """
    parser = OFXTree()
    parser.parse(markup)
    ofx = parser.convert()

    sonrs = ofx.signonmsgsrsv1.sonrs
    assert isinstance(sonrs, models.SONRS)
    verify_status(sonrs)

    msgs = ofx.signupmsgsrsv1
    assert msgs is not None and len(msgs) == 1
    trnrs = msgs[0]
    assert isinstance(trnrs, models.ACCTINFOTRNRS)
    verify_status(trnrs)

    acctinfors = trnrs.acctinfors
    assert isinstance(acctinfors, models.ACCTINFORS)

    # ACCTINFOs are ListItems of ACCTINFORS
    # *ACCTINFOs are ListItems of ACCTINFO
    # The data we want is in a nested list
    return itertools.chain.from_iterable(acctinfors)


def parse_bankacctinfos(acctinfos: Sequence[models.BANKACCTINFO]) -> ParsedAcctinfo:
    bankids = []
    args_: MutableMapping = defaultdict(list)
    for inf in acctinfos:
        if _acctIsActive(inf):
            bankids.append(inf.bankid)
            args_[inf.accttype.lower()].append(inf.acctid)

    args_["bankid"] = utils.collapseToSingle(bankids, "BANKIDs")
    return dict(args_)


def parse_invacctinfos(acctinfos: Sequence[models.INVACCTINFO]) -> ParsedAcctinfo:
    brokerids = []
    args_: MutableMapping = defaultdict(list)
    for inf in acctinfos:
        if _acctIsActive(inf):
            acctfrom = inf.invacctfrom
            brokerids.append(acctfrom.brokerid)
            args_["investment"].append(acctfrom.acctid)

    args_["brokerid"] = utils.collapseToSingle(brokerids, "BROKERIDs")
    return dict(args_)


def parse_ccacctinfos(acctinfos: Sequence[models.CCACCTINFO]) -> ParsedAcctinfo:
    return {"creditcard": [i.acctid for i in acctinfos if _acctIsActive(i)]}


###############################################################################
# CLI UTILITIES
###############################################################################
def list_fis(args: ArgsType) -> None:
    server = args["server"]
    if server in NULL_ARGS:
        entries = ["{:<40}{:<30}{:<8}".format(*srv) for srv in fi_index()]
        entries.insert(0, " ".join(("=" * 39, "=" * 29, "=" * 8)))
        entries.insert(0, "{:^40}{:^30}{:^8}".format("Name", "Nickname", "OFX Home"))
        pydoc.pager("\n".join(entries))
    elif server not in UserConfig:
        msg = f"Unknown server '{server}'"
        raise ValueError(msg)
    else:
        ofxhome = UserConfig[server].get("ofxhome", "")
        name = UserConfig["NAMES"].get(ofxhome, "")
        config = [" = ".join(pair) for pair in UserConfig[server].items()]
        print()
        if name:
            print(name)
        print("\n".join(config))
        print()


def fi_index() -> Sequence[Tuple[str, str, str]]:
    """ All FIs known to ofxget """
    names = {id_: name for id_, name in UserConfig["NAMES"].items()}
    cfg_default_sect = UserConfig.default_section  # type: ignore
    servers = [
        (names.get(sct.get("ofxhome", None), ""), nick, sct.get("ofxhome", "--"))
        for nick, sct in UserConfig.items()
        if nick not in (cfg_default_sect, "NAMES") and "url" in sct
    ]

    def sortkey(srv):
        key = srv[0].lower()
        if key.startswith("the "):
            key = key[4:]
        return key

    servers.sort(key=sortkey)
    return servers


def convert_datetime(args: ArgsType) -> Mapping[str, Optional[datetime.datetime]]:
    """ Convert dtstart/dtend/dtasof to Python datetime type for request """
    D = DateTime().convert
    return {d[2:]: D(args[d] or None) for d in ("dtstart", "dtend", "dtasof")}


def get_passwd(args: ArgsType) -> str:
    """
    1.  For dry run, use dummy password from OFX spec
    2.  If python-keyring is installed and --savepass is unset, try to use it
    3.  Prompt for password in terminal
    """
    if args["dryrun"]:
        logger.debug("Dry run; using dummy password")
        password = "{:0<32}".format("anonymous")
    else:
        password = ""
        if HAS_KEYRING and not args["savepass"]:
            server = args["server"]
            logger.debug("Found python-keyring; loading password for {server}")
            password = keyring.get_password("ofxtools", server) or ""
        if not password:
            password = getpass.getpass()
    return password


def save_passwd(args: ArgsType, password: str) -> None:
    if args["dryrun"]:
        msg = "Dry run; won't store password"
        logger.warn(msg)
    if not HAS_KEYRING:
        msg = "Can't find python-keyring pacakge; can't save password"
        logger.error(msg)
        raise RuntimeError(msg)
    if not password:
        msg = "Empty password; won't store"
        logger.warn(msg)

    server = args["server"]
    logger.debug("Found python-keyring; storing password for {server}")
    keyring.set_password("ofxtools", server, password)


LOG_LEVELS = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}


# Map "request" arg to handler function
REQUEST_HANDLERS = {
    "list": list_fis,
    "scan": scan_profile,
    "prof": request_profile,
    "acctinfo": request_acctinfo,
    "stmt": request_stmt,
    "stmtend": request_stmtend,
    "tax1099": request_tax1099,
}


def main() -> None:
    argparser = make_argparser()
    args_ = argparser.parse_args()

    log_level = LOG_LEVELS.get(args_.verbose, logging.DEBUG)
    logger.setLevel(log_level)
    logger.debug(f"Parsed CLI args: {args_}")

    if not hasattr(args_, "request"):
        argparser.print_help()
        sys.exit()

    args = merge_config(args_, UserConfig)
    REQUEST_HANDLERS[args["request"]](args)


if __name__ == "__main__":
    main()
