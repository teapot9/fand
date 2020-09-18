==========
Exceptions
==========

.. module:: fand.exceptions

The exception module provides fand-specific exceptions.
All exceptions raised by fand descend from :exc:`FandError`.

Certain errors have multiple parents.
For instance, :exc:`ShelfNotFoundError` is a :exc:`FandError`,
but also a :exc:`ValueError`.

Python API
==========

Common fand errors
------------------

.. autoexception:: FandError
   :show-inheritance:

.. autoexception:: TerminatingError
   :show-inheritance:

Communication related errors
----------------------------

.. autoexception:: CommunicationError
   :show-inheritance:

.. autoexception:: SendReceiveError
   :show-inheritance:

.. autoexception:: ListeningError
   :show-inheritance:

.. autoexception:: ConnectionFailedError
   :show-inheritance:

.. autoexception:: CorruptedDataError
   :show-inheritance:

.. autoexception:: FandConnectionResetError
   :show-inheritance:

.. autoexception:: FandTimeoutError
   :show-inheritance:

.. autoexception:: UnpicklableError
   :show-inheritance:

Shelf related errors
--------------------

.. autoexception:: ShelfTemperatureBadValue
   :show-inheritance:

.. autoexception:: ShelfRpmBadValue
   :show-inheritance:

.. autoexception:: ShelfPwmBadValue
   :show-inheritance:

.. autoexception:: ShelfPwmExpireBadValue
   :show-inheritance:

.. autoexception:: ShelfNotFoundError
   :show-inheritance:

Server and clients specific errors
----------------------------------

.. autoexception:: ServerNoConfigError
   :show-inheritance:

.. autoexception:: GpioError
   :show-inheritance:

.. autoexception:: FanctlActionBadValue
   :show-inheritance:

