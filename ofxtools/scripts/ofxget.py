#!/usr/bin/env python
# coding: utf-8
"""
Configurable CLI front end for ``ofxtools.Client``
"""
# stdlib imports
import os
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
import warnings
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
from ofxtools import (utils, ofxhome, config, models)
from ofxtools.Client import (
    OFXClient, StmtRq, CcStmtRq, InvStmtRq,
    StmtEndRq, CcStmtEndRq,
)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools.header import OFXHeaderError
from ofxtools.Parser import OFXTree, ParseError


class OfxgetWarning(UserWarning):
    """ Base class for warnings in this module """


###############################################################################
# TYPE ALIASES
###############################################################################
# Loaded Argparser args
ArgType = typing.ChainMap[str, Any]

# OFX connection params (OFX version, prettyprint, unclosedelements) tagged
# onto the OFXClient.request_profile() job submitted to the ThreadPoolExecutor
# during a profile scan
OFXVersion = int
MarkupFormat = OrderedDict  # keys are "pretty", "unclosedelements"
ScanMetadata = Tuple[OFXVersion, MarkupFormat]

# All working FormatArgs for a given OFX version
FormatMap = Mapping[OFXVersion, List[MarkupFormat]]

# Scan result of a single OFX protocol version
ScanResult = Mapping[str, Union[list, dict]]

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
    argparser = argparse.ArgumentParser(
        description="Download OFX financial data",
        prog="ofxget",
    )
    argparser.add_argument(
        "request",
        choices=list(REQUEST_HANDLERS.keys()),
        help="Request type")
    argparser.add_argument(
        "server", nargs="?",
        help="OFX server - URL or FI name from ofxget.cfg/fi.cfg")
    argparser.add_argument("--url", help="OFX server URL")
    argparser.add_argument("--ofxhome", metavar="ID#",
                           help="FI id# on http://www.ofxhome.com/")
    argparser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        default=None,
        help="Display OFX request and exit without sending",
    )
    argparser.add_argument(
        "-w",
        "--write",
        action="store_true",
        default=None,
        help="Write working parameters to config file"
    )
    argparser.add_argument(
        "--savepass",
        action="store_true",
        default=None,
        help="Store password in system keyring (requires python-keyring)",
    )
    argparser.add_argument(
        "--unsafe",
        action="store_true",
        default=None,
        help="Disable SSL certificate verification",
    )

    format_group = argparser.add_argument_group(title="Format Options")
    format_group.add_argument("--version", help="OFX version")
    format_group.add_argument(
        "--unclosedelements",
        action="store_true",
        default=None,
        help="Omit end tags for elements (OFXv1 only)",
    )
    format_group.add_argument(
        "--pretty",
        action="store_true",
        default=None,
        help="Insert newlines and whitespace indentation",
    )

    signon_group = argparser.add_argument_group(title="Signon Options")
    signon_group.add_argument("-u", "--user", help="FI login username")
    signon_group.add_argument("--clientuid",
                              nargs=0,
                              action=UuidAction,
                              metavar="UUID4",
                              help="Override default CLIENTUID with random #")
    signon_group.add_argument("--org", help="FI.ORG")
    signon_group.add_argument("--fid", help="FI.FID")
    signon_group.add_argument("--appid", help="OFX client app identifier")
    signon_group.add_argument("--appver", help="OFX client app version")
    signon_group.add_argument("--language", help="OFX language")

    stmt_group = argparser.add_argument_group(title="Statement Options")
    stmt_group.add_argument("--bankid", help="ABA routing#")
    stmt_group.add_argument("--brokerid", help="Broker ID string")
    stmt_group.add_argument(
        "-C", "--checking", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-S", "--savings", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-M", "--moneymrkt", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-L", "--creditline", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-c", "--creditcard", "--cc", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-i", "--investment", metavar="#", action="append",
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-s", "--start", metavar="DATE", dest="dtstart",
        help="(YYYYmmdd) Transactions list start date"
    )
    stmt_group.add_argument(
        "-e", "--end", metavar="DATE", dest="dtend",
        help="(YYYYmmdd) Transactions list end date"
    )
    stmt_group.add_argument(
        "-a", "--asof", metavar="DATE", dest="dtasof",
        help="(YYYYmmdd) As-of date for balances and investment positions",
    )
    stmt_group.add_argument(
        "--no-transactions",
        dest="inctran",
        action="store_false",
        default=None,
        help="Omit transactions (config 'inctran: false')",
    )
    stmt_group.add_argument(
        "--no-balances",
        dest="incbal",
        action="store_false",
        default=None,
        help="Omit balances (config 'incbal: false')",
    )
    stmt_group.add_argument(
        "--no-positions",
        dest="incpos",
        action="store_false",
        default=None,
        help="Omit investment positions (config 'incpos: false')",
    )
    stmt_group.add_argument(
        "--open-orders",
        dest="incoo",
        action="store_true",
        default=None,
        help="Include open orders (config 'incoo: true')",
    )
    stmt_group.add_argument(
        "--all",
        dest="all",
        action="store_true",
        default=None,
        help="Request ACCTINFO; download statements for all",
    )

    tax_group = argparser.add_argument_group(title="Tax Form Options")
    tax_group.add_argument(
        "-y", "--year", metavar="YEAR", dest="years",
        type=int, action="append",
        help="(YYYY) Tax year (option can be repeated)",
    )
    tax_group.add_argument(
        "--acctnum",
        dest="acctnum",
        help="Account # of recipient, if different than tax ID",
    )
    tax_group.add_argument(
        "--recid",
        dest="recid",
        help="ID of recipient",
    )

    return argparser


###############################################################################
# CLI METHODS
###############################################################################
def scan_profile(args: ArgType) -> None:
    """
    Report working connection parameters
    """
    scan_results = _scan_profile(args["url"], args["org"], args["fid"])

    v1, v2, signoninfo = scan_results
    if (not v2["versions"]) and (not v1["versions"]):
        msg = "Scan found no working formats for {}"
        print(msg.format(args["url"]))
    else:
        print(json.dumps(scan_results))

        if args["write"] and not args["dryrun"]:
            extra_args = _best_scan_format(scan_results)
            #  args.maps.insert(0, extra_args)
            #  write_config(args)
            write_config(ChainMap(extra_args, dict(args)))


def _best_scan_format(scan_results: ScanResults) -> MutableMapping:
    """
    Given the results of _scan_profile(), choose the best parameters;
    return as dict (compatible with ArgParser/ ChainMap).

    "Best" here means highest working version with the minimal configuration
    delta, i.e. we prefer formats with "pretty"/"unclosedelements" given as
    False (the default) over True.
    """
    v1, v2, signoninfo = scan_results
    if v2["versions"]:
        result = v2
    elif v1["versions"]:
        result = v1
    else:
        return {}

    formats = sorted(result["formats"], key=lambda f: sum(f.values()))
    args = {k: v for k, v in formats[0].items() if v}

    args["version"] = result["versions"][-1]

    return args


def request_profile(args: ArgType) -> None:
    """
    Send PROFRQ
    """
    client = init_client(args)

    with client.request_profile(
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)


def request_acctinfo(args: ArgType) -> None:
    """
    Send ACCTINFORQ
    """

    if not args["user"]:
        raise ValueError("Please configure 'user'")

    password = get_passwd(args)
    acctinfo = _request_acctinfo(args, password)

    print(acctinfo.read().decode())
    acctinfo.seek(0)

    if args["write"] and not args["dryrun"]:
        _merge_acctinfo(args, acctinfo)

        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def _request_acctinfo(args: ArgType, password: str) -> BytesIO:
    client = init_client(args)
    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(password,
                                 dtacctup,
                                 dryrun=args["dryrun"],
                                 verify_ssl=not args["unsafe"]) as f:
        response = f.read()

    return BytesIO(response)


def _merge_acctinfo(args: ArgType, markup: BytesIO) -> None:
    # *ACCTINFO classes don't have rich comparison methods;
    # can't sort by class
    sortKey = attrgetter("__class__.__name__")
    acctinfos: List[AcctInfo] = sorted(extract_acctinfos(markup), key=sortKey)

    def parse_acctinfos(clsName, acctinfos):
        dispatcher = {"BANKACCTINFO": parse_bankacctinfos,
                      "CCACCTINFO": parse_ccacctinfos,
                      "INVACCTINFO": parse_invacctinfos}
        parser = dispatcher.get(clsName, lambda x: {})
        return parser(acctinfos)

    parsed_args: List[ParsedAcctinfo] = [parse_acctinfos(clsnm, infos)
                                         for clsnm, infos in itertools.groupby(
                                             acctinfos, key=sortKey)]

    # Insert extracted ACCTINFO after CLI commands, but before config files
    args.maps.insert(1, ChainMap(*parsed_args))


def request_stmt(args: ArgType) -> None:
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
            [StmtRq(acctid=acctid, accttype=accttype.upper(),
                    dtstart=dt["start"], dtend=dt["end"],
                    inctran=args["inctran"]) for acctid in args[accttype]])

    for acctid in args["creditcard"]:
        stmtrqs.append(
            CcStmtRq(acctid=acctid, dtstart=dt["start"], dtend=dt["end"],
                     inctran=args["inctran"]))

    for acctid in args["investment"]:
        stmtrqs.append(
            InvStmtRq(acctid=acctid, dtstart=dt["start"], dtend=dt["end"],
                      dtasof=dt["asof"], inctran=args["inctran"],
                      incoo=args["incoo"], incpos=args["incpos"],
                      incbal=args["incbal"]))

    client = init_client(args)
    with client.request_statements(
        password,
        *stmtrqs,
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def request_stmtend(args: ArgType) -> None:
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
            [StmtEndRq(acctid=acctid, accttype=accttype.upper(),
                       dtstart=dt["start"], dtend=dt["end"])
             for acctid in acctids])

    for acctid in args["creditcard"]:
        stmtendrqs.append(
            CcStmtEndRq(acctid=acctid, dtstart=dt["start"], dtend=dt["end"]))

    client = init_client(args)
    with client.request_statements(
        password,
        *stmtendrqs,
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())

    if args["write"] and not args["dryrun"]:
        write_config(args)

    if args["savepass"] and not args["dryrun"]:
        save_passwd(args, password)


def request_tax1099(args: ArgType) -> None:
    """
    Send TAX1099RQ
    """
    client = init_client(args)

    password = get_passwd(args)

    with client.request_tax1099(password,
                                *args["years"],
                                acctnum=args["acctnum"],
                                recid=args["recid"],
                                dryrun=args["dryrun"],
                                verify_ssl=not args["unsafe"]
                                ) as f:
        response = f.read()

    print(response.decode())


###############################################################################
# ARGUMENT/CONFIG HANDLERS
###############################################################################
CONFIGPATH = os.path.join(config.CONFIGDIR, "fi.cfg")
USERCONFIGPATH = os.path.join(config.USERCONFIGDIR, "ofxget.cfg")
UserConfig = configparser.ConfigParser()
UserConfig.read([CONFIGPATH, USERCONFIGPATH])


DEFAULTS: Dict[str, Union[str, int, bool, list]] = {
    "server": "", "url": "", "ofxhome": "", "version": 203, "org": "", "fid": "",
    "appid": "", "appver": "", "language": "", "bankid": "", "brokerid": "",
    "unclosedelements": False, "pretty": False, "user": "", "clientuid": "",
    "checking": [], "savings": [], "moneymrkt": [], "creditline": [],
    "creditcard": [], "investment": [], "dtstart": "", "dtend": "",
    "dtasof": "", "inctran": True, "incbal": True, "incpos": True,
    "incoo": False, "all": False, "years": [], "acctnum": "", "recid": "",
    "dryrun": False, "unsafe": False, "write": False, "savepass": False,
}


NULL_ARGS = [None, "", []]


def read_config(cfg, section):
    return {k: config2arg(k, v)
            for k, v in cfg[section].items()} if section in cfg else {}


def config2arg(key: str, value: str) -> Union[List[str], bool, int, str]:
    """
    Transform a config value from ConfigParser format to ArgParser format
    """
    def read_string(string: str) -> str:
        return string

    def read_int(string: str) -> int:
        return int(value)

    def read_bool(string: str) -> bool:
        BOOLY = configparser.ConfigParser.BOOLEAN_STATES  # type: ignore
        keys = list(BOOLY.keys())
        if string not in BOOLY:
            msg = f"Can't interpret '{list}' as bool; must be one of {keys}"
            raise ValueError(msg)
        return BOOLY[string]

    def read_list(string: str) -> List[str]:
        return [sub.strip() for sub in string.split(",")]

    handlers = {str: read_string,
                bool: read_bool,
                list: read_list,
                int: read_int}

    if key not in DEFAULTS:
        msg = f"Don't know type of {key}; define in ofxget.DEFAULTS"
        raise ValueError(msg)

    cfg_type = type(DEFAULTS[key])

    if cfg_type not in handlers:
        msg = f"Config key {key}: no handler defined for type '{cfg_type}'"
        raise ValueError(msg)

    return handlers[cfg_type](value)  # type: ignore


def write_config(args: ArgType) -> None:
    mk_server_cfg(args)

    #  msg = "\nWriting '{}' configs {} to {}..."
    #  print(msg.format(args["server"], dict(cfg.items()), USERCONFIGPATH))

    with open(USERCONFIGPATH, "w") as f:
        UserConfig.write(f)

    #  print("...write OK")


def mk_server_cfg(args: ArgType) -> configparser.SectionProxy:
    """
    Load user config from disk; apply key args to the section corresponding to
    the server nickname.
    """
    UserConfig.clear()
    UserConfig.read(USERCONFIGPATH)

    defaults = UserConfig[UserConfig.default_section]  # type: ignore
    if "clientuid" not in defaults:
        defaults["clientuid"] = OFXClient.uuid

    server = args.get("server", None)
    # args.server might actually be a URL from CLI, not a nickname
    if (not server) or server == args["url"]:
        msg = "Please provide a server nickname to write the config"
        raise ValueError(msg)

    if not UserConfig.has_section(server):
        UserConfig[server] = {}
    cfg = UserConfig[server]

    LibraryConfig = configparser.ConfigParser()
    LibraryConfig.read(CONFIGPATH)
    lib_cfg = read_config(LibraryConfig, server)

    for opt in ("url", "version", "ofxhome", "org", "fid", "brokerid",
                "bankid", "user", "checking", "savings", "moneymrkt",
                "creditline", "creditcard", "investment", "pretty",
                "unclosedelements"):
        if opt in args:
            value = args[opt]
            default_value = lib_cfg.get(opt, DEFAULTS[opt])
            if value != default_value and value not in NULL_ARGS:
                cfg[opt] = arg2config(opt, value)

    # Don't include CLIENTUID in the server section if it's sourced from
    # UserConfig.default_section
    if "clientuid" in args:
        value = args["clientuid"]
        if value not in NULL_ARGS and value != defaults["clientuid"]:
            cfg["clientuid"] = value

    return cfg


def arg2config(key: str, value: Union[list, bool, int, str]) -> str:
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
        # INI-friendly string representation of Python list type
        return str(value).strip("[]").replace("'", "")

    handlers = {str: write_string,
                bool: write_bool,
                list: write_list,
                int: write_int}

    if key not in DEFAULTS:
        msg = f"Don't know type of {key}; define in ofxget.DEFAULTS"
        raise ValueError(msg)

    cfg_type = type(DEFAULTS[key])

    return handlers[cfg_type](value)  # type: ignore


def merge_config(args: argparse.Namespace,
                 config: configparser.ConfigParser) -> ArgType:
    """
    Merge CLI args > user config > library config > OFX Home > defaults
    """
    # All ArgumentParser args that have a value set
    _args = {k: v for k, v in vars(args).items() if v is not None}

    if "server" in _args:
        user_cfg = read_config(config, _args["server"])
    else:
        user_cfg = {}
    merged = ChainMap(_args, user_cfg, DEFAULTS)

    ofxhome_id = merged["ofxhome"]
    if ofxhome_id:
        lookup = ofxhome.lookup(ofxhome_id)

        if lookup is not None:
            # Insert OFX Home lookup ahead of DEFAULTS but after
            # user configs and library configs
            merged.maps.insert(-1, {"url": lookup.url, "org": lookup.org,
                                    "fid": lookup.fid,
                                    "brokerid": lookup.brokerid})

    if not (merged.get("url", None)
            or merged.get("dryrun", False)
            or merged.get("request", None) == "list"):
        err = "Missing URL"

        if "server" not in _args:
            msg = (f"{err} - please provide a server nickname, "
                   "or configure 'url' / 'ofxhome'")
            raise ValueError(msg)

        server = _args["server"]
        # Allow sloppy CLI args - passing URL as "server" positional arg
        if urllib_parse.urlparse(server).scheme:
            merged["url"] = server
            merged["server"] = None
        else:
            msg = (f"{err} - please configure 'url' or 'ofxhome' "
                   f"for server '{server}'")
            raise ValueError(msg)

    return merged


def init_client(args: ArgType) -> OFXClient:
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
    return client


###############################################################################
# PROFILE SCAN
###############################################################################
def _scan_profile(url: str,
                  org: Optional[str],
                  fid: Optional[str],
                  max_workers: Optional[int] = None,
                  timeout: Optional[float] = None) -> ScanResults:
    """
    Report permutations of OFX version/prettyprint/unclosedelements that
    successfully download OFX profile from server.

    Returns a 3-tuple of (OFXv1 results, OFXv2 results, signoninfo), each
    type(dict).  OFX results provide ``ofxget`` configs that will work to
    make a basic OFX connection. SIGNONINFO reports further information
    that may be helpful to authenticate successfully.
    """
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
        success_params[version].append(format)

    v2, v1 = utils.partition(lambda it: it[0] < 200, success_params.items())
    v1_versions, v1_formats = collate_scan_results(v1)
    v2_versions, v2_formats = collate_scan_results(v2)

    # V2 always has closing tags for elements; just report prettyprint
    for format in v2_formats:
        assert not format["unclosedelements"]
        del format["unclosedelements"]

    v1_result: ScanResult = OrderedDict([("versions", v1_versions),
                                         ("formats", v1_formats)])
    v2_result: ScanResult = OrderedDict([("versions", v2_versions),
                                         ("formats", v2_formats)])
    return (v1_result, v2_result, signoninfo)


def _queue_scans(client: OFXClient,
                 max_workers: Optional[int],
                 timeout: Optional[float],
                 ) -> Dict[concurrent.futures.Future, ScanMetadata]:
    ofxv1 = [102, 103, 151, 160]
    ofxv2 = [200, 201, 202, 203, 210, 211, 220]

    BOOLS = (False, True)

    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers) as executor:
        for version, pretty, close in itertools.product(ofxv1, BOOLS, BOOLS):
            future = executor.submit(client.request_profile,
                                     version=version,
                                     prettyprint=pretty,
                                     close_elements=close,
                                     timeout=timeout)
            #  futures[future] = (version, pretty, True)
            futures[future] = (version,
                               OrderedDict([("pretty", pretty),
                                            ("unclosedelements", not close)]))

        for version, pretty in itertools.product(ofxv2, BOOLS):
            future = executor.submit(client.request_profile,
                                     version=version,
                                     prettyprint=pretty,
                                     close_elements=True,
                                     timeout=timeout)
            #  futures[future] = (version, pretty, True)
            futures[future] = (version,
                               OrderedDict([("pretty", pretty),
                                            ("unclosedelements", not close)]))

    return futures


def _read_scan_response(future: concurrent.futures.Future,
                        read_signoninfo: bool = False,
                        ) -> Tuple[bool, SignoninfoReport]:
    valid: bool = False
    signoninfo: SignoninfoReport = {}

    try:
        # ``future.result()`` returns an http.client.HTTPResponse
        response = future.result()
    except (URLError, HTTPError, ConnectionError, OSError, socket.timeout):
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

            signoninfos: List[models.SIGNONINFO] \
                = extract_signoninfos(BytesIO(response_))

            assert len(signoninfos) > 0
            valid = True
            info = signoninfos[0]
            bool_attrs = ("chgpinfirst",
                          "clientuidreq",
                          "authtokenfirst",
                          "mfachallengefirst")
            signoninfo = OrderedDict([
                (attr, getattr(info, attr, None) or False)
                for attr in bool_attrs])
        except (socket.timeout, ):
            # We didn't receive a response at all
            valid = False
        except (ParseError, ET.ParseError, OFXHeaderError):
            # We didn't receive valid OFX in the response
            valid = False
        except (ValueError, ):
            # We received OFX, but not a valid PROFRS
            valid = True
    else:
        # IF we're not parsing the PROFRS, then we interpret receiving a good
        # HTTP response as valid.
        valid = True

    return valid, signoninfo


def collate_scan_results(
    scan_results: Iterable[Tuple[OFXVersion, MarkupFormat]]
) -> Tuple[List[OFXVersion], List[MarkupFormat]]:
    """
    Input ``scan_results`` needs to be a complete set for either OFXv1 or v2,
    with no results for the other version admixed.
    """
    results_ = list(scan_results)
    if not results_:
        return [], []
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

    return sorted(versions), formats


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
        msg = (f"{cls}: Request failed, code={status.code}, "
               f"severity={status.severity}, message='{status.message}'")
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
    return list(itertools.chain.from_iterable(
        extract_signoninfo(trnrs) for trnrs in msgs))


def extract_acctinfos(
    markup: BytesIO
) -> Iterable[AcctInfo]:
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


def parse_bankacctinfos(
    acctinfos: Sequence[models.BANKACCTINFO]
) -> ParsedAcctinfo:
    bankids = []
    args_: MutableMapping = defaultdict(list)
    for inf in acctinfos:
        if _acctIsActive(inf):
            bankids.append(inf.bankid)
            args_[inf.accttype.lower()].append(inf.acctid)

    args_["bankid"] = utils.collapseToSingle(bankids, "BANKIDs")
    return dict(args_)


def parse_invacctinfos(
    acctinfos: Sequence[models.INVACCTINFO]
) -> ParsedAcctinfo:
    brokerids = []
    args_: MutableMapping = defaultdict(list)
    for inf in acctinfos:
        if _acctIsActive(inf):
            acctfrom = inf.invacctfrom
            brokerids.append(acctfrom.brokerid)
            args_["investment"].append(acctfrom.acctid)

    args_["brokerid"] = utils.collapseToSingle(brokerids, "BROKERIDs")
    return dict(args_)


def parse_ccacctinfos(
    acctinfos: Sequence[models.CCACCTINFO]
) -> ParsedAcctinfo:
    return {"creditcard": [i.acctid for i in acctinfos if _acctIsActive(i)]}


###############################################################################
# CLI UTILITIES
###############################################################################
def list_fis(args: ArgType) -> None:
    server = args["server"]
    if server in NULL_ARGS:
        entries = ["{:<40}{:<30}{:<8}".format(*srv) for srv in fi_index()]
        entries.insert(0, " ".join(("=" * 39, "=" * 29, "=" * 8)))
        entries.insert(0, "{:^40}{:^30}{:^8}".format("Name",
                                                     "Nickname",
                                                     "OFX Home"))
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
    servers = [(names.get(sct.get("ofxhome", None), ""),
                nick,
                sct.get("ofxhome", "--"))
               for nick, sct in UserConfig.items()
               if nick not in (cfg_default_sect, "NAMES")
               and "url" in sct]

    def sortkey(srv):
        key = srv[0].lower()
        if key.startswith("the "):
            key = key[4:]
        return key

    servers.sort(key=sortkey)
    return servers


def convert_datetime(args: ArgType) -> Mapping[str,
                                               Optional[datetime.datetime]]:
    """ Convert dtstart/dtend/dtasof to Python datetime type for request """
    D = DateTime().convert
    return {d[2:]: D(args[d] or None) for d in ("dtstart", "dtend", "dtasof")}


def get_passwd(args: ArgType) -> str:
    """
    1.  For dry run, use dummy password from OFX spec
    2.  If python-keyring is installed and --savepass is unset, try to use it
    3.  Prompt for password in terminal
    """
    if args["dryrun"]:
        password = "{:0<32}".format("anonymous")
    else:
        password = ""
        if HAS_KEYRING and not args["savepass"]:
            password = keyring.get_password("ofxtools", args["server"]) or ""
        if not password:
            password = getpass.getpass()
    return password


def save_passwd(args: ArgType, password: str) -> None:
    if args["dryrun"]:
        msg = "Dry run; won't store password"
        warnings.warn(msg, category=OfxgetWarning)
    if not HAS_KEYRING:
        msg = "You must install https://pypi.org/project/keyring"
        raise RuntimeError(msg)
    if not password:
        msg = "Empty password; won't store"
        warnings.warn(msg, category=OfxgetWarning)

    assert isinstance(password, str)
    keyring.set_password("ofxtools", args["server"], password)


# Map "request" arg to handler function
REQUEST_HANDLERS = {"list": list_fis,
                    "scan": scan_profile,
                    "prof": request_profile,
                    "acctinfo": request_acctinfo,
                    "stmt": request_stmt,
                    "stmtend": request_stmtend,
                    "tax1099": request_tax1099}


def main() -> None:
    argparser = make_argparser()
    args = merge_config(argparser.parse_args(), UserConfig)
    REQUEST_HANDLERS[args["request"]](args)


if __name__ == "__main__":
    main()
