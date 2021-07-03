# coding: utf-8
"""
Examples - OFX Section 11.14
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


BANKACCTFROM = models.BANKACCTFROM(
    bankid="121099999", acctid="999988", accttype="CHECKING"
)

BANKACCTTO = models.BANKACCTTO(bankid="121099999", acctid="999977", accttype="SAVINGS")


class Example1RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.1"""

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
        <BANKMSGSRQV1>
            <STMTTRNRQ>
                <TRNUID>1001</TRNUID>
                <STMTRQ>
                    <BANKACCTFROM>
                        <BANKID>121099999</BANKID>
                        <ACCTID>999988</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                    </BANKACCTFROM>
                    <INCTRAN>
                        <INCLUDE>Y</INCLUDE>
                    </INCTRAN>
                </STMTRQ>
            </STMTTRNRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        stmttrnrq = models.STMTTRNRQ(
            trnuid="1001",
            stmtrq=models.STMTRQ(
                bankacctfrom=BANKACCTFROM, inctran=models.INCTRAN(include=True)
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(stmttrnrq)
        )


class Example1ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.1"""

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
        <BANKMSGSRSV1>
            <STMTTRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <STMTRS>
                    <CURDEF>USD</CURDEF>
                    <BANKACCTFROM>
                        <BANKID>121099999</BANKID>
                        <ACCTID>999988</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                    </BANKACCTFROM>
                    <BANKTRANLIST>
                        <DTSTART>20051001000000.000[+0:UTC]</DTSTART>
                        <DTEND>20051028000000.000[+0:UTC]</DTEND>
                        <STMTTRN>
                            <TRNTYPE>CHECK</TRNTYPE>
                            <DTPOSTED>20051004000000.000[+0:UTC]</DTPOSTED>
                            <TRNAMT>-200.00</TRNAMT>
                            <FITID>00002</FITID>
                            <CHECKNUM>1000</CHECKNUM>
                        </STMTTRN>
                        <STMTTRN>
                            <TRNTYPE>ATM</TRNTYPE>
                            <DTPOSTED>20051020000000.000[+0:UTC]</DTPOSTED>
                            <DTUSER>20051020000000.000[+0:UTC]</DTUSER>
                            <TRNAMT>-300.00</TRNAMT>
                            <FITID>00003</FITID>
                        </STMTTRN>
                    </BANKTRANLIST>
                    <LEDGERBAL>
                        <BALAMT>200.29</BALAMT>
                        <DTASOF>20051029112000.000[+0:UTC]</DTASOF>
                    </LEDGERBAL>
                    <AVAILBAL>
                        <BALAMT>200.29</BALAMT>
                        <DTASOF>20051029112000.000[+0:UTC]</DTASOF>
                    </AVAILBAL>
                </STMTRS>
            </STMTTRNRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        banktranlist = models.BANKTRANLIST(
            models.STMTTRN(
                trntype="CHECK",
                dtposted=datetime(2005, 10, 4, tzinfo=UTC),
                trnamt=Decimal("-200.00"),
                fitid="00002",
                checknum="1000",
            ),
            models.STMTTRN(
                trntype="ATM",
                dtposted=datetime(2005, 10, 20, tzinfo=UTC),
                dtuser=datetime(2005, 10, 20, tzinfo=UTC),
                trnamt=Decimal("-300.00"),
                fitid="00003",
            ),
            dtstart=datetime(2005, 10, 1, tzinfo=UTC),
            dtend=datetime(2005, 10, 28, tzinfo=UTC),
        )

        balargs = {
            "balamt": Decimal("200.29"),
            "dtasof": datetime(2005, 10, 29, 11, 20, tzinfo=UTC),
        }

        stmttrnrs = models.STMTTRNRS(
            trnuid="1001",
            status=STATUS,
            stmtrs=models.STMTRS(
                curdef="USD",
                bankacctfrom=BANKACCTFROM,
                banktranlist=banktranlist,
                ledgerbal=models.LEDGERBAL(**balargs),
                availbal=models.AVAILBAL(**balargs),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, bankmsgsrsv1=models.BANKMSGSRSV1(stmttrnrs)
        )


class Example2RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.2"""

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
        <BANKMSGSRQV1>
            <INTRATRNRQ>
                <TRNUID>1001</TRNUID>
                <INTRARQ>
                    <XFERINFO>
                        <BANKACCTFROM>
                            <BANKID>121099999</BANKID>
                            <ACCTID>999988</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <BANKACCTTO>
                            <BANKID>121099999</BANKID>
                            <ACCTID>999977</ACCTID>
                            <ACCTTYPE>SAVINGS</ACCTTYPE>
                        </BANKACCTTO>
                        <TRNAMT>200.00</TRNAMT>
                    </XFERINFO>
                </INTRARQ>
            </INTRATRNRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        intratrnrq = models.INTRATRNRQ(
            trnuid="1001",
            intrarq=models.INTRARQ(
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("200.00"),
                )
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(intratrnrq)
        )


class Example2ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.2"""

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
        <BANKMSGSRSV1>
            <INTRATRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <INTRARS>
                    <CURDEF>USD</CURDEF>
                    <SRVRTID>1001</SRVRTID>
                    <XFERINFO>
                        <BANKACCTFROM>
                            <BANKID>121099999</BANKID>
                            <ACCTID>999988</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <BANKACCTTO>
                            <BANKID>121099999</BANKID>
                            <ACCTID>999977</ACCTID>
                            <ACCTTYPE>SAVINGS</ACCTTYPE>
                        </BANKACCTTO>
                        <TRNAMT>200.00</TRNAMT>
                    </XFERINFO>
                    <DTXFERPRJ>20060829100000.000[+0:UTC]</DTXFERPRJ>
                </INTRARS>
            </INTRATRNRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        intrars = models.INTRARS(
            curdef="USD",
            srvrtid="1001",
            xferinfo=models.XFERINFO(
                bankacctfrom=BANKACCTFROM,
                bankacctto=BANKACCTTO,
                trnamt=Decimal("200.00"),
            ),
            dtxferprj=datetime(2006, 8, 29, 10, tzinfo=UTC),
        )

        intratrnrs = models.INTRATRNRS(trnuid="1001", status=STATUS, intrars=intrars)
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, bankmsgsrsv1=models.BANKMSGSRSV1(intratrnrs)
        )


class Example3RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.3"""

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000</DTCLIENT>
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
        <BANKMSGSRQV1>
            <STPCHKTRNRQ>
                <TRNUID>1001</TRNUID>
                <STPCHKRQ>
                    <BANKACCTFROM>
                        <BANKID>121099999</BANKID>
                        <ACCTID>999988</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                    </BANKACCTFROM>
                    <CHKRANGE>
                        <CHKNUMSTART>200</CHKNUMSTART>
                        <CHKNUMEND>202</CHKNUMEND>
                    </CHKRANGE>
                </STPCHKRQ>
            </STPCHKTRNRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrq = models.STPCHKTRNRQ(
            trnuid="1001",
            stpchkrq=models.STPCHKRQ(
                bankacctfrom=BANKACCTFROM,
                chkrange=models.CHKRANGE(chknumstart="200", chknumend="202"),
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(trnrq)
        )


class Example3ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.3"""

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
        <BANKMSGSRSV1>
            <STPCHKTRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <STPCHKRS>
                    <CURDEF>USD</CURDEF>
                    <BANKACCTFROM>
                        <BANKID>121099999</BANKID>
                        <ACCTID>999988</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                    </BANKACCTFROM>
                    <STPCHKNUM>
                        <CHECKNUM>200</CHECKNUM>
                        <CHKSTATUS>101</CHKSTATUS>
                    </STPCHKNUM>
                    <STPCHKNUM>
                        <CHECKNUM>201</CHECKNUM>
                        <CHKSTATUS>0</CHKSTATUS>
                    </STPCHKNUM>
                    <STPCHKNUM>
                        <CHECKNUM>202</CHECKNUM>
                        <CHKSTATUS>0</CHKSTATUS>
                    </STPCHKNUM>
                    <FEE>10.00</FEE>
                    <FEEMSG>Fee for stop payment</FEEMSG>
                </STPCHKRS>
            </STPCHKTRNRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rs = models.STPCHKRS(
            models.STPCHKNUM(checknum="200", chkstatus="101"),
            models.STPCHKNUM(checknum="201", chkstatus="0"),
            models.STPCHKNUM(checknum="202", chkstatus="0"),
            curdef="USD",
            bankacctfrom=BANKACCTFROM,
            fee=Decimal("10.00"),
            feemsg="Fee for stop payment",
        )

        trnrs = models.STPCHKTRNRS(trnuid="1001", status=STATUS, stpchkrs=rs)
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, bankmsgsrsv1=models.BANKMSGSRSV1(trnrs)
        )


class Example4RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000</DTCLIENT>
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
        <BANKMSGSRQV1>
            <RECINTRATRNRQ>
                <TRNUID>1001</TRNUID>
                <RECINTRARQ>
                    <RECURRINST>
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <INTRARQ>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                            <DTDUE>20061115000000.000[+0:UTC]</DTDUE>
                        </XFERINFO>
                    </INTRARQ>
                </RECINTRARQ>
            </RECINTRATRNRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.RECINTRARQ(
            recurrinst=models.RECURRINST(freq="MONTHLY"),
            intrarq=models.INTRARQ(
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("1000.00"),
                    dtdue=datetime(2006, 11, 15, tzinfo=UTC),
                )
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1,
            bankmsgsrqv1=models.BANKMSGSRQV1(
                models.RECINTRATRNRQ(recintrarq=rq, trnuid="1001")
            ),
        )


class Example4ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

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
        <BANKMSGSRSV1>
            <RECINTRATRNRS>
                <TRNUID>1001</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <RECINTRARS>
                    <RECSRVRTID>20000</RECSRVRTID>
                    <RECURRINST>
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <INTRARS>
                        <CURDEF>USD</CURDEF?
                        <SRVRTID>20000</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                            <DTDUE>20061115</DTDUE>
                        </XFERINFO>
                    </INTRARS>
                </RECINTRARS>
            </RECINTRATRNRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rs = models.INTRARS(
            curdef="USD",
            srvrtid="20000",
            xferinfo=models.XFERINFO(
                bankacctfrom=BANKACCTFROM,
                bankacctto=BANKACCTTO,
                trnamt=Decimal("1000.00"),
                dtdue=datetime(2006, 11, 15, tzinfo=UTC),
            ),
        )

        trnrs = models.RECINTRATRNRS(
            trnuid="1001",
            status=STATUS,
            recintrars=models.RECINTRARS(
                recsrvrtid="20000",
                recurrinst=models.RECURRINST(freq="MONTHLY"),
                intrars=rs,
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, bankmsgsrsv1=models.BANKMSGSRSV1(trnrs)
        )


class Example4SyncRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000</DTCLIENT>
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
        <BANKMSGSRQV1>
            <INTRASYNCRQ>
                <TOKEN>0</TOKEN>
                <REJECTIFMISSING>N</REJECTIFMISSING>
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
            </INTRASYNCRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.INTRASYNCRQ(
            token="0", rejectifmissing=False, bankacctfrom=BANKACCTFROM
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(rq)
        )


class Example4SyncResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

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
        <BANKMSGSRSV1>
            <INTRASYNCRS>
                <TOKEN>22243</TOKEN>
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRARS>
                        <CURDEF>USD</CURDEF>
                        <SRVRTID>100100000</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                        </XFERINFO>
                        <DTXFERPRJ>20061115000000.000[+0:UTC]</DTXFERPRJ>
                        <RECSRVRTID>20000</RECSRVRTID>
                    </INTRARS>
                </INTRATRNRS>
            </INTRASYNCRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rs = models.INTRARS(
            curdef="USD",
            srvrtid="100100000",
            xferinfo=models.XFERINFO(
                bankacctfrom=BANKACCTFROM,
                bankacctto=BANKACCTTO,
                trnamt=Decimal("1000.00"),
            ),
            dtxferprj=datetime(2006, 11, 15, tzinfo=UTC),
            recsrvrtid="20000",
        )

        trnrs = models.INTRATRNRS(trnuid="0", status=STATUS, intrars=rs)
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            bankmsgsrsv1=models.BANKMSGSRSV1(
                models.INTRASYNCRS(trnrs, token="22243", bankacctfrom=BANKACCTFROM)
            ),
        )


class Example4RecsyncRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000</DTCLIENT>
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
        <BANKMSGSRQV1>
            <RECINTRASYNCRQ>
                <TOKEN>324789987</TOKEN>
                <REJECTIFMISSING>Y</REJECTIFMISSING>
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <RECINTRATRNRQ>
                    <TRNUID>1005</TRNUID>
                    <RECINTRACANRQ>
                        <RECSRVRTID>20000</RECSRVRTID>
                        <CANPENDING>Y</CANPENDING>
                    </RECINTRACANRQ>
                </RECINTRATRNRQ>
            </RECINTRASYNCRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.RECINTRASYNCRQ(
            models.RECINTRATRNRQ(
                trnuid="1005",
                recintracanrq=models.RECINTRACANRQ(recsrvrtid="20000", canpending=True),
            ),
            token="324789987",
            rejectifmissing=True,
            bankacctfrom=BANKACCTFROM,
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(rq)
        )


class Example4RecsyncResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

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
        <BANKMSGSRSV1>
            <RECINTRASYNCRS>
                <TOKEN>324789988</TOKEN
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <RECINTRATRNRS>
                    <TRNUID>1005</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <RECINTRACANRS>
                        <RECSRVRTID>20000</RECSRVRTID>
                        <CANPENDING>Y</CANPENDING>
                    </RECINTRACANRS>
                </RECINTRATRNRS>
            </RECINTRASYNCRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrs = models.RECINTRATRNRS(
            trnuid="1005",
            status=STATUS,
            recintracanrs=models.RECINTRACANRS(recsrvrtid="20000", canpending=True),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            bankmsgsrsv1=models.BANKMSGSRSV1(
                models.RECINTRASYNCRS(
                    trnrs, token="324789988", bankacctfrom=BANKACCTFROM
                )
            ),
        )


class Example4NextSyncRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000</DTCLIENT>
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
        <BANKMSGSRQV1>
            <INTRASYNCRQ>
                <TOKEN>22243</TOKEN>
                <REJECTIFMISSING>N</REJECTIFMISSING>
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
            </INTRASYNCRQ>
        </BANKMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.INTRASYNCRQ(
            token="22243", rejectifmissing=False, bankacctfrom=BANKACCTFROM
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, bankmsgsrqv1=models.BANKMSGSRQV1(rq)
        )


class Example4NextSyncResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """OFX Section 11.14.4"""

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
        <BANKMSGSRSV1>
            <INTRASYNCRS>
                <TOKEN>22244</TOKEN>
                <BANKACCTFROM>
                    <BANKID>121099999</BANKID>
                    <ACCTID>999988</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRAMODRS>
                        <SRVRTID>100100000</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                        </XFERINFO>
                        <XFERPRCSTS>
                            <XFERPRCCODE>POSTEDON</XFERPRCCODE>
                            <DTXFERPRC>20061115000000.000[+0:UTC]</DTXFERPRC>
                        </XFERPRCSTS>
                    </INTRAMODRS>
                </INTRATRNRS>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRARS>
                        <CURDEF>USD</CURDEF>
                        <SRVRTID>112233</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                        </XFERINFO>
                        <DTXFERPRJ>20061215000000.000[+0:UTC]</DTXFERPRJ>
                        <RECSRVRTID>20000</RECSRVRTID>
                    </INTRARS>
                </INTRATRNRS>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRAMODRS>
                        <SRVRTID>112233</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                        </XFERINFO>
                        <XFERPRCSTS>
                            <XFERPRCCODE>POSTEDON</XFERPRCCODE>
                            <DTXFERPRC>20061215000000.000[+0:UTC]</DTXFERPRC>
                        </XFERPRCSTS>
                    </INTRAMODRS>
                </INTRATRNRS>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRARS>
                        <CURDEF>USD</CURDEF>
                        <SRVRTID>112255</SRVRTID>
                        <XFERINFO>
                            <BANKACCTFROM>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999988</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <BANKACCTTO>
                                <BANKID>121099999</BANKID>
                                <ACCTID>999977</ACCTID>
                                <ACCTTYPE>SAVINGS</ACCTTYPE>
                            </BANKACCTTO>
                            <TRNAMT>1000.00</TRNAMT>
                        </XFERINFO>
                        <DTXFERPRJ>20060115000000.000[+0:UTC]</DTXFERPRJ>
                        <RECSRVRTID>20000</RECSRVRTID>
                    </INTRARS>
                </INTRATRNRS>
                <INTRATRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <INTRACANRS>
                        <SRVRTID>112255</SRVRTID>
                    </INTRACANRS>
                </INTRATRNRS>
            </INTRASYNCRS>
        </BANKMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrs0 = models.INTRATRNRS(
            trnuid="0",
            status=STATUS,
            intramodrs=models.INTRAMODRS(
                srvrtid="100100000",
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("1000.00"),
                ),
                xferprcsts=models.XFERPRCSTS(
                    xferprccode="POSTEDON", dtxferprc=datetime(2006, 11, 15, tzinfo=UTC)
                ),
            ),
        )

        trnrs1 = models.INTRATRNRS(
            trnuid="0",
            status=STATUS,
            intrars=models.INTRARS(
                curdef="USD",
                srvrtid="112233",
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("1000.00"),
                ),
                dtxferprj=datetime(2006, 12, 15, tzinfo=UTC),
                recsrvrtid="20000",
            ),
        )

        trnrs2 = models.INTRATRNRS(
            trnuid="0",
            status=STATUS,
            intramodrs=models.INTRAMODRS(
                srvrtid="112233",
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("1000.00"),
                ),
                xferprcsts=models.XFERPRCSTS(
                    xferprccode="POSTEDON", dtxferprc=datetime(2006, 12, 15, tzinfo=UTC)
                ),
            ),
        )

        trnrs3 = models.INTRATRNRS(
            trnuid="0",
            status=STATUS,
            intrars=models.INTRARS(
                curdef="USD",
                srvrtid="112255",
                xferinfo=models.XFERINFO(
                    bankacctfrom=BANKACCTFROM,
                    bankacctto=BANKACCTTO,
                    trnamt=Decimal("1000.00"),
                ),
                dtxferprj=datetime(2006, 1, 15, tzinfo=UTC),
                recsrvrtid="20000",
            ),
        )

        trnrs4 = models.INTRATRNRS(
            trnuid="0", status=STATUS, intracanrs=models.INTRACANRS(srvrtid="112255")
        )

        syncrs = models.INTRASYNCRS(
            trnrs0,
            trnrs1,
            trnrs2,
            trnrs3,
            trnrs4,
            token="22244",
            bankacctfrom=BANKACCTFROM,
        )

        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, bankmsgsrsv1=models.BANKMSGSRSV1(syncrs)
        )


if __name__ == "__main__":
    unittest.main()
