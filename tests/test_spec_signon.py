# coding: utf-8
"""
Examples - OFX Section 2.5.6
"""
# stdlib imports
import unittest
from datetime import datetime

# local imports
from ofxtools import models
from ofxtools.utils import classproperty, UTC

# test imports
import base


# Common aggregates used across tests
FI = models.FI(org="ABC", fid="000111222")
OK_STATUS = models.STATUS(code=0, severity="INFO")
SUCCESS_STATUS = models.STATUS(code=0, severity="INFO", message="Success")


class PinchRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    User requests a password change
    (only pin change transaction portion is shown)
    """

    ofx = """
    <PINCHTRNRQ>
        <TRNUID>888</TRNUID>
        <PINCHRQ>
            <USERID>12345</USERID>
            <NEWUSERPASS>5321</NEWUSERPASS>
        </PINCHRQ>
    </PINCHTRNRQ>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.PINCHTRNRQ(
            trnuid="888", pinchrq=models.PINCHRQ(userid="12345", newuserpass="5321")
        )


class PinchResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    The server responds with:
    """

    ofx = """
    <PINCHTRNRS>
        <TRNUID>888</TRNUID>
        <STATUS>
            <CODE>0</CODE>
            <SEVERITY>INFO</SEVERITY>
        </STATUS>
        <PINCHRS>
            <USERID>12345</USERID>
        </PINCHRS>
    </PINCHTRNRS>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.PINCHTRNRS(
            trnuid="888", status=OK_STATUS, pinchrs=models.PINCHRS(userid="12345")
        )


class ExtraCredentialsRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Signon in OFX 2.0.3 which includes CLIENTUID and both additional credential tags
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20060321083010.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
                <USERCRED1>MyPin</USERCRED1>
                <USERCRED2>MyID</USERCRED2>
            </SONRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    dtclient=datetime(2006, 3, 21, 8, 30, 10, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                    usercred1="MyPin",
                    usercred2="MyID",
                )
            )
        )


class NeedsAuthtokenRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    The following series shows the OFX 2.0.3 exchanges that occur when a
    server requires the client to collect a one time authentication token.
    Note: This could also be requested in profile, but this example is a case
    where user is an existing OFX consumer.

    Client sends OFX request to server.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>20060321083010.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
            </SONRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    dtclient=datetime(2006, 3, 21, 8, 30, 10, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                )
            )
        )


class NeedsAuthtokenResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Server accepts credentials but wants one-time token.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>15512</CODE>
                    <SEVERITY>ERROR</SEVERITY>
                    <MESSAGE>Please provide Authentication Token</MESSAGE>
                </STATUS>
                <DTSERVER>20060321083015.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(
                sonrs=models.SONRS(
                    status=models.STATUS(
                        code="15512",
                        severity="ERROR",
                        message="Please provide Authentication Token",
                    ),
                    dtserver=datetime(2006, 3, 21, 8, 30, 15, tzinfo=UTC),
                    language="ENG",
                    fi=FI,
                )
            )
        )


class HasAuthtokenRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Client collects the answers and returns them to server along with
    the original request.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>20060321083415.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
                <AUTHTOKEN>1234567890</AUTHTOKEN>
            </SONRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    dtclient=datetime(2006, 3, 21, 8, 34, 15, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                    authtoken="1234567890",
                )
            )
        )


class HasAuthtokenResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Server accepts requests and returns an ACCESSKEY.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                    <MESSAGE>Success</MESSAGE>
                </STATUS>
                <DTSERVER>20060321083445.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <ACCESSKEY>EE225228-38E6-4E35-8266-CD69B5370675</ACCESSKEY>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(
                sonrs=models.SONRS(
                    status=SUCCESS_STATUS,
                    dtserver=datetime(2006, 3, 21, 8, 34, 45, tzinfo=UTC),
                    language="ENG",
                    fi=FI,
                    accesskey="EE225228-38E6-4E35-8266-CD69B5370675",
                )
            )
        )


class NeedsMfachallengeRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    The following series shows the OFX 2.0.3 exchanges that occur when a server
    requires the client to collect answers to MFA Challenge questions.

    Client sends OFX request to server.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
                <DTCLIENT>20060321083010</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
            </SONRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    dtclient=datetime(2006, 3, 21, 8, 30, 10, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                )
            )
        )


class NeedsMfachallengeResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Server accepts credentials but wants additional challenge data.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>3000</CODE>
                    <SEVERITY>ERROR</SEVERITY>
                    <MESSAGE>Further information required</MESSAGE>
                </STATUS>
                <DTSERVER>20060321083015.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(
                sonrs=models.SONRS(
                    status=models.STATUS(
                        code="3000",
                        severity="ERROR",
                        message="Further information required",
                    ),
                    dtserver=datetime(2006, 3, 21, 8, 30, 15, tzinfo=UTC),
                    language="ENG",
                    fi=FI,
                )
            )
        )


class MfachallengeRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Client requests challenge questions.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>20060321083020.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
            </SONRQ>
            <MFACHALLENGETRNRQ>
                <TRNUID>66D3749F-5B3B-4DC3-87A3-8F795EA59EDB</TRNUID>
                <MFACHALLENGERQ>
                <DTCLIENT>20060321083020.000[+0:UTC]</DTCLIENT
                </MFACHALLENGERQ>
            </MFACHALLENGETRNRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    dtclient=datetime(2006, 3, 21, 8, 30, 20, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                ),
                mfachallengetrnrq=models.MFACHALLENGETRNRQ(
                    trnuid="66D3749F-5B3B-4DC3-87A3-8F795EA59EDB",
                    mfachallengerq=models.MFACHALLENGERQ(
                        dtclient=datetime(2006, 3, 21, 8, 30, 20, tzinfo=UTC)
                    ),
                ),
            )
        )


class MfachallengeResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Server returns challenge answers which include:
    * Enumerated phrase ID requiring a user response
    * Enumerated phrase ID requiring only client response
    * Custom question.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>20060321083025.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
            </SONRS>
            <MFACHALLENGETRNRS>
                <TRNUID>66D3749F-5B3B-4DC3-87A3-8F795EA59EDB</TRNUID>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                    <MESSAGE>Success</MESSAGE>
                </STATUS>
                <MFACHALLENGERS>
                    <MFACHALLENGE>
                        <MFAPHRASEID>MFA13</MFAPHRASEID>
                        <MFAPHRASELABEL>Please enter the last four digits of your social security number</MFAPHRASELABEL>
                    </MFACHALLENGE>
                    <MFACHALLENGE>
                        <MFAPHRASEID>MFA107</MFAPHRASEID>
                    </MFACHALLENGE>
                    <MFACHALLENGE>
                        <MFAPHRASEID>123</MFAPHRASEID>
                        <MFAPHRASELABEL>With which branch is your account associated?</MFAPHRASELABEL>
                    </MFACHALLENGE>
                </MFACHALLENGERS>
            </MFACHALLENGETRNRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(
                sonrs=models.SONRS(
                    status=OK_STATUS,
                    dtserver=datetime(2006, 3, 21, 8, 30, 25, tzinfo=UTC),
                    language="ENG",
                    fi=FI,
                ),
                mfachallengetrnrs=models.MFACHALLENGETRNRS(
                    trnuid="66D3749F-5B3B-4DC3-87A3-8F795EA59EDB",
                    status=SUCCESS_STATUS,
                    mfachallengers=models.MFACHALLENGERS(
                        models.MFACHALLENGE(
                            mfaphraseid="MFA13",
                            mfaphraselabel="Please enter the last four digits of your social security number",
                        ),
                        models.MFACHALLENGE(mfaphraseid="MFA107"),
                        models.MFACHALLENGE(
                            mfaphraseid="123",
                            mfaphraselabel="With which branch is your account associated?",
                        ),
                    ),
                ),
            )
        )


class HasMfachallengeaRequestTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Client collects the answers and returns them to server along with the original request.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>20060321083415.000[+0:UTC]</DTCLIENT>
                <USERID>12345</USERID>
                <USERPASS>MyPassword</USERPASS>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <APPID>MyApp</APPID>
                <APPVER>1600</APPVER>
                <CLIENTUID>22576921-8E39-4A82-9E3E-EDDB121ADDEE</CLIENTUID>
                <MFACHALLENGEA>
                    <MFAPHRASEID>MFA13</MFAPHRASEID
                    <MFAPHRASEA>1234</MFAPHRASEA>
                </MFACHALLENGEA>
                <MFACHALLENGEA>
                    <MFAPHRASEID>MFA107</MFAPHRASEID>
                    <MFAPHRASEA>ClientUserAgent</MFAPHRASEA>
                </MFACHALLENGEA>
                <MFACHALLENGEA>
                    <MFAPHRASEID>123</MFAPHRASEID>
                    <MFAPHRASEA>Anytown</MFAPHRASEA>
                </MFACHALLENGEA>
            </SONRQ>
        </SIGNONMSGSRQV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrqv1=models.SIGNONMSGSRQV1(
                sonrq=models.SONRQ(
                    models.MFACHALLENGEA(mfaphraseid="MFA13", mfaphrasea="1234"),
                    models.MFACHALLENGEA(
                        mfaphraseid="MFA107", mfaphrasea="ClientUserAgent"
                    ),
                    models.MFACHALLENGEA(mfaphraseid="123", mfaphrasea="Anytown"),
                    dtclient=datetime(2006, 3, 21, 8, 34, 15, tzinfo=UTC),
                    userid="12345",
                    userpass="MyPassword",
                    language="ENG",
                    fi=FI,
                    appid="MyApp",
                    appver="1600",
                    clientuid="22576921-8E39-4A82-9E3E-EDDB121ADDEE",
                )
            )
        )


class HasMfachallengeaResponseTestCase(base.OfxTestCase, unittest.TestCase):
    """
    Server accepts requests and returns an ACCESSKEY.
    """

    ofx = """
    <OFX>
        <SIGNONMSGSRSV1>
            <SONRS>
                <STATUS>
                    <CODE>0</CODE>
                    <SEVERITY>INFO</SEVERITY>
                    <MESSAGE>Success</MESSAGE>
                </STATUS>
                <DTSERVER>20060321083445.000[+0:UTC]</DTSERVER>
                <LANGUAGE>ENG</LANGUAGE>
                <FI>
                    <ORG>ABC</ORG>
                    <FID>000111222</FID>
                </FI>
                <ACCESSKEY>EE225228-38E6-4E35-8266-CD69B5370675</ACCESSKEY>
            </SONRS>
        </SIGNONMSGSRSV1>
    </OFX>
    """

    @classproperty
    @classmethod
    def aggregate(cls):
        return models.OFX(
            signonmsgsrsv1=models.SIGNONMSGSRSV1(
                sonrs=models.SONRS(
                    status=SUCCESS_STATUS,
                    dtserver=datetime(2006, 3, 21, 8, 34, 45, tzinfo=UTC),
                    language="ENG",
                    fi=FI,
                    accesskey="EE225228-38E6-4E35-8266-CD69B5370675",
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
