======
Server
======

.. module:: fand.server
   :platform: Linux, FreeBSD

The server is a daemon monitoring devices temperatures.

Devices are separated in shelves.
Each shelf contains a set of devices.
Each device has a type (HDD, SSD, CPU).

Fan speed is determined from the temperature of the device which is in most
need of cooling.

For each type of device, an effective temperature is determined from the
maximum temperature of all the devices of this type.
With this temperature, an effective fan speed is determined.
We then have an effective fan speed for each device type, the highest
fan speed is then defined as the speed for the entire shelf.

Examples
========

Start the server:

.. code-block:: console

   # fand server

Start and listen on ``0.0.0.0:1234``:

.. code-block:: console

   # fand server -a 0.0.0.0 -P 1234

Start and show very verbose logging:

.. code-block:: console

   # fand server -vvv

Configuration file
==================

Default configuration file is read from either ``/etc/fand.ini``, the
``FAND_CONFIG`` environment variable, or ``./fand.ini``.
There is also a ``-c`` parameter to specify the config file path.

The configuration is in the ``ini`` format.

It must have a ``[DEFAULT]`` section wich contain a ``shelves`` key listing
shelves names to use.
This section also contains default configuration for fan speed.

For each shelf, a section with its name has to be defined.
It will contain a ``devices`` key listing devices assigned to this shelf.
It can also override fan speed defined in ``[DEFAULT]``.

Example configuration file:

.. literalinclude:: ../config/fand.ini.example
   :language: ini
   :linenos:

Python API
==========

.. autodata:: REQUEST_HANDLERS
   :annotation:

Device
------

.. autoclass:: Device
   :members: serial, position, find, update, temperature, type

.. autoclass:: fand.server::Device.DeviceType
   :members: NONE, HDD, SSD, CPU
   :show-inheritance:

Shelf
-----

.. autoclass:: Shelf
   :members: identifier, sleep_time, rpm, pwm, pwm_expire, update

add_shelf
---------

.. autofunction:: add_shelf

listen_client
-------------

.. autofunction:: listen_client

read_config
-----------

.. autofunction:: read_config

shelf_thread
------------

.. autofunction:: shelf_thread

main
----

.. autofunction:: main

daemon
------

.. autofunction:: daemon

