__author__ = 'nmarchenko'

from django.db import connection
from django.db.backends.mysql import base as mysql_base
from functools import wraps
import time
import logging


def operation_error_handler(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        self = args[0]
        tries = self.settings_dict.get('OPERATION_ERROR_TRIES', 30)

        while tries > 0:
            try:
                return function(*args, **kwargs)
            except mysql_base.Database.OperationalError:
                log = logging.getLogger(__name__)
                log.warning('', exc_info=1)
                try:
                    if connection.connection:
                        connection.connection.ping(True)
                except mysql_base.Database.OperationalError:
                    log.warning('', exc_info=1)

                tries -= 1
                sleep = self.settings_dict.get('OPERATION_ERROR_SLEEP', 2)
                time.sleep(sleep)

        log = logging.getLogger(__name__)
        log.exception('')

    return wrapper


class CursorWrapper(mysql_base.CursorWrapper):

    def __init__(self, cursor, settings_dict):
        super(CursorWrapper, self).__init__(cursor)
        self.settings_dict = settings_dict

    @operation_error_handler
    def execute(self, *args, **kwargs):
        return super(CursorWrapper, self).execute(*args, **kwargs)

    @operation_error_handler
    def executemany(self, *args, **kwargs):
        return super(CursorWrapper, self).executemany(*args, **kwargs)

    @operation_error_handler
    def __exit__(self, *args, **kwargs):
        return super(CursorWrapper, self).__exit__(*args, **kwargs)


class DatabaseWrapper(mysql_base.DatabaseWrapper):

    @operation_error_handler
    def get_new_connection(self, *args, **kwargs):
        return super(DatabaseWrapper, self).get_new_connection(*args, **kwargs)

    @operation_error_handler
    def create_cursor(self):
        cursor = self.connection.cursor()
        return CursorWrapper(cursor, self.settings_dict)

    @operation_error_handler
    def _rollback(self):
        return super(DatabaseWrapper, self)._rollback()

    @operation_error_handler
    def _set_autocommit(self, *args, **kwargs):
        return super(DatabaseWrapper, self)._set_autocommit(*args, **kwargs)

    @operation_error_handler
    def is_usable(self):
        return super(DatabaseWrapper, self).is_usable()

    @operation_error_handler
    def mysql_version(self, *args, **kwargs):
        return super(DatabaseWrapper, self).mysql_version(*args, **kwargs)
