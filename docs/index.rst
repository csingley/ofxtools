.. You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _index:

Open Financial Exchange (OFX) Tools for Python
==============================================
``ofxtools`` is a Python library for working with Open Financial Exchange (OFX)
data - the standard format for downloading financial information from banks
and stockbrokers.  OFX data is widely provided by financial institutions so
that their customers can import transactions into financial management
software such as Quicken, Microsoft Money, or GnuCash.

If you want to download your transaction data outside of one of these
programs - if you wish to develop a Python application to use this data -
if you need to generate your own OFX-formatted data... ``ofxtools`` is for you!

``ofxtools`` consumes and produces both OFXv1 (SGML) and OFXv2 (XML) formats.
It also handles Quicken's QFX format, although it ignores Intuit's proprietary
extension tags.  It targets compliance with the `OFX specification`_,
specifically OFX versions 1.6 and 2.02.

``ofxtools`` is compatible with Python version 2.7+ and 3.1+.  Its only
external dependency is `Requests`_.

Full documentation is available at `Read the Docs`_.

Development of ``ofxtools`` is centralized at `GitHub`_, where you will find
a `bug tracker`_.

For ease of installation, ``ofxtools`` is released on `PyPI`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   client
   parser
   ofxalchemy
   contributing
   resources


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _OFX specification: http://www.ofx.net/downloads.html
.. _Requests: http://docs.python-requests.org/en/master/
.. _Read the Docs: https://ofxtools.readthedocs.io/
.. _GitHub: https://github.com/csingley/ofxtools
.. _bug tracker: https://github.com/csingley/ofxtools/issues
.. _PyPI: https://pypi.python.org/pypi/ofxtools
