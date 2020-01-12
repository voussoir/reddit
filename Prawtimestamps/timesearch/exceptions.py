class TimesearchException(Exception):
    '''
    Base type for all of the Timesearch exceptions.
    Subtypes should have a class attribute `error_message`. The error message
    may contain {format} strings which will be formatted using the
    Exception's constructor arguments.
    '''
    error_message = ''
    def __init__(self, *args, **kwargs):
        self.given_args = args
        self.given_kwargs = kwargs
        self.error_message = self.error_message.format(*args, **kwargs)
        self.args = (self.error_message, args, kwargs)

    def __str__(self):
        return self.error_message

OUTOFDATE = '''
Database is out of date. {current} should be {new}.
Please use utilities\\database_upgrader.py
'''.strip()
class DatabaseOutOfDate(TimesearchException):
    '''
    Raised by TSDB __init__ if the user's database is behind.
    '''
    error_message = OUTOFDATE

class DatabaseNotFound(TimesearchException, FileNotFoundError):
    error_message = 'Database file not found: "{}"'

class NotExclusive(TimesearchException):
    '''
    For when two or more mutually exclusive actions have been requested.
    '''
    error_message = 'One and only one of {} must be passed.'
