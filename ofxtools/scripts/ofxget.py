#!/usr/bin/env python
# coding: utf-8
"""
"""
# stdlib imports
import datetime
from collections import defaultdict, OrderedDict
import getpass
import urllib
import concurrent.futures
import json
from io import BytesIO


# local imports
from ofxtools.Client import (OFXClient, StmtRq, CcStmtRq, InvStmtRq)
from ofxtools.Types import DateTime
from ofxtools.utils import UTC
from ofxtools import (utils, ofxhome, config)
from ofxtools.Parser import OFXTree
from ofxtools.models.signup import (
    BANKACCTINFO, CCACCTINFO, INVACCTINFO,
)


def make_argparser(fi_index):
    from argparse import ArgumentParser

    argparser = ArgumentParser(
        description="Download OFX financial data",
        epilog="FIs configured: {}".format(fi_index),
    )
    argparser.add_argument(
        "request", choices=["scan", "prof", "acctinfo", "stmt", "tax1099"],
        help="Request type")
    argparser.add_argument(
        "server", help="OFX server - URL or FI name from ofxget.cfg/fi.cfg")
    argparser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        default=False,
        help="display OFX request and exit without sending",
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
    argparser.add_argument(
        "--unsafe",
        action="store_true",
        default=False,
        help="Disable SSL certificate verification",
    )

    signon_group = argparser.add_argument_group(title="Signon Options")
    signon_group.add_argument("-u", "--user", help="FI login username")
    signon_group.add_argument("--clientuid", metavar="UUID4", help="OFX client UID")
    signon_group.add_argument("--org", help="FI.ORG")
    signon_group.add_argument("--fid", help="FI.FID")
    signon_group.add_argument("--bankid", help="ABA routing#")
    signon_group.add_argument("--brokerid", help="Broker ID string")
    signon_group.add_argument("--version", help="OFX version")
    signon_group.add_argument("--appid", help="OFX client app identifier")
    signon_group.add_argument("--appver", help="OFX client app version")
    signon_group.add_argument("--language", default="ENG", help="OFX language")

    stmt_group = argparser.add_argument_group(title="Statement Options")
    stmt_group.add_argument(
        "-C", "--checking", metavar="#", action="append", default=[],
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-S", "--savings", metavar="#", action="append", default=[],
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-M", "--moneymrkt", metavar="#", action="append", default=[],
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-L", "--creditline", metavar="#", action="append", default=[],
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-c", "--creditcard", "--cc", metavar="#", action="append", default=[],
        help="Account number (option can be repeated)"
    )
    stmt_group.add_argument(
        "-i", "--investment", metavar="#", action="append", default=[],
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
        default=True,
        help="Omit transactions list",
    )
    stmt_group.add_argument(
        "--no-balances",
        dest="incbal",
        action="store_false",
        default=True,
        help="Omit balances",
    )
    stmt_group.add_argument(
        "--no-positions",
        dest="incpos",
        action="store_false",
        default=True,
        help="Omit investment positions",
    )
    stmt_group.add_argument(
        "--open-orders",
        dest="incoo",
        action="store_true",
        default=False,
        help="Include open orders for investments",
    )
    stmt_group.add_argument(
        "--all",
        dest="all",
        action="store_true",
        default=False,
        help="Request ACCTINFO; download statements for all",
    )

    tax_group = argparser.add_argument_group(title="Tax Form Options")
    tax_group.add_argument(
        "-y", "--year", metavar="YEAR", dest="years",
        type=int, action="append", default=[],
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
    for institution in institutions[start:stop]:
        ofxhome_id = int(institution.get("id"))
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
    results = _scan_profile(args.url, args.org, args.fid)
    print(results)


def _scan_profile(url, org, fid, max_workers=None, timeout=None):
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


def request_stmt(args):
    """
    Send STMTRQ/INVSTMTRQ
    """
    client = init_client(args)

    # Convert dtstart/dtend/dtasof to Python datetime type
    D = DateTime().convert
    dt = {d[2:]: D(getattr(args, d)) for d in ("dtstart", "dtend", "dtasof")}

    # Prompt for password
    if args.dryrun:
        # Use dummy password for dummy request
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    # Define statement requests
    stmtrqs = []
    if args.all:
        # Download ACCTINFORS; create *STMTRQ for each account therein.
        parser = OFXTree()
        acctinfo = _request_acctinfo(args, password)
        parser.parse(acctinfo)
        ofx = parser.convert()
        msgs = ofx.signupmsgsrsv1
        assert len(msgs) == 1
        acctinfors = msgs[0].acctinfors
        for _acctinfo in acctinfors:
            for acctinfo in _acctinfo:
                if isinstance(acctinfo, BANKACCTINFO):
                    acct = acctinfo.bankacctfrom
                    stmtrqs.append(
                        StmtRq(
                            acctid=acct.acctid,
                            acctype=acct.accttype,
                            dtstart=dt["start"],
                            dtend=dt["end"],
                            inctran=args.inctran))
                elif isinstance(acctinfo, CCACCTINFO):
                    acct = acctinfo.ccacctfrom
                    stmtrqs.append(
                        CcStmtRq(
                            acctid=acct.acctid,
                            dtstart=dt["start"],
                            dtend=dt["end"],
                            inctran=args.inctran))
                elif isinstance(acctinfo, INVACCTINFO):
                    acct = acctinfo.invacctfrom
                    stmtrqs.append(
                        InvStmtRq(
                            acctid=acct.acctid,
                            dtstart=dt["start"],
                            dtend=dt["end"],
                            dtasof=dt["asof"],
                            inctran=args.inctran,
                            incoo=args.incoo,
                            incpos=args.incpos,
                            incbal=args.incbal))
    else:
        # Create *STMTRQ for each account specified by config/args
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


def request_profile(args):
    """
    Send PROFRQ
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


def request_acctinfo(args):
    """
    Send ACCTINFORQ
    """

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    print(_request_acctinfo(args, password).read().decode())


def _request_acctinfo(args, password):
    client = init_client(args)

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

    return BytesIO(response)


def request_tax1099(args):
    """
    Send TAX1099RQ
    """
    client = init_client(args)

    # Use dummy password for dummy request
    if args.dryrun:
        password = "{:0<32}".format("anonymous")
    else:
        password = getpass.getpass()

    with client.request_tax1099(args.user,
                                password,
                                *args.years,
                                acctnum=args.acctnum,
                                recid=args.recid,
                                dryrun=args.dryrun,
                                close_elements=not args.unclosedelements,
                                prettyprint=args.pretty,
                                verify_ssl=not args.unsafe
                               ) as f:
        response = f.read()

    print(response.decode())


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


# Map args.request choices to request function
REQUEST_FNS = {"scan": scan_profile,
               "prof": request_profile,
               "acctinfo": request_acctinfo,
               "stmt": request_stmt,
               "tax1099": request_tax1099,
              }


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

    REQUEST_FNS[args.request](args)


if __name__ == "__main__":
    main()
