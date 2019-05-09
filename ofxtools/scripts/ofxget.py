#!/usr/bin/env python
# coding: utf-8
"""
Configurable CLI front end for ``ofxtools.Client``
"""
# stdlib imports
import os
from argparse import ArgumentParser
from configparser import ConfigParser
import datetime
from collections import defaultdict, OrderedDict, ChainMap
import getpass
import urllib
import concurrent.futures
import json
from io import BytesIO
import itertools
from operator import attrgetter
import sys
import warnings

# 3rd party imports
try:
    import keyring
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
from ofxtools.Parser import OFXTree, ParseError


CONFIGPATH = os.path.join(config.CONFIGDIR, "fi.cfg")
DefaultConfig = ConfigParser()
DefaultConfig.read(CONFIGPATH)

USERCONFIGPATH = os.path.join(config.USERCONFIGDIR, "ofxget.cfg")
UserConfig = ConfigParser()
UserConfig.read(USERCONFIGPATH)

DEFAULTS = {"url": None, "org": None, "fid": None, "version": 203,
            "appid": None, "appver": None, "bankid": None, "brokerid": None,
            "user": None, "clientuid": None, "language": None, "dryrun": False,
            "unsafe": False, "unclosedelements": False, "pretty": False,
            "checking": [], "savings": [], "moneymrkt": [], "creditline": [],
            "creditcard": [], "investment": [], "dtstart": None, "dtend": None,
            "dtasof": None, "inctran": True, "incbal": True, "incpos": True,
            "incoo": False, "all": False, "years": [], "acctnum": None,
            "recid": None, "write": False, "savepass": False}


class OfxgetWarning(UserWarning):
    """ Base class for warnings in this module """


def fi_index():
    return sorted(set(UserConfig.sections() + DefaultConfig.sections()))


def get_passwd(args):
    """
    1.  For dry run, use dummy password from OFX spec
    2.  If python-keyring is installed and --savepass is unset, try to use it
    3.  Prompt for password in terminal
    """
    if args["dryrun"]:
        password = "{:0<32}".format("anonymous")
    else:
        password = None
        if HAS_KEYRING and not args["savepass"]:
            password = keyring.get_password("ofxtools", args["server"])
        if password is None:
            password = getpass.getpass()
    return password


def save_passwd(args, password):
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


def make_argparser():
    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index()),
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
    scan_group.add_argument("--ofxhome", default=None,
                            help="FI id# on http://www.ofxhome.com/")

    signon_group = argparser.add_argument_group(title="Signon Options")
    signon_group.add_argument("-u", "--user", help="FI login username")
    signon_group.add_argument("--clientuid", metavar="UUID4",
                              help="OFX client UID")
    signon_group.add_argument("--org", help="FI.ORG")
    signon_group.add_argument("--fid", help="FI.FID")
    signon_group.add_argument("--appid", help="OFX client app identifier")
    signon_group.add_argument("--appver", help="OFX client app version")
    signon_group.add_argument("--language", default=None, help="OFX language")

    stmt_group = argparser.add_argument_group(title="Statement Options")
    stmt_group.add_argument("--bankid", help="ABA routing#")
    stmt_group.add_argument("--brokerid", help="Broker ID string")
    stmt_group.add_argument(
        "-C", "--checking", metavar="#", action="append", default=None,
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-S", "--savings", metavar="#", action="append", default=None,
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-M", "--moneymrkt", metavar="#", action="append", default=None,
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-L", "--creditline", metavar="#", action="append", default=None,
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-c", "--creditcard", "--cc", metavar="#", action="append", default=None,
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-i", "--investment", metavar="#", action="append", default=None,
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
        type=int, action="append", default=None,
        help="(YYYY) Tax year (option can be repeated)",
    )
    tax_group.add_argument(
        "--acctnum",
        dest="acctnum",
        default=None,
        help="Account # of recipient, if different than tax ID",
    )
    tax_group.add_argument(
        "--recid",
        dest="recid",
        default=None,
        help="ID of recipient",
    )

    return argparser


###############################################################################
# CLI METHODS
###############################################################################
def scan_profiles(start, stop, timeout=None):
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


def scan_profile(args):
    """
    Report working connection parameters
    """
    scan_results = _scan_profile(args["url"], args["org"], args["fid"])

    v1, v2 = scan_results
    if (not v2["versions"]) and (not v1["versions"]):
        msg = "Scan found no working formats for {}"
        print(msg.format(args["url"]))
        sys.exit()

    print(json.dumps(scan_results))

    if args["write"]:
        extra_args = _best_scan_format(scan_results)

        write_config(args, extra_args=extra_args)


def _best_scan_format(scan_results):
    """
    Given the results of _scan_profile(), choose the best parameters;
    return as dict (compatible with ArgParser/ ChainMap).

    "Best" here means highest working version with the minimal configuration
    delta, i.e. we prefer formats with "pretty"/"unclosedelements" given as
    False (the default) over True.
    """
    v1, v2 = scan_results
    if v2["versions"]:
        result = v2
    elif v1["versions"]:
        result = v1

    formats = sorted(result["formats"], key=lambda f: sum(f.values()))
    args = {k: v for k, v in formats[0].items() if v}

    args["version"] = result["versions"].pop()

    return args


def request_profile(args):
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


def request_acctinfo(args):
    """
    Send ACCTINFORQ
    """

    if not args["user"]:
        msg = "Please configure 'user'"
        raise ValueError(msg.format(msg))

    password = get_passwd(args)
    acctinfo = _request_acctinfo(args, password)

    print(acctinfo.read().decode())

    if args["write"]:
        acctinfo.seek(0)
        extra_args = extract_acctinfos(acctinfo)
        extra_args = {k: arg2config(k, v) for k, v in extra_args.items()}

        write_config(args, extra_args=extra_args)

    if args["savepass"]:
        save_passwd(args, password)


def _request_acctinfo(args, password):
    client = init_client(args)
    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(password,
                                 dtacctup,
                                 dryrun=args["dryrun"],
                                 verify_ssl=not args["unsafe"]) as f:
        response = f.read()

    return BytesIO(response)


def request_stmt(args):
    """
    Send *STMTRQ
    """
    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(args[d]) for d in ("dtstart", "dtend", "dtasof")}

    password = get_passwd(args)

    if args["all"]:
        acctinfo = _request_acctinfo(args, password)
        args_ = extract_acctinfos(acctinfo)
        args.maps.insert(1, args_)

    stmtrqs = []
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

    if args["write"]:
        write_config(args)

    if args["savepass"]:
        save_passwd(args, password)


def request_stmtend(args):
    """
    Send *STMTENDRQ
    """
    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(args[d]) for d in ("dtstart", "dtend", "dtasof")}

    password = get_passwd(args)

    if args["all"]:
        acctinfo = _request_acctinfo(args, password)
        args_ = extract_acctinfos(acctinfo)
        args.maps.insert(1, args_)

    stmtendrqs = []
    for accttype in ("checking", "savings", "moneymrkt", "creditline"):
        acctids = args.get(accttype, [])
        stmtendrqs.extend(
            [StmtEndRq(acctid=acctid, accttype=accttype.upper(),
                       dtstart=dt["start"], dtend=dt["end"])
             for acctid in acctids])

    for acctid in args.get("creditcard", []):
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

    if args["write"]:
        write_config(args)

    if args["savepass"]:
        save_passwd(args, password)


def request_tax1099(args):
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
def init_client(args):
    """
    Initialize OFXClient with connection info from args
    """
    client = OFXClient(
        args["url"],
        userid=args["user"],
        clientuid=args["clientuid"],
        org=args["org"],
        fid=args["fid"],
        version=args["version"],
        appid=args["appid"],
        appver=args["appver"],
        language=args["language"],
        prettyprint=args["pretty"],
        close_elements=not args["unclosedelements"],
        bankid=args["bankid"],
        brokerid=args["brokerid"],
    )
    return client


def merge_config(args):
    """
    Merge CLI args > user config > library config > OFX Home > defaults
    """
    # dict of all ArgumentParser args that have a value set
    args = {k: v for k, v in vars(args).items() if v is not None}
    server = args["server"]

    def read_config(cfg, section):
        return {k: config2arg(k, v)
                for k, v in cfg[server].items()} if section in cfg else {}

    user_cfg = read_config(UserConfig, server)
    default_cfg = read_config(DefaultConfig, server)

    merged = ChainMap(args, user_cfg, default_cfg, DEFAULTS)

    if "ofxhome" in merged:
        lookup = ofxhome.lookup(merged["ofxhome"])

        # Insert OFX Home lookup ahead of DEFAULTS but after
        # user configs and library configs
        merged.maps.insert(-1, {"url": lookup.url, "org": lookup.org,
                                "fid": lookup.fid,
                                "brokerid": lookup.brokerid})

    if merged.get("url", None) is None:
        msg = "Unknown server '{}'; please configure 'url' or 'ofxhome'"
        raise ValueError(msg.format(server))

    return merged


def config2arg(key, value):
    """
    Transform a config value from ConfigParser format to ArgParser format
    """
    default = DEFAULTS.get(key, None)

    if type(default) is list:
        # Allow sequences of acct nos
        value = [v.strip() for v in value.split(",")]
    elif type(default) is bool:
        BOOLY = ConfigParser.BOOLEAN_STATES
        value_ = BOOLY.get(value, None)
        if value_ is None:
            msg = "Can't interpret '{}' as bool; must be in {}"
            raise ValueError(msg.format(value, list(BOOLY.keys())))
        value = value_
    elif type(default) is int:
        value = int(value)

    return value


def arg2config(key, value):
    """
    Transform a config value from ArgParser format to ConfigParser format
    """
    default = DEFAULTS.get(key, None)

    if type(default) is list:
        # INI-friendly string representation of Python list type
        value = str(value).strip("[]").replace("'", "")
    elif type(default) is bool:
        value = {True: "true", False: "false", None: ""}[value]

    if value is None:
        value = ""

    return str(value)


def mk_server_cfg(args):
    """
    Copy key parameters to UserConfig, under the indicated section
    """
    server = args.get("server", None)
    # args.server might actually be a URL from CLI, not a nickname
    if (not server) or server == args["url"]:
        msg = "Please provide a server nickname to write the config"
        raise ValueError(msg)

    if not UserConfig.has_section(server):
        UserConfig[server] = {}
    cfg = UserConfig[server]

    for opt in ("url", "version", "ofxhome", "org", "fid", "brokerid",
                "bankid", "user", "pretty", "unclosedelements"):
        if (opt in args) and (args[opt] not in (None, [])):
            cfg[opt] = arg2config(opt, args[opt])

    return cfg


def write_config(args, *, extra_args=None):
    args.maps.insert(0, extra_args)
    cfg = mk_server_cfg(args)

    #  msg = "\nWriting '{}' configs {} to {}..."
    #  print(msg.format(args["server"], dict(cfg.items()), USERCONFIGPATH))

    with open(USERCONFIGPATH, "w") as f:
        UserConfig.write(f)

    #  print("...write OK")


###############################################################################
# HEAVY LIFTING
###############################################################################
def _scan_profile(url, org, fid, max_workers=None, timeout=None):
    """
    Report permutations of OFX version/prettyprint/unclosedelements that
    successfully download OFX profile from server.

    Returns a pair of (OFXv1 results, OFXv2 results), each type(dict).
    dict values provide ``ofxget`` configs that will work to connect.
    """
    if timeout is None:
        timeout = 5

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
    working = defaultdict(list)

    for future in concurrent.futures.as_completed(futures):
        try:
            response = future.result()
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                ConnectionError,
                OSError,
                ) as exc:
            future.cancel()
            continue


        # ``response`` is an HTTPResponse; doesn't have seek() method used by
        # ``header.parse_header()``.  Repackage as a BytesIO for parsing.
        try:
            signoninfos = extract_signoninfos(BytesIO(response.read()))
        except ValueError:
            signoninfos = []

        (version, prettyprint, close_elements) = futures[future]
        working[version].append((prettyprint, close_elements))

    def collate_results(results):
        """
        Transform our metadata results (version, prettyprint, close_elements)
        into a 2-tuple of ([OFX version], [format]) where each format is a dict
        of {"pretty": bool, "unclosedelements": bool} representing a pair
        of configs that should successully connect for those versions.

        Input ``results`` needs to be a complete set for either OFXv1 or v2,
        with no results for the other version admixed.
        """
        results = list(results)
        if not results:
            return [], []
        versions, formats = zip(*results)

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
        del format["unclosedelements"]

    return (OrderedDict([("versions", v1_versions), ("formats", v1_formats)]),
            OrderedDict([("versions", v2_versions), ("formats", v2_formats)]))


def verify_status(trnrs):
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


def extract_signoninfos(markup):
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
        return itertools.chain.from_iterable(list_)

    return [extract_signoninfo(trnrs) for trnrs in msgs]


def extract_acctinfos(markup):
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


# Map "request" arg to handler function
REQUEST_HANDLERS = {"scan": scan_profile,
                    "prof": request_profile,
                    "acctinfo": request_acctinfo,
                    "stmt": request_stmt,
                    "stmtend": request_stmtend,
                    "tax1099": request_tax1099}


def main():
    argparser = make_argparser()
    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urllib.parse.urlparse(server).scheme:
        args.url = server
        args = ChainMap(vars(args))
    else:
        args = merge_config(args)

    REQUEST_HANDLERS[args["request"]](args)


if __name__ == "__main__":
    main()
