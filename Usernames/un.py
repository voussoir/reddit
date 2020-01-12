#/u/GoldenSights
import bot3 as bot
import datetime
import praw
import random
import requests
import sqlite3
import string
import sys
import time
import traceback

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
    lastscan INT)
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
r = praw.Reddit(USERAGENT)
bot.login(r)


def allpossiblefromset(characters, length=None, minlength=None, maxlength=None):
    '''
    Given an iterable of characters, return a generator that creates every
    permutation of length `length`.

    If `minlength` and `maxlength` are both provided, all values of intermediate
    lengths will be generated
    '''

    if not (minlength is None or maxlength is None):
        for x in range(minlength, maxlength+1):
            for item in allpossiblefromset(characters, x):
                yield item
    elif length is None:
        raise ValueError('`length` must be provided if you arent using the min/max')
    else:
        endingpoint = len(characters) ** length

        characters = ''.join(sorted(list(set(characters))))

        for permutation in range(endingpoint):
            permutation = base36encode(permutation, alphabet=characters)
            l = len(permutation)
            if l < length:
                permutation = (characters[0] * (length-l)) + permutation
            yield permutation

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

def check_old(available=None, threshold=86400):
    '''
    Update names in ascending order of their last scan
    available = False : do not include available names
                None  : do include available names
                True  : only include available names
    threshold = how long ago the lastscan must be.
    '''
    now = getnow()
    threshold = now - threshold
    assert available in (False, None, True)
    if available == False:
        query = 'SELECT name FROM users WHERE available = 0 AND lastscan < ? ORDER BY lastscan ASC'
    elif available == None:
        query = 'SELECT name FROM users WHERE lastscan < ? ORDER BY lastscan ASC'
    elif available == True:
        query = 'SELECT name FROM users WHERE available = 1 AND lastscan < ? ORDER BY lastscan ASC'
    cur.execute(query, [threshold])
    availables = cur.fetchall()
    for item in availables:
        process(item, quiet=True, noskip=True)

def count(validonly=False):
    if validonly:
        cur.execute('SELECT COUNT(*) FROM users WHERE idint IS NOT NULL AND available == 0')
    else:
        cur.execute('SELECT COUNT(*) FROM users')
    return cur.fetchone()[0]

def execit(*args, **kwargs):
    '''
    Allows another module to do stuff here using local names instead of qual names.
    '''
    exec(*args, **kwargs)

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

def fetchwriter(cur, outfile, spacer1=' ', spacer2=None, brief=False):
    '''
    Write items from the current sql query to the specified file.

    If two spacers are provided, it will flip-flop between them
    on alternating lines to help readability.
    '''
    flipflop = True
    for item in fetchgenerator(cur):
        spacer = spacer1 if flipflop else spacer2
        if brief:
            item = memberformat_brief(item)
        else:
            item = memberformat_full(item)
        print(item, file=outfile)
        if spacer2 is not None:
            flipflop = not flipflop

def find(name, doreturn=False):
    '''
    Print the details of a username.
    '''
    f = getentry(name=name)
    if f:
        if doreturn:
            return f
        print_message(f)
    return None

def get_from_hot(sr, limit=None, submissions=True, comments=False, returnnames=False):
    '''
    Shortcut for get_from_listing, using /hot
    '''
    listfunction = praw.objects.Subreddit.get_hot
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_listing(sr, limit, listfunction, submissions=True, comments=True, returnnames=False):
    '''
    Get submission listings using one of PRAW's get methods
    and process those usernames

    `listfunction` would be praw.objects.Subreddit.get_new for example
    '''
    subreddit = r.get_subreddit(sr, fetch=sr != 'all')
    if limit is None:
        limit = 1000
    authors = set()
    if submissions is True:
        print('/r/%s, %d submissions' % (subreddit.display_name, limit))
        subreddit.lf = listfunction
        for item in subreddit.lf(subreddit, limit=limit):
            if item.author is not None:
                authors.add(item.author.name)
    if comments is True:
        print('/r/%s, %d comments' % (subreddit.display_name, limit))
        for item in subreddit.get_comments(limit=limit):
            if item.author is not None:
                authors.add(item.author.name)

    if returnnames is True:
        return authors

    try:
        process(authors)
    except KeyboardInterrupt:
        sql.commit()
        raise

def get_from_new(sr, limit=None, submissions=True, comments=True, returnnames=False):
    '''
    Shortcut for get_from_listing, using /new
    '''
    listfunction = praw.objects.Subreddit.get_new
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_top(sr, limit=None, submissions=True, comments=False, returnnames=False):
    '''
    Shortcut for get_from_listing, using /top?t=all
    '''
    listfunction = praw.objects.Subreddit.get_top_from_all
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

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

def idlenew(subreddit='all', limit=100, sleepy=15):
    '''
    Infinitely grab the /new queue and process names, ignoring any
    exceptions. Great for processing while AFK.
    '''
    while True:
        try:
            get_from_new(subreddit, limit)
        except KeyboardInterrupt:
            raise
        except:
            traceback.print_exc()
        r._use_oauth = False
        time.sleep(sleepy)

def load_textfile(filename):
    '''
    Returns list of lines.
    See also `save_textfile`.
    '''
    f = open(filename, 'r')
    lines = [x.strip() for x in f.readlines()]
    f.close()
    return lines

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

def popgenerator(x):
    '''
    Create a generator which whittles away at the input
    list until there are no items left.
    This destroys the input list in-place.
    '''
    while len(x) > 0:
        yield x.pop()

def process(users, quiet=False, knownid='', noskip=False):
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

    if isinstance(users, str):
        users = [users]
    # I don't want to import types.GeneratorType just for one isinstance
    if type(users).__name__ == 'generator' or len(users) > 1:
        knownid=''
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
        x = smartinsert(data, printprefix)

        if x is False:
            olds += 1
    if quiet is False:
        print('%d old' % olds)
p = process

def processid(idnum, ranger=1):
    '''
    Do an author_fullname search in an attempt to find a user by their ID.
    This is not reliable if the user has no public submissions.
    '''
    idnum = idnum.split('_')[-1]
    base = b36(idnum)
    for x in range(ranger):
        idnum = x + base
        exists = getentry(idint=idnum)
        if exists is not None:
            print('Skipping %s : %s' % (b36(idnum), exists[SQL_USER['name']]))
            continue
        idnum = 't2_' + b36(idnum)
        idnum = idnum.lower()
        print('%s - ' % idnum, end='', flush=True)
        search = list(r.search('author_fullname:%s' % idnum))
        if len(search) > 0:
            item = search[0].author.name
            process(item, quiet=True, knownid=idnum[3:])
        else:
            print('No idea.')
pid = processid

def process_input():
    while True:
        try:
            x = input('p> ')
        except KeyboardInterrupt:
            print()
            break
        if not x:
            continue
        try:
            process(x, quiet=True, noskip=True)
        except:
            traceback.print_exc()

def process_from_database(filename, table, column, delete_original=False):
    '''
    Warning: if delete_original is True, the original database will lose each username
    as it is processed
    '''
    s = sqlite3.connect(filename)
    c = s.cursor()
    c2 = s.cursor()
    query = 'SELECT DISTINCT %s FROM %s' % (column, table)
    c.execute(query)
    i = 0
    try:
        for item in fetchgenerator(c):
            i = (i + 1) % 100
            if i == 0:
                s.commit()
            username = item[0]
            if username is not None:
                p(username, quiet=True)
            if delete_original:
                c2.execute('DELETE FROM %s WHERE %s == ?' % (table, column), [username])
    except (Exception, KeyboardInterrupt) as e:
        if delete_original:
            print('Committing changes...')
            s.commit()
        e.sql = s
        raise e
    return s

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

def save_textfile(filename, lines):
    '''
    Write items of list as lines in file.
    See also `load_textfile`.
    '''
    f = open(filename, 'w')
    for x in lines:
        print(x, file=f)
    f.close()

def show():
    '''
    Create a bunch of text files that nobody will read
    '''
    file_time = open('show\\time.txt', 'w')
    file_name = open('show\\name.txt', 'w')
    file_karma_total = open('show\\karma_total.txt', 'w')
    #file_karma_link = open('show\\karma_link.txt', 'w')
    #file_karma_comment = open('show\\karma_comment.txt', 'w')
    file_available = open('show\\available.txt', 'w')
    file_stats = open('show\\stats.txt', 'w')
    file_readme = open('README.md', 'r')

    totalitems = count(validonly=False)
    validitems = count(validonly=True)
    print(totalitems, validitems)

    print('Updating readme')
    readmelines = file_readme.readlines()
    file_readme.close()
    readmelines[3] = '##### {0:,} accounts\n'.format(validitems)
    readmelines = ''.join(readmelines)
    file_readme = open('README.md', 'w')
    file_readme.write(readmelines)
    file_readme.close()

    print('Writing stats file.')
    print('DO SOMETHING')
    file_stats.close()

    print('Writing time file.')
    print(HEADER_FULL, file=file_time)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL AND created IS NOT NULL ORDER BY created ASC')
    fetchwriter(cur, file_time)
    file_time.close()

    print('Writing name file.')
    print(HEADER_FULL, file=file_name)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY lowername ASC')
    fetchwriter(cur, file_name)
    file_name.close()
    
    print('Writing karma total file.')
    print(HEADER_FULL, file=file_karma_total)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY total_karma DESC, lowername ASC')
    fetchwriter(cur, file_karma_total)
    file_karma_total.close()

    #print('Writing karma link file.')
    #print(HEADER_FULL, file=file_karma_link)
    #cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY link_karma DESC, lowername ASC')
    #fetchwriter(cur, file_karma_link)
    #file_karma_link.close()

    #print('Writing karma comment file.')
    #print(HEADER_FULL, file=file_karma_comment)
    #cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY comment_karma DESC, lowername ASC')
    #fetchwriter(cur, file_karma_comment)
    #file_karma_comment.close()

    print('Writing available')
    print(HEADER_BRIEF, file=file_available)
    cur.execute('SELECT * FROM users WHERE available == 1 AND LENGTH(name) > 3 ORDER BY lowername ASC')
    fetchwriter(cur, file_available, spacer1=' ', brief=True)
    file_available.close()

def smartinsert(data, printprefix=''):
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
    sql.commit()
    return isnew

def userify_list(users, noskip=False, quiet=False):
    if quiet is False:
        if hasattr(users, '__len__'):
            print('Processing %d unique names' % len(users))


    for username in users:
        if isinstance(username, str):
            if len(username) < 3 or len(username) > 20:
                print('%s : Invalid length of %d' % (username, len(username)))
                continue
            if not all(c in VALID_CHARS for c in username):
                print('%s : Contains invalid characters' % username)
                continue
        elif isinstance(username, praw.objects.Redditor):
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
            user = r.get_redditor(username, fetch=True)
            if getattr(user, 'is_suspended', False):
                # Suspended accounts provide extremely little info
                # {"kind": "t2", "data": {"is_suspended": true, "name": "*****"}}
                continue
            yield user
        except praw.errors.NotFound:
            availability = r.is_username_available(username)
            availability = AVAILABILITY[availability]
            yield [username, availability]
