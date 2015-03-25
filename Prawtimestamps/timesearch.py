import traceback
import praw
import time
import datetime
import sqlite3

USERAGENT = ''
# Enter a useragent
try:
    import bot
    USERAGENT = bot.aPT
except ImportError:
    pass

print('Connecting to reddit')
r = praw.Reddit(USERAGENT)

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
    #  0 - idint
    #  1 - idstr
    #  2 - created
    #  3 - self
    #  4 - nsfw
    #  5 - author
    #  6 - title
    #  7 - url
    #  8 - selftext
    #  9 - score
    # 10 - subreddit
    # 11 - distinguished
    # 12 - textlen
    # 13 - num_comments
    # 14 - flair_text
    # 15 - flair_css_class

    if lower == 'update':
        cur.execute('SELECT * FROM posts ORDER BY idint DESC LIMIT 1')
        lower = cur.fetchone()[2]

    offset = -time.timezone
    subname = subreddit if type(subreddit)==str else subreddit.display_name
    if lower is None:
        if usermode is False:
            if not isinstance(subreddit, praw.objects.Subreddit):
                subreddit = r.get_subreddit(subreddit)
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
    #lower -= offset
    maxupper -= offset
    cutlower = lower
    cutupper = maxupper
    upper = lower + interval
    itemcount = 0

    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(lower), "%b %d %Y %H:%M:%S"), lower)
        print('Upper', datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(upper), "%b %d %Y %H:%M:%S"), upper)
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

        searchresults.reverse()
        print([i.id for i in searchresults])
        smartinsert(sql, cur, searchresults)

        itemsfound = len(searchresults)
        itemcount += itemsfound
        print('Found', itemsfound, 'items')
        if itemsfound < 75:
            print('Too few results, increasing interval', end='')
            diff = (1 - (itemsfound / 75)) + 1
            interval = int(interval * diff)
        if itemsfound > 99:
            print('Too many results, reducing interval', end='')
            interval = int(interval * 0.8)
            upper = lower + interval
        else:
            #Intentionally not elif
            lower = upper
            upper = lower + interval
        print()

    cur.execute('SELECT COUNT(idint) FROM posts')
    itemcount = cur.fetchone()[0]
    print('Ended with %d items in %s' % (itemcount, databasename))

def smartinsert(sql, cur, results):
    for o in results:
        cur.execute('SELECT * FROM posts WHERE idint=?', [b36(o.id)])
        if not cur.fetchone():
            try:
                o.authorx = o.author.name
            except AttributeError:
                o.authorx = '[DELETED]'

            postdata = [b36(o.id), o.fullname, o.created_utc, o.is_self, o.over_18,
            o.authorx, o.title, o.url, o.selftext, o.score,
            o.subreddit.display_name, o.distinguished, len(o.selftext),
            o.num_comments, o.link_flair_text, o.link_flair_css_class]
            cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', postdata)
            sql.commit()

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
    get_all_posts(sub, lower, maxupper, interval, usermode)
    print("Done. Press Enter to close window")
    input()
    quit()


if __name__ == '__main__':
    main()