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

Poke around in the Makefile; there's a few developer-friendly commands there.

If you commit working tests for your code, you'll be my favorite person.

Feel free to `create pull requests`_ on `ofxtools repository on GitHub`_.


.. _create pull requests: https://help.github.com/articles/using-pull-requests/
.. _ofxtools repository on GitHub: https://github.com/csingley/ofxtools
