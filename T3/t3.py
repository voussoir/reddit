#/u/GoldenSights
import datetime
import praw
import random
import sqlite3
import time


USERAGENT = ""
try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print('Connecting (unauthenticated).')
r = praw.Reddit(USERAGENT)

sql = sqlite3.connect('D:/T3/t3.db')
cur = sql.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS posts(
    idint INT, 
    idstr TEXT, 
    created INT, 
    author TEXT, 
    subreddit TEXT, 
    self INT, 
    nsfw INT, 
    title TEXT, 
    url TEXT, 
    selftext TEXT, 
    score INT, 
    distinguished INT, 
    textlen INT, 
    num_comments INT)
    ''')
cur.execute('CREATE INDEX IF NOT EXISTS idintindex on posts(idint)')
SQL_COLUMNCOUNT = 14
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_AUTHOR = 3
SQL_SUBREDDIT = 4
SQL_SELF = 5
SQL_NSFW = 6
SQL_TITLE = 7
SQL_URL = 8
SQL_SELFTEXT = 9
SQL_SCORE = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13

DISTINGUISHMAP   = {0:'user', 1:'moderator', 2:'admin'}
DISTINGUISHMAP_R = {'user':0, 'moderator':1, 'admin':2, None:0}

LOWERBOUND = 9999000
#            5yba0
UPPERBOUND = 164790958
#            2q41im

#    1,679,616 = 10000
#    9,999,000 = 5yba0
#   60,466,176 = 100000
#  120,932,352 = 200000
#  164,790,958 = 2q41im


class Post:
    ''' Generic class to map the indices of DB entries to names '''
    def __init__(self, data):
        self.idint = data[SQL_IDINT]
        self.idstr = data[SQL_IDSTR]
        self.created_utc = data[SQL_CREATED]
        self.is_self = True if data[SQL_SELF] == 1 else False
        self.over_18 = True if data[SQL_NSFW] == 1 else False
        self.author = data[SQL_AUTHOR]
        self.title = data[SQL_TITLE]
        self.url = data[SQL_URL]
        self.selftext = data[SQL_SELFTEXT]
        self.score = data[SQL_SCORE]
        self.subreddit = data[SQL_SUBREDDIT]
        self.distinguished = DISTINGUISHMAP[data[SQL_DISTINGUISHED]]
        self.distinguished_int = data[SQL_DISTINGUISHED]
        self.textlen = data[SQL_TEXTLEN]
        self.num_comments = data[SQL_NUM_COMMENTS]

def process(idstr, ranger=0):
    '''
    Given a string or a set of strings that represent thread IDs,
    get those Submissions and put them into the database
    '''

    if isinstance(idstr, str):
        idstr = [idstr]
    last = b36(idstr[-1])
    for x in range(ranger):
        # Take the last item in the list and get its ID in decimal
        # Then add the next `ranger` IDs into the list
        idstr.append(b36(last+x+1))
    idstr = remove_existing(idstr)
    idstr = verify_t3(idstr)
    while len(idstr) > 0:
        hundred = idstr[:100]
        print('(%d) %s > %s' % (len(idstr), hundred[0], hundred[-1]))
        try:
            items = list(r.get_submissions(hundred))
        except praw.errors.HTTPException as e:
            # 404 error means no posts exist for that ID.
            # So we know there's no posts here, and continue on
            # Anything other than 404, we need to hear about please
            if e._raw.status_code != 404:
                raise e
            items = []
            pass
        idstr = idstr[100:]
        for item in items:
            print(' %s, %s' % (item.fullname, item.subreddit.display_name))
            item = dataformat(item)
            # Preverification happens via remove_existing
            smartinsert(item, preverified=True)
        sql.commit()
p = process

def remove_existing(idstr):
    '''
    Given a list of IDs, remove any which are already
    in the database

    This serves as preverification for process() so we don't
    do a SELECT for the same item twice.
    '''
    outset = []
    for i in idstr:
        if i in outset:
            continue
        check = i.replace('t3_', '')
        check = b36(check)
        cur.execute('SELECT * FROM posts WHERE idint==?', [check])
        if not cur.fetchone():
            outset.append(i)
        else:
            print(' %s preverify' % i)
    return outset

def dataformat(item):
    '''
    Given a Subission, return a list
    where the indices contain the data that corresponds
    to the the SQL column with the same indice
    '''

    data = [None] * SQL_COLUMNCOUNT
    data[SQL_IDINT] = b36(item.id)
    data[SQL_IDSTR] = item.id
    data[SQL_CREATED] = item.created_utc

    author = item.author
    if author is not None:
        author = author.name
    data[SQL_AUTHOR] = author
    data[SQL_SUBREDDIT] = item.subreddit.display_name
    data[SQL_SELF] = 1 if item.is_self else 0
    data[SQL_NSFW] = 1 if item.over_18 else 0
    data[SQL_TITLE] = item.title

    url = item.url
    if ('/comments/%s/' % item.id) in url:
        # Don't waste your bytes saving the URL for selfposts
        url = None
    data[SQL_URL] = url
    selftext = item.selftext

    if selftext == '':
        selftext = None
    data[SQL_SELFTEXT] = selftext
    data[SQL_SCORE] = item.score

    distinguished = item.distinguished

    data[SQL_DISTINGUISHED] = DISTINGUISHMAP_R[item.distinguished]
    data[SQL_TEXTLEN] = len(item.selftext)
    data[SQL_NUM_COMMENTS] = item.num_comments
    return data

def smartinsert(data, preverified=False):
    '''
    Given a list, into the database if the item does not already exist
    Preverification means that it will not perform a SELECT to see
    if the item exists, because you have already guaranteed this.
    '''

    if not preverified:
        cur.execute('SELECT * FROM posts WHERE idint==?', [data[SQL_IDINT]])
    if (preverified) or (cur.fetchone() is None):
        cur.execute('''
            INSERT INTO posts VALUES(
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)

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

def base36decode(number):
    return int(number, 36)

def b36(i):
    if type(i) == int:
        return base36encode(i)
    if type(i) == str:
        return base36decode(i)

def verify_t3(items):
    for index in range(len(items)):
        i = items[index]
        if 't3_' not in i:
            items[index] = 't3_' + i
    return items

def human(timestamp):
    day = datetime.datetime.utcfromtimestamp(timestamp)
    human = datetime.datetime.strftime(day, "%b %d %Y %H:%M:%S UTC")
    return human

def lastitem():
    cur.execute('SELECT * FROM posts ORDER BY idint DESC LIMIT 1')
    return cur.fetchone()[SQL_IDSTR]