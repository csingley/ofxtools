# coding: utf-8
""" Unit tests for models.billpay.mail"""
# stdlib imports
import unittest
import xml.etree.ElementTree as ET


# local imports
from ofxtools.models.billpay.mail import (
    PMTMAILRQ,
    PMTMAILRS,
    PMTMAILTRNRQ,
    PMTMAILTRNRS,
    PMTMAILSYNCRQ,
    PMTMAILSYNCRS,
)
from ofxtools.utils import classproperty


# test imports
import base
import test_models_email as email
import test_models_billpay_common as bp_common


class PmtmailrqTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]
    optionalElements = ["SRVRTID", "PMTINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("PMTMAILRQ")
        root.append(email.MailTestCase.etree)
        ET.SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bp_common.PmtinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMAILRQ(
            mail=email.MailTestCase.aggregate,
            srvrtid="DEADBEEF",
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
        )


class PmtmailrsTestCase(unittest.TestCase, base.TestAggregate):
    __test__ = True

    requiredElements = ["MAIL"]
    optionalElements = ["SRVRTID", "PMTINFO"]

    @classproperty
    @classmethod
    def etree(cls):
        root = ET.Element("PMTMAILRS")
        root.append(email.MailTestCase.etree)
        ET.SubElement(root, "SRVRTID").text = "DEADBEEF"
        root.append(bp_common.PmtinfoTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMAILRS(
            mail=email.MailTestCase.aggregate,
            srvrtid="DEADBEEF",
            pmtinfo=bp_common.PmtinfoTestCase.aggregate,
        )


class PmtmailtrnrqTestCase(unittest.TestCase, base.TrnrqTestCase):
    __test__ = True

    wraps = PmtmailrqTestCase

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMAILTRNRQ(
            trnuid="DEADBEEF",
            cltcookie="B00B135",
            tan="B16B00B5",
            pmtmailrq=PmtmailrqTestCase.aggregate,
        )


class PmtmailtrnrsTestCase(unittest.TestCase, base.TrnrsTestCase):
    __test__ = True

    wraps = PmtmailrsTestCase

    @classproperty
    @classmethod
    def etree(cls):
        root = cls.emptyBase
        root.append(PmtmailrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(cls):
        return PMTMAILTRNRS(
            trnuid="DEADBEEF",
            status=base.StatusTestCase.aggregate,
            cltcookie="B00B135",
            pmtmailrs=PmtmailrsTestCase.aggregate,
        )


class PmtmailsyncrqTestCase(unittest.TestCase, base.SyncrqTestCase):
    __test__ = True

    requiredElements = base.SyncrqTestCase.requiredElements + ["INCIMAGES", "USEHTML"]

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PMTMAILSYNCRQ")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "REJECTIFMISSING").text = "Y"
        ET.SubElement(root, "INCIMAGES").text = "Y"
        ET.SubElement(root, "USEHTML").text = "N"
        root.append(PmtmailtrnrqTestCase.etree)
        root.append(PmtmailtrnrqTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PMTMAILSYNCRQ(
            PmtmailtrnrqTestCase.aggregate,
            PmtmailtrnrqTestCase.aggregate,
            token="DEADBEEF",
            rejectifmissing=True,
            incimages=True,
            usehtml=False,
        )

    @classproperty
    @classmethod
    def validSoup(self):
        for root in super().validSoup:
            ET.SubElement(root, "INCIMAGES").text = "Y"
            ET.SubElement(root, "USEHTML").text = "N"
            # No contained *TRNRS
            yield root

            # 1 contained *TRNRS
            root.append(PmtmailtrnrqTestCase.etree)
            yield root

            # multiple contained *TRNRS
            root.append(PmtmailtrnrqTestCase.etree)
            root.append(PmtmailtrnrqTestCase.etree)
            yield root


class PmtmailsyncrsTestCase(unittest.TestCase, base.SyncrsTestCase):
    __test__ = True

    @classproperty
    @classmethod
    def etree(self):
        root = ET.Element("PMTMAILSYNCRS")
        ET.SubElement(root, "TOKEN").text = "DEADBEEF"
        ET.SubElement(root, "LOSTSYNC").text = "Y"
        root.append(PmtmailtrnrsTestCase.etree)
        root.append(PmtmailtrnrsTestCase.etree)
        return root

    @classproperty
    @classmethod
    def aggregate(self):
        return PMTMAILSYNCRS(
            PmtmailtrnrsTestCase.aggregate,
            PmtmailtrnrsTestCase.aggregate,
            token="DEADBEEF",
            lostsync=True,
        )


if __name__ == "__main__":
    unittest.main()
