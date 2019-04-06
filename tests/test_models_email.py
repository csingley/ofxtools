# coding: utf-8
""" Unit tests for models.email """
# stdlib imports
import unittest
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from datetime import datetime
from copy import deepcopy


# local imports
from ofxtools.models.base import Aggregate
from ofxtools.models.email import MAIL, MAILRQ, MAILRS, GETMIMERQ, GETMIMERS
from ofxtools.utils import UTC


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

    @property
    def root(self):
        root = Element("MAIL")
        SubElement(root, "USERID").text = "somebody"
        SubElement(root, "DTCREATED").text = "19990909110000"
        SubElement(root, "FROM").text = "rolltide420@yahoo.com"
        SubElement(root, "TO").text = "support@ubs.com"
        SubElement(root, "SUBJECT").text = "I've got a problem"
        SubElement(root, "MSGBODY").text = "All my money is gone"
        SubElement(root, "INCIMAGES").text = "N"
        SubElement(root, "USEHTML").text = "N"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, MAIL)
        self.assertEqual(instance.userid, "somebody")
        self.assertEqual(instance.dtcreated, datetime(1999, 9, 9, 11, tzinfo=UTC))
        # FROM (reserved Python keyword) renamed to "frm"
        self.assertEqual(instance.frm, "rolltide420@yahoo.com")
        self.assertEqual(instance.to, "support@ubs.com")
        self.assertEqual(instance.subject, "I've got a problem")
        self.assertEqual(instance.msgbody, "All my money is gone")
        self.assertEqual(instance.incimages, False)
        self.assertEqual(instance.usehtml, False)

    def testToEtree(self):
        # "frm" gets translated back to FROM in etree
        root = MAIL(
            userid="somebody",
            dtcreated=datetime(1999, 9, 9, 11, tzinfo=UTC),
            frm="rolltide420@yahoo.com",
            to="support@ubs.com",
            subject="I've got a problem",
            msgbody="All my money is gone",
            incimages=False,
            usehtml=False,
        )
        root = root.to_etree()
        #  frm = root.find("./FROM")
        #  self.assertIsNotNone(frm)
        #  self.assertEqual(frm.text, "rolltide420@yahoo.com")
        #  frm = root.find("./FRM")
        #  self.assertIsNone(frm)
        ofx = ET.tostring(root).decode()
        self.maxDiff = None
        self.assertEqual(
            ofx,
            (
                "<MAIL>"
                "<USERID>somebody</USERID>"
                "<DTCREATED>19990909110000.000[0:GMT]</DTCREATED>"
                "<FROM>rolltide420@yahoo.com</FROM>"
                "<TO>support@ubs.com</TO>"
                "<SUBJECT>I've got a problem</SUBJECT>"
                "<MSGBODY>All my money is gone</MSGBODY>"
                "<INCIMAGES>N</INCIMAGES>"
                "<USEHTML>N</USEHTML>"
                "</MAIL>"
            ),
        )


class MailrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @property
    def root(self):
        mail = MailTestCase().root
        root = Element("MAILRQ")
        root.append(mail)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, MAILRQ)
        self.assertIsInstance(instance.mail, MAIL)


class MailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]

    @property
    def root(self):
        mail = MailTestCase().root
        root = Element("MAILRS")
        root.append(mail)
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, MAILRS)
        self.assertIsInstance(instance.mail, MAIL)


class MailtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = MailrqTestCase


class MailtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = MailrsTestCase


class MailsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["INCIMAGES", "USEHTML"]

    @property
    def validSoup(self):
        trnrq = MailtrnrqTestCase().root

        for root in super().validSoup:
            SubElement(root, "INCIMAGES").text = "Y"
            SubElement(root, "USEHTML").text = "N"
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrq))
                yield root

    @property
    def invalidSoup(self):
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

        # INCIMAGES in the wrong place
        # (should be right after REJECTIFMISSING)
        for root_ in super().validSoup:
            index = list(root_).index(root_.find("REJECTIFMISSING"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, incimages)
                root.append(usehtml)
                yield root

        # USEHTML in the wrong place
        # (should be right after INCIMAGES)
        for root_ in super().validSoup:
            root_.append(incimages)
            index = list(root_).index(root_.find("INCIMAGES"))
            for n in range(index):
                root = deepcopy(root_)
                root.insert(n, usehtml)
                yield root

        #  MAILTRNRQ in the wrong place
        #  (should be right after USEHTML)
        #
        # FIXME
        # Currently the ``List`` data model offers no way to verify that
        # data appears in correct position relative to metadata, since
        # ``dataTags`` doesn't appear in the ``cls.spec``.


class MailsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @property
    def validSoup(self):
        trnrs = MailtrnrsTestCase().root

        for root in super().validSoup:
            # 0 contained aggregrates
            yield root
            # 1 or more contained aggregates
            for n in range(2):
                root.append(deepcopy(trnrs))
                yield root

    @property
    def invalidSoup(self):
        trnrs = MailtrnrsTestCase().root
        # SYNCRS base malformed; MAIL additions OK
        for root in super().invalidSoup:
            yield root
            root.append(trnrs)
            yield root

        # SYNCRS base OK; MAIL additions malformed
        #  MAILTRNRS in the wrong place
        #  (should be right after LOSTSYNC)
        #
        # FIXME
        # Currently the ``List`` data model offers no way to verify that
        # data appears in correct position relative to metadata, since
        # ``dataTags`` doesn't appear in the ``cls.spec``.


class GetmimerqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @property
    def root(self):
        root = Element("GETMIMERQ")
        SubElement(root, "URL").text = "https://example.com"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, GETMIMERQ)
        self.assertEqual(instance.url, "https://example.com")


class GetmimersTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["URL"]

    @property
    def root(self):
        root = Element("GETMIMERS")
        SubElement(root, "URL").text = "https://example.com"
        return root

    def testConvert(self):
        instance = Aggregate.from_etree(self.root)
        self.assertIsInstance(instance, GETMIMERS)
        self.assertEqual(instance.url, "https://example.com")


class GetmimetrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = GetmimerqTestCase


class GetmimetrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = GetmimersTestCase


if __name__ == "__main__":
    unittest.main()
