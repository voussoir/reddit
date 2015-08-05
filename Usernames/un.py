#/u/GoldenSights
import datetime
import praw
import random
import requests
import sqlite3
import string
import sys
import time
import traceback


sql = sqlite3.connect('un.db')
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
cur.execute('CREATE INDEX IF NOT EXISTS nameindex ON users(name)')
sql.commit()
#  0 - idint
#  1 - idstr
#  2 - created
#  3 - human
#  4 - name
#  5 - link karma
#  6 - comment karma
#  7 - total karma
#  8 - available
#  9 - lastscan
SQL_COLUMNCOUNT = 10
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_HUMAN = 3
SQL_NAME = 4
SQL_LINK_KARMA = 5
SQL_COMMENT_KARMA = 6
SQL_TOTAL_KARMA = 7
SQL_AVAILABLE = 8
SQL_LASTSCAN = 9

USERAGENT = '''
/u/GoldenSights Usernames data collection:
Gathering the creation dates of user accounts for visualization.
More at https://github.com/voussoir/reddit/tree/master/Usernames
'''.replace('\n', ' ')
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
try:
    import bot
    #USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass
    
print('Logging in.')
# http://redd.it/3cm1p8
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


AVAILABILITY = {True:'available', False:'unavailable', 'available':1, 'unavailable':0}
HEADER_FULL = '  ID            CREATED                  NAME             LINK     COMMENT      TOTAL            LAST SCANNED'
HEADER_BRIEF = '      LAST SCANNED       |   NAME'

MEMBERFORMAT_FULL = '%s  %s  %s  %s  %s (%s) | %s'
MEMBERFORMAT_BRIEF = '%s | %s'

MIN_LASTSCAN_DIFF = 86400 * 365
# Don't rescan a name if we scanned it this many days ago

def human(timestamp):
    day = datetime.datetime.utcfromtimestamp(timestamp)
    human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
    return human

def getnow(timestamp=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        return now.timestamp()
    return now

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

def getentry(**kwargs):
    if len(kwargs) != 1:
        raise Exception("Only 1 argument please")
    kw = list(kwargs.keys())[0]
    if kw == 'idint':
        cur.execute('SELECT * FROM users WHERE idint=?', [kwargs[kw]])
    elif kw == 'idstr':
        cur.execute('SELECT * FROM users WHERE idstr=?', [kwargs[kw]])
    elif kw == 'name':
        cur.execute('SELECT * FROM users WHERE LOWER(name)=?', [kwargs[kw].lower()])
    else:
        return None
    return cur.fetchone()

def reducetonames(users):
    outlist = set()
    for name in users:
        if isinstance(name, str):
            if 2 < len(name) < 21:
                outlist.add(name.lower())
        elif isinstance(name, praw.objects.Redditor):
            outlist.add(name.name.lower())
    return outlist

def userify_list(users, noskip=False):
    users = list(reducetonames(users))
    for username in users:
        try:
            preexisting = getentry(name=username)
            if preexisting is not None:
                lastscan = preexisting[SQL_LASTSCAN]
                preverify = getnow() - lastscan
                preverify = (preverify > MIN_LASTSCAN_DIFF)
                if not preverify and noskip is False:
                    print('skipping ' + username)
                    continue
            else:
                preverify = noskip
            user = r.get_redditor(username, fetch=True)
            user.preverify = preverify
            yield user
        except praw.errors.NotFound as he:
            availability = r.is_username_available(username)
            availability = AVAILABILITY[availability]
            yield [username, availability]

def process(users, quiet=False, knownid='', noskip=False):
    olds = 0
    if isinstance(users, str):
        users = [users]
    # I don't want to import types.GeneratorType just for one isinstance
    if type(users).__name__ == 'generator' or len(users) > 1:
        knownid=''
    users = userify_list(users, noskip=noskip)
    current = 0
    for user in users:
        current += 1
        data = [None] * SQL_COLUMNCOUNT
        now = int(getnow())
        data[SQL_LASTSCAN] = now
        preverify=False
        if isinstance(user, list):
            if knownid != '':
                data[SQL_IDINT] = b36(knownid)
                data[SQL_IDSTR] = knownid
            data[SQL_NAME] = user[0]
            data[SQL_AVAILABLE] = AVAILABILITY[user[1]]
        else:
            h = human(user.created_utc)
            data[SQL_IDINT] = b36(user.id)
            data[SQL_IDSTR] = user.id
            data[SQL_CREATED] = user.created_utc
            data[SQL_HUMAN] = h
            data[SQL_NAME] = user.name
            data[SQL_LINK_KARMA] = user.link_karma
            data[SQL_COMMENT_KARMA] = user.comment_karma
            data[SQL_TOTAL_KARMA] = user.comment_karma + user.link_karma
            data[SQL_AVAILABLE] = 0
            preverify = user.preverify

        # preverification happens within userify_list
        x = smartinsert(data, '%04d' % current, preverified=preverify)

        if x is False:
            olds += 1
    if quiet is False:
        print('%d old' % olds)
p = process

def processid(idnum, ranger=1):
    idnum = idnum.split('_')[-1]
    base = b36(idnum)
    for x in range(ranger):
        idnum = x + base
        if getentry(idint=idnum) != None:
            print('Skipping %s' % b36(idnum))
            continue
        idnum = 't2_' + b36(idnum)
        idnum = idnum.lower()
        search = list(r.search('author_fullname:%s' % idnum))
        print('%s - ' % idnum, end='')
        sys.stdout.flush()
        if len(search) > 0:
            item = search[0].author.name
            process(item, quiet=True, knownid=idnum[3:])
        else:
            print('No idea.')
pid = processid

def smartinsert(data, printprefix='', preverified=False):
    '''
    Originally, all queries were based on idint, but this caused problems
    when accounts were deleted / banned, because it wasn't possible to
    sql-update without knowing the ID.
    '''
    print_message(data, printprefix)
    check = False
    if not preverified:
        cur.execute('SELECT * FROM users WHERE LOWER(name)=?', [data[SQL_NAME].lower()])
        check = cur.fetchone()
        check = check is not None
    if preverified or check:
        isnew = False
        data = [
            data[SQL_IDINT],
            data[SQL_IDSTR],
            data[SQL_CREATED],
            data[SQL_HUMAN],
            data[SQL_LINK_KARMA],
            data[SQL_COMMENT_KARMA],
            data[SQL_TOTAL_KARMA],
            data[SQL_AVAILABLE],
            data[SQL_LASTSCAN],
            data[SQL_NAME],
            data[SQL_NAME].lower()]
        cur.execute('UPDATE users SET \
            idint=?, idstr=?, created=?, \
            human=?, link_karma=?, comment_karma=?, \
            total_karma=?, available=?, lastscan=?, \
            name=? WHERE LOWER(name)=?', data)
    else:
        isnew = True
        cur.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
    sql.commit()
    return isnew

def print_message(data, printprefix=''):
    if data[SQL_HUMAN] is not None:
        print('%s %s : %s : %s : %d : %d' % (
                printprefix,
                data[SQL_IDSTR],
                data[SQL_HUMAN],
                data[SQL_NAME],
                data[SQL_LINK_KARMA],
                data[SQL_COMMENT_KARMA]))
    else:
        statement = 'available' if data[SQL_AVAILABLE] is 1 else 'unavailable'
        print('%s : %s' % (data[SQL_NAME], statement))

def get_from_listing(sr, limit, listfunction, submissions=True, comments=True, returnnames=False):
    '''
    Get submission listings using one of PRAW's get methods
    and process those usernames

    `listfunction` would be praw.objects.Subreddit.get_new for example
    '''
    subreddit = r.get_subreddit(sr, fetch=sr != 'all')
    if limit is None:
        limit = 1000
    items = []
    if submissions is True:
        print('/r/%s, %d submissions' % (subreddit.display_name, limit))
        subreddit.lf = listfunction
        items += list(subreddit.lf(subreddit, limit=limit))
    if comments is True:
        print('/r/%s, %d comments' % (subreddit.display_name, limit))
        items += list(subreddit.get_comments(limit=limit))

    items = [x.author for x in items]
    while None in items:
        items.remove(None)

    if returnnames is True:
        return items

    process(items)

def get_from_new(sr, limit=None, submissions=True, comments=True, returnnames=False):
    '''
    Shortcut for get_from_listing, using /new
    '''
    listfunction = praw.objects.Subreddit.get_new
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_top(sr, limit=None, submissions=True, comments=True, returnnames=False):
    '''
    Shortcut for get_from_listing, using /top?t=all
    '''
    listfunction = praw.objects.Subreddit.get_top_from_all
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def get_from_hot(sr, limit=None, submissions=True, comments=True, returnnames=False):
    '''
    Shortcut for get_from_listing, using /hot
    '''
    listfunction = praw.objects.Subreddit.get_hot
    return get_from_listing(sr, limit, listfunction, submissions, comments, returnnames)

def fetchgenerator():
    '''
    Create an generator from cur fetches so I don't
    have to use while loops for everything
    '''
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def popgenerator(x):
    '''
    Create a generator which whittles away at the input
    list until there are no items left.
    This destroys the input list in-place.
    '''
    while len(x) > 0:
        yield x.pop()

def fetchwriter(outfile, spacer1=' ', spacer2=None, brief=False):
    '''
    Write items from the current sql query to the specified file

    If two spacers are provided, it will flip-flop between them
    on alternating lines
    '''
    flipflop = True
    for item in fetchgenerator():
        spacer = spacer1 if flipflop else spacer2
        if brief:
            item = memberformat_brief(item, spacer)
        else:
            item = memberformat_full(item, spacer)
        print(item, file=outfile)
        if spacer2 is not None:
            flipflop = not flipflop

def count(validonly=False):
    if validonly:
        cur.execute('SELECT COUNT(*) FROM users WHERE idint IS NOT NULL AND available == 0')
    else:
        cur.execute('SELECT COUNT(*) FROM users')
    return cur.fetchone()[0]

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
    file_readme = open('README.md', 'r')

    totalitems = count(validonly=False)
    validitems = count(validonly=True)
    print(totalitems, validitems)

    print('Updating readme')
    readmelines = file_readme.readlines()
    file_readme.close()
    readmelines[3] = '#####{0:,} accounts\n'.format(validitems)
    readmelines = ''.join(readmelines)
    file_readme = open('README.md', 'w')
    file_readme.write(readmelines)
    file_readme.close()

    print('Writing time file.')
    print(HEADER_FULL, file=file_time)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL AND created IS NOT NULL ORDER BY created ASC')
    fetchwriter(file_time)
    file_time.close()

    print('Writing name file.')
    print(HEADER_FULL, file=file_name)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY LOWER(name) ASC')
    fetchwriter(file_name)
    file_name.close()
    
    print('Writing karma total file.')
    print(HEADER_FULL, file=file_karma_total)
    cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY total_karma DESC, LOWER(name) ASC')
    fetchwriter(file_karma_total)
    file_karma_total.close()

    #print('Writing karma link file.')
    #print(HEADER_FULL, file=file_karma_link)
    #cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY link_karma DESC, LOWER(name) ASC')
    #fetchwriter(file_karma_link)
    #file_karma_link.close()

    #print('Writing karma comment file.')
    #print(HEADER_FULL, file=file_karma_comment)
    #cur.execute('SELECT * FROM users WHERE idint IS NOT NULL ORDER BY comment_karma DESC, LOWER(name) ASC')
    #fetchwriter(file_karma_comment)
    #file_karma_comment.close()

    print('Writing available')
    print(HEADER_BRIEF, file=file_available)
    cur.execute('SELECT * FROM users WHERE available == 1 AND LENGTH(name) > 3 ORDER BY LOWER(name) ASC')
    fetchwriter(file_available, spacer1=' ', brief=True)
    file_available.close()

def commapadding(s, spacer, spaced, left=True, forcestring=False):
    '''
    Given a number 's', make it comma-delimted and then
    pad it on the left or right using character 'spacer'
    so the whole string is of length 'spaced'

    Providing a non-numerical string will skip straight
    to padding
    '''
    if not forcestring:
        try:
            s = int(s)
            s = '{0:,}'.format(s)
        except:
            pass

    spacer = spacer * (spaced - len(s))
    if left:
        return spacer + s
    return s + spacer

def memberformat_full(data, spacer='.'):
    '''
    Given a data list, create a string that will
    become a single row in one of the show() files
    '''
    idstr = data[SQL_IDSTR]
    idstr = commapadding(idstr, spacer, 5, forcestring=True)

    # Usernames are maximum of 20 chars
    name = data[SQL_NAME]
    name += spacer*(20 - len(name))

    thuman = data[SQL_HUMAN]
    if thuman is None:
        thuman = ' '*24
    link_karma = data[SQL_LINK_KARMA]
    comment_karma = data[SQL_COMMENT_KARMA]
    total_karma = data[SQL_TOTAL_KARMA]
    if link_karma is None:
        link_karma = commapadding('None', spacer, 9)
        comment_karma = commapadding('None', spacer, 9)
        total_karma = commapadding('None', spacer, 10)
    else:
        link_karma = commapadding(link_karma, spacer, 9)
        comment_karma = commapadding(comment_karma, spacer, 9)
        total_karma = commapadding(total_karma, spacer, 10)

    lastscan = data[SQL_LASTSCAN]
    lastscan = human(lastscan)
    out = MEMBERFORMAT_FULL % (
        idstr,
        thuman,
        name,
        link_karma,
        comment_karma,
        total_karma,
        lastscan)
    return out

def memberformat_brief(data, spacer='.'):
    '''
    Shorter version of memberformat for avaialbe names.
    '''
    name = data[SQL_NAME]
    lastscan = data[SQL_LASTSCAN]
    lastscan = human(lastscan)

    out = MEMBERFORMAT_BRIEF % (lastscan, name)
    return out

def find(name, doreturn=False):
    '''
    Print the details of a username.
    '''
    cur.execute('SELECT * FROM users WHERE LOWER(name)=?', [name])
    f = cur.fetchone()
    if f:
        if doreturn:
            return f
        print_message(f)
    else:
        print(f)

def load_textfile(filename):
    '''
    Returns list of lines.
    '''
    f = open(filename, 'r')
    lines = [x.strip() for x in f.readlines()]
    f.close()
    return lines

def save_textfile(filename, lines):
    '''
    Write items of list as lines in file.
    '''
    f = open(filename, 'w')
    for x in lines:
        print(x, file=f)
    f.close()
    
def idlenew(subreddit='all', sleepy=15):
    '''
    For processing while AFK.
    '''
    while True:
        try:
            get_from_new(subreddit, 100)
        except KeyboardInterrupt:
            break
        except:
            traceback.print_exc()
        time.sleep(sleepy)