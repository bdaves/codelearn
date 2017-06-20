from __future__ import absolute_import

import functools

from . import dbutil

from flask import session, redirect, url_for


def logged_in(func):
    """
    Enforce that a user must be logged in before the wrapped function may be called.  Reroutes to
    the login method if the user is not currently logged in.

    :param func: Function which should only be accessed when user is logged in
    :return: wrapped function
    """
    @functools.wraps(func)
    def decoration(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login'))
        else:
            return func(*args, **kwargs)

    return decoration


def with_cursor(func):
    """
    Establish a database connection, and pass cursor to wrapped function

    :param func: function requiring a database cursor
    :return: wrapped function
    """
    @functools.wraps(func)
    def decoration(*args, **kwargs):
        conn = cursor = None
        try:
            conn = dbutil.connect()
            kwargs['cursor'] = conn.cursor()
            return func(*args, **kwargs)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return decoration
