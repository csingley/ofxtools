# coding: utf-8
"""
Examples - OFX Section 13.11
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
SONRQ = models.SONRQ(
    dtclient=datetime(2005, 10, 29, 10, 10, tzinfo=UTC),
    userid="12345",
    userpass="MyPassword",
    language="ENG",
    fi=models.FI(org="NCH", fid="1001"),
    appid="MyApp",
    appver="0500",
)
SIGNONMSGSRQV1 = models.SIGNONMSGSRQV1(sonrq=SONRQ)


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


INVACCTFROM = models.INVACCTFROM(brokerid="121099999", acctid="999988")


STOCK_SECID = models.SECID(uniqueid="123456789", uniqueidtype="CUSIP")
OPT_SECID = models.SECID(uniqueid="000342222", uniqueidtype="CUSIP")
MF_SECID = models.SECID(uniqueid="744316100", uniqueidtype="CUSIP")


class InvstmtRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 13.11

    This example is for a user who requests an investment statement download
    for a single account
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>NCH</ORG>
                    <FID>1001</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>0500</APPVER>
            </SONRQ>
        </SIGNONMSGSRQV1>
        <INVSTMTMSGSRQV1>
            <INVSTMTTRNRQ>
                <TRNUID>1001</TRNUID>
                <INVSTMTRQ>
                    <INVACCTFROM>
                        <BROKERID>121099999</BROKERID>
                        <ACCTID>999988</ACCTID>
                    </INVACCTFROM>
                    <INCTRAN>
                        <DTSTART>20050824130105.000[+0:UTC]</DTSTART>
                        <INCLUDE>Y</INCLUDE>
                    </INCTRAN>
                    <INCOO>Y</INCOO>
                    <INCPOS>
                        <INCLUDE>Y</INCLUDE>
                    </INCPOS>
                    <INCBAL>Y</INCBAL>
                </INVSTMTRQ>
            </INVSTMTTRNRQ>
        </INVSTMTMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.INVSTMTRQ(
            invacctfrom=INVACCTFROM,
            inctran=models.INCTRAN(
                dtstart=datetime(2005, 8, 24, 13, 1, 5, tzinfo=UTC), include=True
            ),
            incoo=True,
            incpos=models.INCPOS(include=True),
            incbal=True,
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1,
            invstmtmsgsrqv1=models.INVSTMTMSGSRQV1(
                models.INVSTMTTRNRQ(trnuid="1001", invstmtrq=rq)
            ),
        )


class InvstmtResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 13.11

    A typical server response:
    This user has one investment transaction, one bank transaction, one open
    order, two position entries, and one balance entry. The user deposits some
    money and buys shares in Acme. The user has an open limit order to buy 100
    shares of Hackson Unlimited at $50/sh. The holdings show the user already
    had 100 shares of Acme and now has 200 shares. The user also has one option
    contract to sell Lucky Airlines shares, bought before this download.
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
        <INVSTMTMSGSRSV1>
            <INVSTMTTRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <INVSTMTRS>
                    <DTASOF>20050827010000.000[+0:UTC]</DTASOF>
                    <CURDEF>USD</CURDEF>
                    <INVACCTFROM>
                        <BROKERID>121099999</BROKERID>
                        <ACCTID>999988</ACCTID>
                    </INVACCTFROM>
                    <INVTRANLIST>
                        <DTSTART>20050824130105.000[+0:UTC]</DTSTART>
                        <DTEND>20050828101000.000[+0:UTC]</DTEND>
                        <BUYSTOCK>
                            <INVBUY>
                                <INVTRAN>
                                    <FITID>23321</FITID>
                                    <DTTRADE>20050825000000.000[+0:UTC]</DTTRADE>
                                    <DTSETTLE>20050828000000.000[+0:UTC]</DTSETTLE>
                                </INVTRAN>
                                <SECID>
                                    <UNIQUEID>123456789</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <UNITS>100</UNITS>
                                <UNITPRICE>50.00</UNITPRICE>
                                <COMMISSION>25.00</COMMISSION>
                                <TOTAL>-5025.00</TOTAL>
                                <SUBACCTSEC>CASH</SUBACCTSEC>
                                <SUBACCTFUND>CASH</SUBACCTFUND>
                            </INVBUY>
                            <BUYTYPE>BUY</BUYTYPE>
                        </BUYSTOCK>
                        <INVBANKTRAN>
                            <STMTTRN>
                                <TRNTYPE>CREDIT</TRNTYPE>
                                <DTPOSTED>20050825000000.000[+0:UTC]</DTPOSTED>
                                <DTUSER>20050825000000.000[+0:UTC]</DTUSER>
                                <TRNAMT>1000.00</TRNAMT>
                                <FITID>12345</FITID>
                                <NAME>Customer deposit</NAME>
                                <MEMO>Your check #1034</MEMO>
                            </STMTTRN>
                            <SUBACCTFUND>CASH</SUBACCTFUND>
                        </INVBANKTRAN>
                    </INVTRANLIST>
                    <INVPOSLIST>
                        <POSSTOCK>
                            <INVPOS>
                                <SECID>
                                    <UNIQUEID>123456789</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <HELDINACCT>CASH</HELDINACCT>
                                <POSTYPE>LONG</POSTYPE>
                                <UNITS>200</UNITS>
                                <UNITPRICE>49.50</UNITPRICE>
                                <MKTVAL>9900.00</MKTVAL>
                                <DTPRICEASOF>20050827010000.000[+0:UTC]</DTPRICEASOF>
                                <MEMO>Next dividend payable Sept 1</MEMO>
                            </INVPOS>
                        </POSSTOCK>
                        <POSOPT>
                            <INVPOS>
                                <SECID>
                                    <UNIQUEID>000342222</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <HELDINACCT>CASH</HELDINACCT>
                                <POSTYPE>LONG</POSTYPE>
                                <UNITS>1</UNITS>
                                <UNITPRICE>5</UNITPRICE>
                                <MKTVAL>500</MKTVAL>
                                <DTPRICEASOF>20050827010000.000[+0:UTC]</DTPRICEASOF>
                                <MEMO> Option is in the money</MEMO>
                            </INVPOS>
                        </POSOPT>
                    </INVPOSLIST>
                    <INVBAL>
                        <AVAILCASH>200.00</AVAILCASH>
                        <MARGINBALANCE>-50.00</MARGINBALANCE>
                        <SHORTBALANCE>0</SHORTBALANCE>
                        <BALLIST>
                            <BAL>
                                <NAME>Margin Interest Rate</NAME>
                                <DESC>Current interest rate on margin balances</DESC>
                                <BALTYPE>PERCENT</BALTYPE>
                                <VALUE>7.85</VALUE>
                                <DTASOF>20050827010000.000[+0:UTC]</DTASOF>
                            </BAL>
                        </BALLIST>
                    </INVBAL>
                    <INVOOLIST>
                        <OOBUYSTOCK>
                            <OO>
                                <FITID>23321</FITID>
                                <SECID>
                                    <UNIQUEID>666678578</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <DTPLACED>20050624031505.000[+0:UTC]</DTPLACED>
                                <UNITS>100</UNITS>
                                <SUBACCT>CASH</SUBACCT>
                                <DURATION>GOODTILCANCEL</DURATION>
                                <RESTRICTION>NONE</RESTRICTION>
                                <LIMITPRICE>50.00</LIMITPRICE>
                            </OO>
                            <BUYTYPE>BUY</BUYTYPE>
                        </OOBUYSTOCK>
                    </INVOOLIST>
                </INVSTMTRS>
            </INVSTMTTRNRS>
        </INVSTMTMSGSRSV1>
        <SECLISTMSGSRSV1>
            <SECLIST>
                <STOCKINFO>
                    <SECINFO>
                        <SECID>
                            <UNIQUEID>123456789</UNIQUEID>
                            <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                        </SECID>
                        <SECNAME>Acme Development, Inc.</SECNAME>
                        <TICKER>ACME</TICKER>
                        <FIID>1024</FIID>
                    </SECINFO>
                    <YIELD>10</YIELD>
                    <ASSETCLASS>SMALLSTOCK</ASSETCLASS>
                </STOCKINFO>
                <STOCKINFO>
                    <SECINFO>
                        <SECID>
                            <UNIQUEID>666678578</UNIQUEID>
                            <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                        </SECID>
                        <SECNAME>Hackson Unlimited, Inc.</SECNAME>
                        <TICKER>HACK</TICKER>
                        <FIID>1027</FIID>
                    </SECINFO>
                    <YIELD>17</YIELD>
                    <ASSETCLASS>SMALLSTOCK</ASSETCLASS>
                </STOCKINFO>
                <OPTINFO>
                    <SECINFO>
                        <SECID>
                            <UNIQUEID>000342222</UNIQUEID>
                            <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                        </SECID>
                        <SECNAME>Lucky Airlines Jan 97 Put</SECNAME>
                        <TICKER>LUAXX</TICKER>
                        <FIID>0013</FIID>
                    </SECINFO>
                    <OPTTYPE>PUT</OPTTYPE>
                    <STRIKEPRICE>35.00</STRIKEPRICE>
                    <DTEXPIRE>20050121000000.000[+0:UTC]</DTEXPIRE>
                    <SHPERCTRCT>100</SHPERCTRCT>
                    <SECID>
                        <UNIQUEID>000342200</UNIQUEID>
                        <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                    </SECID>
                    <ASSETCLASS>LARGESTOCK</ASSETCLASS>
                </OPTINFO>
            </SECLIST>
        </SECLISTMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        invtranlist = models.INVTRANLIST(
            models.BUYSTOCK(
                invbuy=models.INVBUY(
                    invtran=models.INVTRAN(
                        fitid="23321",
                        dttrade=datetime(2005, 8, 25, tzinfo=UTC),
                        dtsettle=datetime(2005, 8, 28, tzinfo=UTC),
                    ),
                    secid=STOCK_SECID,
                    units=Decimal("100"),
                    unitprice=Decimal("50.00"),
                    commission=Decimal("25.00"),
                    total=Decimal("-5025.00"),
                    subacctsec="CASH",
                    subacctfund="CASH",
                ),
                buytype="BUY",
            ),
            models.INVBANKTRAN(
                stmttrn=models.STMTTRN(
                    trntype="CREDIT",
                    dtposted=datetime(2005, 8, 25, tzinfo=UTC),
                    dtuser=datetime(2005, 8, 25, tzinfo=UTC),
                    trnamt=Decimal("1000.00"),
                    fitid="12345",
                    name="Customer deposit",
                    memo="Your check #1034",
                ),
                subacctfund="CASH",
            ),
            dtstart=datetime(2005, 8, 24, 13, 1, 5, tzinfo=UTC),
            dtend=datetime(2005, 8, 28, 10, 10, tzinfo=UTC),
        )

        invposlist = models.INVPOSLIST(
            models.POSSTOCK(
                invpos=models.INVPOS(
                    secid=STOCK_SECID,
                    heldinacct="CASH",
                    postype="LONG",
                    units=Decimal("200"),
                    unitprice=Decimal("49.50"),
                    mktval=Decimal("9900.00"),
                    dtpriceasof=datetime(2005, 8, 27, 1, tzinfo=UTC),
                    memo="Next dividend payable Sept 1",
                )
            ),
            models.POSOPT(
                invpos=models.INVPOS(
                    secid=OPT_SECID,
                    heldinacct="CASH",
                    postype="LONG",
                    units=Decimal("1"),
                    unitprice=Decimal("5"),
                    mktval=Decimal("500"),
                    dtpriceasof=datetime(2005, 8, 27, 1, tzinfo=UTC),
                    memo="Option is in the money",
                )
            ),
        )

        invbal = models.INVBAL(
            availcash=Decimal("200.00"),
            marginbalance=Decimal("-50.00"),
            shortbalance=Decimal("0"),
            ballist=models.BALLIST(
                models.BAL(
                    name="Margin Interest Rate",
                    desc="Current interest rate on margin balances",
                    baltype="PERCENT",
                    value=Decimal("7.85"),
                    dtasof=datetime(2005, 8, 27, 1, tzinfo=UTC),
                )
            ),
        )

        invoolist = models.INVOOLIST(
            models.OOBUYSTOCK(
                oo=models.OO(
                    fitid="23321",
                    secid=models.SECID(uniqueid="666678578", uniqueidtype="CUSIP"),
                    dtplaced=datetime(2005, 6, 24, 3, 15, 5, tzinfo=UTC),
                    units=Decimal("100"),
                    subacct="CASH",
                    duration="GOODTILCANCEL",
                    restriction="NONE",
                    limitprice=Decimal("50.00"),
                ),
                buytype="BUY",
            )
        )

        rs = models.INVSTMTRS(
            dtasof=datetime(2005, 8, 27, 1, tzinfo=UTC),
            curdef="USD",
            invacctfrom=INVACCTFROM,
            invtranlist=invtranlist,
            invposlist=invposlist,
            invbal=invbal,
            invoolist=invoolist,
        )

        seclist = models.SECLIST(
            models.STOCKINFO(
                secinfo=models.SECINFO(
                    secid=STOCK_SECID,
                    secname="Acme Development, Inc.",
                    ticker="ACME",
                    fiid="1024",
                ),
                yld=Decimal("10"),
                assetclass="SMALLSTOCK",
            ),
            models.STOCKINFO(
                secinfo=models.SECINFO(
                    secid=models.SECID(uniqueid="666678578", uniqueidtype="CUSIP"),
                    secname="Hackson Unlimited, Inc.",
                    ticker="HACK",
                    fiid="1027",
                ),
                yld=Decimal("17"),
                assetclass="SMALLSTOCK",
            ),
            models.OPTINFO(
                secinfo=models.SECINFO(
                    secid=OPT_SECID,
                    secname="Lucky Airlines Jan 97 Put",
                    ticker="LUAXX",
                    fiid="0013",
                ),
                opttype="PUT",
                strikeprice=Decimal("35.00"),
                dtexpire=datetime(2005, 1, 21, tzinfo=UTC),
                shperctrct=Decimal("100"),
                secid=models.SECID(uniqueid="000342200", uniqueidtype="CUSIP"),
                assetclass="LARGESTOCK",
            ),
        )

        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            invstmtmsgsrsv1=models.INVSTMTMSGSRSV1(
                models.INVSTMTTRNRS(trnuid="1001", status=STATUS, invstmtrs=rs)
            ),
            seclistmsgsrsv1=models.SECLISTMSGSRSV1(seclist),
        )


class Inc401kRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 13.12

    This example is for a user who requests a 401(k) investment statement
    download for a single account.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>NCH</ORG>
                    <FID>1001</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>0500</APPVER>
            </SONRQ>
        </SIGNONMSGSRQV1>
        <INVSTMTMSGSRQV1>
            <INVSTMTTRNRQ>
                <TRNUID>1002</TRNUID>
                <INVSTMTRQ>
                    <INVACCTFROM>
                        <BROKERID>121099999</BROKERID>
                        <ACCTID>999988</ACCTID>
                    </INVACCTFROM>
                    <INCTRAN>
                    <DTSTART>20050101120000.000[+0:UTC]</DTSTART>
                        <INCLUDE>Y</INCLUDE>
                    </INCTRAN>
                    <INCOO>N</INCOO>
                    <INCPOS>
                        <INCLUDE>Y</INCLUDE>
                    </INCPOS>
                    <INCBAL>N</INCBAL>
                    <INC401K>Y</INC401K>
                    <INC401KBAL>Y</INC401KBAL>
                </INVSTMTRQ>
            </INVSTMTTRNRQ>
        </INVSTMTMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.INVSTMTRQ(
            invacctfrom=INVACCTFROM,
            inctran=models.INCTRAN(
                dtstart=datetime(2005, 1, 1, 12, tzinfo=UTC), include=True
            ),
            incoo=False,
            incpos=models.INCPOS(include=True),
            incbal=False,
            inc401k=True,
            inc401kbal=True,
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1,
            invstmtmsgsrqv1=models.INVSTMTMSGSRQV1(
                models.INVSTMTTRNRQ(trnuid="1002", invstmtrq=rq)
            ),
        )


class Inc401kResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 13.12

    A typical server response:
    This user is paying back a loan from the 401(k) account and then
    contributing pretax dollars. A transaction is shown paying principal to
    Rollover and another paying interest to Rollover. Following that is a
    pretax contribution transaction. This is then followed by the list of the
    401(k) balances and finally the 401(k) account information including a
    year-to-date summary.
    """

    # N.B. the example server response in Section 13.12 of the OFXv2 spec contains
    # two errors:
    #
    # 1) an out-of-sequence error; INV401KBAL appears before INV401K when it should come
    #    after it.  Cf. the schema file for INVSTMTRS, OFX_Investment_Messages.xsd
    # 2) an opening <YEARTODATE> tag without a corresponding closeing </YEARTODATE> tag.
    #
    # These errors are corrected for the test below.
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
        <INVSTMTMSGSRSV1>
            <INVSTMTTRNRS>
                <TRNUID>1002</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <INVSTMTRS>
                    <DTASOF>20050131172605.000[-4:EST]</DTASOF>
                    <CURDEF>USD</CURDEF>
                    <INVACCTFROM>
                        <BROKERID>121099999</BROKERID>
                        <ACCTID>999988</ACCTID>
                    </INVACCTFROM>
                    <INVTRANLIST>
                        <DTSTART>20050105172532.000[-5:EST]</DTSTART>
                        <DTEND>20050131172532.000[-4:EST]</DTEND>
                        <BUYMF>
                            <INVBUY>
                                <INVTRAN>
                                    <FITID>212839062820295310723</FITID>
                                    <DTTRADE>20050119000000.000[-5:EST]</DTTRADE>
                                </INVTRAN>
                                <SECID>
                                    <UNIQUEID>744316100</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <UNITS>14.6860</UNITS>
                                <UNITPRICE>18.9000</UNITPRICE>
                                <TOTAL>-277.5700</TOTAL>
                                <CURRENCY>
                                    <CURRATE>1.0000</CURRATE>
                                    <CURSYM>USD</CURSYM>
                                </CURRENCY>
                                <SUBACCTSEC>OTHER</SUBACCTSEC>
                                <SUBACCTFUND>OTHER</SUBACCTFUND>
                                <LOANID>2</LOANID>
                                <LOANPRINCIPAL>277.5700</LOANPRINCIPAL>
                                <LOANINTEREST>0.0000</LOANINTEREST>
                                <INV401KSOURCE>ROLLOVER</INV401KSOURCE>
                                <DTPAYROLL>20050114000000.000[-5:EST]</DTPAYROLL>
                                <PRIORYEARCONTRIB>N</PRIORYEARCONTRIB>
                            </INVBUY>
                            <BUYTYPE>BUY</BUYTYPE>
                        </BUYMF>
                        <BUYMF>
                            <INVBUY>
                                <INVTRAN>
                                    <FITID>212839062820510822977</FITID>
                                    <DTTRADE>20050119000000.000[-5:EST]</DTTRADE>
                                </INVTRAN>
                                <SECID>
                                    <UNIQUEID>744316100</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <UNITS>2.0220</UNITS>
                                <UNITPRICE>18.9000</UNITPRICE>
                                <TOTAL>-38.2200</TOTAL>
                                <CURRENCY>
                                    <CURRATE>1.0000</CURRATE>
                                    <CURSYM>USD</CURSYM>
                                </CURRENCY>
                                <SUBACCTSEC>OTHER</SUBACCTSEC>
                                <SUBACCTFUND>OTHER</SUBACCTFUND>
                                <LOANID>2</LOANID>
                                <LOANPRINCIPAL>0.0000</LOANPRINCIPAL>
                                <LOANINTEREST>38.2200</LOANINTEREST>
                                <INV401KSOURCE>ROLLOVER</INV401KSOURCE>
                                <DTPAYROLL>20050114000000.000[-5:EST]</DTPAYROLL>
                                <PRIORYEARCONTRIB>N</PRIORYEARCONTRIB>
                            </INVBUY>
                            <BUYTYPE>BUY</BUYTYPE>
                        </BUYMF>
                        <BUYMF>
                            <INVBUY>
                                <INVTRAN>
                                    <FITID>212849815151950488609</FITID>
                                    <DTTRADE>20050106000000.000[-5:EST]</DTTRADE>
                                </INVTRAN>
                                <SECID>
                                    <UNIQUEID>744316100</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <UNITS>4.9010</UNITS>
                                <UNITPRICE>18.7900</UNITPRICE>
                                <TOTAL>-92.0900</TOTAL>
                                <CURRENCY>
                                    <CURRATE>1.0000</CURRATE>
                                    <CURSYM>USD</CURSYM>
                                </CURRENCY>
                                <SUBACCTSEC>OTHER</SUBACCTSEC>
                                <SUBACCTFUND>OTHER</SUBACCTFUND>
                                <INV401KSOURCE>PRETAX</INV401KSOURCE>
                                <DTPAYROLL>20051231000000.000[-5:EST]</DTPAYROLL>
                                <PRIORYEARCONTRIB>Y</PRIORYEARCONTRIB>
                            </INVBUY>
                            <BUYTYPE>BUY</BUYTYPE>
                        </BUYMF>
                    </INVTRANLIST>
                    <INV401K>
                        <EMPLOYERNAME>ELGIN NATIONAL INDUSTRIES INC</EMPLOYERNAME>
                        <PLANID>4343</PLANID>
                        <PLANJOINDATE>19940101000000.000[-5:EST]</PLANJOINDATE>
                        <MATCHINFO>
                            <MATCHPCT>0.00</MATCHPCT>
                        </MATCHINFO>
                        <CONTRIBINFO>
                            <CONTRIBSECURITY>
                                <SECID>
                                    <UNIQUEID>744316100</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <PRETAXCONTRIBPCT>50.0000</PRETAXCONTRIBPCT>
                                <PROFITSHARINGCONTRIBPCT>100.0000
                                </PROFITSHARINGCONTRIBPCT>
                                <ROLLOVERCONTRIBPCT>100.0000</ROLLOVERCONTRIBPCT>
                                <OTHERVESTPCT>100.0000</OTHERVESTPCT>
                            </CONTRIBSECURITY>
                            <CONTRIBSECURITY>
                                <SECID>
                                    <UNIQUEID>74431M105</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <PRETAXCONTRIBPCT>25.0000</PRETAXCONTRIBPCT>
                                <PROFITSHARINGCONTRIBPCT>0.0000
                                </PROFITSHARINGCONTRIBPCT>
                                <ROLLOVERCONTRIBPCT>0.0000</ROLLOVERCONTRIBPCT>
                                <OTHERVESTPCT>0.0000</OTHERVESTPCT>
                            </CONTRIBSECURITY>
                            <CONTRIBSECURITY>
                                <SECID>
                                    <UNIQUEID>743969107</UNIQUEID>
                                    <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
                                </SECID>
                                <PRETAXCONTRIBPCT>25.0000</PRETAXCONTRIBPCT>
                                <PROFITSHARINGCONTRIBPCT>0.0000
                                </PROFITSHARINGCONTRIBPCT>
                                <ROLLOVERCONTRIBPCT>0.0000</ROLLOVERCONTRIBPCT>
                                <OTHERVESTPCT>0.0000</OTHERVESTPCT>
                            </CONTRIBSECURITY>
                        </CONTRIBINFO>
                        <INV401KSUMMARY>
                            <YEARTODATE>
                                <DTSTART>20050101000000.000[+0:UTC]</DTSTART>
                                <DTEND>20050131000000.000[+0:UTC]</DTEND>
                                <CONTRIBUTIONS>
                                    <PRETAX>843.2500</PRETAX>
                                    <AFTERTAX>43.4200</AFTERTAX>
                                    <MATCH>421.6200</MATCH>
                                    <TOTAL>1308.2900</TOTAL>
                                </CONTRIBUTIONS>
                            </YEARTODATE>
                        </INV401KSUMMARY>
                    </INV401K>
                    <INV401KBAL>
                        <PRETAX>31690.340000</PRETAX>
                        <PROFITSHARING>10725.640000</PROFITSHARING>
                        <ROLLOVER>15945.750000</ROLLOVER>
                        <OTHERVEST>108.800000</OTHERVEST>
                        <TOTAL>58470.530000</TOTAL>
                    </INV401KBAL>
                </INVSTMTRS>
            </INVSTMTTRNRS>
        </INVSTMTMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        invtranlist = models.INVTRANLIST(
            models.BUYMF(
                invbuy=models.INVBUY(
                    invtran=models.INVTRAN(
                        fitid="212839062820295310723",
                        dttrade=datetime(2005, 1, 19, 5, tzinfo=UTC),
                    ),
                    secid=MF_SECID,
                    units=Decimal("14.6860"),
                    unitprice=Decimal("18.9000"),
                    total=Decimal("-277.5700"),
                    currency=models.CURRENCY(currate=Decimal("1.0000"), cursym="USD"),
                    subacctsec="OTHER",
                    subacctfund="OTHER",
                    loanid="2",
                    loanprincipal=Decimal("277.5700"),
                    loaninterest=Decimal("0.0000"),
                    inv401ksource="ROLLOVER",
                    dtpayroll=datetime(2005, 1, 14, 5, tzinfo=UTC),
                    prioryearcontrib=False,
                ),
                buytype="BUY",
            ),
            models.BUYMF(
                invbuy=models.INVBUY(
                    invtran=models.INVTRAN(
                        fitid="212839062820510822977",
                        dttrade=datetime(2005, 1, 19, 5, tzinfo=UTC),
                    ),
                    secid=MF_SECID,
                    units=Decimal("2.0220"),
                    unitprice=Decimal("18.9000"),
                    total=Decimal("-38.2200"),
                    currency=models.CURRENCY(currate=Decimal("1.0000"), cursym="USD"),
                    subacctsec="OTHER",
                    subacctfund="OTHER",
                    loanid="2",
                    loanprincipal=Decimal("0.0000"),
                    loaninterest=Decimal("38.2200"),
                    inv401ksource="ROLLOVER",
                    dtpayroll=datetime(2005, 1, 14, 5, tzinfo=UTC),
                    prioryearcontrib=False,
                ),
                buytype="BUY",
            ),
            models.BUYMF(
                invbuy=models.INVBUY(
                    invtran=models.INVTRAN(
                        fitid="212849815151950488609",
                        dttrade=datetime(2005, 1, 6, 5, tzinfo=UTC),
                    ),
                    secid=MF_SECID,
                    units=Decimal("4.9010"),
                    unitprice=Decimal("18.7900"),
                    total=Decimal("-92.0900"),
                    currency=models.CURRENCY(currate=Decimal("1.0000"), cursym="USD"),
                    subacctsec="OTHER",
                    subacctfund="OTHER",
                    inv401ksource="PRETAX",
                    dtpayroll=datetime(2005, 12, 31, 5, tzinfo=UTC),
                    prioryearcontrib=True,
                ),
                buytype="BUY",
            ),
            dtstart=datetime(2005, 1, 5, 22, 25, 32, tzinfo=UTC),
            dtend=datetime(2005, 1, 31, 21, 25, 32, tzinfo=UTC),
        )

        inv401k = models.INV401K(
            employername="ELGIN NATIONAL INDUSTRIES INC",
            planid="4343",
            planjoindate=datetime(1994, 1, 1, 5, tzinfo=UTC),
            matchinfo=models.MATCHINFO(matchpct=Decimal("0.00")),
            contribinfo=models.CONTRIBINFO(
                models.CONTRIBSECURITY(
                    secid=MF_SECID,
                    pretaxcontribpct=Decimal("50.0000"),
                    profitsharingcontribpct=Decimal("100.0000"),
                    rollovercontribpct=Decimal("100.0000"),
                    othervestpct=Decimal("100.0000"),
                ),
                models.CONTRIBSECURITY(
                    secid=models.SECID(uniqueid="74431M105", uniqueidtype="CUSIP"),
                    pretaxcontribpct=Decimal("25.0000"),
                    profitsharingcontribpct=Decimal("0.0000"),
                    rollovercontribpct=Decimal("0.0000"),
                    othervestpct=Decimal("0.0000"),
                ),
                models.CONTRIBSECURITY(
                    secid=models.SECID(uniqueid="743969107", uniqueidtype="CUSIP"),
                    pretaxcontribpct=Decimal("25.0000"),
                    profitsharingcontribpct=Decimal("0.0000"),
                    rollovercontribpct=Decimal("0.0000"),
                    othervestpct=Decimal("0.0000"),
                ),
            ),
            inv401ksummary=models.INV401KSUMMARY(
                yeartodate=models.YEARTODATE(
                    dtstart=datetime(2005, 1, 1, tzinfo=UTC),
                    dtend=datetime(2005, 1, 31, tzinfo=UTC),
                    contributions=models.CONTRIBUTIONS(
                        pretax=Decimal("843.2500"),
                        aftertax=Decimal("43.4200"),
                        match=Decimal("421.6200"),
                        total=Decimal("1308.2900"),
                    ),
                )
            ),
        )

        inv401kbal = models.INV401KBAL(
            pretax=Decimal("31690.340000"),
            profitsharing=Decimal("10725.640000"),
            rollover=Decimal("15945.750000"),
            othervest=Decimal("108.800000"),
            total=Decimal("58470.530000"),
        )

        invstmtrs = models.INVSTMTRS(
            dtasof=datetime(2005, 1, 31, 21, 26, 5, tzinfo=UTC),
            curdef="USD",
            invacctfrom=INVACCTFROM,
            invtranlist=invtranlist,
            inv401k=inv401k,
            inv401kbal=inv401kbal,
        )

        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            invstmtmsgsrsv1=models.INVSTMTMSGSRSV1(
                models.INVSTMTTRNRS(trnuid="1002", status=STATUS, invstmtrs=invstmtrs)
            ),
        )


if __name__ == "__main__":
    unittest.main()
