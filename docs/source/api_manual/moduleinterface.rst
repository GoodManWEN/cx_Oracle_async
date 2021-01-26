.. module:: cx_Oracle_async

.. _moduleinterface:

****************
Module Interface
****************

.. data:: DEQ_NO_WAIT

    This constant is used to specify that dequeue not wait for messages to be available for dequeuing.

    .. versionadded:: 0.2.0

.. data:: DEQ_WAIT_FOREVER

    This constant is used to specify that dequeue should wait forever for messages to be available for dequeuing. This is the default value.

    .. versionadded:: 0.2.0

.. function:: makedsn(host, port, sid=None, service_name=None)

    Return a string suitable for use as the dsn parameter for
    :meth:`~cx_Oracle_async.create_pool()`. This string is identical to the strings that
    are defined by the Oracle names server or defined in the tnsnames.ora file.

    .. note::

        This method is an extension to the cx_Oracle's DB API definition.

.. function:: create_pool(user=None, password=None, dsn=None, min=2, max=4, \
        increment=1, connectiontype=cx_Oracle.Connection, threaded=True, \
        getmode=cx_Oracle.SPOOL_ATTRVAL_NOWAIT, events=False, \
        homogeneous=True, externalauth=False, encoding='UTF-8', \
        edition=None, timeout=0, waitTimeout=0, maxLifetimeSession=0, \
        sessionCallback=None, maxSessionsPerShard=0)

    Create and return a :ref:`AsyncPoolWrapper object <sessionpool>` which wraps a cx_Oracle.SessionPool.

    Different from the original library , ``threaded`` is set to ``True`` by default , and encoding is set to ``UTF-8``.

    .. note::

        This method is an extension to cx_Oracle's DB API definition.

