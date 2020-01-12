import datetime
import logging
import os
import time
import traceback

try:
    import praw
except ImportError:
    praw = None
if praw is None or praw.__version__.startswith('3.'):
    import praw4
    praw = praw4

try:
    import bot
except ImportError:
    bot = None
if bot is None or bot.praw != praw:
    import bot4
    bot = bot4


logging.basicConfig()
log = logging.getLogger(__name__)

r = bot.anonymous()

def assert_file_exists(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

def b36(i):
    if isinstance(i, int):
        return base36encode(i)
    return base36decode(i)

def base36decode(number):
    return int(number, 36)

def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def fetchgenerator(cursor):
    while True:
        item = cursor.fetchone()
        if item is None:
            break
        yield item

def generator_chunker(generator, chunk_size):
    chunk = []
    for item in generator:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if len(chunk) != 0:
        yield chunk

def get_now(stamp=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    if stamp:
        return int(now.timestamp())
    return now

def human(timestamp):
    x = datetime.datetime.utcfromtimestamp(timestamp)
    x = datetime.datetime.strftime(x, "%b %d %Y %H:%M:%S")
    return x

def int_none(x):
    if x is None:
        return None
    return int(x)

def is_xor(*args):
    '''
    Return True if and only if one arg is truthy.
    '''
    return [bool(a) for a in args].count(True) == 1

def nofailrequest(function):
    '''
    Creates a function that will retry until it succeeds.
    This function accepts 1 parameter, a function, and returns a modified
    version of that function that will try-catch, sleep, and loop until it
    finally returns.
    '''
    def a(*args, **kwargs):
        while True:
            try:
                result = function(*args, **kwargs)
                return result
            except KeyboardInterrupt:
                raise
            except Exception:
                traceback.print_exc()
                print('Retrying in 2...')
                time.sleep(2)
    return a
