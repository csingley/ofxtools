# coding: utf-8
""" Unit tests for models.invest """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from decimal import Decimal
from datetime import datetime


# local imports
from ofxtools.models.base import Aggregate, UnknownTagWarning
from ofxtools.models.common import SVCSTATUSES
from ofxtools.models.bank.stmt import INV401KSOURCES
from ofxtools.models.invest import (
    USPRODUCTTYPES,
    INVACCTTYPES,
    INVSUBACCTS,
    LOANPMTFREQUENCIES,
    INVPOS,
    POSDEBT,
    POSMF,
    POSOPT,
    POSOTHER,
    POSSTOCK,
    INVTRANLIST,
    INVPOSLIST,
    INCPOS,
    INVACCTFROM,
    INVACCTTO,
    INVACCTINFO,
    INVBAL,
    INV401KBAL,
    MATCHINFO,
    CONTRIBSECURITY,
    CONTRIBINFO,
    VESTINFO,
    LOANINFO,
    CONTRIBUTIONS,
    WITHDRAWALS,
    EARNINGS,
    YEARTODATE,
    INCEPTODATE,
    PERIODTODATE,
    INV401KSUMMARY,
    INV401K,
    INVSTMTRQ,
    INVSTMTRS,
    INVSTMTTRNRQ,
    INVSTMTTRNRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base
import test_models_bank_stmt as bk_stmt
import test_models_securities as securities
import test_models_i18n as i18n
import test_models_invest_oo as oo


class InvacctfromTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTFROM")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTFROM(brokerid="111000614", acctid="123456789123456789")


class InvaccttoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["BROKERID", "ACCTID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTTO")
        SubElement(root, "BROKERID").text = "111000614"
        SubElement(root, "ACCTID").text = "123456789123456789"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTTO(brokerid="111000614", acctid="123456789123456789")


class InvacctinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "USPRODUCTTYPE", "CHECKING", "SVCSTATUS"]
    optionalElements = ["INVACCTTYPE", "OPTIONLEVEL"]
    oneOfs = {
        "USPRODUCTTYPE": USPRODUCTTYPES,
        "SVCSTATUS": SVCSTATUSES,
        "INVACCTTYPE": INVACCTTYPES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVACCTINFO")
        acctfrom = InvacctfromTestCase.etree
        root.append(acctfrom)
        SubElement(root, "USPRODUCTTYPE").text = "401K"
        SubElement(root, "CHECKING").text = "Y"
        SubElement(root, "SVCSTATUS").text = "ACTIVE"
        SubElement(root, "INVACCTTYPE").text = "INDIVIDUAL"
        SubElement(root, "OPTIONLEVEL").text = "No way Jose"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVACCTINFO(
            invacctfrom=InvacctfromTestCase.aggregate,
            usproducttype="401K",
            checking=True,
            svcstatus="ACTIVE",
            invaccttype="INDIVIDUAL",
            optionlevel="No way Jose",
        )


class IncposTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INCLUDE"]
    optionalElements = ["DTASOF"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INCPOS")
        SubElement(root, "DTASOF").text = "20091122000000.000[+0:UTC]"
        SubElement(root, "INCLUDE").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INCPOS(dtasof=datetime(2009, 11, 22, tzinfo=UTC), include=True)


class InvposlistTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVPOSLIST")
        for invpos in ("Posdebt", "Posmf", "Posopt", "Posother", "Posstock"):
            testCase = "{}TestCase".format(invpos)
            elem = globals()[testCase].etree
            root.append(elem)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVPOSLIST(
            PosdebtTestCase.aggregate,
            PosmfTestCase.aggregate,
            PosoptTestCase.aggregate,
            PosotherTestCase.aggregate,
            PosstockTestCase.aggregate,
        )

    def testListAggregates(cls):
        # INVPOSLIST may only contain
        # ['POSDEBT', 'POSMF', 'POSOPT', 'POSOTHER', 'POSSTOCK', ]
        listaggregates = INVPOSLIST.listaggregates
        cls.assertEqual(len(listaggregates), 5)
        root = cls.etree
        root.append(bk_stmt.StmttrnTestCase.etree)

        with cls.assertWarns(UnknownTagWarning):
            Aggregate.from_etree(root)


class InvbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["AVAILCASH", "MARGINBALANCE", "SHORTBALANCE"]
    optionalElements = ["BUYPOWER"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVBAL")
        SubElement(root, "AVAILCASH").text = "12345.67"
        SubElement(root, "MARGINBALANCE").text = "23456.78"
        SubElement(root, "SHORTBALANCE").text = "34567.89"
        SubElement(root, "BUYPOWER").text = "45678.90"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVBAL(
            availcash=Decimal("12345.67"),
            marginbalance=Decimal("23456.78"),
            shortbalance=Decimal("34567.89"),
            buypower=Decimal("45678.90"),
        )


class Inv401kbalTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TOTAL"]
    optionalElements = [
        "CASHBAL",
        "PRETAX",
        "AFTERTAX",
        "MATCH",
        "PROFITSHARING",
        "ROLLOVER",
        "OTHERVEST",
        "OTHERNONVEST",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INV401KBAL")
        SubElement(root, "CASHBAL").text = "1"
        SubElement(root, "PRETAX").text = "2"
        SubElement(root, "AFTERTAX").text = "3"
        SubElement(root, "MATCH").text = "4"
        SubElement(root, "PROFITSHARING").text = "5"
        SubElement(root, "ROLLOVER").text = "6"
        SubElement(root, "OTHERVEST").text = "7"
        SubElement(root, "OTHERNONVEST").text = "8"
        SubElement(root, "TOTAL").text = "36"
        ballist = bk_stmt.BallistTestCase.etree
        root.append(ballist)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INV401KBAL(
            cashbal=Decimal("1"),
            pretax=Decimal("2"),
            aftertax=Decimal("3"),
            match=Decimal("4"),
            profitsharing=Decimal("5"),
            rollover=Decimal("6"),
            othervest=Decimal("7"),
            othernonvest=Decimal("8"),
            total=Decimal("36"),
            ballist=bk_stmt.BallistTestCase.aggregate,
        )


class MatchinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MATCHPCT"]
    optionalElements = [
        "MAXMATCHAMT",
        "MAXMATCHPCT",
        "STARTOFYEAR",
        "BASEMATCHAMT",
        "BASEMATCHPCT",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MATCHINFO")
        SubElement(root, "MATCHPCT").text = "25.0"
        SubElement(root, "MAXMATCHAMT").text = "5000"
        SubElement(root, "MAXMATCHPCT").text = "20.0"
        SubElement(root, "STARTOFYEAR").text = "19990101000000.000[+0:UTC]"
        SubElement(root, "BASEMATCHAMT").text = "1000"
        SubElement(root, "BASEMATCHPCT").text = "1.0"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MATCHINFO(
            matchpct=Decimal("25.0"),
            maxmatchamt=Decimal("5000"),
            maxmatchpct=Decimal("20.0"),
            startofyear=datetime(1999, 1, 1, tzinfo=UTC),
            basematchamt=Decimal("1000"),
            basematchpct=Decimal("1.0"),
        )


class ContribsecurityTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["SECID"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CONTRIBSECURITY")
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "PRETAXCONTRIBPCT").text = "25.0"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CONTRIBSECURITY(
            secid=securities.SecidTestCase.aggregate, pretaxcontribpct=Decimal("25.0")
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        pretaxcontribpct = Element("PRETAXCONTRIBPCT")
        pretaxcontribpct.text = "25.0"
        pretaxcontribamt = Element("PRETAXCONTRIBAMT")
        pretaxcontribamt.text = "5000"
        aftertaxcontribpct = Element("AFTERTAXCONTRIBPCT")
        aftertaxcontribpct.text = "25.0"
        aftertaxcontribamt = Element("AFTERTAXCONTRIBAMT")
        aftertaxcontribamt.text = "5000"
        matchcontribpct = Element("MATCHCONTRIBPCT")
        matchcontribpct.text = "25.0"
        matchcontribamt = Element("MATCHCONTRIBAMT")
        matchcontribamt.text = "5000"
        profitsharingcontribpct = Element("PROFITSHARINGCONTRIBPCT")
        profitsharingcontribpct.text = "25.0"
        profitsharingcontribamt = Element("PROFITSHARINGCONTRIBAMT")
        profitsharingcontribamt.text = "5000"
        rollovercontribpct = Element("ROLLOVERCONTRIBPCT")
        rollovercontribpct.text = "25.0"
        rollovercontribamt = Element("ROLLOVERCONTRIBAMT")
        rollovercontribamt.text = "5000"
        othervestpct = Element("OTHERVESTPCT")
        othervestpct.text = "25.0"
        othervestamt = Element("OTHERVESTAMT")
        othervestamt.text = "5000"
        othernonvestpct = Element("OTHERNONVESTPCT")
        othernonvestpct.text = "25.0"
        othernonvestamt = Element("OTHERNONVESTAMT")
        othernonvestamt.text = "5000"

        root = Element("CONTRIBSECURITY")
        root.append(securities.SecidTestCase.etree)

        for pct in (
            pretaxcontribpct,
            aftertaxcontribpct,
            matchcontribpct,
            profitsharingcontribpct,
            rollovercontribpct,
            othervestpct,
            othernonvestpct,
        ):
            root.append(pct)
            yield root

        root = Element("CONTRIBSECURITY")
        root.append(securities.SecidTestCase.etree)

        for amt in (
            pretaxcontribamt,
            aftertaxcontribamt,
            matchcontribamt,
            profitsharingcontribamt,
            rollovercontribamt,
            othervestamt,
            othernonvestamt,
        ):
            root.append(amt)
            yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        pretaxcontribpct = Element("PRETAXCONTRIBPCT")
        pretaxcontribpct.text = "25.0"
        pretaxcontribamt = Element("PRETAXCONTRIBAMT")
        pretaxcontribamt.text = "5000"
        aftertaxcontribpct = Element("AFTERTAXCONTRIBPCT")
        aftertaxcontribpct.text = "25.0"
        aftertaxcontribamt = Element("AFTERTAXCONTRIBAMT")
        aftertaxcontribamt.text = "5000"
        matchcontribpct = Element("MATCHCONTRIBPCT")
        matchcontribpct.text = "25.0"
        matchcontribamt = Element("MATCHCONTRIBAMT")
        matchcontribamt.text = "5000"
        profitsharingcontribpct = Element("PROFITSHARINGCONTRIBPCT")
        profitsharingcontribpct.text = "25.0"
        profitsharingcontribamt = Element("PROFITSHARINGCONTRIBAMT")
        profitsharingcontribamt.text = "5000"
        rollovercontribpct = Element("ROLLOVERCONTRIBPCT")
        rollovercontribpct.text = "25.0"
        rollovercontribamt = Element("ROLLOVERCONTRIBAMT")
        rollovercontribamt.text = "5000"
        othervestpct = Element("OTHERVESTPCT")
        othervestpct.text = "25.0"
        othervestamt = Element("OTHERVESTAMT")
        othervestamt.text = "5000"
        othernonvestpct = Element("OTHERNONVESTPCT")
        othernonvestpct.text = "25.0"
        othernonvestamt = Element("OTHERNONVESTAMT")
        othernonvestamt.text = "5000"

        # No sources is invalid
        root = Element("CONTRIBSECURITY")
        root.append(securities.SecidTestCase.etree)
        yield root

        # Mixing *pct and *amt is invalid
        for pct in (
            pretaxcontribpct,
            aftertaxcontribpct,
            matchcontribpct,
            profitsharingcontribpct,
            rollovercontribpct,
            othervestpct,
            othernonvestpct,
        ):
            for amt in (
                pretaxcontribamt,
                aftertaxcontribamt,
                matchcontribamt,
                profitsharingcontribamt,
                rollovercontribamt,
                othervestamt,
                othernonvestamt,
            ):
                root = Element("CONTRIBSECURITY")
                root.append(securities.SecidTestCase.etree)
                root.append(pct)
                root.append(amt)
                yield root


class ContribinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CONTRIBINFO")
        root.append(ContribsecurityTestCase.etree)
        root.append(ContribsecurityTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CONTRIBINFO(
            ContribsecurityTestCase.aggregate, ContribsecurityTestCase.aggregate
        )

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # zero contained CONTRIBSECURITY elmenet is invalid
        root = Element("CONTRIBINFO")
        yield root


class VestinfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["VESTPCT"]
    optionalElements = ["VESTDATE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("VESTINFO")
        SubElement(root, "VESTDATE").text = "20040928000000.000[+0:UTC]"
        SubElement(root, "VESTPCT").text = "29.6671"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return VESTINFO(
            vestdate=datetime(2004, 9, 28, tzinfo=UTC), vestpct=Decimal("29.6671")
        )


class LoaninfoTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["LOANID", "CURRENTLOANBAL", "DTASOF"]
    optionalElements = [
        "LOANDESC",
        "INITIALLOANBAL",
        "LOANSTARTDATE",
        "LOANRATE",
        "LOANPMTAMT",
        "LOANPMTFREQ",
        "LOANPMTSINITIAL",
        "LOANPMTSREMAINING",
        "LOANMATURITYDATE",
        "LOANTOTALPROJINTEREST",
        "LOANINTERESTTODATE",
        "LOANNEXTPMTDATE",
    ]
    oneOfs = {"LOANPMTFREQ": LOANPMTFREQUENCIES}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("LOANINFO")
        SubElement(root, "LOANID").text = "1"
        SubElement(root, "LOANDESC").text = "House down payment"
        SubElement(root, "INITIALLOANBAL").text = "21000"
        SubElement(root, "LOANSTARTDATE").text = "20050701000000.000[+0:UTC]"
        SubElement(root, "CURRENTLOANBAL").text = "12000"
        SubElement(root, "DTASOF").text = "20090701000000.000[+0:UTC]"
        SubElement(root, "LOANRATE").text = "5.0"
        SubElement(root, "LOANPMTAMT").text = "865.34"
        SubElement(root, "LOANPMTFREQ").text = "MONTHLY"
        SubElement(root, "LOANPMTSINITIAL").text = "60"
        SubElement(root, "LOANPMTSREMAINING").text = "12"
        SubElement(root, "LOANMATURITYDATE").text = "20100701000000.000[+0:UTC]"
        SubElement(root, "LOANTOTALPROJINTEREST").text = "13000"
        SubElement(root, "LOANINTERESTTODATE").text = "8500"
        SubElement(root, "LOANNEXTPMTDATE").text = "20090801000000.000[+0:UTC]"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return LOANINFO(
            loanid="1",
            loandesc="House down payment",
            initialloanbal=Decimal("21000"),
            loanstartdate=datetime(2005, 7, 1, tzinfo=UTC),
            currentloanbal=Decimal("12000"),
            dtasof=datetime(2009, 7, 1, tzinfo=UTC),
            loanrate=Decimal("5.0"),
            loanpmtamt=Decimal("865.34"),
            loanpmtfreq="MONTHLY",
            loanpmtsinitial=60,
            loanpmtsremaining=12,
            loanmaturitydate=datetime(2010, 7, 1, tzinfo=UTC),
            loantotalprojinterest=Decimal("13000"),
            loaninteresttodate=Decimal("8500"),
            loannextpmtdate=datetime(2009, 8, 1, tzinfo=UTC),
        )


class ContributionsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TOTAL"]
    optionalElements = [
        "PRETAX",
        "AFTERTAX",
        "MATCH",
        "PROFITSHARING",
        "ROLLOVER",
        "OTHERVEST",
        "OTHERNONVEST",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("CONTRIBUTIONS")
        SubElement(root, "PRETAX").text = "1"
        SubElement(root, "AFTERTAX").text = "2"
        SubElement(root, "MATCH").text = "3"
        SubElement(root, "PROFITSHARING").text = "4"
        SubElement(root, "ROLLOVER").text = "5"
        SubElement(root, "OTHERVEST").text = "6"
        SubElement(root, "OTHERNONVEST").text = "7"
        SubElement(root, "TOTAL").text = "28"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return CONTRIBUTIONS(
            pretax=Decimal("1"),
            aftertax=Decimal("2"),
            match=Decimal("3"),
            profitsharing=Decimal("4"),
            rollover=Decimal("5"),
            othervest=Decimal("6"),
            othernonvest=Decimal("7"),
            total=Decimal("28"),
        )


class WithdrawalsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TOTAL"]
    optionalElements = [
        "PRETAX",
        "AFTERTAX",
        "MATCH",
        "PROFITSHARING",
        "ROLLOVER",
        "OTHERVEST",
        "OTHERNONVEST",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("WITHDRAWALS")
        SubElement(root, "PRETAX").text = "1"
        SubElement(root, "AFTERTAX").text = "2"
        SubElement(root, "MATCH").text = "3"
        SubElement(root, "PROFITSHARING").text = "4"
        SubElement(root, "ROLLOVER").text = "5"
        SubElement(root, "OTHERVEST").text = "6"
        SubElement(root, "OTHERNONVEST").text = "7"
        SubElement(root, "TOTAL").text = "28"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return WITHDRAWALS(
            pretax=Decimal("1"),
            aftertax=Decimal("2"),
            match=Decimal("3"),
            profitsharing=Decimal("4"),
            rollover=Decimal("5"),
            othervest=Decimal("6"),
            othernonvest=Decimal("7"),
            total=Decimal("28"),
        )


class EarningsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["TOTAL"]
    optionalElements = [
        "PRETAX",
        "AFTERTAX",
        "MATCH",
        "PROFITSHARING",
        "ROLLOVER",
        "OTHERVEST",
        "OTHERNONVEST",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("EARNINGS")
        SubElement(root, "PRETAX").text = "1"
        SubElement(root, "AFTERTAX").text = "2"
        SubElement(root, "MATCH").text = "3"
        SubElement(root, "PROFITSHARING").text = "4"
        SubElement(root, "ROLLOVER").text = "5"
        SubElement(root, "OTHERVEST").text = "6"
        SubElement(root, "OTHERNONVEST").text = "7"
        SubElement(root, "TOTAL").text = "28"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return EARNINGS(
            pretax=Decimal("1"),
            aftertax=Decimal("2"),
            match=Decimal("3"),
            profitsharing=Decimal("4"),
            rollover=Decimal("5"),
            othervest=Decimal("6"),
            othernonvest=Decimal("7"),
            total=Decimal("28"),
        )


class YeartodateTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTSTART", "DTEND"]
    optionalElements = ["CONTRIBUTIONS", "WITHDRAWALS", "EARNINGS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("YEARTODATE")
        SubElement(root, "DTSTART").text = "20010101000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20011231000000.000[+0:UTC]"
        root.append(ContributionsTestCase.etree)
        root.append(WithdrawalsTestCase.etree)
        root.append(EarningsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return YEARTODATE(
            dtstart=datetime(2001, 1, 1, tzinfo=UTC),
            dtend=datetime(2001, 12, 31, tzinfo=UTC),
            contributions=ContributionsTestCase.aggregate,
            withdrawals=WithdrawalsTestCase.aggregate,
            earnings=EarningsTestCase.aggregate,
        )


class InceptodateTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTSTART", "DTEND"]
    optionalElements = ["CONTRIBUTIONS", "WITHDRAWALS", "EARNINGS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INCEPTODATE")
        SubElement(root, "DTSTART").text = "20010101000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20011231000000.000[+0:UTC]"
        root.append(ContributionsTestCase.etree)
        root.append(WithdrawalsTestCase.etree)
        root.append(EarningsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INCEPTODATE(
            dtstart=datetime(2001, 1, 1, tzinfo=UTC),
            dtend=datetime(2001, 12, 31, tzinfo=UTC),
            contributions=ContributionsTestCase.aggregate,
            withdrawals=WithdrawalsTestCase.aggregate,
            earnings=EarningsTestCase.aggregate,
        )


class PeriodtodateTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTSTART", "DTEND"]
    optionalElements = ["CONTRIBUTIONS", "WITHDRAWALS", "EARNINGS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("PERIODTODATE")
        SubElement(root, "DTSTART").text = "20010101000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20011231000000.000[+0:UTC]"
        root.append(ContributionsTestCase.etree)
        root.append(WithdrawalsTestCase.etree)
        root.append(EarningsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PERIODTODATE(
            dtstart=datetime(2001, 1, 1, tzinfo=UTC),
            dtend=datetime(2001, 12, 31, tzinfo=UTC),
            contributions=ContributionsTestCase.aggregate,
            withdrawals=WithdrawalsTestCase.aggregate,
            earnings=EarningsTestCase.aggregate,
        )


class Inv401ksummaryTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["YEARTODATE"]
    optionalElements = ["INCEPTODATE", "PERIODTODATE"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INV401KSUMMARY")
        root.append(YeartodateTestCase.etree)
        root.append(InceptodateTestCase.etree)
        root.append(PeriodtodateTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INV401KSUMMARY(
            yeartodate=YeartodateTestCase.aggregate,
            inceptodate=InceptodateTestCase.aggregate,
            periodtodate=PeriodtodateTestCase.aggregate,
        )


class Inv401kTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["EMPLOYERNAME"]
    optionalElements = [
        "PLANID",
        "PLANJOINDATE",
        "EMPLOYERCONTACTINFO",
        "BROKERCONTACTINFO",
        "DEFERPCTPRETAX",
        "DEFERPCTAFTERTAX",
        "MATCHINFO",
        "CONTRIBINFO",
        "CURRENTVESTPCT",
        "INV401KSUMMARY",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INV401K")
        SubElement(root, "EMPLOYERNAME").text = "V2 Rockets GmbH"
        SubElement(root, "PLANID").text = "1"
        SubElement(root, "PLANJOINDATE").text = "20040707000000.000[+0:UTC]"
        SubElement(root, "EMPLOYERCONTACTINFO").text = "plan_help@v2.com"
        SubElement(root, "BROKERCONTACTINFO").text = "plan_help@dch.com"
        SubElement(root, "DEFERPCTPRETAX").text = "15.0"
        SubElement(root, "DEFERPCTAFTERTAX").text = "15.0"
        root.append(MatchinfoTestCase.etree)
        root.append(ContribinfoTestCase.etree)
        SubElement(root, "CURRENTVESTPCT").text = "75.0"
        root.append(VestinfoTestCase.etree)
        root.append(VestinfoTestCase.etree)
        root.append(LoaninfoTestCase.etree)
        root.append(LoaninfoTestCase.etree)
        root.append(Inv401ksummaryTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INV401K(
            VestinfoTestCase.aggregate,
            VestinfoTestCase.aggregate,
            LoaninfoTestCase.aggregate,
            LoaninfoTestCase.aggregate,
            employername="V2 Rockets GmbH",
            planid="1",
            planjoindate=datetime(2004, 7, 7, tzinfo=UTC),
            employercontactinfo="plan_help@v2.com",
            brokercontactinfo="plan_help@dch.com",
            deferpctpretax=Decimal("15.0"),
            deferpctaftertax=Decimal("15.0"),
            matchinfo=MatchinfoTestCase.aggregate,
            contribinfo=ContribinfoTestCase.aggregate,
            currentvestpct=Decimal("75.0"),
            inv401ksummary=Inv401ksummaryTestCase.aggregate,
        )


class InvposTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "SECID",
        "HELDINACCT",
        "POSTYPE",
        "UNITS",
        "UNITPRICE",
        "MKTVAL",
        "DTPRICEASOF",
    ]
    optionalElements = ["AVGCOSTBASIS", "CURRENCY", "MEMO", "INV401KSOURCE"]
    oneOfs = {
        "HELDINACCT": INVSUBACCTS,
        "POSTYPE": ("SHORT", "LONG"),
        "INV401KSOURCE": INV401KSOURCES,
    }

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVPOS")
        root.append(securities.SecidTestCase.etree)
        SubElement(root, "HELDINACCT").text = "MARGIN"
        SubElement(root, "POSTYPE").text = "LONG"
        SubElement(root, "UNITS").text = "100"
        SubElement(root, "UNITPRICE").text = "90"
        SubElement(root, "MKTVAL").text = "9000"
        SubElement(root, "AVGCOSTBASIS").text = "85"
        SubElement(root, "DTPRICEASOF").text = "20130630000000.000[+0:UTC]"
        root.append(i18n.CurrencyTestCase.etree)
        SubElement(root, "MEMO").text = "Marked to myth"
        SubElement(root, "INV401KSOURCE").text = "PROFITSHARING"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVPOS(
            secid=securities.SecidTestCase.aggregate,
            heldinacct="MARGIN",
            postype="LONG",
            units=Decimal("100"),
            unitprice=Decimal("90"),
            mktval=Decimal("9000"),
            avgcostbasis=Decimal("85"),
            dtpriceasof=datetime(2013, 6, 30, tzinfo=UTC),
            currency=i18n.CurrencyTestCase.aggregate,
            memo="Marked to myth",
            inv401ksource="PROFITSHARING",
        )


class PosdebtTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSDEBT")
        invpos = InvposTestCase.etree
        root.append(invpos)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSDEBT(invpos=InvposTestCase.aggregate)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosmfTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV", "REINVCG"]
    oneOf = {"REINVDIV": ("Y", "N")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSMF")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        SubElement(root, "REINVCG").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSMF(
            invpos=InvposTestCase.aggregate,
            unitsstreet=Decimal("200"),
            unitsuser=Decimal("300"),
            reinvdiv=False,
            reinvcg=True,
        )

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosoptTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["SECURED"]
    oneOfs = {"SECURED": ("NAKED", "COVERED")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSOPT")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "SECURED").text = "COVERED"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSOPT(invpos=InvposTestCase.aggregate, secured="COVERED")

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosotherTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVPOS"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSOTHER")
        invpos = InvposTestCase.etree
        root.append(invpos)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSOTHER(invpos=InvposTestCase.aggregate)

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class PosstockTestCase(unittest.TestCase, base.TestAggregate):
    """ """

    __test__ = True

    requiredElements = ["INVPOS"]
    optionalElements = ["UNITSSTREET", "UNITSUSER", "REINVDIV"]
    oneOfs = {"REINVDIV": ("Y", "N")}

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("POSSTOCK")
        invpos = InvposTestCase.etree
        root.append(invpos)
        SubElement(root, "UNITSSTREET").text = "200"
        SubElement(root, "UNITSUSER").text = "300"
        SubElement(root, "REINVDIV").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return POSSTOCK(
            invpos=InvposTestCase.aggregate,
            unitsstreet=Decimal("200"),
            unitsuser=Decimal("300"),
            reinvdiv=False,
        )

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertEqual(instance.uniqueid, instance.invpos.secid.uniqueid)
        cls.assertEqual(instance.uniqueidtype, instance.invpos.secid.uniqueidtype)
        cls.assertEqual(instance.heldinacct, instance.invpos.heldinacct)
        cls.assertEqual(instance.postype, instance.invpos.postype)
        cls.assertEqual(instance.units, instance.invpos.units)
        cls.assertEqual(instance.unitprice, instance.invpos.unitprice)
        cls.assertEqual(instance.mktval, instance.invpos.mktval)
        cls.assertEqual(instance.dtpriceasof, instance.invpos.dtpriceasof)
        cls.assertEqual(instance.cursym, instance.invpos.currency.cursym)
        cls.assertEqual(instance.currate, instance.invpos.currency.currate)


class InvstmtrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["INVACCTFROM", "INCOO", "INCPOS", "INCBAL"]
    optionalElements = ["INCTRAN", "INC401K", "INC401KBAL", "INCTRANIMG"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTRQ")
        root.append(InvacctfromTestCase.etree)
        root.append(bk_stmt.InctranTestCase.etree)
        SubElement(root, "INCOO").text = "N"
        root.append(IncposTestCase.etree)
        SubElement(root, "INCBAL").text = "N"
        SubElement(root, "INC401K").text = "Y"
        SubElement(root, "INC401KBAL").text = "N"
        SubElement(root, "INCTRANIMG").text = "Y"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTRQ(
            invacctfrom=InvacctfromTestCase.aggregate,
            inctran=bk_stmt.InctranTestCase.aggregate,
            incoo=False,
            incpos=IncposTestCase.aggregate,
            incbal=False,
            inc401k=True,
            inc401kbal=False,
            inctranimg=True,
        )


class InvstmtrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["DTASOF", "CURDEF", "INVACCTFROM"]
    optionalElements = [
        "INVTRANLIST",
        "INVPOSLIST",
        "INVBAL",
        "INVOOLIST",
        "MKTGINFO",
        "INV401K",
        "INV401KBAL",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVSTMTRS")
        SubElement(root, "DTASOF").text = "20010530000000.000[+0:UTC]"
        SubElement(root, "CURDEF").text = "USD"
        root.append(InvacctfromTestCase.etree)
        root.append(InvtranlistTestCase.etree)
        root.append(InvposlistTestCase.etree)
        root.append(InvbalTestCase.etree)
        root.append(oo.InvoolistTestCase.etree)
        SubElement(root, "MKTGINFO").text = "Get Free Stuff NOW!!"
        root.append(Inv401kTestCase.etree)
        root.append(Inv401kbalTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTRS(
            dtasof=datetime(2001, 5, 30, tzinfo=UTC),
            curdef="USD",
            invacctfrom=InvacctfromTestCase.aggregate,
            invtranlist=InvtranlistTestCase.aggregate,
            invposlist=InvposlistTestCase.aggregate,
            invbal=InvbalTestCase.aggregate,
            invoolist=oo.InvoolistTestCase.aggregate,
            inv401k=Inv401kTestCase.aggregate,
            inv401kbal=Inv401kbalTestCase.aggregate,
            mktginfo="Get Free Stuff NOW!!",
        )

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        cls.assertIs(instance.account, instance.invacctfrom)
        cls.assertIs(instance.balances, instance.invbal)
        cls.assertIs(instance.transactions, instance.invtranlist)
        cls.assertIs(instance.positions, instance.invposlist)


class InvstmttrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = InvstmtrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            invstmtrq=InvstmtrqTestCase.aggregate,
        )


class InvstmttrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = InvstmtrsTestCase

    def testPropertyAliases(cls):
        instance = Aggregate.from_etree(cls.etree)
        stmt = instance.statement
        cls.assertIsInstance(stmt, INVSTMTRS)

    @classproperty
    @classmethod
    def aggregate(cls):
        return INVSTMTTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            invstmtrs=InvstmtrsTestCase.aggregate,
        )


class InvtranlistTestCase(unittest.TestCase, base.TranlistTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def transactions(cls):
        # Avoid circular imports in the global scope
        import test_models_invest_transactions as test_txs

        return (
            test_txs.InvbanktranTestCase,
            test_txs.BuydebtTestCase,
            test_txs.BuymfTestCase,
            test_txs.BuyoptTestCase,
            test_txs.BuyotherTestCase,
            test_txs.BuystockTestCase,
            test_txs.ClosureoptTestCase,
            test_txs.IncomeTestCase,
            test_txs.InvexpenseTestCase,
            test_txs.JrnlfundTestCase,
            test_txs.JrnlsecTestCase,
            test_txs.MargininterestTestCase,
            test_txs.ReinvestTestCase,
            test_txs.RetofcapTestCase,
            test_txs.SelldebtTestCase,
            test_txs.SellmfTestCase,
            test_txs.SelloptTestCase,
            test_txs.SellotherTestCase,
            test_txs.SellstockTestCase,
            test_txs.SplitTestCase,
            test_txs.TransferTestCase,
        )

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("INVTRANLIST")
        SubElement(root, "DTSTART").text = "20160101000000.000[+0:UTC]"
        SubElement(root, "DTEND").text = "20161231000000.000[+0:UTC]"
        for tx in cls.transactions:
            root.append(tx.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        txs = [tx.aggregate for tx in cls.transactions]
        return INVTRANLIST(
            *txs,
            dtstart=datetime(2016, 1, 1, tzinfo=UTC),
            dtend=datetime(2016, 12, 31, tzinfo=UTC),
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # Multiple contained aggregates of different types
            for transaction in cls.transactions:
                root.append(transaction.etree)
                yield root
                root.append(transaction.etree)
                yield root


if __name__ == "__main__":
    unittest.main()
