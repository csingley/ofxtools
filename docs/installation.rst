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
You need Python 3.10 or later to use ``ofxtools``.

In order to use the OFX client to download OFX files, your Python installation
needs to be able to validate SSL certificates.  macOS users who installed
Python from python.org may need to install root certificates separately:

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
    $ pip install -e ".[dev]"


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
