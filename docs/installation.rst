.. _installation:

Installing ``ofxtools``
=======================
You have a few options to install ``ofxtools``.  If you like, you can install
it in a `virtual environment`_, but since ``ofxtools`` has no external
dependencies, that doesn't really gain you much.

A simpler option for keeping clutter out of your system Python site is the
`user install`_ option, which is recommended if only one system user needs
the package (the normal situation).

Installation dependencies
-------------------------
You need to install Python 3 (at least version 3.6) in order to use ``ofxtools``.
It won't work at all under Python 2.

In order to use the OFX client to download OFX files, your Python 3 installation
needs to be able to validate SSL certificates.  Users of Mac OS X should heed
the following note from the `ReadMe.rtf` included with the Python installer as
of version 3.6:

    This variant of Python 3.6 now includes its own private copy of OpenSSL 1.0.2.
    Unlike previous releases, the deprecated Apple-supplied OpenSSL libraries are
    no longer used.  This also means that the trust certificates in system and user
    keychains managed by the Keychain Access application and the security command
    line utility are no longer used as defaults by the Python ssl module.
    For 3.6.0, a sample command script is included in /Applications/Python 3.6
    to install a curated bundle of default root certificates from the
    third-party `certifi`_ package.

To facilitate keeping this important security package up to date, it's advisable
for Mac users to instead employ `pip`:

.. code-block:: bash

    $ pip install certifi


Standard installation
---------------------
If you just want to use the ``ofxtools`` library, and you don't have any
special needs, you should probably install the most recent release on `PyPI`_:

.. code-block:: bash

    $ pip install --user ofxtools

Or if you want to install it systemwide, as root just run:

.. code-block:: bash

    $ pip install ofxtools


Bleeding edge installation
--------------------------
To install the most recent prerelease (which is where the magic happens, and
also the bugs), you can download the `current master`_, unzip it, and install
via the included setup file:

.. code-block:: bash

    $ pip install --user .


Developer's installation
------------------------
If you want to hack on ``ofxtools``, you should clone the source and install
is in `development mode`_:

.. code-block:: bash

    $ git clone https://github.com/csingley/ofxtools.git
    $ cd ofxtools
    $ pip install -e .
    $ pip install -r ofxtools/requirements-development.txt


Extra goodies
-------------
In addition to the Python package, these methods will also install the
``ofxget`` script - a basic command line interface for downloading files from
OFX servers.  ``pip uninstall ofxtools`` will remove this script along with
the package.


.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
.. _user install: https://pip.pypa.io/en/stable/user_guide/#user-installs
.. _PyPI: https://pypi.python.org/pypi/ofxtools
.. _current master: https://github.com/csingley/ofxtools/archive/master.zip
.. _development mode: https://setuptools.readthedocs.io/en/latest/setuptools.html?highlight=development%20mode#develop-deploy-the-project-source-in-development-mode
.. _certifi: https://pypi.org/project/certifi/
