================
Utilities module
================

.. module:: fand.util

The ``util`` module provides some functions used by most fand modules.

It provides a :func:`terminate` function to make the daemon and its threads
terminate cleanly.
It provide a :func:`when_terminate` function decorator to add
functions to call when :func:`terminate` is called, allowing custom cleanup
from modules.

It also has a default signal handler, and a default argument parser.

Python API
==========

terminate
---------

.. autofunction:: terminate

sys_exit
--------

.. autofunction:: sys_exit

terminating
-----------

.. autofunction:: terminating

when_terminate
--------------

.. autofunction:: when_terminate

sleep
-----

.. autofunction:: sleep

default_signal_handler
----------------------

.. autofunction:: default_signal_handler

parse_args
----------

.. autofunction:: parse_args

