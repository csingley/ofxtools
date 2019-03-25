Open Financial Exchange (OFX) Tools for Python
==============================================
.. Travis CI badge
.. .. image:: https://travis-ci.org/csingley/ofxtools.svg?branch=master
    :target: https://travis-ci.org/csingley/ofxtools

.. Codecov badge
.. .. image:: https://codecov.io/gh/csingley/ofxtools/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/csingley/ofxtools

``ofxtools`` is a Python library for working with Open Financial Exchange (OFX)
data - the standard format for downloading financial information from banks
and stockbrokers.  OFX data is widely provided by financial institutions so
that their customers can import transactions into financial management
software such as Quicken, Microsoft Money, or GnuCash.

If you want to download your transaction data outside of one of these
programs - if you wish to develop a Python application to use this data -
if you need to generate your own OFX-formatted data... ``ofxtools`` is for you!

What is it?
-----------
``ofxtools`` requests, consumes and
produces both OFXv1 (SGML) and OFXv2 (XML) formats.
It converts serialized markup to/from native Python objects of
the appropriate data type, while preserving structure.
It also handles Quicken's QFX format, although it ignores Intuit's proprietary
extension tags.

In a nutshell, ``ofxtools`` makes it simple to get OFX data and extract it,
or export your data in OFX format.

``ofxtools`` takes a comprehensive, standards-based approach to processing OFX.
It targets compliance with the `OFX specification`_, specifically OFX versions
1.6 and 2.03.

The OFX message sets are defined in Sections 7-14 of the spec.  Of these,
so far ``ofxtools`` complies with nearly all of
    * Section 7 (financial institution profile)
    * Section 8 (service activation; account information)
    * Section 11 (banking)
    * Section 13 (investments)

This should cover the great majority of real-world OFX use cases.  A particular
focus of ``ofxtools`` is full support of the OFX investment message set,
which has been somewhat neglected by the Python community.

The major item remaining on the ``ofxtools`` "to do" list is implementing
OFX Section 12 (payments).  Absent a compelling use case, I can't see
implementing Section 9 (email in OFX) or 14 (bill presentment).  Section 10
(recurring payments) is a low priority.

Some care has been taken with the data model to make it easily maintainable
and extensible.  The ``ofxtools.models`` subpackage contains simple, direct
translations of the relevant sections of the OFX specification.  Using existing
models as templates, it's quite straightforward to define new models and
cover more of the spec as needed (the odd corner case notwithstanding).

More than 10 years' worth of OFX data from various financial institutions
has been run through the ``ofxtools`` parser, with the results checked.  Test
coverage is high.

Where is it?
------------
Full documentation is available at `Read the Docs`_.

For ease of installation, ``ofxtools`` is released on `PyPI`_.

Development of ``ofxtools`` is centralized at `GitHub`_, where you will find
a `bug tracker`_.

Dependencies
------------
``ofxtools`` is compatible with Python version 3.1+.  Its only external
dependency is `Requests`_.

**NOTE: As of version 0.6, ``ofxtools`` no longer supports Python version 2,
which goes EOL 2019-01-01.**

.. _OFX specification: http://www.ofx.net/downloads.html
.. _Requests: http://docs.python-requests.org/en/master/
.. _Read the Docs: https://ofxtools.readthedocs.io/
.. _GitHub: https://github.com/csingley/ofxtools
.. _bug tracker: https://github.com/csingley/ofxtools/issues
.. _PyPI: https://pypi.python.org/pypi/ofxtools
