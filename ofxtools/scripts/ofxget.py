#!/usr/bin/env python
# coding: utf-8
"""
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
from functools import singledispatch
import sys


# local imports
from ofxtools.Client import (
    OFXClient, StmtRq, CcStmtRq, InvStmtRq,
    StmtEndRq, CcStmtEndRq,
)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools import (utils, ofxhome, config, models)
from ofxtools.Parser import OFXTree
from ofxtools import models


CONFIGPATH = os.path.join(config.CONFIGDIR, "fi.cfg")
DefaultConfig = ConfigParser()
DefaultConfig.read(CONFIGPATH)

USERCONFIGPATH = os.path.join(config.USERCONFIGDIR, "ofxget.cfg")
UserConfig = ConfigParser()
UserConfig.read(USERCONFIGPATH)


DEFAULTS = {"url": None, "org": None, "fid": None, "version": None,
            "appid": None, "appver": None, "bankid": None, "brokerid": None,
            "user": None, "clientuid": None, "language": None, "dryrun": False,
            "unsafe": False, "unclosedelements": False, "pretty": False,
            "checking": [], "savings": [], "moneymrkt": [], "creditline": [],
            "creditcard": [], "investment": [], "dtstart": None, "dtend": None,
            "dtasof": None, "inctran": True,
            "incbal": True, "incpos": True, "incoo": False, "all": False,
            "years": [], "acctnum": None, "recid": None, "write": False}


def fi_index():
    return sorted(set(UserConfig.sections() + DefaultConfig.sections()))


def make_argparser():
    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index()),
    )
    argparser.add_argument(
        "request",
        choices=list(REQUEST_FNS.keys()),
        help="Request type")
    argparser.add_argument(
        "server", help="OFX server - URL or FI name from ofxget.cfg/fi.cfg")
    argparser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        default=None,
        help="display OFX request and exit without sending",
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
    scan_group.add_argument("-w", "--write", action="store_true", default=None,
                            help="Write scan results to config file")
    scan_group.add_argument("--ofxhome_id", default=None,
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


def scan_profiles(start, stop, timeout=None):
    """
    Scan OFX Home's list of FIs for working connection configs.
    """
    results = {}

    institutions = ofxhome.list_institutions()
    for ofxhome_id in list(institutions.keys())[start:stop]:
        lookup = ofxhome.lookup(ofxhome_id)
        if lookup is None or ofxhome.ofx_invalid(lookup) or ofxhome.ssl_invalid(lookup):
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
    results = _scan_profile(args["url"], args["org"], args["fid"])

    v1, v2 = results
    if v2["versions"]:
        result = v2
    elif v1["versions"]:
        result = v1
    else:
        msg = "Scan found no working formats for {}"
        print(msg.format(args["url"]))
        sys.exit()

    print(json.dumps(results))

    if args["write"]:
        server = args["server"]
        if server == args["url"]:
            msg = "Please provide a server nickname to write the config"
            raise ValueError(msg)

        # Prefer the highest version
        version = result["versions"].pop()

        # Prefer formats with "pretty"/"unclosedelements" False over True
        formats = sorted(result["formats"], key=lambda f: sum(f.values()))
        fmt = formats[0]

        if not UserConfig.has_section(server):
            UserConfig[server] = {}
        cfg = UserConfig[server]

        for opt in "url", "ofxhome_id", "org", "fid", "brokerid", "bankid":
            if (opt in args) and args[opt]:
                cfg[opt] = str(args[opt])

        cfg["version"] = str(version)
        for k, v in fmt.items():
            if v:
                cfg[k] = str(v).lower()

        msg = "Writing '{}' configs {} to {}"
        print(msg.format(server, dict(cfg.items()), USERCONFIGPATH))
        with open(USERCONFIGPATH, "w") as f:
            UserConfig.write(f)


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

    working = defaultdict(list)

    for future in concurrent.futures.as_completed(futures):
        try:
            response = future.result()
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                ConnectionError,
                OSError) as exc:
            cancelled = future.cancel()
            continue
        else:
            (version, prettyprint, close_elements) = futures[future]
            working[version].append((prettyprint, close_elements))

    def collate_results(results):
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
        formats = [OrderedDict([("pretty", format[0]),
                               ("unclosedelements", not format[1])])
                   for format in formats]
        return sorted(list(versions)), formats

    v2, v1 = utils.partition(lambda pair: pair[0] < 200, working.items())
    v1_versions, v1_formats = collate_results(v1)
    v2_versions, v2_formats = collate_results(v2)

    # V2 always has closing tags for elements; just report prettyprint
    for format in v2_formats:
        del format["unclosedelements"]

    return (OrderedDict([("versions", v1_versions), ("formats", v1_formats)]),
            OrderedDict([("versions", v2_versions), ("formats", v2_formats)]))


def request_stmt(args):
    """
    Send *STMTRQ
    """
    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(args[d]) for d in ("dtstart", "dtend", "dtasof")}

    # Prompt for password
    if args["dryrun"]:
        # Use dummy password for dummy request
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    # Define statement requests
    if args["all"]:
        stmtrqs = all_stmts(args, dt, password)
    else:
        stmtrqs = []
        # Create *STMTRQ for each account specified by config/args
        for accttype in ("checking", "savings", "moneymrkt", "creditline"):
            acctids = args.get(accttype, [])
            stmtrqs.extend(
                [
                    StmtRq(
                        acctid=acctid,
                        accttype=accttype.upper(),
                        dtstart=dt["start"],
                        dtend=dt["end"],
                        inctran=args["inctran"],
                    )
                    for acctid in acctids
                ]
            )

        for acctid in args.get("creditcard", []):
            stmtrqs.append(
                CcStmtRq(
                    acctid=acctid,
                    dtstart=dt["start"],
                    dtend=dt["end"],
                    inctran=args["inctran"],
                )
            )

        for acctid in args.get("investment", []):
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

    client = init_client(args)
    with client.request_statements(
        password,
        *stmtrqs,
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())


def all_stmts(args, dt, password):
    """ Download ACCTINFORS; create *STMTRQ for each account therein. """
    acctinfo = _request_acctinfo(args, password)
    parser = OFXTree()
    parser.parse(acctinfo)
    ofx = parser.convert()
    status = ofx.signonmsgsrsv1.sonrs.status
    if status.code != 0:
        msg = "OFX signon failed, code={}, severity={}, message='{}'"
        raise ValueError(msg.format(status.code, status.severity,
                                    status.message))
    msgs = ofx.signupmsgsrsv1
    assert msgs is not None and len(msgs) == 1
    trnrs = msgs[0]
    assert isinstance(trnrs, models.ACCTINFOTRNRS)
    status = trnrs.status
    if status.code != 0:
        msg = "ACCTINFO request failed, code={}, severity={}, message='{}'"
        raise ValueError(msg.format(status.code, status.severity,
                                    status.message))

    rs = trnrs.acctinfors
    assert isinstance(rs, models.ACCTINFORS)

    stmtrqs = []
    for acctinfo in rs:
        assert isinstance(acctinfo, models.ACCTINFO)
        stmtrqs.extend([mkstmtrq(acctinf, args, dt) for acctinf in acctinfo])
    return stmtrqs


@singledispatch
def mkstmtrq(acctinfo, args, dt):
    acct = acctinfo.bankacctfrom
    return StmtRq(acctid=acct.acctid, accttype=acct.accttype,
                  dtstart=dt["start"], dtend=dt["end"], inctran=args["inctran"])


@mkstmtrq.register(models.CCACCTINFO)
def _(acctinfo, args, dt):
    acct = acctinfo.ccacctfrom
    return CcStmtRq(acctid=acct.acctid, dtstart=dt["start"], dtend=dt["end"],
                    inctran=args["inctran"])


@mkstmtrq.register(models.INVACCTINFO)
def _(acctinfo, args, dt):
    acct = acctinfo.invacctfrom
    return InvStmtRq(acctid=acct.acctid, dtstart=dt["start"], dtend=dt["end"],
                     inctran=args["inctran"], incoo=args["incoo"],
                     incpos=args["incpos"], incbal=args["incbal"])


def request_stmtend(args):
    """
    Send *STMTENDRQ
    """
    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(args[d]) for d in ("dtstart", "dtend", "dtasof")}

    # Prompt for password
    if args["dryrun"]:
        # Use dummy password for dummy request
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    # Define statement requests
    stmtendrqs = []

    # Create *STMTENDRQ for each account specified by config/args
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


def request_profile(args):
    """
    Send PROFRQ
    """
    client = init_client(args)

    with client.request_profile(
        version=args["version"],
        prettyprint=args["pretty"],
        close_elements=not args["unclosedelements"],
        dryrun=args["dryrun"],
        verify_ssl=not args["unsafe"]
    ) as f:
        response = f.read()

    print(response.decode())


def request_acctinfo(args):
    """
    Send ACCTINFORQ
    """

    # Use dummy password for dummy request
    if args["dryrun"]:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    print(_request_acctinfo(args, password).read().decode())


def _request_acctinfo(args, password):
    client = init_client(args)

    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(password,
                                 dtacctup,
                                 dryrun=args["dryrun"],
                                 verify_ssl=not args["unsafe"]) as f:
        response = f.read()

    return BytesIO(response)


def request_tax1099(args):
    """
    Send TAX1099RQ
    """
    client = init_client(args)

    # Use dummy password for dummy request
    if args["dryrun"]:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    with client.request_tax1099(password,
                                *args["years"],
                                acctnum=args["acctnum"],
                                recid=args["recid"],
                                dryrun=args["dryrun"],
                                verify_ssl=not args["unsafe"]
                               ) as f:
        response = f.read()

    print(response.decode())


# Map args.request choices to request function
REQUEST_FNS = {"scan": scan_profile,
               "prof": request_profile,
               "acctinfo": request_acctinfo,
               "stmt": request_stmt,
               "stmtend": request_stmtend,
               "tax1099": request_tax1099,
              }


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


def parse_config(key, value):
    LISTS = ["checking", "savings", "moneymrkt", "creditline", "creditcard",
             "investment", "years"]
    BOOLS = ["dryrun", "unsafe", "pretty", "unclosedelements", "inctran",
             "incpos", "incbal", "incoo", "all"]
    INTS = ["version"]

    if key in LISTS:
        # Allow sequences of acct nos
        value = [v.strip() for v in value.split(",")]
    elif key in BOOLS:
        BOOLY = ConfigParser.BOOLEAN_STATES
        value_ = BOOLY.get(value, None)
        if value_ is None:
            msg = "Can't interpret '{}' as bool; must be in {}"
            raise ValueError(msg.format(value, list(BOOLY.keys())))
        value = value_
    elif key in INTS:
        value = int(value)

    return value


def merge_config(args):
    """
    Merge CLI args > user config > library config > OFX Home > defaults
    """
    # dict of all ArgumentParser args that have a value set
    args = {k: v for k, v in vars(args).items() if v is not None}
    server = args["server"]

    def read_cfg(cfg, section):
        return {k: parse_config(k, v)
                for k, v in cfg[server].items()} if section in cfg else {}

    user_cfg = read_cfg(UserConfig, server)
    default_cfg = read_cfg(DefaultConfig, server)

    merged = ChainMap(args, user_cfg, default_cfg, DEFAULTS)

    # If we don't know URL, try to fall back to OFX Home
    if merged.get("url", None) is None:
        if merged.get("ofxhome_id", None) is None:
            msg = "Unknown server '{}'; please configure 'url' or 'ofxhome_id'"
            raise ValueError(msg.format(server))

        lookup = ofxhome.lookup(merged["ofxhome_id"])

        # There's no reason why DEFAULTS should have any overlap with
        # an ofxhome lookup, but on general principles we'll make sure
        # DEFAULTS comes last in the mapping order
        merged.maps.insert(-1, {"url": lookup.url, "org": lookup.org,
                                "fid": lookup.fid,
                                "brokerid": lookup.brokerid})

    return merged


def main():
    argparser = make_argparser()
    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urllib.parse.urlparse(server).scheme:
        args.url = server
        args = vars(args)
    else:
        args = merge_config(args)

    REQUEST_FNS[args["request"]](args)


if __name__ == "__main__":
    main()
