#/u/GoldenSights
import traceback
import praw
import time
import datetime
import sqlite3

USERAGENT = ''
# Enter a useragent
MAXIMUM_EXPANSION_MULTIPLIER = 2
# The maximum amount by which it can multiply the interval
# when not enough posts are found.

try:
    import bot
    USERAGENT = bot.aPT
except ImportError:
    pass

print('Connecting to reddit')
r = praw.Reddit(USERAGENT)

SQL_COLUMNCOUNT = 16
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_SELF = 3
SQL_NSFW = 4
SQL_AUTHOR = 5
SQL_TITLE = 6
SQL_URL = 7
SQL_SELFTEXT = 8
SQL_SCORE = 9
SQL_SUBREDDIT = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13
SQL_FLAIR_TEXT = 14
SQL_FLAIR_CSS_CLASS = 15

def get_all_posts(subreddit, lower=None, maxupper=None, interval=86400, usermode=False):
    if usermode is False:
        databasename = '%s.db' % subreddit
    else:
        databasename = '@%s.db' % usermode

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute(('CREATE TABLE IF NOT EXISTS posts(idint INT, idstr TEXT, '
    'created INT, self INT, nsfw INT, author TEXT, title TEXT, '
    'url TEXT, selftext TEXT, score INT, subreddit TEXT, distinguish INT, '
    'textlen INT, num_comments INT, flair_text TEXT, flair_css_class TEXT)'))
    cur.execute('CREATE INDEX IF NOT EXISTS postindex ON posts(idint)')

    offset = -time.timezone
    subname = subreddit if type(subreddit)==str else subreddit.display_name


    if lower == 'update':
        cur.execute('SELECT * FROM posts ORDER BY idint DESC LIMIT 1')
        f = cur.fetchone()
        if f:
            lower = f[SQL_CREATED]
            print(lower)
        else:
            lower = None

    if lower is None:
        if usermode is False:
            if not isinstance(subreddit, praw.objects.Subreddit):
                subreddits = subreddit.split('+')
                subreddits = [r.get_subreddit(sr) for sr in subreddits]
                creation = min([sr.created_utc for sr in subreddits])
            else:
                creation = subreddit.created_utc
        else:
            if not isinstance(usermode, praw.objects.Redditor):
                user = r.get_redditor(usermode)
            creation = user.created_utc
        lower = creation

    if maxupper is None:
        nowstamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
        maxupper = nowstamp
        
    #outfile = open('%s-%d-%d.txt'%(subname, lower, maxupper), 'w', encoding='utf-8')
    lower -= offset
    maxupper -= offset
    cutlower = lower
    cutupper = maxupper
    upper = lower + interval
    itemcount = 0

    toomany_inarow = 0
    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower', datetime.datetime.strftime(datetime.datetime.fromtimestamp(lower), "%b %d %Y %H:%M:%S"), lower)
        print('Upper', datetime.datetime.strftime(datetime.datetime.fromtimestamp(upper), "%b %d %Y %H:%M:%S"), upper)
        #timestamps = [lower, upper]
        while True:
            try:
                if usermode is not False:
                    query = '(and author:"%s" (and timestamp:%d..%d))' % (usermode, lower, upper)
                else:
                    query = 'timestamp:%d..%d' % (lower, upper)
                searchresults = list(r.search(query, subreddit=subreddit, sort='new', limit=100, syntax='cloudsearch'))
                break
            except:
                traceback.print_exc()
                print('resuming in 5...')
                time.sleep(5)
                continue

        searchresults.reverse()
        print([i.id for i in searchresults])

        itemsfound = len(searchresults)
        itemcount += itemsfound
        print('Found', itemsfound, 'items')
        if itemsfound < 75:
            print('Too few results, increasing interval', end='')
            diff = (1 - (itemsfound / 75)) + 1
            diff = min(MAXIMUM_EXPANSION_MULTIPLIER, diff)
            interval = int(interval * diff)
        if itemsfound > 99:
            print('Too many results, reducing interval', end='')
            interval = int(interval * (0.8 - (0.05*toomany_inarow)))
            upper = lower + interval
            toomany_inarow += 1
        else:
            #Intentionally not elif
            lower = upper
            upper = lower + interval
            toomany_inarow = max(0, toomany_inarow-1)
            smartinsert(sql, cur, searchresults)
        print()

    cur.execute('SELECT COUNT(idint) FROM posts')
    itemcount = cur.fetchone()[SQL_IDINT]
    print('Ended with %d items in %s' % (itemcount, databasename))

def smartinsert(sql, cur, results, delaysave=False):
    for o in results:
        cur.execute('SELECT * FROM posts WHERE idint=?', [b36(o.id)])
        if not cur.fetchone():
            try:
                o.authorx = o.author.name
            except AttributeError:
                o.authorx = '[DELETED]'

            if o.is_self:
                o.url = None
            postdata = [None] * SQL_COLUMNCOUNT
            postdata[SQL_IDINT] = b36(o.id)
            postdata[SQL_IDSTR] = o.fullname
            postdata[SQL_CREATED] = o.created_utc
            postdata[SQL_SELF] = o.is_self
            postdata[SQL_NSFW] = o.over_18
            postdata[SQL_AUTHOR] = o.authorx
            postdata[SQL_TITLE] = o.title
            postdata[SQL_URL] = o.url
            postdata[SQL_SELFTEXT] = o.selftext
            postdata[SQL_SCORE] = o.score
            postdata[SQL_SUBREDDIT] = o.subreddit.display_name
            postdata[SQL_DISTINGUISHED] = o.distinguished
            postdata[SQL_TEXTLEN] = len(o.selftext)
            postdata[SQL_NUM_COMMENTS] = o.num_comments
            postdata[SQL_FLAIR_TEXT] = o.link_flair_text
            postdata[SQL_FLAIR_CSS_CLASS] = o.link_flair_css_class
            cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', postdata)
        else:
            cur.execute('UPDATE posts SET score=? WHERE idint=?', [o.score, b36(o.id)])
    if not delaysave:
        sql.commit()

def updatescores(databasename):
    if '.db' not in databasename:
        databasename += '.db'
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    cur.execute('SELECT COUNT(*) FROM posts')
    totalitems = cur.fetchone()[0]
    cur.execute('SELECT * FROM posts')
    itemcount = 0
    while True:
        f = []
        for x in range(100):
            x = cur.fetchone()
            if x is not None and 't3_' in x[SQL_IDSTR]:
                f.append(x[SQL_IDSTR])
        if len(f) == 0:
            break
        posts = r.get_info(thing_id=f)
        itemcount += len(f)
        print('%d / %d updated' % (itemcount, totalitems))
        smartinsert(sql, cur2, posts, delaysave=True)
    sql.commit()
    sql.close()

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

def main():
    usermode = False
    maxupper = None
    interval = 86400
    print('\nGet posts from subreddit\n/r/', end='')
    sub = input()
    if sub == '':
        print('Get posts from user\n/u/', end='')
        usermode = input()
        sub = 'all'
    print('\nLower bound (Leave blank to get ALL POSTS)\nEnter "update" to use last entry\n]: ', end='')
    lower  = input().lower()
    if lower == '':
        lower = None
    if lower not in [None, 'update']:
        print('Maximum upper bound\n]: ', end='')
        maxupper = input()
        if maxupper == '':
            maxupper = datetime.datetime.now(datetime.timezone.utc).timestamp()
        print('Starting interval (Leave blank for standard)\n]: ', end='')
        interval = input()
        if interval == '':
            interval = 84600
        try:
            maxupper = int(maxupper)
            lower = int(lower)
            interval = int(interval)
        except ValueError:
            print("lower and upper bounds must be unix timestamps")
            input()
            quit()
    get_all_posts(sub, lower, maxupper, interval, usermode)
    print('\nDone. Press Enter to close window or type "restart"')
    return input().lower() == 'restart'
    quit()


if __name__ == '__main__':
    go= True
    while go:
        go = main()