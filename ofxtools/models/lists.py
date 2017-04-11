# vim: set fileencoding=utf-8
"""
"""
# stdlib imports
from collections import UserList

# local imports
from ofxtools.models import Aggregate
from ofxtools.Types import DateTime


class List(Aggregate, UserList):  # pylint: disable=too-many-ancestors
    """
    Base class for OFX *LIST
    """
    def __init__(self, **kwargs):
        UserList.__init__(self)
        Aggregate.__init__(self, **kwargs)

    def __hash__(self):
        """
        HACK - as a subclass of UserList, List is unhashable, but we need to
        use it as a dict key in Type.Element.{__get__, __set__}
        """
        return object.__hash__(self)

    @classmethod
    def _preflatten(cls, elem):
        """
        UserList is a wrapper around a standard list, accessible through its
        'data' attribute.  If we create a synthetic subaggregate
        named 'data', whose value is a list of Etree.Elements, then
        Aggregate._postflatten() will set List.data to a list of converted
        Aggregates, and the Userlist interface will work normally.
        """
        subaggs = super(List, cls)._preflatten(elem)

        lst = []

        # The first two children of *TRANLIST are DTSTART/DTEND; don't remove.
        dataStart = ('TRANLIST' in cls.__name__) * 2

        for tran in elem[dataStart:]:
            lst.append(tran)
            elem.remove(tran)
        subaggs['data'] = lst

        return subaggs


class BANKTRANLIST(List):  # pylint: disable=too-many-ancestors
    """ OFX section 11.4.2.2 """
    dtstart = DateTime(required=True)
    dtend = DateTime(required=True)


class INVTRANLIST(BANKTRANLIST):  # pylint: disable=too-many-ancestors
    """ OFX section 13.9.2.2 """
    pass


class SECLIST(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.4.4 """
    pass


class BALLIST(List):  # pylint: disable=too-many-ancestors
    """ OFX section 11.4.2.2 & 13.9.2.7 """
    pass


class MFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    pass


class FIMFASSETCLASS(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.8.5.3 """
    pass


class INVPOSLIST(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.9.2.2 """
    pass


class INVOOLIST(List):  # pylint: disable=too-many-ancestors
    """ OFX section 13.9.2.2 """
    pass


class OFXEXTENSION(List):  # pylint: disable=too-many-ancestors
    """ OFX section 2.7.2 """
    pass
