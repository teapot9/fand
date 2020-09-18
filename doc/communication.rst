====================
Communication module
====================

.. module:: fand.communication

The communication module handles the low level communication between the
server and the clients.

It provides functions to send and receive a request with arguments
to a given socket.

It can start a connection with the server and close a socket.
It also keep track of sockets to close them automatically at the end
of the program.

Examples
========

.. code-block:: python

   from fand.communication import *
   s = connect('myserver.example.com', 9999)
   send(s, Request.GET_PWM, 'myshelf1')
   req, args = recv(s)
   if req == Request.SET_PWM:
       print("The fan speed of", args[0], "is", args[1])
   else:
       print("The server did not answer the expected request")

Python API
==========

Request
-------

.. autoclass:: Request

add_socket
----------

.. autofunction:: add_socket

is_socket_open
--------------

.. autofunction:: is_socket_open

send
----

.. autofunction:: send

recv
----

.. autofunction:: recv

connect
-------

.. autofunction:: connect

reset_connection
----------------

.. autofunction:: reset_connection

