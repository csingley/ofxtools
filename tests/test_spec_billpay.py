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
SONRQ = models.SONRQ(dtclient=datetime(2005, 10, 29, 10, 10, tzinfo=UTC),
                     userid="12345", userpass="MyPassword", language="ENG",
                     fi=models.FI(org="NCH", fid="1001"),
                     appid="MyApp", appver="0500")
SIGNONMSGSRQV1 = models.SIGNONMSGSRQV1(sonrq=SONRQ)


STATUS = models.STATUS(code=0, severity="INFO")


SONRS = models.SONRS(status=STATUS,
                     dtserver=datetime(2005, 10, 29, 10, 10, 3, tzinfo=UTC),
                     language="ENG",
                     dtprofup=datetime(2004, 10, 29, 10, 10, 3, tzinfo=UTC),
                     dtacctup=datetime(2004, 10, 29, 10, 10, 3, tzinfo=UTC),
                     fi=models.FI(org="NCH", fid="1001"))
SIGNONMSGSRSV1 = models.SIGNONMSGSRSV1(sonrs=SONRS)


BANKACCTFROM = models.BANKACCTFROM(bankid="123432123", acctid="516273",
                                   accttype="CHECKING")

BANKACCTTO = models.BANKACCTTO(bankid="121099999", acctid="999977",
                               accttype="SAVINGS")


class Example1RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    Create a payment to "J.C. Counts" for $123.45 to be paid on October 1, 2005
    using funds in a checking account
    """
    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
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
                        <DTDUE>20051001000000.000[0:GMT]</DTDUE>
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
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("123.45"),
                                 payee=models.PAYEE(
                                     name="J. C. Counts", addr1="100 Main St.",
                                     city="Turlock", state="CA",
                                     postalcode="90101", phone="415.987.6543"),
                                 payacct="10101",
                                 dtdue=datetime(2005, 10, 1, tzinfo=UTC),
                                 memo="payment #3")
        billpay = models.BILLPAYMSGSRQV1(models.PMTTRNRQ(
            trnuid="1001", pmtrq=models.PMTRQ(pmtinfo=pmtinfo)))
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class Example1ResponseTestCase(base.OfxTestCase, unittest.TestCase):
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
                <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
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
                    <DTDUE>20051001000000.000[0:GMT]</DTDUE>
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
                    <DTPMTPRC>20050928000000.000[0:GMT]</DTPMTPRC>
                </PMTPRCSTS>
            </PMTRS>
        </PMTTRNRS>
    </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("123.45"),
                                 payee=models.PAYEE(
                                     name="J. C. Counts", addr1="100 Main St.",
                                     city="Turlock", state="CA",
                                     postalcode="90101", phone="415.987.6543"),
                                 payeelstid="123214", payacct="10101",
                                 dtdue=datetime(2005, 10, 1, tzinfo=UTC),
                                 memo="payment #3")
        trnrs = models.PMTTRNRS(trnuid="1001", status=STATUS,
                                pmtrs=models.PMTRS(
                                    srvrtid="1030155", payeelstid="123214",
                                    curdef="USD", pmtinfo=pmtinfo,
                                    extdpayee=models.EXTDPAYEE(
                                        payeeid="9076", idscope="USER",
                                        name="J. C. Counts", daystopay=3),
                                    pmtprcsts=models.PMTPRCSTS(
                                        pmtprccode="WILLPROCESSON",
                                        dtpmtprc=datetime(2005, 9, 28, tzinfo=UTC))))
        return models.OFX(signonmsgsrsv1=SIGNONMSGSRSV1,
                          billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs))


class Example1NextRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.1

    Create a second payment to the payee, using the payee ID returned in the
    previous example
    """
    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
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
                        <DTDUE>20051101000000.000[0:GMT]</DTDUE>
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
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("123.45"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 11, 1, tzinfo=UTC),
                                 memo="Payment #4")
        billpay = models.BILLPAYMSGSRQV1(models.PMTTRNRQ(
            trnuid="1002", pmtrq=models.PMTRQ(pmtinfo=pmtinfo)))
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class Example1NextResponseTestCase(base.OfxTestCase, unittest.TestCase):
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
                <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
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
                        <DTDUE>20051101000000.000[0:GMT]</DTDUE>
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
                        <DTPMTPRC>20051029000000.000[0:GMT]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("123.45"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 11, 1, tzinfo=UTC),
                                 memo="payment #4")
        trnrs = models.PMTTRNRS(trnuid="1002", status=STATUS,
                                pmtrs=models.PMTRS(
                                    srvrtid="1068405", payeelstid="123214",
                                    curdef="USD", pmtinfo=pmtinfo,
                                    extdpayee=models.EXTDPAYEE(
                                        payeeid="9076", idscope="USER",
                                        name="J. C. Counts", daystopay=3),
                                    pmtprcsts=models.PMTPRCSTS(
                                        pmtprccode="WILLPROCESSON",
                                        dtpmtprc=datetime(2005, 10, 29, tzinfo=UTC))))
        return models.OFX(signonmsgsrsv1=SIGNONMSGSRSV1,
                          billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs))


class Example2RequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    Change the amount of the first payment to $125.99
    """
    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
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
                        <DTDUE>20051001000000.000[0:GMT]</DTDUE>
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
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("125.99"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 10, 1, tzinfo=UTC),
                                 memo="payment #3")
        billpay = models.BILLPAYMSGSRQV1(models.PMTTRNRQ(
            trnuid="1021", pmtmodrq=models.PMTMODRQ(srvrtid="1030155",
                                                    pmtinfo=pmtinfo)))
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class Example2ResponseTestCase(base.OfxTestCase, unittest.TestCase):
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
                <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
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
                        <DTDUE>20051001000000.000[0:GMT]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                    <PMTPRCSTS>
                        <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                        <DTPMTPRC>20050928000000.000[0:GMT]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTMODRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("125.99"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 10, 1, tzinfo=UTC),
                                 memo="payment #3")
        trnrs = models.PMTTRNRS(trnuid="1021", status=STATUS,
                                pmtmodrs=models.PMTMODRS(
                                    srvrtid="1030155", pmtinfo=pmtinfo,
                                    pmtprcsts=models.PMTPRCSTS(
                                        pmtprccode="WILLPROCESSON",
                                        dtpmtprc=datetime(2005, 9, 28, tzinfo=UTC))))
        return models.OFX(signonmsgsrsv1=SIGNONMSGSRSV1,
                          billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs))


class Example2ChangeRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    OFX Section 12.12.2

    Change the date of the same payment to December 12, 2005
    """
    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
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
                        <DTDUE>20051212000000.000[0:GMT]</DTDUE>
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
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("125.99"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 12, 12, tzinfo=UTC),
                                 memo="payment #3")
        billpay = models.BILLPAYMSGSRQV1(models.PMTTRNRQ(
            trnuid="32456", pmtmodrq=models.PMTMODRQ(srvrtid="1030155",
                                                     pmtinfo=pmtinfo)))
        return models.OFX(signonmsgsrqv1=SIGNONMSGSRQV1, billpaymsgsrqv1=billpay)


class Example2ChangeResponseTestCase(base.OfxTestCase, unittest.TestCase):
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
                <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
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
                        <DTDUE>20051212000000.000[0:GMT]</DTDUE>
                        <MEMO>payment #3</MEMO>
                    </PMTINFO>
                    <PMTPRCSTS>
                        <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                        <DTPMTPRC>20051209000000.000[0:GMT]</DTPMTPRC>
                    </PMTPRCSTS>
                </PMTMODRS>
            </PMTTRNRS>
        </BILLPAYMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        pmtinfo = models.PMTINFO(bankacctfrom=BANKACCTFROM,
                                 trnamt=Decimal("125.99"),
                                 payeeid="9076", payeelstid="123214",
                                 payacct="10101",
                                 dtdue=datetime(2005, 12, 12, tzinfo=UTC),
                                 memo="payment #3")
        trnrs = models.PMTTRNRS(trnuid="32456", status=STATUS,
                                pmtmodrs=models.PMTMODRS(
                                    srvrtid="1030155", pmtinfo=pmtinfo,
                                    pmtprcsts=models.PMTPRCSTS(
                                        pmtprccode="WILLPROCESSON",
                                        dtpmtprc=datetime(2005, 12, 9, tzinfo=UTC))))
        return models.OFX(signonmsgsrsv1=SIGNONMSGSRSV1,
                          billpaymsgsrsv1=models.BILLPAYMSGSRSV1(trnrs))


#  class Example3RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.3

    #  Cancel a payment
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <PMTTRNRQ>
                #  <TRNUID>54601</TRNUID>
                #  <PMTCANCRQ>
                    #  <SRVRTID>1030155</SRVRTID>
                #  </PMTCANCRQ>
            #  </PMTTRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example3ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.3

    #  The server responds
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <PMTTRNRS>
                #  <TRNUID>54601</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <PMTCANCRS>
                    #  <SRVRTID>1030155</SRVRTID>
                #  </PMTCANCRS>
            #  </PMTTRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


#  class Example4RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.4

    #  Update payment status
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <PMTINQTRNRQ>
                #  <TRNUID>7865</TRNUID>
                #  <PMTINQRQ>
                    #  <SRVRTID>565321</SRVRTID>
                #  </PMTINQRQ>
            #  </PMTINQTRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example4ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.4


    #  The server responds with updated status and check number
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <PMTINQTRNRS>
                #  <TRNUID>7865</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <PMTINQRS>
                    #  <SRVRTID>565321</SRVRTID>
                    #  <PMTPRCSTS>
                        #  <PMTPRCCODE>PROCESSEDON</PMTPRCCODE>
                        #  <DTPMTPRC>20050201000000.000[0:GMT]</DTPMTPRC>
                    #  </PMTPRCSTS>
                    #  <CHECKNUM>6017</CHECKNUM>
                #  </PMTINQRS>
            #  </PMTINQTRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


#  class Example5RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.5

    #  Create a recurring payment of 36 monthly payments of $395 to a (previously
    #  known) standard payee. The first payment will be on November 15, 2005
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <RECPMTTRNRQ>
                #  <TRNUID>12354</TRNUID>
                #  <RECPMTRQ>
                    #  <RECURRINST>
                        #  <NINSTS>36</NINSTS/
                        #  <FREQ>MONTHLY</FREQ>
                    #  </RECURRINST>
                    #  <PMTINFO>
                        #  <BANKACCTFROM>
                            #  <BANKID>555432180</BANKID>
                            #  <ACCTID>763984</ACCTID>
                            #  <ACCTTYPE>CHECKING</ACCTTYPE>
                        #  </BANKACCTFROM>
                        #  <TRNAMT>395.00</TRNAMT>
                        #  <PAYEEID>77810</PAYEEID>
                        #  <PAYEELSTID>27983</PAYEELSTID>
                        #  <PAYACCT>444-78-97572</PAYACCT>
                        #  <DTDUE>20051115</DTDUE>
                        #  <MEMO>Auto loan payment</MEMO>
                    #  </PMTINFO>
                #  </RECPMTRQ>
            #  </RECPMTTRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example5ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.5

    #  The server responds with the assigned server transaction ID
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <RECPMTTRNRS>
                #  <TRNUID>12345</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</INFO>
                #  </STATUS>
                #  <RECPMTRS>
                    #  <RECSRVRTID>387687138</RECSRVRTID>
                    #  <PAYEELSTID>27983</PAYEELSTID>
                    #  <CURDEF>USD</CURDEF>
                    #  <RECURRINST>
                        #  <NINSTS>36</NINSTS>
                        #  <FREQ>MONTHLY</FREQ>
                    #  </RECURRINST>
                    #  <PMTINFO>
                        #  <BANKACCTFROM>
                            #  <BANKID>555432180</BANKID>
                            #  <ACCTID>763984</ACCTID>
                            #  <ACCTTYPE>CHECKING</ACCTTYPE>
                        #  </BANKACCTFROM>
                        #  <TRNAMT>395.00</TRNAMT>
                        #  <PAYEEID>77810</PAYEEID>
                        #  <PAYEELSTID>27983</PAYEELSTID>
                        #  <PAYACCT>444-78-97572</PAYACCT>
                        #  <DTDUE>20051115</DTDUE>
                        #  <MEMO>Auto loan payment
                    #  </PMTINFO>
                    #  <EXTDPAYEE>
                        #  <PAYEEID>77810</PAYEEID>
                        #  <IDSCOPE>USER</IDSCOPE>
                        #  <NAME>Mel’s Used Cars</NAME>
                        #  <DAYSTOPAY>3</DAYSTOPAY>
                    #  </EXTDPAYEE>
                #  </RECPMTRS>
            #  </RECPMTTRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """



#  class Example6RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.6

    #  Change the amount of a recurring payment
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <RECPMTTRNRQ>
                #  <TRNUID>98765</TRNUID>
                #  <RECPMTMODRQ>
                    #  <RECSRVRTID>387687138</RECSRVRTID>
                    #  <RECURRINST>
                        #  <NINSTS>36</NINSTS>
                        #  <FREQ>MONTHLY</FREQ>
                    #  </RECURRINST>
                    #  <PMTINFO>
                        #  <BANKACCTFROM>
                            #  <BANKID>555432180</BANKID>
                            #  <ACCTID>763984</ACCTID>
                            #  <ACCTTYPE>CHECKING</ACCTTYPE>
                        #  </BANKACCTFROM>
                        #  <TRNAMT>399.95</TRNAMT>
                        #  <PAYEEID>77810</PAYEEID>
                        #  <PAYEELSTID>27983</PAYEELSTID>
                        #  <PAYACCT>444-78-97572</PAYACCT>
                        #  <DTDUE>20051115</DTDUE>
                        #  <MEMO>Auto loan payment</MEMO>
                    #  </PMTINFO>
                    #  <MODPENDING>N</MODPENDING>
                #  </RECPMTMODRQ>
            #  </RECPMTTRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example6ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.6

    #  The server responds
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <RECPMTTRNRS>
                #  <TRNUID>98765</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <RECPMTMODRS>
                    #  <RECSRVRTID>387687138</RECSRVRTID>
                    #  <RECURRINST>
                        #  <NINSTS>36</NINSTS>
                        #  <FREQ>MONTHLY</FREQ>
                    #  </RECURRINST>
                    #  <PMTINFO>
                        #  <BANKACCTFROM>
                            #  <BANKID>555432180</BANKID>
                            #  <ACCTID>763984</ACCTID>
                            #  <ACCTTYPE>CHECKING</ACCTTYPE>
                        #  </BANKACCTFROM>
                        #  <TRNAMT>399.95</TRNAMT>
                        #  <PAYEEID>77810</PAYEEID>
                        #  <PAYEELSTID>27983</PAYEELSTID>
                        #  <PAYACCT>444-78-97572</PAYACCT>
                        #  <DTDUE>20051115</DTDUE>
                        #  <MEMO>Auto loan payment</MEMO>
                    #  </PMTINFO>
                    #  <MODPENDING>N</MODPENDING>
                #  </RECPMTMODRS>
            #  </RECPMTTRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


#  class Example7RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.7

    #  Cancel a recurring payment
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
        #  <SONRQ>
            #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
            #  <USERID>12345</USERID>
            #  <USERPASS>MyPassword</USERPASS>
            #  <LANGUAGE>ENG</LANGUAGE>
            #  <FI>
                #  <ORG>NCH</ORG>
                #  <FID>1001</FID>
            #  </FI>
            #  <APPID>MyApp</APPID>
            #  <APPVER>0500</APPVER>
        #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <RECPMTTRNRQ>
                #  <TRNUID>11122</TRNUID>
                #  <RECPMTCANCRQ>
                    #  <RECSRVRTID>387687138</RECSRVRTID>
                    #  <CANPENDING>Y</CANPENDING>
                #  </RECPMTCANCRQ>
            #  </RECPMTTRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example7ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.7

    #  The server responds
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <RECPMTTRNRS>
                #  <TRNUID>11122</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <RECPMTCANCRS>
                    #  <RECSRVRTID>387687138</RECSRVRTID>
                    #  <CANPENDING>Y</CANPENDING>
                #  </RECPMTCANCRS>
            #  </RECPMTTRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


#  class Example8RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.8

    #  The user sends a request to add a payee to the user’s payee list
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <PAYEETRNRQ>
                #  <TRNUID>127677</TRNUID>
                #  <PAYEERQ>
                    #  <PAYEE>
                        #  <NAME>ACME Rocket Works</NAME>
                        #  <ADDR1>101 Spring St.</ADDR1>
                        #  <ADDR2>Suite 503</ADDR2>
                        #  <CITY>Watkins Glen</CITY>
                        #  <STATE>NY</STATE>
                        #  <POSTALCODE>12345-6789</POSTALCODE>
                        #  <PHONE>888.555.1212</PHONE>
                    #  </PAYEE>
                    #  <PAYACCT>1001-99-8876</PAYACCT>
                #  </PAYEERQ>
            #  </PAYEETRNRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example8ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.8

    #  The server responds
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <PAYEETRNRS>
                #  <TRNUID>127677</TRNUID>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <PAYEERS>
                    #  <PAYEELSTID>78096786</PAYEELSTID>
                    #  <PAYEE>
                        #  <NAME>ACME Rocket Works</NAME>
                        #  <ADDR1>101 Spring St.</ADDR1>
                        #  <ADDR2>Suite 503</ADDR2>
                        #  <CITY>Watkins Glen</CITY>
                        #  <STATE>NY</STATE>
                        #  <POSTALCODE>12345-6789</POSTALCODE>
                        #  <PHONE>888.555.1212</PHONE>
                    #  </PAYEE>
                    #  <EXTDPAYEE>
                        #  <PAYEEID>88878</PAYEEID>
                        #  <IDSCOPE>GLOBAL</IDSCOPE>
                        #  <NAME>ACME Rocket Works, Inc.</NAME>
                        #  <DAYSTOPAY>2</DAYSTOPAY>
                    #  </EXTDPAYEE>
                    #  <PAYACCT>1001-99-8876</PAYACCT>
                #  </PAYEERS>
            #  </PAYEETRNRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


#  class Example9RequestTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.9

    #  A client wishes to obtain all Payments active on the server for a
    #  particular account
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRQV1>
            #  <SONRQ>
                #  <DTCLIENT>20051029101000.000[0:GMT]</DTCLIENT>
                #  <USERID>12345</USERID>
                #  <USERPASS>MyPassword</USERPASS>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
                #  <APPID>MyApp</APPID>
                #  <APPVER>0500</APPVER>
            #  </SONRQ>
        #  </SIGNONMSGSRQV1>
        #  <BILLPAYMSGSRQV1>
            #  <PMTSYNCRQ>
                #  <REFRESH>Y</REFRESH>
                #  <REJECTIFMISSING>N</REJECTIFMISSING>
                #  <BANKACCTFROM>
                    #  <BANKID>123432123</BANKID>
                    #  <ACCTID>516273</ACCTID>
                    #  <ACCTTYPE>CHECKING</ACCTTYPE>
                #  </BANKACCTFROM>
            #  </PMTSYNCRQ>
        #  </BILLPAYMSGSRQV1>
    #  </OFX>
    #  """


#  class Example9ResponseTestCase(base.OfxTestCase, unittest.TestCase):
    #  """
    #  OFX Section 12.12.9

    #  Assuming the only activity on this account has been the two payments
    #  created above, the server responds with one payment since the other payment
    #  was cancelled. The server also includes the current <TOKEN> value.
    #  """
    #  ofx = """
    #  <OFX>
        #  <SIGNONMSGSRSV1>
            #  <SONRS>
                #  <STATUS>
                    #  <CODE>0</CODE>
                    #  <SEVERITY>INFO</SEVERITY>
                #  </STATUS>
                #  <DTSERVER>20051029101003.000[0:GMT]</DTSERVER>
                #  <LANGUAGE>ENG</LANGUAGE>
                #  <DTPROFUP>20041029101003.000[0:GMT]</DTPROFUP>
                #  <DTACCTUP>20041029101003.000[0:GMT]</DTACCTUP>
                #  <FI>
                    #  <ORG>NCH</ORG>
                    #  <FID>1001</FID>
                #  </FI>
            #  </SONRS>
        #  </SIGNONMSGSRSV1>
        #  <BILLPAYMSGSRSV1>
            #  <PMTSYNCRS>
                #  <TOKEN>3247989384</TOKEN>
                #  <BANKACCTFROM>
                    #  <BANKID>123432123</BANKID>
                    #  <ACCTID>516273</ACCTID>
                    #  <ACCTTYPE>CHECKING</ACCTTYPE>
                #  </BANKACCTFROM>
                #  <PMTTRNRS>
                    #  <TRNUID>0</TRNUID>
                    #  <STATUS>
                        #  <CODE>0</CODE>
                        #  <SEVERITY>INFO</SEVERITY>
                    #  </STATUS>
                    #  <PMTRS>
                        #  <SRVRTID>1068405</SRVRTID>
                        #  <PAYEELSTID>123214</PAYEELSTID>
                        #  <CURDEF>USD</CURDEF>
                        #  <PMTINFO>
                            #  <BANKACCTFROM>
                                #  <BANKID>123432123</BANKID>
                                #  <ACCTID>516273</ACCTID>
                                #  <ACCTTYPE>CHECKING</ACCTTYPE>
                            #  </BANKACCTFROM>
                            #  <TRNAMT>123.45</TRNAMT>
                            #  <PAYEEID>9076</PAYEEID>
                            #  <PAYEELSTID>123214</PAYEELSTID>
                            #  <PAYACCT>10101</PAYACCT>
                            #  <DTDUE>20051001</DTDUE>
                            #  <MEMO>payment #4</MEMO>
                        #  </PMTINFO>
                        #  <EXTDPAYEE>
                            #  <PAYEEID>9076</PAYEEID>
                            #  <IDSCOPE>USER</IDSCOPE>
                            #  <NAME>J. C. Counts</NAME>
                            #  <DAYSTOPAY>3</DAYSTOPAY>
                        #  </EXTDPAYEE>
                        #  <PMTPRCSTS>
                            #  <PMTPRCCODE>WILLPROCESSON</PMTPRCCODE>
                            #  <DTPMTPRC>20051001</DTPMTPRC>
                        #  </PMTPRCSTS>
                    #  </PMTRS>
                #  </PMTTRNRS>
            #  </PMTSYNCRS>
        #  </BILLPAYMSGSRSV1>
    #  </OFX>
    #  """


if __name__ == "__main__":
    unittest.main()
