.. _connobj:

*****************************
AsyncConnectionWrapper Object
*****************************

Wraps a cx_Oracle.Connection object.

.. method:: AsyncConnectionWrapper.cursor()

    Return a new :ref:`async cursor wrapper object <cursorobj>` using the connection.

    This is a asynchronous method.

.. method:: AsyncConnectionWrapper.msgproperties(payload, correlation, delay, exceptionq, \
        expiration, priority)

    Returns an object specifying the properties of messages used in advanced
    queuing.

    This is a synchronous method.

    .. versionadded:: 0.2.0

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. method:: AsyncConnectionWrapper.queue(name, payloadType=None)

    Creates a :ref:`queue <queue>` which is used to enqueue and dequeue
    messages in Advanced Queueing.

    The name parameter is expected to be a string identifying the queue in
    which messages are to be enqueued or dequeued.

    This is a asynchronous method.

    .. versionadded:: 0.2.0

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. method:: AsyncConnectionWrapper.gettype(name)

    Return a ``cx_Oracle.type object`` given its name. This can then be
    used to create objects which can be bound to cursors created by this
    connection.

    This is a asynchronous method.

    .. versionadded:: 0.2.0

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. method:: AsyncConnectionWrapper.commit()

    Commit any pending transactions to the database.

    This is a asynchronous method.

.. method:: AsyncConnectionWrapper.release()

    Equals to cx_Oracle.SessionPool.release(connection) , by using this equivalent 
    you don't need to operate with another ``AsyncPoolWrapper`` object.

    This is a asynchronous method.

.. method:: AsyncConnectionWrapper.cancel()

    Break a long-running transaction.

    This is a asynchronous method.

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. method:: AsyncConnectionWrapper.rollback()

    Rollback any pending transactions.

    This is a asynchronous method.

.. method:: AsyncConnectionWrapper.ping()

    Ping the server which can be used to test if the connection is still
    active.

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. attribute:: AsyncConnectionWrapper.encoding

    This read-only attribute returns the IANA character set name of the
    character set in use by the Oracle client for regular strings.

    .. note::

        This attribute is an extension to the cx_Oracle's DB API definition.

.. attribute:: AsyncConnectionWrapper.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

.. attribute:: AsyncConnectionWrapper.module

    This write-only attribute sets the module column in the v$session table.
    The maximum length for this string is 48 and if you exceed this length you
    will get ORA-24960.

    .. note:

        This attribute is an extension to the cx_Oracle's DB API definition.

.. attribute:: AsyncConnectionWrapper.action

    This write-only attribute sets the action column in the v$session table. It
    is a string attribute and cannot be set to None -- use the empty string
    instead.

    .. note::

        This attribute is an extension to the cx_Oracle's DB API definition.

.. attribute:: AsyncConnectionWrapper.client_identifier

    This write-only attribute sets the client_identifier column in the
    v$session table.

    .. note::

        This attribute is an extension to the cx_Oracle's DB API definition.

.. attribute:: AsyncConnectionWrapper.clientinfo

    This write-only attribute sets the client_info column in the v$session
    table.

    .. note::

        This attribute is an extension to the cx_Oracle's DB API definition.