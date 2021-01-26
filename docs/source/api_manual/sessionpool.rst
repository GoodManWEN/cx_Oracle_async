.. _sessionpool:

***********************
AsyncPoolWrapper Object
***********************

Wraps a cx_Oracle.SessionPool object.

.. note::

    This object is an extension to cx_Oracle's DB API.

.. method:: AsyncPoolWrapper.acquire()

    Acquire a connection from the session pool and return a
    :ref:`async connection wrapper object <connobj>`.

.. method:: AsyncPoolWrapper.drop(AsyncConnectionWrapper)

    Drop the connection from the pool which is useful if the connection is no
    longer usable (such as when the session is killed).


.. method:: AsyncPoolWrapper.release(AsyncConnectionWrapper)

    Release the connection back to the pool now, rather than whenever __del__
    is called. The connection will be unusable from this point forward; an
    Error exception will be raised if any operation is attempted with the
    connection. Any cursors or LOBs created by the connection will also be
    marked unusable and an Error exception will be raised if any operation is
    attempted with them.

.. method:: AsyncPoolWrapper.close(force=False , interrupt=False)

    If any connections have been acquired and not released back to the pool
    this method will fail unless the force parameter is set to True.

    If interrupt is set to true , the session pool will close now, 
    rather than when the last reference to it is released , 
    Which makes it unusable for further work.

    The interrupt feature is not supported in legacy oracle versions.
