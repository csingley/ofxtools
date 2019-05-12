#!/usr/bin/env python
# coding: utf-8
"""
Configurable CLI front end for ``ofxtools.Client``
"""
# stdlib imports
import os
import argparse
from argparse import ArgumentParser, Action
import configparser
from configparser import ConfigParser
import datetime
from collections import defaultdict, OrderedDict, ChainMap
import getpass
from urllib import parse as urllib_parse
from urllib.error import HTTPError, URLError
import concurrent.futures
import json
from io import BytesIO
import itertools
from operator import attrgetter
import sys
import warnings
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
)

# 3rd party imports
try:
    # No library stub file for module 'keyring'
    import keyring  # type: ignore
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

# local imports
from ofxtools.Client import (
    OFXClient, StmtRq, CcStmtRq, InvStmtRq,
    StmtEndRq, CcStmtEndRq,
)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools import (utils, ofxhome, config, models)
from ofxtools.Parser import OFXTree


CONFIGPATH = os.path.join(config.CONFIGDIR, "fi.cfg")
USERCONFIGPATH = os.path.join(config.USERCONFIGDIR, "ofxget.cfg")
UserConfig = ConfigParser()
UserConfig.read([CONFIGPATH, USERCONFIGPATH])


DEFAULTS = {"url": "", "org": "", "fid": "", "version": 203,
            "appid": "", "appver": "", "bankid": "", "brokerid": "",
            "user": "", "clientuid": "", "language": "", "dryrun": False,
            "unsafe": False, "unclosedelements": False, "pretty": False,
            "checking": [], "savings": [], "moneymrkt": [], "creditline": [],
            "creditcard": [], "investment": [], "dtstart": "", "dtend": "",
            "dtasof": "", "inctran": True, "incbal": True, "incpos": True,
            "incoo": False, "all": False, "years": [], "acctnum": "",
            "recid": "", "ofxhome": "", "write": False, "savepass": False}


class OfxgetWarning(UserWarning):
    """ Base class for warnings in this module """


ArgType = typing.ChainMap[str, Any]  # Type alias for loaded Argparser args
ScanResult = Mapping[str, Union[list, dict]]  # Type alias for scan result


class UuidAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        uuid = OFXClient.uuid
        setattr(namespace, self.dest, uuid)


def make_argparser() -> ArgumentParser:
    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index()),
        prog="ofxget",
    )
    argparser.add_argument(
        "request",
        choices=list(REQUEST_HANDLERS.keys()),
        help="Request type")
    argparser.add_argument(
        "server", help="OFX server - URL or FI name from ofxget.cfg/fi.cfg")
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

    scan_group = argparser.add_argument_group(title="Profile Scan Options")
    scan_group.add_argument("--ofxhome",
                            help="FI id# on http://www.ofxhome.com/")

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
        help="(YYYYmmdd) As-of date for investment positions",
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
def scan_profiles(start: int,
                  stop: int,
                  timeout: Optional[float] = None
                  ) -> Dict[str,
                            Tuple[ScanResult, ScanResult, Mapping[str, bool]]]:
    """
    Scan OFX Home's list of FIs for working connection configs.
    """
    results = {}

    institutions = ofxhome.list_institutions()
    for ofxhome_id in list(institutions.keys())[start:stop]:
        lookup = ofxhome.lookup(ofxhome_id)
        if lookup is None\
           or ofxhome.ofx_invalid(lookup)\
           or ofxhome.ssl_invalid(lookup):
            continue
        working = _scan_profile(url=lookup.url,
                                org=lookup.org,
                                fid=lookup.fid,
                                timeout=timeout)
        if working:
            results[ofxhome_id] = working

    return results


def scan_profile(args: ArgType) -> None:
    """
    Report working connection parameters
    """
    scan_results = _scan_profile(args["url"], args["org"], args["fid"])

    v1, v2, signoninfo = scan_results
    if (not v2["versions"]) and (not v1["versions"]):
        msg = "Scan found no working formats for {}"
        print(msg.format(args["url"]))
        sys.exit()

    print(json.dumps(scan_results))

    if args["write"] and not args["dryrun"]:
        extra_args = _best_scan_format(scan_results)
        args.maps.insert(0, extra_args)

        write_config(args)


def _best_scan_format(scan_results: Tuple[ScanResult,
                                          ScanResult,
                                          Mapping[str, bool],
                                          ]) -> MutableMapping:
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


def request_acctinfo(args: ArgType) -> None:
    """
    Send ACCTINFORQ
    """

    if not args["user"]:
        msg = "Please configure 'user'"
        raise ValueError(msg.format(msg))

    password = get_passwd(args)
    acctinfo = _request_acctinfo(args, password)

    print(acctinfo.read().decode())

    if args["write"] and not args["dryrun"]:
        acctinfo.seek(0)
        extra_args = dict(extract_acctinfos(acctinfo))
        extra_args = {k: arg2config(k, v) for k, v in extra_args.items()}
        args.maps.insert(0, extra_args)

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


def request_stmt(args: ArgType) -> None:
    """
    Send *STMTRQ
    """
    dt = convert_datetime(args)
    password = get_passwd(args)

    if args["all"]:
        acctinfo = _request_acctinfo(args, password)
        args_ = extract_acctinfos(acctinfo)
        args.maps.insert(1, args_)

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
        args_ = extract_acctinfos(acctinfo)
        args.maps.insert(1, args_)

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


def read_config(cfg, section):
    return {k: config2arg(k, v)
            for k, v in cfg[section].items()} if section in cfg else {}


def merge_config(args: argparse.Namespace,
                 config: configparser.ConfigParser) -> ArgType:
    """
    Merge CLI args > user config > library config > OFX Home > defaults
    """
    # All ArgumentParser args that have a value set
    _args = {k: v for k, v in vars(args).items() if v is not None}

    server = _args["server"]
    user_cfg = read_config(config, server)
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

    if not merged["url"]:
        msg = "Unknown server '{}'; please configure 'url' or 'ofxhome'"
        raise ValueError(msg.format(server))

    return merged


def config2arg(key: str, value: str) -> Union[List[str], bool, int, str]:
    """
    Transform a config value from ConfigParser format to ArgParser format
    """
    def read_string(string: str) -> str:
        return string

    def read_int(string: str) -> int:
        return int(value)

    def read_bool(string: str) -> bool:
        BOOLY = ConfigParser.BOOLEAN_STATES  # type: ignore
        if string not in BOOLY:
            msg = "Can't interpret '{}' as bool; must be one of {}"
            raise ValueError(msg.format(string, list(BOOLY.keys())))
        return BOOLY[string]

    def read_list(string: str) -> List[str]:
        return [sub.strip() for sub in string.split(",")]

    handlers = {str: read_string,
                bool: read_bool,
                list: read_list,
                int: read_int}

    if key not in DEFAULTS:
        msg = "Don't know type of {}; define in ofxget.DEFAULTS"
        raise ValueError(msg.format(key))

    cfg_type = type(DEFAULTS[key])

    if cfg_type not in handlers:
        msg = "Config key {}: no handler defined for type '{}'"
        raise ValueError(msg.format(key, cfg_type))

    return handlers[cfg_type](value)  # type: ignore


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
        msg = "Don't know type of {}; define in ofxget.DEFAULTS"
        raise ValueError(msg.format(key))

    cfg_type = type(DEFAULTS[key])

    return handlers[cfg_type](value)  # type: ignore


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

    LibraryConfig = ConfigParser()
    LibraryConfig.read(CONFIGPATH)
    lib_cfg = read_config(LibraryConfig, server)

    for opt in ("url", "version", "ofxhome", "org", "fid", "brokerid",
                "bankid", "user", "checking", "savings", "moneymrkt",
                "creditline", "creditcard", "investment", "pretty",
                "unclosedelements"):
        if opt in args:
            value = args[opt]
            default_value = lib_cfg.get(opt, DEFAULTS[opt])
            if value != default_value:
                cfg[opt] = arg2config(opt, args[opt])

    if "clientuid" in args:
        cfg["clientuid"] = args["clientuid"]

    return cfg


def write_config(args: ArgType) -> None:
    mk_server_cfg(args)

    #  msg = "\nWriting '{}' configs {} to {}..."
    #  print(msg.format(args["server"], dict(cfg.items()), USERCONFIGPATH))

    with open(USERCONFIGPATH, "w") as f:
        UserConfig.write(f)

    #  print("...write OK")


###############################################################################
# HEAVY LIFTING
###############################################################################
def _scan_profile(url: str,
                  org: str,
                  fid: str,
                  max_workers: Optional[int] = None,
                  timeout: Optional[float] = None) -> Tuple[ScanResult,
                                                            ScanResult,
                                                            Mapping[str, bool],
                                                           ]:
    """
    Report permutations of OFX version/prettyprint/unclosedelements that
    successfully download OFX profile from server.

    Returns a 3-tuple of (OFXv1 results, OFXv2 results, signoninfo), each
    type(dict).  OFX results provide ``ofxget`` configs that will work to
    make a basic OFX connection. SIGNONINFO provides further auth information
    that may be needed to succssfully log in.
    """
    if timeout is None:
        timeout = 5.0

    if max_workers is None:
        max_workers = 5

    ofxv1 = [102, 103, 151, 160]
    ofxv2 = [200, 201, 202, 203, 210, 211, 220]

    futures = {}
    client = OFXClient(url, org=org, fid=fid)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for prettyprint in (False, True):
            for close_elements in (False, True):
                futures.update({executor.submit(
                    client.request_profile,
                    version=version,
                    prettyprint=prettyprint,
                    close_elements=close_elements,
                    timeout=timeout):
                    (version, prettyprint, close_elements)
                    for version in ofxv1})

            futures.update({executor.submit(
                client.request_profile,
                version=version,
                prettyprint=prettyprint,
                close_elements=True,
                timeout=timeout):
                (version, prettyprint, True) for version in ofxv2})

    # The only thing we're measuring here is success (indicated by receiving
    # a valid HTTP response) or failure (indicated by the request's
    # throwing any of various errors).  We don't examine the actual response
    # beyond simply parsing it to verify that it's valid OFX.  The data we keep
    # is actually the metadata (i.e. connection parameters like OFX version
    # tried for a request) stored as values in the ``futures`` dict.
    working: Mapping[int, List[tuple]] = defaultdict(list)
    signoninfos: MutableMapping[int, Any] = defaultdict(OrderedDict)

    for future in concurrent.futures.as_completed(futures):
        try:
            response = future.result()
        except (URLError,
                HTTPError,
                ConnectionError,
                OSError,
                ) as exc:
            future.cancel()
            continue

        (version, prettyprint, close_elements) = futures[future]
        working[version].append((prettyprint, close_elements))

        # ``response`` is an HTTPResponse; doesn't have seek() method used
        # by ``header.parse_header()``.  Repackage as BytesIO for parsing.
        if not signoninfos[version]:
            try:
                signoninfos_ = extract_signoninfos(BytesIO(response.read()))
                assert len(signoninfos_) > 0
                info = signoninfos_[0]
                bool_attrs = ("chgpinfirst",
                              "clientuidreq",
                              "authtokenfirst",
                              "mfachallengefirst",
                              )
                signoninfo_ = OrderedDict([
                    (attr, getattr(info, attr, None) or False)
                    for attr in bool_attrs])
                signoninfos[version] = signoninfo_
            except (ValueError, ):
                pass

    signoninfos = {k: v for k, v in signoninfos.items() if v}
    if signoninfos:
        highest_version = max(signoninfos.keys())
        signoninfo = signoninfos[highest_version]
    else:
        signoninfo = OrderedDict()

    def collate_results(
        results: Tuple[int, Tuple[bool, bool]]
    ) -> Tuple[List[int], List[MutableMapping[str, bool]]]:
        """
        Transform our metadata results (version, prettyprint, close_elements)
        into a 2-tuple of ([OFX version], [format]) where each format is a dict
        of {"pretty": bool, "unclosedelements": bool} representing a pair
        of configs that should successully connect for those versions.

        Input ``results`` needs to be a complete set for either OFXv1 or v2,
        with no results for the other version admixed.
        """
        results_ = list(results)
        if not results_:
            return [], []
        versions, formats = zip(*results_)  # type: ignore

        # Assumption: the same formatting requirements apply to all
        # sub-versions (e.g. 1.0.2 and 1.0.3, or 2.0.3 and 2.2.0).
        # If a (pretty, close_elements) pair succeeds on most sub-versions
        # but fails on a few, we'll chalk it up to network transmission
        # errors and ignore it.
        #
        # Translation: just pick the longest sequence of successful
        # formats and assume it applies to the whole version.
        formats = max(formats, key=len)
        formats.sort()
        formats = [OrderedDict([("pretty", fmt[0]),
                               ("unclosedelements", not fmt[1])])
                   for fmt in formats]
        return sorted(list(versions)), formats

    v2, v1 = utils.partition(lambda result: result[0] < 200, working.items())
    v1_versions, v1_formats = collate_results(v1)
    v2_versions, v2_formats = collate_results(v2)

    # V2 always has closing tags for elements; just report prettyprint
    for format in v2_formats:
        assert not format["unclosedelements"]
        del format["unclosedelements"]

    return (OrderedDict([("versions", v1_versions), ("formats", v1_formats)]),
            OrderedDict([("versions", v2_versions), ("formats", v2_formats)]),
            signoninfo,
            )


def verify_status(trnrs: models.Aggregate) -> None:
    """
    Input a models.Aggregate instance representing a transaction wrapper.
    """
    status = trnrs.status
    if status.code != 0:
        msg = ("{cls}: Request failed, code={code}, "
               "severity={severity}, message='{msg}'")
        raise ValueError(msg.format(cls=trnrs.__class__.__name__,
                                    code=status.code,
                                    severity=status.severity,
                                    msg=status.message))


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

    def extract_signoninfo(trnrs):
        assert isinstance(trnrs, models.PROFTRNRS)
        verify_status(trnrs)
        rs = trnrs.profrs
        assert rs is not None

        list_ = rs.signoninfolist
        assert list_ is not None
        return list_[:]

    return list(itertools.chain.from_iterable(
        [extract_signoninfo(trnrs) for trnrs in msgs]))


def extract_acctinfos(markup: BytesIO) -> ChainMap:
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

    # *ACCTINFO classes don't have rich comparison methods;
    # can't sort by class
    sortKey = attrgetter("__class__.__name__")

    # ACCTINFOs are ListItems of ACCTINFORS
    # *ACCTINFOs are ListItems of ACCTINFO
    # The data we want is in a nested list
    acctinfos = sorted(itertools.chain.from_iterable(acctinfors), key=sortKey)

    def _unique(ids, label):
        ids = set(ids)
        if len(ids) > 1:
            msg = "Multiple {} {}; can't configure automatically"
            raise ValueError(msg.format(label, list(ids)))
        try:
            id = ids.pop()
        except KeyError:
            msg = "{} is empty"
            raise ValueError(msg.format(label))
        return id

    def _ready(acctinfo):
        return acctinfo.svcstatus == "ACTIVE"

    def parse_bank(acctinfos):
        bankids = []
        args_ = defaultdict(list)
        for inf in acctinfos:
            if _ready(inf):
                bankids.append(inf.bankid)
                args_[inf.accttype.lower()].append(inf.acctid)

        args_["bankid"] = _unique(bankids, "BANKIDs")
        return dict(args_)

    def parse_inv(acctinfos):
        brokerids = []
        args_ = defaultdict(list)
        for inf in acctinfos:
            if _ready(inf):
                acctfrom = inf.invacctfrom
                brokerids.append(acctfrom.brokerid)
                args_["investment"].append(acctfrom.acctid)

        args_["brokerid"] = _unique(brokerids, "BROKERIDs")
        return dict(args_)

    def parse_cc(acctinfos):
        return {"creditcard": [inf.acctid for inf in acctinfos if _ready(inf)]}

    dispatcher = {"BANKACCTINFO": parse_bank,
                  "CCACCTINFO": parse_cc,
                  "INVACCTINFO": parse_inv}

    return ChainMap(*[dispatcher.get(clsName, lambda x: {})(_acctinfos)
                      for clsName, _acctinfos in itertools.groupby(
                          acctinfos, key=sortKey)])


def fi_index() -> List[str]:
    """ All FIs known to ofxget """
    return sorted(UserConfig.sections())


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
REQUEST_HANDLERS = {"scan": scan_profile,
                    "prof": request_profile,
                    "acctinfo": request_acctinfo,
                    "stmt": request_stmt,
                    "stmtend": request_stmtend,
                    "tax1099": request_tax1099}


def main() -> None:
    argparser = make_argparser()
    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urllib_parse.urlparse(server).scheme:
        args.url = server
        args_ = ChainMap(vars(args))
    else:
        args_ = merge_config(args, UserConfig)

    REQUEST_HANDLERS[args_["request"]](args_)


if __name__ == "__main__":
    main()
