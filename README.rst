``ofxtools``
============

Description
-----------

| ``ofxtools`` is a Python library for working with Open Financial
  Exchange (OFX)
| data - both OFXv1 (SGML) and OFXv2 (pure XML) - which is the standard
  format
| for downloading financial information from banks and stockbrokers.

| ``ofxtools`` is compatible with Python version 2.7+ and 3.1+.
| It depends on `Requests`_

The primary facilities provided include:

-  The ``OFXClient`` class; which dowloads OFX statements from the
   Internet
-  The ``OFXTree`` class; which parses OFX data into a standard
   ElementTree
   structure for further processing in Python.
-  The ``OFXResponse`` class; which validates and converts OFX data
   parsed by
   OFXParser into Python types and exposes them through more Pythonic
   attribute access (e.g. ``OFXResponse.statements[0].ledgerbal``).

Installation
============

Use the Python user installation scheme:

::

    python setup.py install --user

| In addition to the Python package, this will also install a script
  ``ofxget``
| in ``~/.local/bin``, and its sample configuration file in
  ``~/.config/ofxtools``.

Basic Usage to Download OFX
===========================

-  Copy ``~/.config/ofxtools/ofxget_example.cfg`` to
   ``~/.config/ofxtools/ofxget.cfg`` and edit:
-  Add a section for your financial institution, including URL, account
   information, login, etc.
-  See comments within.
-  Execute ``ofxget`` with appropriate arguments, for example:

``ofxget amex stmt -s 20140101 -e 20140630 > foobar.ofx``

See the ``--help`` for explanation of the script options.

Parser Usage Example
--------------------

.. code:: python

    >>> from ofxtools import OFXTree
    >>> tree = OFXTree()
    >>> tree.parse('stmtrs.ofx')
    >>> response = tree.convert()
    >>> response
    <OFXResponse fid='1001' org='NCH' dtserver='2005-10-29 10:10:03' len(statements)=1 len(securities)=0>
    >>> stmt = response.statements[0]
    >>> stmt
    <BankStatement account=<BANKACCTFROM acctid='999988' accttype='CHECKING' bankid='121099999'> currency=USD ledgerbal=<LEDGERBAL balamt='200.29' dtasof='2005-10-29 11:20:00'> availbal=<AVAILBAL balamt='200.29' dtasof='2005-10-29 11:20:00'> len(other_balances)=0 len(transactions)=2>
    >>> stmt.transactions[-1]
    <STMTTRN dtposted='2005-10-20 00:00:00' trntype='ATM' trnamt='-300.00' fitid='00003' dtuser='2005-10-20 00:00:00'>

Contributing
------------

| If you want to contribute with this project, create a virtualenv and
  install
| all development requirements:

::

    virtualenv .venv
    source .venv/bin/activate
    pip install -r requirements-development.txt

Then, run the tests with ``make``:

::

    make test

Or directly with ``nosetests``:

::

    nosetests -dsv --with-yanc --with-coverage --cover-package ofxtools

Feel free to `create pull requests`_ on `ofxtools repository on GitHub`_.

.. _Requests: http://docs.python-requests.org/en/master/
.. _create pull requests: https://help.github.com/articles/using-pull-requests/
.. _ofxtools repository on GitHub: https://github.com/csingley/ofxtools
