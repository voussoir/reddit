#/u/GoldenSights
import bot
import bot3
import datetime
import praw4 as praw
import prawcore
import random
import requests
import sqlite3
import string
import sys
import time
import traceback
import types

USERAGENT = '''
/u/GoldenSights Usernames data collection:
Gathering the creation dates of user accounts for visualization.
More at https://github.com/voussoir/reddit/tree/master/Usernames
'''.replace('\n', ' ').strip()
    
sql = sqlite3.connect('D:\\git\\reddit\\usernames\\un.db')
cur = sql.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
    idint INT,
    idstr TEXT,
    created INT,
    human TEXT,
    name TEXT,
    link_karma INT,
    comment_karma INT,
    total_karma INT,
    available INT,
    lastscan INT,
    lowername TEXT)
    ''')
cur.execute('CREATE INDEX IF NOT EXISTS userindex ON users(idint)')
cur.execute('CREATE INDEX IF NOT EXISTS index_users_available ON users(available)')
cur.execute('CREATE INDEX IF NOT EXISTS nameindex ON users(lowername)')
sql.commit()

# These numbers are used for interpreting the tuples that come from SELECT
SQL_USER_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'human',
    'name',
    'link_karma',
    'comment_karma',
    'total_karma',
    'available',
    'lastscan',
    'lowername',
]

SQL_USER = {key:index for (index, key) in enumerate(SQL_USER_COLUMNS)}


AVAILABILITY = {True:'available', False:'unavailable', 'available':1, 'unavailable':0}
HEADER_FULL = '  ID            CREATED                  NAME             LINK     COMMENT      TOTAL            LAST SCANNED'
HEADER_BRIEF = '      LAST SCANNED       |   NAME'

MEMBERFORMAT_FULL = '{id:>6} {created} {username:<20} {link_karma:>9} {comment_karma:>9} ({total_karma:>10}) | {lastscan}'
MEMBERFORMAT_BRIEF = '{lastscan} | {username}'

MIN_LASTSCAN_DIFF = 86400 * 2000
# Don't rescan a name if we scanned it this many days ago

VALID_CHARS = string.ascii_letters + string.digits + '_-'

# If True, print the name of the user we're about to fetch.
# Good for debugging problematic users.
PREPRINT = False


print('Logging in.')
r = bot.login()
r3 = bot3.login(bot3.praw.Reddit(USERAGENT))


def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
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

def base36decode(number):
    return int(number, 36)

def b36(i):
    if type(i) == int:
        return base36encode(i)
    if type(i) == str:
        return base36decode(i)

def fetchgenerator(cur):
    '''
    Create an generator from cur fetches so I don't
    have to use while loops for everything
    '''
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def getentry(**kwargs):
    if len(kwargs) != 1:
        raise Exception("Only 1 argument please")
    kw = list(kwargs.keys())[0]
    if kw == 'idint':
        cur.execute('SELECT * FROM users WHERE idint=?', [kwargs[kw]])
    elif kw == 'idstr':
        cur.execute('SELECT * FROM users WHERE idstr=?', [kwargs[kw]])
    elif kw == 'name':
        cur.execute('SELECT * FROM users WHERE lowername=?', [kwargs[kw].lower()])
    else:
        return None
    return cur.fetchone()

def getnow(timestamp=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        return now.timestamp()
    return now

def human(timestamp):
    day = datetime.datetime.utcfromtimestamp(timestamp)
    human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
    return human

def memberformat_brief(data):
    '''
    Shorter version of memberformat which I'm using for the "available" list.
    '''
    name = data[SQL_USER['name']]
    lastscan = data[SQL_USER['lastscan']]
    lastscan = human(lastscan)

    out = MEMBERFORMAT_BRIEF.format(lastscan=lastscan, username=name)
    return out

def memberformat_full(data):
    '''
    Given a data list, create a string that will
    become a single row in one of the show files.
    '''
    idstr = data[SQL_USER['idstr']]

    # Usernames are maximum of 20 chars
    name = data[SQL_USER['name']]

    created = data[SQL_USER['human']]
    created = created or ''
    link_karma = data[SQL_USER['link_karma']]
    comment_karma = data[SQL_USER['comment_karma']]
    total_karma = data[SQL_USER['total_karma']]
    if link_karma is None:
        link_karma = 'None'
        comment_karma = 'None'
        total_karma = 'None'
    else:
        link_karma = '{:,}'.format(link_karma)
        comment_karma = '{:,}'.format(comment_karma)
        total_karma = '{:,}'.format(total_karma)

    lastscan = data[SQL_USER['lastscan']]
    lastscan = human(lastscan)
    out = MEMBERFORMAT_FULL.format(
        id=idstr,
        created=created,
        username=name,
        link_karma=link_karma,
        comment_karma=comment_karma,
        total_karma=total_karma,
        lastscan=lastscan,
    )
    return out

def print_message(data, printprefix=''):
    if data[SQL_USER['human']] is not None:
        print('{prefix:>5} {idstr:>6} : {human} : {name} : {link_karma} : {comment_karma}'.format(
            prefix=printprefix,
            idstr=data[SQL_USER['idstr']],
            human=data[SQL_USER['human']],
            name=data[SQL_USER['name']],
            link_karma=data[SQL_USER['link_karma']],
            comment_karma=data[SQL_USER['comment_karma']],
            )
        )
    else:
        availability = 'available' if data[SQL_USER['available']] is 1 else 'unavailable'
        print('{prefix:>5} {availability:>33} : {name}'.format(
            prefix=printprefix,
            availability=availability,
            name=data[SQL_USER['name']],
            )
        )

def process(users, quiet=False, knownid='', noskip=False, commit=True):
    '''
    Fetch the /u/ page for a user or list of users

    users :   A list of strings, each representing a username. Since reddit
               usernames must be 3 - 20 characters and only contain
               alphanumeric + "_-", any improper strings will be removed.
    quiet :   Silences the "x old" report at the end
    knownid : If you're processing a user which does not exist, but you know
               what their user ID was supposed to be, this will at least allow
               you to flesh out the database entry a little better.
    noskip :  Do not skip usernames which are already in the database.
    '''
    olds = 0
    if isinstance(users, list):
        users = list(set(users))

    if isinstance(users, (str, praw.models.Redditor)):
        users = [users]

    if isinstance(users, types.GeneratorType) or len(users) > 1:
        knownid = ''

    users = userify_list(users, noskip=noskip, quiet=quiet)
    current = 0
    for user in users:
        current += 1
        data = [None] * len(SQL_USER)
        data[SQL_USER['lastscan']] = int(getnow())
        if isinstance(user, list):
            # This happens when we receive NotFound. [name, availability]
            if knownid != '':
                data[SQL_USER['idint']] = b36(knownid)
                data[SQL_USER['idstr']] = knownid
            data[SQL_USER['name']] = user[0]
            data[SQL_USER['available']] = AVAILABILITY[user[1]]
        else:
            # We have a Redditor object.
            h = human(user.created_utc)
            data[SQL_USER['idint']] = b36(user.id)
            data[SQL_USER['idstr']] = user.id
            data[SQL_USER['created']] = user.created_utc
            data[SQL_USER['human']] = h
            data[SQL_USER['name']] = user.name
            data[SQL_USER['link_karma']] = user.link_karma
            data[SQL_USER['comment_karma']] = user.comment_karma
            data[SQL_USER['total_karma']] = user.comment_karma + user.link_karma
            data[SQL_USER['available']] = 0
        data[SQL_USER['lowername']] = data[SQL_USER['name']].lower()

        printprefix = '%04d' % current
        x = smartinsert(data, printprefix, commit=commit)

        if x is False:
            olds += 1
    if quiet is False:
        print('%d old' % olds)

def process_from_database(filename, table, column, delete_original=False):
    '''
    Warning: if delete_original is True, the original database will lose each username
    as it is processed
    '''
    s = sqlite3.connect(filename)
    c = s.cursor()
    c2 = s.cursor()
    query = 'SELECT %s FROM %s ORDER BY RANDOM()' % (column, table)
    c.execute(query)
    i = 0
    try:
        for (index, item) in enumerate(fetchgenerator(c)):
            i = (i + 1) % 100
            if i == 0:
                s.commit()
            username = item[0]
            if username is not None:
                process(username, quiet=True, commit=index % 100 == 0)
            if delete_original:
                c2.execute('DELETE FROM %s WHERE %s == ?' % (table, column), [username])
    except (Exception, KeyboardInterrupt) as e:
        sql.commit()
        if delete_original:
            s.commit()
            print('Committing changes...')
        s.close()
        raise e
    sql.commit()
    s.commit()
    s.close()

def smartinsert(data, printprefix='', commit=True):
    '''
    Originally, all queries were based on idint, but this caused problems
    when accounts were deleted / banned, because it wasn't possible to
    sql-update without knowing the ID.
    '''
    print_message(data, printprefix)

    exists_in_db = (getentry(name=data[SQL_USER['name']].lower()) is not None)
    if exists_in_db:
        isnew = False
        data = [
            data[SQL_USER['idint']],
            data[SQL_USER['idstr']],
            data[SQL_USER['created']],
            data[SQL_USER['human']],
            data[SQL_USER['link_karma']],
            data[SQL_USER['comment_karma']],
            data[SQL_USER['total_karma']],
            data[SQL_USER['available']],
            data[SQL_USER['lastscan']],
            data[SQL_USER['name']],
            data[SQL_USER['name']].lower()]
        # coalesce allows us to fallback on the existing values
        # if the given values are null, to avoid erasing data about users
        # whose accounts are now deleted.
        command = '''
            UPDATE users SET
            idint = coalesce(?, idint),
            idstr = coalesce(?, idstr),
            created = coalesce(?, created),
            human = coalesce(?, human),
            link_karma = coalesce(?, link_karma),
            comment_karma = coalesce(?, comment_karma),
            total_karma = coalesce(?, total_karma),
            available = coalesce(?, available),
            lastscan = coalesce(?, lastscan),
            name = coalesce(?, name)
            WHERE lowername == ?
        '''
        cur.execute(command, data)
    else:
        isnew = True
        cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
    if commit:
        sql.commit()
    return isnew

def userify_list(users, noskip=False, quiet=False):
    if quiet is False:
        if hasattr(users, '__len__'):
            print('Processing %d unique names' % len(users))

    for username in users:
        if isinstance(username, str):
            if len(username) < 3 or len(username) > 20:
                #print('%s : Invalid length of %d' % (username, len(username)))
                #continue
                pass
            if not all(c in VALID_CHARS for c in username):
                print('%s : Contains invalid characters' % username)
                continue
        elif isinstance(username, praw.models.Redditor):
            username = username.name.lower()
        else:
            print('Don\'t know what to do with %s' % username)

        existing_entry = getentry(name=username)
        if existing_entry is not None:
            lastscan = existing_entry[SQL_USER['lastscan']]
            should_rescan = (getnow() - lastscan) > MIN_LASTSCAN_DIFF
            if should_rescan is False and noskip is False:
                prefix = ' ' * 31
                appendix = '(available)' if existing_entry[SQL_USER['available']] else ''
                print('%sskipping : %s %s' % (prefix, username, appendix))
                continue

        try:
            if PREPRINT:
                print(username)
            user = r.redditor(username)
            if getattr(user, 'is_suspended', False):
                # Suspended accounts provide extremely little info
                # {"kind": "t2", "data": {"is_suspended": true, "name": "*****"}}
                continue
            yield user
        except prawcore.exceptions.NotFound:
            availability = r3.is_username_available(username)
            availability = AVAILABILITY[availability]
            yield [username, availability]
