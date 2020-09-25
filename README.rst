====
fand
====

.. image:: https://badge.fury.io/gh/lleseur%2Ffand.svg
   :target: https://github.com/lleseur/fand
   :alt: Github repository

.. image:: https://badge.fury.io/py/fand.svg
   :target: https://pypi.org/project/fand/
   :alt: PyPI package

.. image:: https://github.com/lleseur/fand/workflows/CI/badge.svg
   :target: https://github.com/lleseur/fand/actions?query=workflow%3ACI
   :alt: Continuous integration

.. image:: https://github.com/lleseur/fand/workflows/QA/badge.svg
   :target: https://github.com/lleseur/fand/actions?query=workflow%3AQA
   :alt: Quality assurance

.. image:: https://readthedocs.org/projects/fand/badge/?version=latest
   :target: https://fand.readthedocs.io/en/latest/
   :alt: Documentation status

Simple daemon to control fan speed.

About
=====

The main executable of this program is the ``fand-server`` daemon.
There are 3 main modules: server, clientrpi and fanctl.
They can be accessed through their respective entry points:
``fand-server``, ``fand-clientrpi`` and ``fanctl``.
They can also be accessed with ``fand <module-name>``.

A server monitor the hardware and clients connect to it to get data (e.g.
fan speed or override a fan speed).

.. code-block:: console

   $ fanctl get-rpm shelf1
   1500
   $ fanctl get-pwm shelf1
   50
   $ fanctl set-pwm-override shelf1 100
   ok
   $ fanctl get-pwm shelf1
   100
   $ fanctl get-rpm shelf1
   3000

Server
------

The server_ module provide a daemon which monitor devices
temperatures and find a corresponding fan speed.
It listens for connections from clients, and answers to requests.

Fan clients
-----------

A client is assigned a shelf and will regularly request the server for the
fan speed (percentage).  It will then ajust the fan to use this speed.

Clients also send the actual fan speed in RPM to the server. This will allow
other client to have access to the data from the server.

Raspberry Pi client
^^^^^^^^^^^^^^^^^^^

The clientrpi_ module will connect to a server and
get a fan speed from it.
It will then set the fan speed with a PWM signal through the GPIO interface
of the Pi.
It will also tell the server the current real speed of the fans in rpm.

Command-line interface
----------------------

The fanctl_ module is a command line interface to interact
with the server.
It provides commands to get the fan speed and rpm, and also allow to override
the fans speed.

Documentation
-------------

The fand documentation is available at https://fand.readthedocs.io/.
The installation_ chapter provides install instructions and compatibility
informations.

.. _server: https://fand.readthedocs.io/en/latest/server.html
.. _clientrpi: https://fand.readthedocs.io/en/latest/clientrpi.html
.. _fanctl: https://fand.readthedocs.io/en/latest/fanctl.html
.. _installation: https://fand.readthedocs.io/en/latest/install.html

