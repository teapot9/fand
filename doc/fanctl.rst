======================
Command-line interface
======================

.. module:: fand.fanctl

``fanctl`` is a CLI allowing to interract with the server.

It is basically a fand client, but does not act as a fan controller.

The user can get the assigned fan speed in percentage, the real fan speed
in rpm.

The user can override the assigned fan speed.
The override can also be set to expire in a given amount of time,
or expire at a given date and time.

Examples
========

Ping the server at 192.168.1.10:1234:

.. code-block:: console

   $ fanctl -a 192.168.1.10 -P 1234 ping

Get the assigned fan speed for shelf 'shelf1':

.. code-block:: console

   $ fanctl get-pwm shelf1


Override fan speed of 'myshelf' to 100%:

.. code-block:: console

   $ fanctl set-pwm-override myshelf 100

Remove override in 1 hour and 30 minutes:

.. code-block:: console

   $ fanctl set-pwm-expire-in myshelf 1h30m

Remove override now:

.. code-block:: console

   $ fanctl set-pwm-override myshelf none

Python API
==========

.. autodata:: DATETIME_DATE_FORMATS
   :annotation:

.. autodata:: DATETIME_DURATION_FORMATS
   :annotation:

.. autodata:: ACTION_DICT
   :annotation:

main
----

.. autofunction:: main

send
----

.. autofunction:: send

