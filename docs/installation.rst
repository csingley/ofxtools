.. _installation:

Installing ``ofxtools``
=======================
You have a few options to install ``ofxtools``.  If you like, you can install
it in a `virtual environment`_, but since ``ofxtools`` has no external
dependencies, that doesn't really gain you much.

A simpler option for keeping clutter out of your system Python site is the
`user install`_ option, which is recommended if only one system user needs
the package (the normal situation).

Standard installation
---------------------
If you just want to use the ``ofxtools`` library, and you don't have any
special needs, you should probably install the most recent release on `PyPI`_:

.. code-block:: bash

    pip install --user ofxtools

Or if you want to install it systemwide, as root just run:

.. code-block:: bash

    pip install ofxtools


Bleeding edge installation
--------------------------
To install the most recent prerelease (which is where the magic happens, and
also the bugs), you can download the `current master`_, unzip it, and install
via the included setup file:

.. code-block:: bash

    pip install .


Developer's installation
------------------------
If you want to hack on ``ofxtools``, you should clone the source and install
is in `development mode`_:

.. code-block:: bash

    git clone https://github.com/csingley/ofxtools.git
    pip install -e .
    pip install -r ofxtools/requirements-development.txt


Extra goodies
-------------
In addition to the Python package, these methods will also install the
``ofxget`` script in ``~/.local/bin`` - a simple command line interface for
downloading files from OFX servers - and its sample configuration file in
``~/.config/ofxtools``.


.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
.. _user intall: https://pip.pypa.io/en/stable/user_guide/#user-installs
.. _PyPI: https://pypi.python.org/pypi/ofxtools
.. _current master: https://github.com/csingley/ofxtools/archive/master.zip
.. _development mode: https://setuptools.readthedocs.io/en/latest/setuptools.html?highlight=development%20mode#develop-deploy-the-project-source-in-development-mode
