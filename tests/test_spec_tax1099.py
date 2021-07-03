# coding: utf-8
"""
Examples - OFX Tax Extensions (Form 1099)
"""
# stdlib imports
import unittest
from datetime import datetime
from decimal import Decimal

# local imports
from ofxtools import models
from ofxtools.utils import classproperty, UTC

# test imports
import base


# Common aggregates used across tests
STATUS = models.STATUS(code=0, severity="INFO")


SONRS = models.SONRS(
    status=STATUS,
    dtserver=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
    language="ENG",
    dtprofup=datetime(2004, 10, 29, 10, 10, 3, tzinfo=UTC),
    dtacctup=datetime(2004, 10, 29, 10, 10, 3, tzinfo=UTC),
    fi=models.FI(org="NCH", fid="1001"),
)
SIGNONMSGSRSV1 = models.SIGNONMSGSRSV1(sonrs=SONRS)

PAYERADDR = models.PAYERADDR(
    payername1="Broker One",
    addr1="1111 MTV",
    city="PAYER CITY",
    state="CA",
    postalcode="12345-6789",
)


class Tax1099BTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Tax Extensions Section 2.2.11"""

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20051029101003.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[+0:UTC]</DTPROFUP>
                <DTACCTUP>20041029101003.000[+0:UTC]</DTACCTUP>
                <FI>
                    <ORG>NCH</ORG>
                    <FID>1001</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
        <TAX1099MSGSRSV1>
            <TAX1099TRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <TAX1099RS>
                    <TAX1099B_V100>
                        <SRVRTID>IMASRVRTID</SRVRTID>
                        <TAXYEAR>2018</TAXYEAR>
                        <EXTDBINFO_V100>
                            <PROCSUM_V100>
                            <FORM8949CODE>A</FORM8949CODE>
                            <ADJCODE>M</ADJCODE>
                            <SUMCOSTBASIS>1050.33</SUMCOSTBASIS>
                            <SUMSALESPR>1140.00</SUMSALESPR>
                            </PROCSUM_V100>
                                <PROCSUM_V100>
                                <FORM8949CODE>A</FORM8949CODE>
                                <ADJCODE>MW</ADJCODE>
                                <SUMCOSTBASIS>1270.00</SUMCOSTBASIS>
                                <SUMSALESPR>1200.00</SUMSALESPR>
                                <SUMADJAMT>100.00</SUMADJAMT>
                                <SUMDESCRIPTION> SHORT TERM WASH SALES</SUMDESCRIPTION>
                            </PROCSUM_V100>
                            <PROCDET_V100>
                                <DTAQD>20170910</DTAQD>
                                <DTSALE>20180618</DTSALE>
                                <SALEDESCRIPTION>12.3 DFA TAX MGD FUND</SALEDESCRIPTION>
                                <COSTBASIS>350.11</COSTBASIS>
                                <SALESPR>380.00</SALESPR>
                                <LONGSHORT>SHORT</LONGSHORT>
                                <NONCOVEREDSECURITY>N</NONCOVEREDSECURITY>
                                <BASISNOTSHOWN>Y</BASISNOTSHOWN>
                            </PROCDET_V100>
                            <PROCDET_V100>
                                <FORM8949CODE>A</FORM8949CODE>
                                <DTAQD>20170910</DTAQD>
                                <DTSALE>20180618</DTSALE>
                                <SALEDESCRIPTION>12.3 DFA TAX MGD FUND</SALEDESCRIPTION>
                                <COSTBASIS>350.11</COSTBASIS>
                                <SALESPR>380.00</SALESPR>
                            </PROCDET_V100>
                            <PROCDET_V100>
                                <FORM8949CODE>A</FORM8949CODE>
                                <DTAQD>20170910</DTAQD>
                                <DTSALE>20180618</DTSALE>
                                <SALEDESCRIPTION>12.3 DFA TAX MGD FUND</SALEDESCRIPTION>
                                <COSTBASIS>350.11</COSTBASIS>
                                <SALESPR>380.00</SALESPR>
                                <LONGSHORT>SHORT</LONGSHORT>
                            </PROCDET_V100>
                            <PROCDET_V100>
                                <FORM8949CODE>D</FORM8949CODE>
                                <DTAQD>20130910</DTAQD>
                                <DTSALE>20180618</DTSALE>
                                <SALEDESCRIPTION>14.3 DFA TAX FUND</SALEDESCRIPTION>
                                <COSTBASIS>350.11</COSTBASIS>
                                <SALESPR>238.00</SALESPR>
                            </PROCDET_V100>
                            <PROCDET_V100>
                                <FORM8949CODE>A</FORM8949CODE>
                                <DTAQD>20180121</DTAQD>
                                <DTSALE>20180201</DTSALE>
                                <SECNAME>Security #1</SECNAME>
                                <NUMSHRS>125</NUMSHRS>
                                <COSTBASIS>1050.00</COSTBASIS>
                                <SALESPR>1000.00</SALESPR>
                                <WASHSALE>Y</WASHSALE>
                                <WASHSALELOSSDISALLOWED>50.00</WASHSALELOSSDISALLOWED>
                            </PROCDET_V100>
                            <PROCDET_V100>
                                <FORM8949CODE>A</FORM8949CODE>
                                <DTAQD>20180121</DTAQD>
                                <DTSALE>20180201</DTSALE>
                                <SECNAME>Security #3</SECNAME>
                                <NUMSHRS>200</NUMSHRS>
                                <COSTBASIS>220.00</COSTBASIS>
                                <SALESPR>200.00</SALESPR>
                                <WASHSALELOSSDISALLOWED>50.00</WASHSALELOSSDISALLOWED>
                            </PROCDET_V100>
                        </EXTDBINFO_V100>
                        <PAYERADDR>
                            <PAYERNAME1>Broker One</PAYERNAME1>
                            <ADDR1>1111 MTV</ADDR1>
                            <CITY>PAYER CITY</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>12345-6789</POSTALCODE>
                        </PAYERADDR>
                        <PAYERID>012345678</PAYERID>
                        <RECADDR>
                            <RECNAME1>Diane Jones</RECNAME1>
                            <ADDR1>7535 Santa Fe Rd</ADDR1>
                            <CITY>Recipient City</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>9876-54321</POSTALCODE>
                        </RECADDR>
                        <RECID>****56789</RECID>
                        <RECACCT>1000002222</RECACCT>
                    </TAX1099B_V100>
                </TAX1099RS>
            </TAX1099TRNRS>
        </TAX1099MSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        procsum0 = models.PROCSUM_V100(
            form8949code="A",
            adjcode="M",
            sumcostbasis=Decimal("1050.33"),
            sumsalespr=Decimal("1140.00"),
        )

        procsum1 = models.PROCSUM_V100(
            form8949code="A",
            adjcode="MW",
            sumcostbasis=Decimal("1270.00"),
            sumsalespr=Decimal("1200.00"),
            sumadjamt=Decimal("100.00"),
            sumdescription="SHORT TERM WASH SALES",
        )

        procdet0 = models.PROCDET_V100(
            dtaqd=datetime(2017, 9, 10, tzinfo=UTC),
            dtsale=datetime(2018, 6, 18, tzinfo=UTC),
            saledescription="12.3 DFA TAX MGD FUND",
            costbasis=Decimal("350.11"),
            salespr=Decimal("380.00"),
            longshort="SHORT",
            noncoveredsecurity=False,
            basisnotshown=True,
        )

        procdet1 = models.PROCDET_V100(
            form8949code="A",
            dtaqd=datetime(2017, 9, 10, tzinfo=UTC),
            dtsale=datetime(2018, 6, 18, tzinfo=UTC),
            saledescription="12.3 DFA TAX MGD FUND",
            costbasis=Decimal("350.11"),
            salespr=Decimal("380.00"),
        )

        procdet2 = models.PROCDET_V100(
            form8949code="A",
            dtaqd=datetime(2017, 9, 10, tzinfo=UTC),
            dtsale=datetime(2018, 6, 18, tzinfo=UTC),
            saledescription="12.3 DFA TAX MGD FUND",
            costbasis=Decimal("350.11"),
            salespr=Decimal("380.00"),
            longshort="SHORT",
        )

        procdet3 = models.PROCDET_V100(
            form8949code="D",
            dtaqd=datetime(2013, 9, 10, tzinfo=UTC),
            dtsale=datetime(2018, 6, 18, tzinfo=UTC),
            saledescription="14.3 DFA TAX FUND",
            costbasis=Decimal("350.11"),
            salespr=Decimal("238.00"),
        )

        procdet4 = models.PROCDET_V100(
            form8949code="A",
            dtaqd=datetime(2018, 1, 21, tzinfo=UTC),
            dtsale=datetime(2018, 2, 1, tzinfo=UTC),
            secname="Security #1",
            numshrs=Decimal("125"),
            costbasis=Decimal("1050.00"),
            salespr=Decimal("1000.00"),
            washsale=True,
            washsalelossdisallowed=Decimal("50.00"),
        )

        procdet5 = models.PROCDET_V100(
            form8949code="A",
            dtaqd=datetime(2018, 1, 21, tzinfo=UTC),
            dtsale=datetime(2018, 2, 1, tzinfo=UTC),
            secname="Security #3",
            numshrs=Decimal("200"),
            costbasis=Decimal("220.00"),
            salespr=Decimal("200.00"),
            washsalelossdisallowed=Decimal("50.00"),
        )

        recaddr = models.RECADDR(
            recname1="Diane Jones",
            addr1="7535 Santa Fe Rd",
            city="Recipient City",
            state="CA",
            postalcode="9876-54321",
        )

        extdbinfo = models.EXTDBINFO_V100(
            procsum0,
            procsum1,
            procdet0,
            procdet1,
            procdet2,
            procdet3,
            procdet4,
            procdet5,
        )

        tax1099b = models.TAX1099B_V100(
            srvrtid="IMASRVRTID",
            taxyear=2018,
            extdbinfo_v100=extdbinfo,
            payeraddr=PAYERADDR,
            payerid="012345678",
            recaddr=recaddr,
            recid="****56789",
            recacct="1000002222",
        )

        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            tax1099msgsrsv1=models.TAX1099MSGSRSV1(
                models.TAX1099TRNRS(
                    trnuid="1001", status=STATUS, tax1099rs=models.TAX1099RS(tax1099b)
                )
            ),
        )


class FidirectdepositinfoTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Sample request

    OFX Tax Extensions Section 2.3.1
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20051029101003.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[+0:UTC]</DTPROFUP>
                <DTACCTUP>20041029101003.000[+0:UTC]</DTACCTUP>
                <FI>
                    <ORG>NCH</ORG>
                    <FID>1001</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
        <TAX1099MSGSRSV1>
            <TAX1099TRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <TAX1099RS>
                    <RECID>111423815</RECID>
                    <FIDIRECTDEPOSITINFO>
                        <FINAME_DIRECTDEPOSIT>Your FI name here</FINAME_DIRECTDEPOSIT>
                        <FIROUTINGNUM>122000247</FIROUTINGNUM>
                        <FIACCTNUM>080808080808</FIACCTNUM>
                    </FIDIRECTDEPOSITINFO>
                    <FIDIRECTDEPOSITINFO>
                        <FINAME_DIRECTDEPOSIT>Your FI name here</FINAME_DIRECTDEPOSIT>
                        <FIROUTINGNUM>933000247</FIROUTINGNUM>
                        <FIACCTNUM>090809080808</FIACCTNUM>
                        <FIACCOUNTNICKNAME>James’ nest egg</FIACCOUNTNICKNAME>
                    </FIDIRECTDEPOSITINFO>
                    <TAX1099B_V100>
                        <SRVRTID>IMASRVRTID</SRVRTID>
                        <TAXYEAR>2018</TAXYEAR>
                        <PAYERADDR>
                            <PAYERNAME1>Broker One</PAYERNAME1>
                            <ADDR1>1111 MTV</ADDR1>
                            <CITY>PAYER CITY</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>12345-6789</POSTALCODE>
                        </PAYERADDR>
                        <PAYERID>012345678</PAYERID>
                        <RECID>****56789</RECID>
                    </TAX1099B_V100>
                </TAX1099RS>
            </TAX1099TRNRS>
        </TAX1099MSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        tax1099b = models.TAX1099B_V100(
            srvrtid="IMASRVRTID",
            taxyear=2018,
            payeraddr=PAYERADDR,
            payerid="012345678",
            recid="****56789",
        )

        dd0 = models.FIDIRECTDEPOSITINFO(
            finame_directdeposit="Your FI name here",
            firoutingnum="122000247",
            fiacctnum="080808080808",
        )
        dd1 = models.FIDIRECTDEPOSITINFO(
            finame_directdeposit="Your FI name here",
            firoutingnum="933000247",
            fiacctnum="090809080808",
            fiaccountnickname="James’ nest egg",
        )

        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            tax1099msgsrsv1=models.TAX1099MSGSRSV1(
                models.TAX1099TRNRS(
                    trnuid="1001",
                    status=STATUS,
                    tax1099rs=models.TAX1099RS(dd0, dd1, tax1099b, recid="111423815"),
                )
            ),
        )


class Tax1099RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Sample request

    OFX Tax Extensions Section 2.3.1
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
        <SONRQ>
            <DTCLIENT>20180130132510</DTCLIENT>
            <USERID>123456789</USERID>
            <USERPASS>money</USERPASS>
            <LANGUAGE>ENG</LANGUAGE>
            <APPID>TTWin</APPID>
            <APPVER>2018</APPVER>
        </SONRQ>
        </SIGNONMSGSRQV1>
        <TAX1099MSGSRQV1>
            <TAX1099TRNRQ>
            <TRNUID>12345</TRNUID>
            <TAX1099RQ>
                <RECID>123456789</RECID>
                <TAXYEAR>2018</TAXYEAR>
            </TAX1099RQ>
            </TAX1099TRNRQ>
        </TAX1099MSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        sonrq = models.SONRQ(
            dtclient=datetime(2018, 1, 30, 13, 25, 10, tzinfo=UTC),
            userid="123456789",
            userpass="money",
            language="ENG",
            appid="TTWin",
            appver="2018",
        )

        trnrq = models.TAX1099TRNRQ(
            trnuid="12345", tax1099rq=models.TAX1099RQ(2018, recid="123456789")
        )

        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(sonrq=sonrq),
            tax1099msgsrqv1=models.TAX1099MSGSRQV1(trnrq),
        )


class Tax1099ResponseDeniedTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Sample response with unsuccessful sign-on due to invalid credentials.

    OFX Tax Extensions Section 2.3.2
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20180127132510</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
            </SONRS>
        </SIGNONMSGSRSV1>
        <TAX1099MSGSRSV1>
            <TAX1099TRNRS>
                <TRNUID>12345</TRNUID>
                <STATUS>
                    <CODE>14501</CODE>
                    <SEVERITY>ERROR</SEVERITY>
                    <MESSAGE>1099 Forms Unavailable for User</MESSAGE>
                </STATUS>
            </TAX1099TRNRS>
        </TAX1099MSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        sonrs = models.SONRS(
            status=STATUS,
            dtserver=datetime(2018, 1, 27, 13, 25, 10, tzinfo=UTC),
            language="ENG",
        )
        trnrs = models.TAX1099TRNRS(
            trnuid="12345",
            status=models.STATUS(
                code="14501",
                severity="ERROR",
                message="1099 Forms Unavailable for User",
            ),
        )
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(sonrs=sonrs),
            tax1099msgsrsv1=models.TAX1099MSGSRSV1(trnrs),
        )


class Tax1099ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Sample response with successful sign-on and two 1099 forms returned:
    one 1099-INT and one 1099-DIV.

    OFX Tax Extensions Section 2.3.3
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20180130132510</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
            </SONRS>
        </SIGNONMSGSRSV1>
        <TAX1099MSGSRSV1>
            <TAX1099TRNRS>
                <TRNUID>12345</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <TAX1099RS>
                    <RECID>123456789</RECID>
                    <TAX1099INT_V100>
                        <SRVRTID>2345</SRVRTID>
                        <TAXYEAR>2018</TAXYEAR>
                        <INTINCOME>3000.12</INTINCOME>
                        <FEDTAXWH>200.56</FEDTAXWH>
                        <PAYERADDR>
                            <PAYERNAME1>Charles Schwab</PAYERNAME1>
                            <ADDR1>123 Schwab Way</ADDR1>
                            <CITY>Philadelphia</CITY>
                            <STATE>PA</STATE>
                            <POSTALCODE>26433</POSTALCODE>
                        </PAYERADDR>
                        <PAYERID>2331243</PAYERID>
                        <RECADDR>
                            <RECNAME1>Mr Investor</RECNAME1>
                            <ADDR1>464 Investor Way</ADDR1>
                            <CITY>Mountain View</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>96433</POSTALCODE>
                        </RECADDR>
                        <RECID>123456789</RECID>
                        <RECACCT>12345</RECACCT>
                    </TAX1099INT_V100>
                    <TAX1099DIV_V100>
                        <SRVRTID>2346</SRVRTID>
                        <TAXYEAR>2018</TAXYEAR>
                        <TOTCAPGAIN>34000</TOTCAPGAIN>
                        <P28GAIN>34000</P28GAIN>
                        <PAYERADDR>
                            <PAYERNAME1>Charles Schwab</PAYERNAME1>
                            <ADDR1>123 Schwab Way</ADDR1>
                            <CITY>Philadelphia</CITY>
                            <STATE>PA</STATE>
                            <POSTALCODE>26433</POSTALCODE>
                        </PAYERADDR>
                        <PAYERID>2331243</PAYERID>
                        <RECADDR>
                            <RECNAME1>Mr Investor</RECNAME1>
                            <ADDR1>464 Investor Way</ADDR1>
                            <CITY>Mountain View</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>96433</POSTALCODE>
                        </RECADDR>
                        <RECID>123456789</RECID>
                        <RECACCT>12345</RECACCT>
                    </TAX1099DIV_V100>
                </TAX1099RS>
            </TAX1099TRNRS>
        </TAX1099MSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        sonrs = models.SONRS(
            status=STATUS,
            dtserver=datetime(2018, 1, 30, 13, 25, 10, tzinfo=UTC),
            language="ENG",
        )

        payeraddr = models.PAYERADDR(
            payername1="Charles Schwab",
            addr1="123 Schwab Way",
            city="Philadelphia",
            state="PA",
            postalcode="26433",
        )

        recaddr = models.RECADDR(
            recname1="Mr Investor",
            addr1="464 Investor Way",
            city="Mountain View",
            state="CA",
            postalcode="96433",
        )

        tax1099int = models.TAX1099INT_V100(
            srvrtid="2345",
            taxyear=2018,
            intincome=Decimal("3000.12"),
            fedtaxwh=Decimal("200.56"),
            payeraddr=payeraddr,
            payerid="2331243",
            recaddr=recaddr,
            recid="123456789",
            recacct="12345",
        )

        tax1099div = models.TAX1099DIV_V100(
            srvrtid="2346",
            taxyear=2018,
            totcapgain=Decimal("34000"),
            p28gain=Decimal("34000"),
            payeraddr=payeraddr,
            payerid="2331243",
            recaddr=recaddr,
            recid="123456789",
            recacct="12345",
        )

        trnrs = models.TAX1099TRNRS(
            trnuid="12345",
            status=STATUS,
            tax1099rs=models.TAX1099RS(tax1099int, tax1099div, recid="123456789"),
        )

        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(sonrs=sonrs),
            tax1099msgsrsv1=models.TAX1099MSGSRSV1(trnrs),
        )


if __name__ == "__main__":
    unittest.main()
