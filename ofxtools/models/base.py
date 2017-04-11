# vim: set fileencoding=utf-8
"""
Python object model for fundamental data aggregates such as transactions,
balances, and securities.
"""
# stdlib imports
import xml.etree.ElementTree as ET
from collections import UserList

# local imports
import ofxtools.models
from ofxtools.Types import (
    Element,
    String,
    NagString,
    OneOf,
    Integer,
    Decimal,
    DateTime,
)
from ofxtools.lib import LANG_CODES, CURRENCY_CODES, COUNTRY_CODES


# Enums used in aggregate validation
INV401KSOURCES = ('PRETAX', 'AFTERTAX', 'MATCH', 'PROFITSHARING',
                  'ROLLOVER', 'OTHERVEST', 'OTHERNONVEST')
ACCTTYPES = ('CHECKING', 'SAVINGS', 'MONEYMRKT', 'CREDITLINE')
INVSUBACCTS = ('CASH', 'MARGIN', 'SHORT', 'OTHER')


class Aggregate(object):
    """
    Base class for Python representation of OFX 'aggregate', i.e. SGML parent
    node that contains no data.

    Most subaggregates have been flattened so that data-bearing Elements are
    directly accessed as attributes of the containing Aggregate.

    The constructor takes an instance of ofx.Parser.Element, but this only
    works for simple Aggregates that don't contain structure that needs to
    be maintained (e.g. lists or subaggregates).  In general, we need to call
    Aggregate.from_etree() as a constructor to do pre- and post-processing.
    """
    # Sequence of subaggregates to strip before _flatten()ing and staple
    # on afterward intact
    _subaggregates = ()
    # Sequence of unsupported subaggregates to strip and remove
    _unsupported = ()

    def __init__(self, **kwargs):
        # Set instance attributes for all input kwargs that are defined by
        # the class
        for attr in self.elements:
            value = kwargs.pop(attr, None)
            try:
                setattr(self, attr, value)
            except ValueError as e:
                msg = "Can't set {}.{} to {}: {}".format(
                    self.__class__.__name__, attr, value, e.args[0]
                )
                raise ValueError(msg)

        # Check that no kwargs (not part of the class definition) are left over
        if kwargs:
            msg = "Parsed Element {} does not define {}".format(
                            self.__class__.__name__, str(list(kwargs.keys()))
            )
            raise ValueError(msg)

    @property
    def elements(self):
        """ dict of all Aggregate attributes that are Elements """
        d = {}
        for m in self.__class__.__mro__:
            d.update({k: v for k, v in m.__dict__.items()
                      if isinstance(v, Element)})
        return d

    @staticmethod
    def from_etree(elem):
        """
        Look up the Aggregate subclass for a given ofx.Parser.Element and
        feed it the Element to instantiate an Aggregate corresponding to the
        Element.tag.

        Main entry point for type conversion from ElementTree to Aggregate;
        invoked by Parser.OFXResponse which is in turn invoked by
        Parser.OFXTree.convert()
        """
        try:
            SubClass = getattr(ofxtools.models, elem.tag)
        except AttributeError:
            msg = "ofxtools.models doesn't define {}".format(elem.tag)
            raise ValueError(msg)
        SubClass._verify(elem)
        SubClass._groom(elem)
        subaggs = SubClass._preflatten(elem)
        attributes = SubClass._flatten(elem)
        instance = SubClass(**attributes)
        SubClass._postflatten(instance, subaggs)
        return instance

    @staticmethod
    def _verify(elem):
        """
        Enforce Aggregate-level structural constraints of the OFX spec.

        Extend in subclass.
        """
        pass

    @staticmethod
    def _groom(elem):
        """
        Modify incoming XML data to play nice with our Python scheme.

        Extend in subclass.
        """
        pass

    @staticmethod
    def _mutex(elem, mutexes):
        """
        Throw an error for Elements containing sub-Elements that are
        mutually exclusive per the OFX spec, and which will cause
        problems for _flatten().

        Used in subclass _verify() methods.
        """
        for mutex in mutexes:
            if (elem.find(mutex[0]) is not None and
                    elem.find(mutex[1]) is not None):
                msg = "{} may not contain both {} and {}".format(
                    elem.tag, mutex[0], mutex[1])
                raise ValueError(msg)

    @classmethod
    def _preflatten(cls, elem):
        """
        Strip any elements that will blow up _flatten(), and store them for
        postprocessing as stapled-on subaggregates.

        Returns a 'subaggregates' dict of {name: value}, where:
            * name is a string (the attribute name)
            * value is either:
                - an Aggregate instance, or
                - a list of Aggregate instances

        Extend in subclass.
        """
        subaggs = {}

        for tag in cls._subaggregates:
            subagg = elem.find(tag)
            if subagg is not None:
                elem.remove(subagg)
                subaggs[tag] = subagg

        # Unsupported subaggregates
        for tag in cls._unsupported:
            subagg = elem.find(tag)
            if subagg is not None:
                elem.remove(subagg)

        return subaggs

    @classmethod
    def _flatten(cls, element):
        """
        Recurse through aggregate and flatten; return an un-nested dict.

        This method will blow up if the aggregate contains LISTs, or if it
        contains multiple subaggregates whose namespaces will collide when
        flattened (e.g. BALAMT/DTASOF elements in LEDGERBAL and AVAILBAL).
        Remove all such hair from any element before passing it in here.
        """
        aggs = {}
        leaves = {}
        for child in element:
            tag = child.tag
            data = child.text or ''
            data = data.strip()
            if data:
                # it's a data-bearing leaf element.
                assert tag not in leaves
                # Silently drop all private tags (e.g. <INTU.XXXX>)
                if '.' not in tag:
                    leaves[tag.lower()] = data
            else:
                # it's an aggregate.
                assert tag not in aggs
                aggs.update(cls._flatten(child))
        # Double-check no key collisions as we flatten aggregates & leaves
        for key in aggs:
            assert key not in leaves
        leaves.update(aggs)

        return leaves

    @staticmethod
    def _postflatten(instance, subaggs):
        """
        Staple on attributes and subaggregates stripped during preprocessing.
        """
        for tag, elem in subaggs.items():
            if isinstance(elem, ET.Element):
                setattr(instance, tag.lower(), Aggregate.from_etree(elem))
            elif isinstance(elem, (list, UserList)):
                lst = [Aggregate.from_etree(e) for e in elem]
                setattr(instance, tag.lower(), lst)
            else:
                msg = "'{}' must be type {} or {}, not {}".format(
                    tag, 'ElementTree.Element', 'list', type(elem)
                )
                raise ValueError(msg)

    def __repr__(self):
        attrs = ['%s=%r' % (attr, str(getattr(self, attr)))
                 for attr in self.elements
                 if getattr(self, attr) is not None]
        return '<%s %s>' % (self.__class__.__name__, ' '.join(attrs))


class FI(Aggregate):
    """
    OFX section 2.5.1.8

    <FI> aggregates are optional in SONRQ/SONRS; not all firms use them.
    Therefore we don't mark ORG as required, so SONRS (which inherits from FI)
    won't throw an error if <FI> is absent.
    """
    org = String(32)
    fid = String(32)


class STATUS(Aggregate):
    """ OFX section 3.1.5 """
    code = Integer(6, required=True)
    severity = OneOf('INFO', 'WARN', 'ERROR', required=True)
    message = String(255)


class SONRS(FI, STATUS):
    """ OFX section 2.5.1.6 """
    dtserver = DateTime(required=True)
    userkey = String(64)
    tskeyexpire = DateTime()
    language = OneOf(*LANG_CODES)
    dtprofup = DateTime()
    dtacctup = DateTime()
    sesscookie = String(1000)
    accesskey = String(1000)


class CURRENCY(Aggregate):
    """
    OFX section 5.2

    <CURRENCY> aggregates are mostly optional, so its elements
    (which are mandatory per the OFX spec) aren't marked as required.
    """
    cursym = OneOf(*CURRENCY_CODES)
    currate = Decimal(8)


class ORIGCURRENCY(CURRENCY):
    """
    OFX section 5.2

    <ORIGCURRENCY> aggregates are mostly optional, so its elements
    (which are mandatory per the OFX spec) aren't marked as required.
    """
    curtype = OneOf('CURRENCY', 'ORIGCURRENCY')

    @staticmethod
    def _verify(elem):
        """
        Aggregates may not contain both CURRENCY and ORIGCURRENCY per OFX spec.
        """
        super(ORIGCURRENCY, ORIGCURRENCY)._verify(elem)

        mutexes = [("CURRENCY", "ORIGCURRENCY")]
        ORIGCURRENCY._mutex(elem, mutexes)

    @classmethod
    def _preflatten(cls, elem):
        """
        See OFX spec section 5.2 for currency handling conventions.
        Flattening the currency definition leaves only the CURRATE/CURSYM
        elements, leaving no indication of whether these were sourced from
        a CURRENCY aggregate or ORIGCURRENCY.  Since this distinction is
        important to interpreting transactions in foreign correncies, we
        preserve this information by adding a nonstandard curtype element.
        """
        subaggs = super(ORIGCURRENCY, cls)._preflatten(elem)

        curtype = elem.find('.//CURRENCY') or elem.find('.//ORIGCURRENCY')
        if curtype is not None:
            ET.SubElement(elem, 'CURTYPE').text = curtype.tag

        return subaggs


class PAYEE(Aggregate):
    """ OFX section 12.5.2.1 """
    # name = String(32, required=True)
    name = NagString(32, required=True)
    addr1 = String(32, required=True)
    addr2 = String(32)
    addr3 = String(32)
    city = String(32, required=True)
    state = String(5, required=True)
    postalcode = String(11, required=True)
    country = OneOf(*COUNTRY_CODES)
    phone = String(32, required=True)


class SECID(Aggregate):
    """ OFX section 13.8.1 """
    uniqueid = String(32, required=True)
    uniqueidtype = String(10, required=True)


class OFXELEMENT(Aggregate):
    """ OFX section 2.7.2 """
    tagname = String(32)
    name = String(32)
    tagtype = String(20)
    tagvalue = String(1000)
