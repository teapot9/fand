====================
Client: Raspberry Pi
====================

.. module:: fand.clientrpi
   :platform: Linux

The Raspberry Pi client control the fan speed by sending a PWM signal through
the GPIO pins.

Two pins are used:

 - The PWM pin used to output the PWM signal regulating the fan speed.
   It should be connected to the PWM input of the fans.
 - The RPM pin used to read the actual fan speed in RPM.
   It should be connected to the tachometer output of the fans.

Examples
--------

Start the client:

.. code-block:: console

   # fand clientrpi

Start and use GPIO pin 17 for PWM, and pin 18 for tacho:

.. code-block:: console

   # fand server -W 17 -r 18

Start with verbose output and connect to server at server-host:1234:

.. code-block:: console

   # fand server -v -a server-host -P 1234

Python API
----------

.. autodata:: SLEEP_TIME

GpioRpm
^^^^^^^

.. autoclass:: GpioRpm
   :members: update, close, rpm

GpioPwm
^^^^^^^

.. autoclass:: GpioPwm
   :members: pwm, close

add_gpio_device
^^^^^^^^^^^^^^^

.. autofunction:: add_gpio_device

main
^^^^

.. autofunction:: main

daemon
^^^^^^

.. autofunction:: daemon

