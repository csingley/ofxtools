.. _installation:

Installing ``ofxtools``
=======================
You have a few options to install ``ofxtools``.  For any installation method,
it's recommended to install ``ofxtools`` in a `virtual environment`_.

Standard installation
---------------------
If you just want to use the ``ofxtools`` library, and you don't have any
special needs, you should probably install the most recent release on `PyPI`_:

::

    pip install ofxtools

Your virtualenv should already have ``pip`` installed.

Bleeding edge installation
--------------------------
To install the most recent prerelease (which is where the magic happens, and
also the bugs), you can download the `current master`_, unzip it, and install
via the included setup file:

.. code-block:: bash

    pip install -r requirements.txt

You did remember to run this in a `virtual environment`_, didn't you?


Developer's installation
------------------------
If you want to hack on ``ofxtools``, here's the way to get started:

.. code-block:: bash

    git clone https://github.com/csingley/ofxtools.git
    pip install -r ofxtools/requirements-development.txt

Of course, this belongs inside a `virtual enviroment`_ - you know the drill.


Extra goodies
-------------
In addition to the Python package, these methods will also install the
``ofxget`` script in ``~/.local/bin`` - a simple command line interface for
downloading files from OFX servers - and its sample configuration file in
``~/.config/ofxtools``.


.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
.. _PyPI: https://pypi.python.org/pypi/ofxtools
.. _current master: https://github.com/csingley/ofxtools/archive/master.zip
