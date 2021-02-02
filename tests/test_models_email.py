# coding: utf-8
""" Unit tests for models.email """
# stdlib imports
import unittest
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.email import (
    MAIL,
    MAILRQ,
    MAILRS,
    MAILTRNRQ,
    MAILTRNRS,
    GETMIMERQ,
    GETMIMERS,
    GETMIMETRNRQ,
    GETMIMETRNRS,
    MAILSYNCRQ,
    MAILSYNCRS,
)
from ofxtools.utils import UTC, classproperty


# test imports
import base


class MailTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = [
        "USERID",
        "DTCREATED",
        "FROM",
        "TO",
        "SUBJECT",
        "MSGBODY",
        "INCIMAGES",
        "USEHTML",
    ]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MAIL")
        SubElement(root, "USERID").text = "somebody"
        SubElement(root, "DTCREATED").text = "19990909110000.000[+0:UTC]"
        SubElement(root, "FROM").text = "rolltide420@yahoo.com"
        SubElement(root, "TO").text = "support@ubs.com"
        SubElement(root, "SUBJECT").text = "I've got a problem"
        SubElement(root, "MSGBODY").text = "All my money is gone"
        SubElement(root, "INCIMAGES").text = "N"
        SubElement(root, "USEHTML").text = "N"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAIL(
            userid="somebody",
            dtcreated=datetime(1999, 9, 9, 11, tzinfo=UTC),
            # FROM (reserved Python keyword) renamed to "frm"
            frm="rolltide420@yahoo.com",
            to="support@ubs.com",
            subject="I've got a problem",
            msgbody="All my money is gone",
            incimages=False,
            usehtml=False,
        )

    #  def testToEtree(cls):
    #  # "frm" gets translated back to FROM in etree
    #  root = MAIL(
    #  userid="somebody",
    #  dtcreated=datetime(1999, 9, 9, 11, tzinfo=UTC),
    #  frm="rolltide420@yahoo.com",
    #  to="support@ubs.com",
    #  subject="I've got a problem",
    #  msgbody="All my money is gone",
    #  incimages=False,
    #  usehtml=False,
    #  )
    #  root = root.to_etree()
    #  #  frm = root.find("./FROM")
    #  #  cls.assertIsNotNone(frm)
    #  #  cls.assertEqual(frm.text, "rolltide420@yahoo.com")
    #  #  frm = root.find("./FRM")
    #  #  cls.assertIsNone(frm)
    #  ofx = ET.tostring(root).decode()
    #  cls.maxDiff = None
    #  cls.assertEqual(
    #  ofx,
    #  (
    #  "<MAIL>"
    #  "<USERID>somebody</USERID>"
    #  "<DTCREATED>19990909110000.000[+0:UTC]</DTCREATED>"
    #  "<FROM>rolltide420@yahoo.com</FROM>"
    #  "<TO>support@ubs.com</TO>"
    #  "<SUBJECT>I've got a problem</SUBJECT>"
    #  "<MSGBODY>All my money is gone</MSGBODY>"
    #  "<INCIMAGES>N</INCIMAGES>"
    #  "<USEHTML>N</USEHTML>"
    #  "</MAIL>"
    #  ),
    #  )


class MailrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MAILRQ")
        root.append(MailTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILRQ(mail=MailTestCase.aggregate)


class MailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MAILRS")
        root.append(MailTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILRS(mail=MailTestCase.aggregate)


class MailtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = MailrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            mailrq=MailrqTestCase.aggregate,
        )


class MailtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = MailrsTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            mailrs=MailrsTestCase.aggregate,
        )


class MailsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["INCIMAGES", "USEHTML"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MAILSYNCRQ")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "REJECTIFMISSING").text = "Y"
        SubElement(root, "INCIMAGES").text = "Y"
        SubElement(root, "USEHTML").text = "N"
        root.append(MailtrnrqTestCase.etree)
        root.append(MailtrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILSYNCRQ(
            MailtrnrqTestCase.aggregate,
            MailtrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
            incimages=True,
            usehtml=False,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            SubElement(root, "INCIMAGES").text = "Y"
            SubElement(root, "USEHTML").text = "N"
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(MailtrnrqTestCase.etree)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        # SYNCRQ base malformed; MAIL additions OK
        for root in super().invalidSoup:
            SubElement(root, "INCIMAGES").text = "Y"
            SubElement(root, "USEHTML").text = "N"
            yield root

        # SYNCRQ base OK; MAIL additions malformed
        incimages = Element("INCIMAGES")
        incimages.text = "Y"
        usehtml = Element("USEHTML")
        usehtml.text = "N"
        trnrq = MailtrnrqTestCase.etree

        # INCIMAGES in the wrong place
        # (should be right after REJECTIFMISSING)
        for root_ in super().validSoup:
            index = list(root_).index(root_.find("REJECTIFMISSING"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, incimages)
                root.append(usehtml)
                root.append(trnrq)
                yield root

        # USEHTML in the wrong place
        # (should be right after INCIMAGES)
        for root_ in super().validSoup:
            root_.append(incimages)
            index = list(root_).index(root_.find("INCIMAGES"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, usehtml)
                root.append(trnrq)
                yield root

        #  MAILTRNRQ in the wrong place
        #  (should be right after USEHTML)
        for root_ in super().validSoup:
            root_.append(incimages)
            root_.append(usehtml)
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrq)
                yield root


class MailsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("MAILSYNCRS")
        SubElement(root, "TOKEN").text = "DEADBEEF"
        SubElement(root, "LOSTSYNC").text = "Y"
        root.append(MailtrnrsTestCase.etree)
        root.append(MailtrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return MAILSYNCRS(
            MailtrnrsTestCase.aggregate,
            MailtrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
        )

    @classproperty
    @classmethod
    def validSoup(cls):
        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(MailtrnrsTestCase.etree)
                yield root

    @classproperty
    @classmethod
    def invalidSoup(cls):
        trnrs = MailtrnrsTestCase.etree
        # SYNCRS base malformed; MAIL additions OK
        for root in super().invalidSoup:
            yield root
            root.append(trnrs)
            yield root

        # SYNCRS base OK; MAIL additions malformed
        #  MAILTRNRS in the wrong place
        #  (should be right after LOSTSYNC)
        for root_ in super().validSoup:
            index = len(root_)
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, trnrs)
                yield root


class GetmimerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("GETMIMERQ")
        SubElement(root, "URL").text = "https://example.com"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return GETMIMERQ(url="https://example.com")


class GetmimersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @classproperty
    @classmethod
    def etree(cls):
        root = Element("GETMIMERS")
        SubElement(root, "URL").text = "https://example.com"
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return GETMIMERS(url="https://example.com")


class GetmimetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = GetmimerqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return GETMIMETRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            getmimerq=GetmimerqTestCase.aggregate,
        )


class GetmimetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = GetmimersTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return GETMIMETRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            getmimers=GetmimersTestCase.aggregate,
        )


if __name__ == "__main__":
    unittest.main()
