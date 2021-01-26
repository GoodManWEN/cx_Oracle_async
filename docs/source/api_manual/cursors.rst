.. _cursorobj:

*************************
AsyncCursorWrapper Object
*************************

.. method:: AsyncCursorWrapper.execute(statement, [parameters], \*\*keywordParameters)

    Execute a statement against the database.

    Parameters may be passed as a dictionary or sequence or as keyword
    parameters. If the parameters are a dictionary, the values will be bound by
    name and if the parameters are a sequence the values will be bound by
    position. Note that if the values are bound by position, the order of the
    variables is from left to right as they are encountered in the statement
    and SQL statements are processed differently than PL/SQL statements. For
    this reason, it is generally recommended to bind parameters by name instead
    of by position.

    Parameters passed as a dictionary are name and value pairs. The name maps
    to the bind variable name used by the statement and the value maps to the
    Python value you wish bound to that bind variable.

    A reference to the statement will be retained by the cursor. If None or the
    same string object is passed in again, the cursor will execute that
    statement again without performing a prepare or rebinding and redefining.
    This is most effective for algorithms where the same statement is used, but
    different parameters are bound to it (many times). Note that parameters
    that are not passed in during subsequent executions will retain the value
    passed in during the last execution that contained them.

    If the statement is a query, the cursor is returned as a convenience to the
    caller (so it can be used directly as an iterator over the rows in the
    cursor); otherwise, ``None`` is returned.

    This is a asynchronous method.

.. method:: AsyncCursorWrapper.executemany(statement, parameters, batcherrors=False, \
        arraydmlrowcounts=False)

    Prepare a statement for execution against a database and then execute it
    against all parameter mappings or sequences found in the sequence
    parameters.

    The statement is managed in the same way as the :meth:`~AsyncCursorWrapper.execute()`
    method manages it. If the size of the buffers allocated for any of the
    parameters exceeds 2 GB, you will receive the error "DPI-1015: array size
    of <n> is too large", where <n> varies with the size of each element being
    allocated in the buffer. If you receive this error, decrease the number of
    elements in the sequence parameters.

    This is a asynchronous method.

.. method:: AsyncCursorWrapper.fetchone()

    Fetch the next row of a query result set, returning a single tuple or None
    when no more data is available.

    An exception is raised if the previous call to :meth:`~Cursor.execute()`
    did not produce any result set or no call was issued yet.

    See :ref:`sqlexecution` for further example.

    This is a asynchronous method.

.. method:: AsyncCursorWrapper.fetchall()

    Fetch all (remaining) rows of a query result, returning them as a list of
    tuples. An empty list is returned if no more rows are available. Note that
    the cursor's arraysize attribute can affect the performance of this
    operation, as internally reads from the database are done in batches
    corresponding to the arraysize.

    An exception is raised if the previous call to :meth:`~Cursor.execute()`
    did not produce any result set or no call was issued yet.

    See :ref:`sqlexecution` for further example.

    This is a asynchronous method.

.. method:: AsyncCursorWrapper.var(dataType, [size, arraysize, inconverter, outconverter, \
        typename, encodingErrors])

    Create a variable with the specified characteristics. This method was
    designed for use with PL/SQL in/out variables where the length or type
    cannot be determined automatically from the Python object passed in or for
    use in input and output type handlers defined on cursors or connections.

    Only accept positional argument.

    This is a asynchronous method.

.. method:: AsyncCursorWrapper.close()

    Close the cursor now, rather than whenever __del__ is called. The cursor
    will be unusable from this point forward; an Error exception will be raised
    if any operation is attempted with the cursor.