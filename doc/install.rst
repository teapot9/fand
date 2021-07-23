============
Installation
============

Python dependencies
===================

Server
------

 - pySMART (homepage__, pypi__, source__): access drives SMART data
 - psutil (homepage__, pypi__, source__, doc__): access CPU temperatures

__ https://github.com/freenas/py-SMART
__ https://pypi.org/project/pySMART/
__ https://github.com/freenas/py-SMART

__ https://github.com/giampaolo/psutil
__ https://pypi.org/project/psutil/
__ https://github.com/giampaolo/psutil
__ https://psutil.readthedocs.io/

Raspberry Pi client
-------------------

 - gpiozero (homepage__, pypi__, source__, doc__):
   access GPIO for PWM and tachometer signals
 - gpiozero's native pin factory does not currently supports PWM (sept 2020),
   you need one of the following packages:

    - RPi.GPIO (homepage__, pypi__, source__, doc__):
      does not supports hardware PWM, only uses software PWM
    - pigpio (homepage__, pypi__, source__, doc__):
      supports hardware PWM but cannot work with Linux's lockdown LSM
    - RPIO (homepage__, pypi__, source__, doc__):
      unmaintained

__ https://github.com/gpiozero/gpiozero
__ https://pypi.org/project/gpiozero/
__ https://github.com/gpiozero/gpiozero
__ https://gpiozero.readthedocs.io/

__ https://sourceforge.net/p/raspberry-gpio-python/
__ https://pypi.org/project/RPi.GPIO/
__ https://sourceforge.net/p/raspberry-gpio-python/
__ https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/

__ http://abyz.me.uk/rpi/pigpio/python.html
__ https://pypi.org/project/pigpio/
__ https://github.com/joan2937/pigpio
__ http://abyz.me.uk/rpi/pigpio/

__ https://github.com/metachris/RPIO
__ https://pypi.org/project/RPIO/
__ https://github.com/metachris/RPIO
__ https://pythonhosted.org/RPIO/

Documentation
-------------

 - sphinx (homepage__, pypi__, source__, doc__): documentation generator

__ http://sphinx-doc.org/
__ https://pypi.org/project/Sphinx/
__ https://github.com/sphinx-doc/sphinx
__ http://sphinx-doc.org/

Test
----

 - tox (homepage__, pypi__, source__, doc__): test management
 - pytest (homepage__, pypi__, source__, doc__): testing
 - flake8 (homepage__, pypi__, source__, doc__): quality assurance
 - mypy (homepage__, pypi__, source__, doc__): type checking

__ http://tox.readthedocs.org/
__ https://pypi.org/project/tox/
__ https://github.com/tox-dev/tox
__ http://tox.readthedocs.org/

__ https://docs.pytest.org/
__ https://pypi.org/project/pytest/
__ https://github.com/pytest-dev/pytest
__ https://docs.pytest.org/

__ https://gitlab.com/pycqa/flake8
__ https://pypi.org/project/flake8/
__ https://gitlab.com/pycqa/flake8
__ https://flake8.pycqa.org/

__ http://www.mypy-lang.org/
__ https://pypi.org/project/mypy/
__ https://github.com/python/mypy
__ https://mypy.readthedocs.io/

Non-Python dependencies
=======================

Server
------

- smartmontools (homepage__, source__, doc__):
  pySMART's backend

__ https://www.smartmontools.org/
__ https://www.smartmontools.org/browser
__ https://www.smartmontools.org/wiki/TocDoc

Installation
============

Server
------

Install smartmontools on your system with your prefered package manager.

Install fand with:

.. code-block:: console

   $ pip install fand[server]

Raspberry Pi client
-------------------

Install fand with one of the following commands:

 - Install with RPi.GPIO:

   .. code-block:: console

      $ pip install fand[clientrpi-rpi-gpio]

 - Install with pigpio:

   .. code-block:: console

      $ pip install fand[clientrpi-pigpio]

 - Install with RPIO:

   .. code-block:: console

      $ pip install fand[clientrpi-rpio]

Other modules
-------------

No extra dependencies required, you can install with:

.. code-block:: console

   $ pip install fand

Custom installation
-------------------

You can cumulate extra dependencies:

.. code-block:: console

   $ pip install fand[server,clientrpi-pigpio]

Documentation
-------------

To build the documentation, you can install fand with:

.. code-block:: console

   $ pip install fand[doc]

Download the fand source code:

.. code-block:: console

   $ pip download --no-deps --no-binary fand fand
   $ tar -xf <filename>
   $ cd <directory>

And build the documentation with:

.. code-block:: console

   $ cd doc
   $ make html

The documentation will be built in the ``build`` directory.

Testing
-------

To run CI or QA tests, you can install fand with:

.. code-block:: console

   $ pip install fand[test,qa]

You may want to also install ``server`` and ``clientrpi-base`` dependencies
to test the corresponding modules.

Run the tests with:

.. code-block:: console

   $ tox

Python version support
======================

Officially supported Python_ versions
-------------------------------------

 - Python 3.6
 - Python 3.7
 - Python 3.8
 - Python 3.9

.. _Python: https://www.python.org/downloads/

Officially supported Python implementations
-------------------------------------------

 - CPython_
 - PyPy_

.. _CPython: https://www.python.org/
.. _PyPy: https://www.pypy.org/

Operating system support
========================

Server
------

 - Linux
 - FreeBSD
 - Windows: untested, missing support for CPU temperature monitoring
   (:func:`psutil.sensors_temperatures` does not supports Windows)

Raspberry Pi client
-------------------

 - Linux
 - Windows: untested
 - FreeBSD: unsupported, missing support for any of the gpiozero's
   backend for PWM

Other modules
-------------

 - Any OS with Python

