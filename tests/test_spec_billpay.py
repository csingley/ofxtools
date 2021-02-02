# coding: utf-8
"""
Examples - OFX Section 12.12
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
    bankid="123432123", acctid="516273", accttype="CHECKING"
)

BANKACCTFROM2 = models.BANKACCTFROM(
    bankid="555432180", acctid="763984", accttype="CHECKING"
)

BANKACCTTO = models.BANKACCTTO(bankid="121099999", acctid="999977", accttype="SAVINGS")


class PaymentRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    Create a payment to "J.C. Counts" for $123.45 to be paid on October 1, 2005
    using funds in a checking account
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
        <BILLPAYMSGSRQV1>
            <PMTTRNRQ>
                <TRNUID>1001</TRNUID>
                <PMTRQ>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>123.45</TRNAMT>
                        <PAYEE>
                            <NAME>J. C. Counts</NAME>
                            <ADDR1>100 Main St.</ADDR1>
                            <CITY>Turlock</CITY>
                            <STATE>CA</STATE>
                            <POSTALCODE>90101</POSTALCODE>
                            <PHONE>415.987.6543</PHONE>
                        </PAYEE>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051001000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                </PMTRQ>
            </PMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("123.45"),
            payee=models.PAYEE(
                name="J. C. Counts",
                addr1="100 Main St.",
                city="Turlock",
                state="CA",
                postalcode="90101",
                phone="415.987.6543",
            ),
            payacct="10101",
            dtdue=datetime(2005, 10, 1, tzinfo=UTC),
            memo="payment #3",
        )
        billpay = models.BILLPAYMSGSRQV1(
            models.PMTTRNRQ(trnuid="1001", pmtrq=models.PMTRQ(pmtinfo=pmtinfo))
        )
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class PaymentResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    The server responds, indicating that it will make the payment on the date
    requested and that the payee is a standard payee
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
    <BILLPAYMSGSRSV1>
        <PMTTRNRS>
            <TRNUID>1001</TRNUID>
            <STATUS>
                <CODE>0</CODE>
                <SEVERITY>INFO</SEVERITY>
            </STATUS>
            <PMTRS>
                <SRVRTID>1030155</SRVRTID>
                <PAYEELSTID>123214</PAYEELSTID>
                <CURDEF>USD</CURDEF>
                <PMTINFO>
                    <BANKACCTFROM>
                        <BANKID>123432123</BANKID>
                        <ACCTID>516273</ACCTID>
                        <ACCTTYPE>CHECKING</ACCTTYPE>
                    </BANKACCTFROM>
                    <TRNAMT>123.45</TRNAMT>
                    <PAYEE>
                        <NAME>J. C. Counts</NAME>
                        <ADDR1>100 Main St.</ADDR1>
                        <CITY>Turlock</CITY>
                        <STATE>CA</STATE>
                        <POSTALCODE>90101</POSTALCODE>
                        <PHONE>415.987.6543</PHONE>
                    </PAYEE>
                    <PAYEELSTID>123214</PAYEELSTID>
                    <PAYACCT>10101</PAYACCT>
                    <DTDUE>20051001000000.000[+0:UTC]</DTDUE>
                    <MEMO>payment #3</MEMO>
                </PMTINFO>
                <EXTDPAYEE>
                    <PAYEEID>9076</PAYEEID>
                    <IDSCOPE>USER</IDSCOPE>
                    <NAME>J. C. Counts</NAME>
                    <DAYSTOPAY>3</DAYSTOPAY>
                </EXTDPAYEE>
                <PMTPRCSTS>
                    <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                    <DTPMTPRC>20050928000000.000[+0:UTC]</DTPMTPRC>
                </PMTPRCSTS>
            </PMTRS>
        </PMTTRNRS>
    </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("123.45"),
            payee=models.PAYEE(
                name="J. C. Counts",
                addr1="100 Main St.",
                city="Turlock",
                state="CA",
                postalcode="90101",
                phone="415.987.6543",
            ),
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 10, 1, tzinfo=UTC),
            memo="payment #3",
        )
        trnrs = models.PMTTRNRS(
            trnuid="1001",
            status=STATUS,
            pmtrs=models.PMTRS(
                srvrtid="1030155",
                payeelstid="123214",
                curdef="USD",
                pmtinfo=pmtinfo,
                extdpayee=models.EXTDPAYEE(
                    payeeid="9076", idscope="USER", name="J. C. Counts", daystopay=3
                ),
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="WILLPROCESSON",
                    dtpmtprc=datetime(2005, 9, 28, tzinfo=UTC),
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PayeeidRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    Create a second payment to the payee, using the payee ID returned in the
    previous example
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
        <BILLPAYMSGSRQV1>
            <PMTTRNRQ>
                <TRNUID>1002</TRNUID>
                <PMTRQ>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>123.45</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051101000000.000[+0:UTC]</DTDUE>
                        <MEMO>Payment #4</MEMO>
                    </PMTINFO>
                </PMTRQ>
            </PMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("123.45"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 11, 1, tzinfo=UTC),
            memo="Payment #4",
        )
        billpay = models.BILLPAYMSGSRQV1(
            models.PMTTRNRQ(trnuid="1002", pmtrq=models.PMTRQ(pmtinfo=pmtinfo))
        )
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class PayeeidResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    The server responds, indicating that it will make the payment on the date
    requested
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
        <BILLPAYMSGSRSV1>
            <PMTTRNRS>
                <TRNUID>1002</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PMTRS>
                    <SRVRTID>1068405</SRVRTID>
                    <PAYEELSTID>123214</PAYEELSTID>
                    <CURDEF>USD</CURDEF>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>123.45</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051101000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #4</MEMO>
                    </PMTINFO>
                    <EXTDPAYEE>
                        <PAYEEID>9076</PAYEEID>
                        <IDSCOPE>USER</IDSCOPE>
                        <NAME>J. C. Counts</NAME>
                        <DAYSTOPAY>3</DAYSTOPAY>
                    </EXTDPAYEE>
                    <PMTPRCSTS>
                        <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                        <DTPMTPRC>20051029000000.000[+0:UTC]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("123.45"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 11, 1, tzinfo=UTC),
            memo="payment #4",
        )
        trnrs = models.PMTTRNRS(
            trnuid="1002",
            status=STATUS,
            pmtrs=models.PMTRS(
                srvrtid="1068405",
                payeelstid="123214",
                curdef="USD",
                pmtinfo=pmtinfo,
                extdpayee=models.EXTDPAYEE(
                    payeeid="9076", idscope="USER", name="J. C. Counts", daystopay=3
                ),
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="WILLPROCESSON",
                    dtpmtprc=datetime(2005, 10, 29, tzinfo=UTC),
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PmtmodAmountRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    Change the amount of the first payment to $125.99
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
        <BILLPAYMSGSRQV1>
            <PMTTRNRQ>
                <TRNUID>1021</TRNUID>
                <PMTMODRQ>
                    <SRVRTID>1030155</SRVRTID>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>125.99</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051001000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                </PMTMODRQ>
            </PMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("125.99"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 10, 1, tzinfo=UTC),
            memo="payment #3",
        )
        billpay = models.BILLPAYMSGSRQV1(
            models.PMTTRNRQ(
                trnuid="1021",
                pmtmodrq=models.PMTMODRQ(srvrtid="1030155", pmtinfo=pmtinfo),
            )
        )
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class PmtmodAmountResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    The server responds
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
        <BILLPAYMSGSRSV1>
            <PMTTRNRS>
                <TRNUID>1021</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PMTMODRS>
                    <SRVRTID>1030155</SRVRTID>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>125.99</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051001000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                    <PMTPRCSTS>
                        <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                        <DTPMTPRC>20050928000000.000[+0:UTC]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTMODRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("125.99"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 10, 1, tzinfo=UTC),
            memo="payment #3",
        )
        trnrs = models.PMTTRNRS(
            trnuid="1021",
            status=STATUS,
            pmtmodrs=models.PMTMODRS(
                srvrtid="1030155",
                pmtinfo=pmtinfo,
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="WILLPROCESSON",
                    dtpmtprc=datetime(2005, 9, 28, tzinfo=UTC),
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PmtmodDateRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    Change the date of the same payment to December 12, 2005
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
        <BILLPAYMSGSRQV1>
            <PMTTRNRQ>
                <TRNUID>32456</TRNUID>
                <PMTMODRQ>
                    <SRVRTID>1030155</SRVRTID>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>125.99</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051212000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                </PMTMODRQ>
            </PMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("125.99"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 12, 12, tzinfo=UTC),
            memo="payment #3",
        )
        billpay = models.BILLPAYMSGSRQV1(
            models.PMTTRNRQ(
                trnuid="32456",
                pmtmodrq=models.PMTMODRQ(srvrtid="1030155", pmtinfo=pmtinfo),
            )
        )
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class PmtmodDateResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    The server responds
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
        <BILLPAYMSGSRSV1>
            <PMTTRNRS>
                <TRNUID>32456</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PMTMODRS>
                    <SRVRTID>1030155</SRVRTID>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>123432123</BANKID>
                            <ACCTID>516273</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>125.99</TRNAMT>
                        <PAYEEID>9076</PAYEEID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <PAYACCT>10101</PAYACCT>
                        <DTDUE>20051212000000.000[+0:UTC]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                    <PMTPRCSTS>
                        <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                        <DTPMTPRC>20051209000000.000[+0:UTC]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTMODRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("125.99"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 12, 12, tzinfo=UTC),
            memo="payment #3",
        )
        trnrs = models.PMTTRNRS(
            trnuid="32456",
            status=STATUS,
            pmtmodrs=models.PMTMODRS(
                srvrtid="1030155",
                pmtinfo=pmtinfo,
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="WILLPROCESSON",
                    dtpmtprc=datetime(2005, 12, 9, tzinfo=UTC),
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PmtcancRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.3

    Cancel a payment
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
        <BILLPAYMSGSRQV1>
            <PMTTRNRQ>
                <TRNUID>54601</TRNUID>
                <PMTCANCRQ>
                    <SRVRTID>1030155</SRVRTID>
                </PMTCANCRQ>
            </PMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrq = models.PMTTRNRQ(
            trnuid="54601", pmtcancrq=models.PMTCANCRQ(srvrtid="1030155")
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class PmtcancResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.3

    The server responds
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
        <BILLPAYMSGSRSV1>
            <PMTTRNRS>
                <TRNUID>54601</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PMTCANCRS>
                    <SRVRTID>1030155</SRVRTID>
                </PMTCANCRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrs = models.PMTTRNRS(
            trnuid="54601", status=STATUS, pmtcancrs=models.PMTCANCRS(srvrtid="1030155")
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PmtinqRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.4

    Update payment status
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
        <BILLPAYMSGSRQV1>
            <PMTINQTRNRQ>
                <TRNUID>7865</TRNUID>
                <PMTINQRQ>
                    <SRVRTID>565321</SRVRTID>
                </PMTINQRQ>
            </PMTINQTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrq = models.PMTINQTRNRQ(
            trnuid="7865", pmtinqrq=models.PMTINQRQ(srvrtid="565321")
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class PmtinqResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.4

    The server responds with updated status and check number
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
        <BILLPAYMSGSRSV1>
            <PMTINQTRNRS>
                <TRNUID>7865</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PMTINQRS>
                    <SRVRTID>565321</SRVRTID>
                    <PMTPRCSTS>
                        <PMTPRCCODE>PROCESSEDON</PMTPRCCODE>
                        <DTPMTPRC>20050201000000.000[+0:UTC]</DTPMTPRC>
                    </PMTPRCSTS>
                    <CHECKNUM>6017</CHECKNUM>
                </PMTINQRS>
            </PMTINQTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrs = models.PMTINQTRNRS(
            trnuid="7865",
            status=STATUS,
            pmtinqrs=models.PMTINQRS(
                srvrtid="565321",
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="PROCESSEDON", dtpmtprc=datetime(2005, 2, 1, tzinfo=UTC)
                ),
                checknum="6017",
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class RecpmtRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.5

    Create a recurring payment of 36 monthly payments of $395 to a (previously
    known) standard payee. The first payment will be on November 15, 2005
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
        <BILLPAYMSGSRQV1>
            <RECPMTTRNRQ>
                <TRNUID>12354</TRNUID>
                <RECPMTRQ>
                    <RECURRINST>
                        <NINSTS>36</NINSTS/
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>555432180</BANKID>
                            <ACCTID>763984</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>395.00</TRNAMT>
                        <PAYEEID>77810</PAYEEID>
                        <PAYEELSTID>27983</PAYEELSTID>
                        <PAYACCT>444-78-97572</PAYACCT>
                        <DTDUE>20051115000000.000[+0:UTC]</DTDUE>
                        <MEMO>Auto loan payment</MEMO>
                    </PMTINFO>
                </RECPMTRQ>
            </RECPMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM2,
            trnamt=Decimal("395.00"),
            payeeid="77810",
            payeelstid="27983",
            payacct="444-78-97572",
            dtdue=datetime(2005, 11, 15, tzinfo=UTC),
            memo="Auto loan payment",
        )
        trnrq = models.RECPMTTRNRQ(
            trnuid="12354",
            recpmtrq=models.RECPMTRQ(
                recurrinst=models.RECURRINST(ninsts=36, freq="MONTHLY"), pmtinfo=pmtinfo
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class RecpmtResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.5

    The server responds with the assigned server transaction ID
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
        <BILLPAYMSGSRSV1>
            <RECPMTTRNRS>
                <TRNUID>12345</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <RECPMTRS>
                    <RECSRVRTID>387687138</RECSRVRTID>
                    <PAYEELSTID>27983</PAYEELSTID>
                    <CURDEF>USD</CURDEF>
                    <RECURRINST>
                        <NINSTS>36</NINSTS>
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>555432180</BANKID>
                            <ACCTID>763984</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>395.00</TRNAMT>
                        <PAYEEID>77810</PAYEEID>
                        <PAYEELSTID>27983</PAYEELSTID>
                        <PAYACCT>444-78-97572</PAYACCT>
                        <DTDUE>20051115000000.000[+0:UTC]</DTDUE>
                        <MEMO>Auto loan payment</MEMO>
                    </PMTINFO>
                    <EXTDPAYEE>
                        <PAYEEID>77810</PAYEEID>
                        <IDSCOPE>USER</IDSCOPE>
                        <NAME>Mel's Used Cars</NAME>
                        <DAYSTOPAY>3</DAYSTOPAY>
                    </EXTDPAYEE>
                </RECPMTRS>
            </RECPMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM2,
            trnamt=Decimal("395.00"),
            payeeid="77810",
            payeelstid="27983",
            payacct="444-78-97572",
            dtdue=datetime(2005, 11, 15, tzinfo=UTC),
            memo="Auto loan payment",
        )
        trnrs = models.RECPMTTRNRS(
            trnuid="12345",
            status=STATUS,
            recpmtrs=models.RECPMTRS(
                recsrvrtid="387687138",
                payeelstid="27983",
                curdef="USD",
                recurrinst=models.RECURRINST(ninsts=36, freq="MONTHLY"),
                pmtinfo=pmtinfo,
                extdpayee=models.EXTDPAYEE(
                    payeeid="77810", idscope="USER", name="Mel's Used Cars", daystopay=3
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class RecpmtmodRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.6

    Change the amount of a recurring payment
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
        <BILLPAYMSGSRQV1>
            <RECPMTTRNRQ>
                <TRNUID>98765</TRNUID>
                <RECPMTMODRQ>
                    <RECSRVRTID>387687138</RECSRVRTID>
                    <RECURRINST>
                        <NINSTS>36</NINSTS>
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>555432180</BANKID>
                            <ACCTID>763984</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>399.95</TRNAMT>
                        <PAYEEID>77810</PAYEEID>
                        <PAYEELSTID>27983</PAYEELSTID>
                        <PAYACCT>444-78-97572</PAYACCT>
                        <DTDUE>20051115000000.000[+0:UTC]</DTDUE>
                        <MEMO>Auto loan payment</MEMO>
                    </PMTINFO>
                    <MODPENDING>N</MODPENDING>
                </RECPMTMODRQ>
            </RECPMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM2,
            trnamt=Decimal("399.95"),
            payeeid="77810",
            payeelstid="27983",
            payacct="444-78-97572",
            dtdue=datetime(2005, 11, 15, tzinfo=UTC),
            memo="Auto loan payment",
        )
        trnrq = models.RECPMTTRNRQ(
            trnuid="98765",
            recpmtmodrq=models.RECPMTMODRQ(
                recsrvrtid="387687138",
                recurrinst=models.RECURRINST(ninsts=36, freq="MONTHLY"),
                pmtinfo=pmtinfo,
                modpending=False,
            ),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class RecpmtmodResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.6

    The server responds
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
        <BILLPAYMSGSRSV1>
            <RECPMTTRNRS>
                <TRNUID>98765</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <RECPMTMODRS>
                    <RECSRVRTID>387687138</RECSRVRTID>
                    <RECURRINST>
                        <NINSTS>36</NINSTS>
                        <FREQ>MONTHLY</FREQ>
                    </RECURRINST>
                    <PMTINFO>
                        <BANKACCTFROM>
                            <BANKID>555432180</BANKID>
                            <ACCTID>763984</ACCTID>
                            <ACCTTYPE>CHECKING</ACCTTYPE>
                        </BANKACCTFROM>
                        <TRNAMT>399.95</TRNAMT>
                        <PAYEEID>77810</PAYEEID>
                        <PAYEELSTID>27983</PAYEELSTID>
                        <PAYACCT>444-78-97572</PAYACCT>
                        <DTDUE>20051115</DTDUE>
                        <MEMO>Auto loan payment</MEMO>
                    </PMTINFO>
                    <MODPENDING>N</MODPENDING>
                </RECPMTMODRS>
            </RECPMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM2,
            trnamt=Decimal("399.95"),
            payeeid="77810",
            payeelstid="27983",
            payacct="444-78-97572",
            dtdue=datetime(2005, 11, 15, tzinfo=UTC),
            memo="Auto loan payment",
        )
        trnrs = models.RECPMTTRNRS(
            trnuid="98765",
            status=STATUS,
            recpmtmodrs=models.RECPMTMODRS(
                recsrvrtid="387687138",
                recurrinst=models.RECURRINST(ninsts=36, freq="MONTHLY"),
                pmtinfo=pmtinfo,
                modpending=False,
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class RecpmtcancRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.7

    Cancel a recurring payment
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
        <BILLPAYMSGSRQV1>
            <RECPMTTRNRQ>
                <TRNUID>11122</TRNUID>
                <RECPMTCANCRQ>
                    <RECSRVRTID>387687138</RECSRVRTID>
                    <CANPENDING>Y</CANPENDING>
                </RECPMTCANCRQ>
            </RECPMTTRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrq = models.RECPMTTRNRQ(
            trnuid="11122",
            recpmtcancrq=models.RECPMTCANCRQ(recsrvrtid="387687138", canpending=True),
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class RecpmtcancResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.7

    The server responds
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
        <BILLPAYMSGSRSV1>
            <RECPMTTRNRS>
                <TRNUID>11122</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <RECPMTCANCRS>
                    <RECSRVRTID>387687138</RECSRVRTID>
                    <CANPENDING>Y</CANPENDING>
                </RECPMTCANCRS>
            </RECPMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        trnrs = models.RECPMTTRNRS(
            trnuid="11122",
            status=STATUS,
            recpmtcancrs=models.RECPMTCANCRS(recsrvrtid="387687138", canpending=True),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PayeeRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.8

    The user sends a request to add a payee to the user’s payee list
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
        <BILLPAYMSGSRQV1>
            <PAYEETRNRQ>
                <TRNUID>127677</TRNUID>
                <PAYEERQ>
                    <PAYEE>
                        <NAME>ACME Rocket Works</NAME>
                        <ADDR1>101 Spring St.</ADDR1>
                        <ADDR2>Suite 503</ADDR2>
                        <CITY>Watkins Glen</CITY>
                        <STATE>NY</STATE>
                        <POSTALCODE>12345-6789</POSTALCODE>
                        <PHONE>888.555.1212</PHONE>
                    </PAYEE>
                    <PAYACCT>1001-99-8876</PAYACCT>
                </PAYEERQ>
            </PAYEETRNRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        payee = models.PAYEE(
            name="ACME Rocket Works",
            addr1="101 Spring St.",
            addr2="Suite 503",
            city="Watkins Glen",
            state="NY",
            postalcode="12345-6789",
            phone="888.555.1212",
        )
        trnrq = models.PAYEETRNRQ(
            trnuid="127677", payeerq=models.PAYEERQ("1001-99-8876", payee=payee)
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(trnrq)
        )


class PayeeResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.8

    The server responds
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
        <BILLPAYMSGSRSV1>
            <PAYEETRNRS>
                <TRNUID>127677</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <PAYEERS>
                    <PAYEELSTID>78096786</PAYEELSTID>
                    <PAYEE>
                        <NAME>ACME Rocket Works</NAME>
                        <ADDR1>101 Spring St.</ADDR1>
                        <ADDR2>Suite 503</ADDR2>
                        <CITY>Watkins Glen</CITY>
                        <STATE>NY</STATE>
                        <POSTALCODE>12345-6789</POSTALCODE>
                        <PHONE>888.555.1212</PHONE>
                    </PAYEE>
                    <EXTDPAYEE>
                        <PAYEEID>88878</PAYEEID>
                        <IDSCOPE>GLOBAL</IDSCOPE>
                        <NAME>ACME Rocket Works, Inc.</NAME>
                        <DAYSTOPAY>2</DAYSTOPAY>
                    </EXTDPAYEE>
                    <PAYACCT>1001-99-8876</PAYACCT>
                </PAYEERS>
            </PAYEETRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        payee = models.PAYEE(
            name="ACME Rocket Works",
            addr1="101 Spring St.",
            addr2="Suite 503",
            city="Watkins Glen",
            state="NY",
            postalcode="12345-6789",
            phone="888.555.1212",
        )
        trnrs = models.PAYEETRNRS(
            trnuid="127677",
            status=STATUS,
            payeers=models.PAYEERS(
                "1001-99-8876",
                payeelstid="78096786",
                payee=payee,
                extdpayee=models.EXTDPAYEE(
                    payeeid="88878",
                    idscope="GLOBAL",
                    name="ACME Rocket Works, Inc.",
                    daystopay=2,
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1, billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs)
        )


class PmtsyncRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.9

    A client wishes to obtain all Payments active on the server for a
    particular account
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
        <BILLPAYMSGSRQV1>
            <PMTSYNCRQ>
                <REFRESH>Y</REFRESH>
                <REJECTIFMISSING>N</REJECTIFMISSING>
                <BANKACCTFROM>
                    <BANKID>123432123</BANKID>
                    <ACCTID>516273</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
            </PMTSYNCRQ>
        </BILLPAYMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        rq = models.PMTSYNCRQ(
            refresh=True, rejectifmissing=False, bankacctfrom=BANKACCTFROM
        )
        return models.OFX(
            signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=models.BILLPAYMSGSRQV1(rq)
        )


class PmtsyncResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.9

    Assuming the only activity on this account has been the two payments
    created above, the server responds with one payment since the other payment
    was cancelled. The server also includes the current <TOKEN> value.
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
        <BILLPAYMSGSRSV1>
            <PMTSYNCRS>
                <TOKEN>3247989384</TOKEN>
                <BANKACCTFROM>
                    <BANKID>123432123</BANKID>
                    <ACCTID>516273</ACCTID>
                    <ACCTTYPE>CHECKING</ACCTTYPE>
                </BANKACCTFROM>
                <PMTTRNRS>
                    <TRNUID>0</TRNUID>
                    <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                    </STATUS>
                    <PMTRS>
                        <SRVRTID>1068405</SRVRTID>
                        <PAYEELSTID>123214</PAYEELSTID>
                        <CURDEF>USD</CURDEF>
                        <PMTINFO>
                            <BANKACCTFROM>
                                <BANKID>123432123</BANKID>
                                <ACCTID>516273</ACCTID>
                                <ACCTTYPE>CHECKING</ACCTTYPE>
                            </BANKACCTFROM>
                            <TRNAMT>123.45</TRNAMT>
                            <PAYEEID>9076</PAYEEID>
                            <PAYEELSTID>123214</PAYEELSTID>
                            <PAYACCT>10101</PAYACCT>
                            <DTDUE>20051001000000.000[+0:UTC]</DTDUE>
                            <MEMO>payment #4</MEMO>
                        </PMTINFO>
                        <EXTDPAYEE>
                            <PAYEEID>9076</PAYEEID>
                            <IDSCOPE>USER</IDSCOPE>
                            <NAME>J. C. Counts</NAME>
                            <DAYSTOPAY>3</DAYSTOPAY>
                        </EXTDPAYEE>
                        <PMTPRCSTS>
                            <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                            <DTPMTPRC>20051001000000.000[+0:UTC]</DTPMTPRC>
                        </PMTPRCSTS>
                    </PMTRS>
                </PMTTRNRS>
            </PMTSYNCRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(
            bankacctfrom=BANKACCTFROM,
            trnamt=Decimal("123.45"),
            payeeid="9076",
            payeelstid="123214",
            payacct="10101",
            dtdue=datetime(2005, 10, 1, tzinfo=UTC),
            memo="payment #4",
        )
        trnrs = models.PMTTRNRS(
            trnuid="0",
            status=STATUS,
            pmtrs=models.PMTRS(
                srvrtid="1068405",
                payeelstid="123214",
                curdef="USD",
                pmtinfo=pmtinfo,
                extdpayee=models.EXTDPAYEE(
                    payeeid="9076", idscope="USER", name="J. C. Counts", daystopay=3
                ),
                pmtprcsts=models.PMTPRCSTS(
                    pmtprccode="WILLPROCESSON",
                    dtpmtprc=datetime(2005, 10, 1, tzinfo=UTC),
                ),
            ),
        )
        return models.OFX(
            signonmsgsrsv1=SIGNONMSGSRSV1,
            billpaymsgsrsv1=models.BILLPAYMSGSRSV1(
                models.PMTSYNCRS(trnrs, token="3247989384", bankacctfrom=BANKACCTFROM)
            ),
        )


if __name__ == "__main__":
    unittest.main()
