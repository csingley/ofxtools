.. _contributing:

Contributing to ``ofxtools``
============================
To start hacking on the source, see the section entitled "Developer's
installation" under :ref:`installation`.

Make sure your changes haven't broken anything by running the tests:

.. code:: bash

    python `which nosetests` -dsv  --with-coverage --cover-package ofxtools

Or even better, use ``make``:

.. code:: bash

    make test

After running one of the above commands, you can view a report of which parts
of the code aren't covered by tests:

.. code:: bash

    coverage report -m

Poke around in the Makefile; there's a few developer-friendly commands there.

Feel free to `create pull requests`_ on `ofxtools repository on GitHub`_.

If you commit working tests for your code, you'll be my favorite person.


Adding New OFX Messages
=======================
As an example, I'll document the implementation of bank account transfer
messages (``INTRARQ`` / ``INTRARS``).

Download a copy of the `OFXv2.03`_ spec.  The messages we want to implement
are located in Section 11.7.  Since these messages appear in the hierarchy
under ``BANKMSGSRQV1`` / ``BANKMSGSRSV1``, they belong in
``ofxtools.models.bank``.

First we need to create classes for any new aggregates appearing in the
basic ``*RQ`` / ``*RS`` - in this case, ``XFERINFO``.

.. image:: xferinfo.png

Here's how we translate the spec info Python.

.. code:: python

    from ofxtools.models.base import Aggregate, SubAggregate
    from ofxtools.Types import String, Decimal, DateTime, OneOf

    class XFERINFO(Aggregate):
        """ OFX section 11.3.5 """

        bankacctfrom = SubAggregate(BANKACCTFROM)
        ccacctfrom = SubAggregate(CCACCTFROM)
        bankacctto = SubAggregate(BANKACCTTO)
        ccacctto = SubAggregate(CCACCTTO)
        trnamt = Decimal(required=True)
        dtdue = DateTime()

We create a subclass of ``ofxtools.models.base.Aggregate``, where the class
name is the OFX tag in ALL CAPS (so that ``Aggregate.from_etree()`` can find
it).  We define a class attribute for each tag that can appear under
``XFERINFO``.  Container aggregates are defined with
``ofx.models.base.SubAggregate``; pass in the relevant model class.
Data-bearing elements are defined as a subclass of ``ofxtools.Types.Element`` -
``Decimal`` in the case of ``TRNAMT`` (which is specified as an amount of
money) and ``DateTime`` for ``DTDUE`` (which the is specified as datetime).
The spec prints ``TRNAMT`` in **bold**, which means it must appear in any
valid ``XFERINFO`` aggregate, so we pass ``required=True`` in its definition.

The spec also states that either ``BANKACCTFROM`` or ``CCACCTFROM`` must
appear in ``XFERINFO``, as well as either ``BANKACCTTO`` or ``CCACCTTO``.
We can't simply pass in ``required=True`` to the relevant class attributes -
that would require all of them to appear in any valid ``XFERINFO`` instance,
which is clearly not right.  Instead of attribute-level validation, these
kinds of class-level constraints are enforced by separate class attributes.
In this case, we employ the awkwardly-named
``ofxtools.models.base.Aggregate.requiredMutexes``, which requires that one
of each tuple must appear.  Note the lower-case naming; this validation is
performed by ``Aggregate.__init__()`` and refers to instance attributes.

.. code:: python

    class XFERINFO(Aggregate):
        """ OFX section 11.3.5 """

        bankacctfrom = SubAggregate(BANKACCTFROM)
        ccacctfrom = SubAggregate(CCACCTFROM)
        bankacctto = SubAggregate(BANKACCTTO)
        ccacctto = SubAggregate(CCACCTTO)
        trnamt = Decimal(required=True)
        dtdue = DateTime()

    requiredMutexes = [
        ('bankacctfrom', 'ccacctfrom'),
        ('bankacctto', 'ccacctto'),
    ]

The spec also says that ``TRNAMT`` "should be specified as a positive number",
but``ofxtools`` doesn't yet have any validators that enforce this constraint,
so we're done with this tag.

With that in hand, defining the request aggregate (``INTRARQ``) is simple.

.. image:: intrarq.png

.. code:: python

    class INTRARQ(Aggregate):
        """ OFX section 11.7.1.1 """

        xferinfo = SubAggregate(required=True)

Now we we move on to the corresponding server response aggregate (``INTRARS``).
``INTRARS`` contains a new kind of subaggregate (``XFERPRCSTS``) for the server
to indicate transfer status; we'll need to implement that first so that
``INTRARS`` can refer to it.  Here's the spec.

.. image:: xferprcsts.png

The ``XFERPRCCODE`` element only allows specifically enumerated values.  Our
validator type for that is ``ofxtools.Types.OneOf``.

.. code:: python

    class XFERPRCSTS(Aggregate):
        """ OFX section 11.3.6 """

        xferprccode = OneOf('WILLPROCESSON', 'POSTEDON', 'NOFUNDSON',
                            'CANCELEDON', 'FAILEDON', required=True)
        dtxferprc = DateTime(required=True)

Having ``XFERPRCSTS``, we proceed to define the response aggregate.

.. image:: intrars.png


This features a new kind of constraint - ``INTRARS`` aggregates may contain
either a ``DTXFERPRJ`` element or a ``DTPOSTED`` element, but not both.  The
lack of boldface type indicates that it's valid OFX to include neither.  Such
a constraint is expressed via ``ofxtools.models.base.Aggregate.optionalMutexes``
which (like ``mandatoryMutexes``) contains lower-case attribute names for use
by ``Agreggate.__init__()``.

.. code:: python

    from ofxtools.models.i18n import CURRENCY_CODES

    class INTRARS(Aggregate):
        """ OFX section 11.7.1.2 """

        curdef = OneOf(*CURRENCY_CODES, required=True)
        srvrtid = String(10, required=True)
        xferinfo = SubAggregate(required=True)
        dtxferprj = DateTime()
        dtposted = DateTime()
        recsrvrtid = String(10)
        xferprcsts = SubAggregate(XFERPRCSTS)

        optionalMutexes = [('dtxferprj', 'dtposted')]

The spec for default currency (``CURDEF``) looks innocent enough, but the
definition of *currsymbol* type in Section 3.2.11 refers to an enumeration of
the dozens of three-letter currency codes in ISO-4217.  Happily we've already
defined them in ``ofxtools.models.i18n``, so we just use them here.

Also note the ``ofxtools.Types.String`` validator, which we haven't seen yet;
it takes an (optional) length argument of type ``int``.  

Now, in addition to creating account transfers with ``INTRARQ``, Sections
17.2 - 17.3 of the OFX spec also define messages for clients to modify or
cancel existing transfer requests (along with corresponding server responses,
naturally).  We'll just bang these out.

.. image:: intramodrq.png

.. code:: python

    class INTRAMODRQ(Aggregate):
        """ OFX section 11.7.2.1 """

        srvrtid = String(10, required=True)
        xferinfo = SubAggregate(required=True)

.. image:: intramodrs.png

.. code:: python

    class INTRAMODRS(Aggregate):
        """ OFX section 11.7.2.2 """

        srvrtid = String(10, required=True)
        xferinfo = SubAggregate(required=True)
        xferprcsts = SubAggregate(XFERPRCSTS)

.. image:: intracanrq.png

.. code:: python

    class INTRACANRQ(Aggregate):
        """ OFX section 11.7.3.1 """

        srvrtid = String(10, required=True)

.. image:: intracanrq.png

.. code:: python

    class INTRACANRS(Aggregate):
        """ OFX section 11.7.3.2 """

        srvrtid = String(10, required=True)

That brings us to the end of the section, but we're not quite done yet.  Every
request or response in OFX is transmitted in a transaction wrapper bearing a
unique identifier, as indicated in the spec by language like "The <INTRARS>
response must appear within an <INTRATRNRS> transaction wrapper".
The structure of ``*TRNRQ`` and ``*TRNRS`` wrappers are defined in Section
2.4.6.1 of the OFX spec.

.. image:: trnrq_trnrs.png

This commonly-repeated pattern is factored out in ``ofxtools.models.common``
as base classes for the various ``*TRNRQ`` / ``*TRNRS`` classes to inherit.

.. code:: python

    class TrnRq(Aggregate):
        """
        Base class implementing common attributes for transaction request wrappers.

        OFX section 2.4.6.1
        """

        trnuid = String(36, required=True)
        cltcookie = String(32)
        tan = String(80)


    class TrnRs(Aggregate):
        """
        Base class implementing common attributes for transaction response wrappers.

        OFX section 2.4.6.1
        """

        trnuid = String(36, required=True)
        status = SubAggregate(STATUS, required=True)
        cltcookie = String(32)

Let's use these base classes to implement our transaction wrappers.  We just
need to add attributes for each type of request/response they can wrap, along
with class-level constraints enforcing the choice of a single wrapped entity.
Note that ``*TRNRQ`` wrappers **must** contain a request, while the spec
allows empty ``*TRNRS`` wrappers, so we set ``requiredMutexes`` and
``optionalMutexes`` respectively.

.. code:: python

    from ofxtools.models.common import TrnRq, TrnRs

    class INTRATRNRQ(TrnRq):
        """ OFX section 11.7.1.1 """

        intrarq = SubAggregate(STMTRQ)
        intramodrq = SubAggregate(INTRAMODRQ)
        intracanrq = SubAggregate(INTRACANRQ)

        requiredMutexes = [("intrarq", "intramodrq", "intracanrq")]


    class INTRATRNRS(TrnRs):
        """ OFX section 11.7.1.2 """

        intrars = SubAggregate(INTRARS)
        intramodrs = SubAggregate(INTRAMODRS)
        intracanrs = SubAggregate(INTRACANRS)

        optionalMutexes = [
            (
                "intrars",
                "intramodrs",
                "intracanrs",
                "intermodrs",
                "intercanrs",
                "intermodrs",
            )
        ]

But wait, there's more!  Notices peppering OFX Section 11.7 alert us to the
application of the synchronization protocol, which directs us to Section 11.12.2.

.. image:: trnrq_trnrs.png

The requirement that each ``*SYNCRQ`` / ``*SYNCRS`` may contain a variable
number of transaction wrappers means that we can't use the ``Aggregate`` base
class, where every child element corresponds to a class attribute.

For this kind of structure, we instead inherit from ``ofxtools.models.base.List``.
Subclasses of ``List`` define tag validators in the usual manner for metadata
(i.e. unique children, which are accessed as instance attributes), but the
(possibly duplicated) sub-aggregates identified by the OFX spec as list
members are defined using the ``dataTags`` class attribute and accessed via the
Python sequence API.  Here's how it looks.

.. code:: python

    from ofxtools.models.base import List
    from ofxtools.models.bank import BANKACCTFROM, CCACCTFROM
    from ofxtools.Types import Bool

    class INTRASYNCRQ(List):
        """ OFX section 11.12.2.1 """
        tokenonly = Bool()
        refresh = Bool()
        rejectifmissing = Bool(required=True)
        bankacctfrom = SubAggregate(BANKACCTFROM)
        ccacctfrom = SubAggregate(CCACCTFROM)

        dataTags = ["INTRATRNRQ"]
        requiredMutexes = [
            ("token", "tokenonly", "refresh"),
            ("bankacctfrom", "ccacctfrom") ]
        ]


    class INTRASYNCRS(List):
        """ OFX section 11.12.2.2 """
        token = String(10, required=True)
        lostsync = Bool()

        bankacctfrom = SubAggregate(BANKACCTFROM)
        ccacctfrom = SubAggregate(CCACCTFROM)

        dataTags = ["INTRATRNRS"]
        requiredMutexes = [ ("bankacctfrom", "ccacctfrom") ]

Note that `dataTags`` are specified as sequences of ALL CAPS strings,
corresponding to the OFX tags that will appear in incoming aggregates.  Order
is significant; these tags must be defined in the same order laid out in the
spec.

Finally, we just need to add our newly-defined models to the API published by
the ``ofxtools.models.bank`` module, so the parser can find them.

.. code:: python

    __all__ = [
        ...
        "XFERINFO",
        "XFERPRCSTS",
        "INTRARQ",
        "INTRARS",
        "INTRAMODRQ",
        "INTRACANRQ",
        "INTRAMODRS",
        "INTRACANRS",
        "INTRATRNRQ",
        "INTRATRNRS",
        "INTRASYNCRQ",
        "INTRASYNCRS",
        ...
    ]

 All done!


.. _create pull requests: https://help.github.com/articles/using-pull-requests/
.. _ofxtools repository on GitHub: https://github.com/csingley/ofxtools
.. _OFXv2.03: http://ofx.net/downloads/OFX2.0.3.zip
