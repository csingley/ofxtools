#!/usr/bin/env python
# coding: utf-8
"""
"""
# stdlib imports
import datetime
from collections import defaultdict, OrderedDict
#  from os import path
import getpass
#  from configparser import ConfigParser
import urllib
import concurrent.futures
import json


# local imports
from ofxtools.Client import (OFXClient, StmtRq, CcStmtRq, InvStmtRq)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools import (utils, ofxhome, config)


def init_client(args):
    """
    Initialize OFXClient with connection info from args
    """
    client = OFXClient(
        args.url,
        org=args.org,
        fid=args.fid,
        version=args.version,
        appid=args.appid,
        appver=args.appver,
        language=args.language,
        bankid=args.bankid,
        brokerid=args.brokerid,
    )
    return client


def do_stmt(args):
    """
    Construct OFX statement request from CLI/config args; send to server.
    """
    client = init_client(args)

    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(getattr(args, d)) for d in ("dtstart", "dtend", "dtasof")}

    # Define statement requests
    stmtrqs = []
    for accttype in ("checking", "savings", "moneymrkt", "creditline"):
        acctids = getattr(args, accttype, [])
        stmtrqs.extend(
            [
                StmtRq(
                    acctid=acctid,
                    accttype=accttype.upper(),
                    dtstart=dt["start"],
                    dtend=dt["end"],
                    inctran=args.inctran,
                )
                for acctid in acctids
            ]
        )

    for acctid in args.creditcard:
        stmtrqs.append(
            CcStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                inctran=args.inctran,
            )
        )

    for acctid in args.investment:
        stmtrqs.append(
            InvStmtRq(
                acctid=acctid,
                dtstart=dt["start"],
                dtend=dt["end"],
                dtasof=dt["asof"],
                inctran=args.inctran,
                incoo=args.incoo,
                incpos=args.incpos,
                incbal=args.incbal,
            )
        )

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    with client.request_statements(
        args.user,
        password,
        *stmtrqs,
        clientuid=args.clientuid,
        dryrun=args.dryrun,
        close_elements=not args.unclosedelements,
        prettyprint=args.pretty,
        verify_ssl=not args.unsafe
    ) as f:
        response = f.read()

    print(response.decode())


def do_profile(args):
    """
    Construct OFX profile request from CLI/config args; send to server.
    """
    client = init_client(args)
    with client.request_profile(
        dryrun=args.dryrun,
        close_elements=not args.unclosedelements,
        prettyprint=args.pretty,
        verify_ssl=not args.unsafe
    ) as f:
        response = f.read()

    print(response.decode())


def do_scan(args):
    """
    Report working connection parameters
    """
    results = scan_profile(args.url, args.org, args.fid)
    print(results)


def do_acctinfo(args):
    """
    Construct OFX account info request from CLI/config args; send to server.
    """
    client = init_client(args)

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    dtacctup = datetime.datetime(1999, 12, 31, tzinfo=UTC)

    with client.request_accounts(args.user,
                                 password,
                                 dtacctup,
                                 dryrun=args.dryrun,
                                 close_elements=not args.unclosedelements,
                                 prettyprint=args.pretty,
                                 verify_ssl=not args.unsafe
                                ) as f:
        response = f.read()

    print(response.decode())


def make_argparser(fi_index):
    from argparse import ArgumentParser

    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index),
    )
    argparser.add_argument("server", help="OFX server - URL or FI name from config")
    argparser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        default=False,
        help="display OFX request and exit",
    )
    argparser.add_argument(
        "-p",
        "--profile",
        action="store_true",
        default=False,
        help="Download OFX profile instead of statement",
    )
    argparser.add_argument(
        "--unsafe",
        action="store_true",
        default=False,
        help="Disable SSL certificate verification",
    )
    argparser.add_argument(
        "--scan",
        action="store_true",
        default=False,
        help="Scan for working OFX connection parameters",
    )
    argparser.add_argument(
        "--accts",
        action="store_true",
        default=False,
        help="Download account information instead of statement",
    )
    argparser.add_argument(
        "--unclosedelements",
        action="store_true",
        default=False,
        help="Omit end tags for elements (OFXv1 only)",
    )
    argparser.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Insert newlines and whitespace indentation",
    )

    signon_group = argparser.add_argument_group(title="Signon Options")
    signon_group.add_argument("-u", "--user", help="FI login username")
    signon_group.add_argument("--clientuid", help="OFX client UID")
    signon_group.add_argument("--org", help="FI.ORG")
    signon_group.add_argument("--fid", help="FI.FID")
    signon_group.add_argument("--bankid", help="ABA routing#")
    signon_group.add_argument("--brokerid", help="Broker ID string")
    signon_group.add_argument("--version", help="OFX version")
    signon_group.add_argument("--appid", help="OFX client app identifier")
    signon_group.add_argument("--appver", help="OFX client app version")
    signon_group.add_argument("--language", default="ENG", help="OFX language")

    acct_group = argparser.add_argument_group(title="Account Options")
    acct_group.add_argument(
        "-C", "--checking", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-S", "--savings", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-M", "--moneymrkt", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-L", "--creditline", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-c", "--creditcard", "--cc", metavar="acct#", action="append", default=[]
    )
    acct_group.add_argument(
        "-i", "--investment", metavar="acct#", action="append", default=[]
    )

    stmt_group = argparser.add_argument_group(title="Statement Options")
    stmt_group.add_argument(
        "-s", "--start", dest="dtstart", help="(YYYYmmdd) Transactions list start date"
    )
    stmt_group.add_argument(
        "-e", "--end", dest="dtend", help="(YYYYmmdd) Transactions list end date"
    )
    stmt_group.add_argument(
        "-d",
        "--date",
        dest="dtasof",
        help="(YYYYmmdd) As-of date for investment positions",
    )
    stmt_group.add_argument(
        "--no-transactions",
        dest="inctran",
        action="store_false",
        default=True,
        help="Omit transactions list",
    )
    stmt_group.add_argument(
        "--no-positions",
        dest="incpos",
        action="store_false",
        default=True,
        help="Omit investment positions",
    )
    stmt_group.add_argument(
        "--no-balances",
        dest="incbal",
        action="store_false",
        default=True,
        help="Omit balances",
    )
    stmt_group.add_argument(
        "--open-orders",
        dest="incoo",
        action="store_true",
        default=False,
        help="Include open orders",
    )

    return argparser


def merge_config(config, args):
    """
    Merge default FI configs with user configs from oftools.cfg and CLI args
    """
    server = args.server
    if server not in config.fi_index:
        raise ValueError(
            "Unknown FI '{}' not in {}".format(server, str(config.fi_index))
        )
    # List of nonempty argparse args set from command line
    overrides = [k for k, v in vars(args).items() if v]
    for cfg, value in config.items(server, raw=True):
        # argparse settings override configparser settings
        if cfg in overrides:
            continue
        if cfg in (
            "checking",
            "savings",
            "moneymrkt",
            "creditline",
            "creditcard",
            "investment",
        ):
            # Allow sequences of acct nos
            values = [v.strip() for v in value.split(",")]
            arg = getattr(args, cfg)
            assert isinstance(arg, list)
            arg.extend(values)
        else:
            # Coerce config to bool, if applicable
            arg = getattr(args, cfg, None)
            if type(arg) is bool:
                value = config.getboolean(server, cfg)
            setattr(args, cfg, value)

    # Fall back to OFX Home, if possible
    url = getattr(args, "url", None)
    if url is None and "ofxhome_id" in config[server]:
        lookup = ofxhome.lookup(config[server]["ofxhome_id"])
        args.url = lookup.url
        for cfg in "fid", "org", "brokerid":
            if getattr(args, cfg, None) is None:
                value = getattr(lookup, cfg)
                setattr(args, cfg, value)

    return args


def scan_profiles(start, stop, timeout=None):
    """
    Scan OFX Home's list of FIs for working connection configs.
    """
    results = {}

    institutions = ofxhome.list_institutions()
    for institution in institutions[start:stop]:
        ofxhome_id = int(institution.get("id"))
        lookup = ofxhome.lookup(ofxhome_id)
        if lookup is None or ofxhome.ofx_invalid(lookup) or ofxhome.ssl_invalid(lookup):
            continue
        working = scan_profile(url=lookup.url,
                               org=lookup.org,
                               fid=lookup.fid,
                               timeout=timeout)
        if working:
            results[ofxhome_id] = working

    return results


def scan_profile(url, org, fid, max_workers=None, timeout=None):
    """
    Report permutations of OFX version/prettyprint/unclosed_elements that
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
    client = OFXClient(url, org, fid)
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
                               ("unclosed_elements", not format[1])])
                   for format in formats]
        return sorted(list(versions)), formats

    v2, v1 = utils.partition(lambda pair: pair[0] < 200, working.items())
    v1_versions, v1_formats = collate_results(v1)
    v2_versions, v2_formats = collate_results(v2)

    # V2 always has closing tags for elements; just report prettyprint
    for format in v2_formats:
        del format["unclosed_elements"]

    return json.dumps((OrderedDict([("versions", v1_versions),
                                    ("formats", v1_formats)]),
                       OrderedDict([("versions", v2_versions),
                                    ("formats", v2_formats)])))


def main():
    # Read config first, so fi_index can be used in help
    cfg = config.OfxgetConfigParser()
    cfg.read()

    argparser = make_argparser(cfg.fi_index)

    args = argparser.parse_args()

    # If positional arg is FI name (not URL), then merge config
    server = args.server
    if urllib.parse.urlparse(server).scheme:
        args.url = server
    else:
        args = merge_config(cfg, args)

    # Pass the parsed args to the statement-request function
    if args.profile:
        do_profile(args)
    elif args.scan:
        do_scan(args)
    elif args.accts:
        do_acctinfo(args)
    else:
        do_stmt(args)


if __name__ == "__main__":
    main()
