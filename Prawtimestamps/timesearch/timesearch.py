import time
import traceback

from . import common
from . import tsdb


# The maximum amount by which it can multiply the interval
# when not enough posts are found.
MAXIMUM_EXPANSION_MULTIPLIER = 2


def timesearch(
        subreddit=None,
        username=None,
        lower=None,
        upper=None,
        interval=86400,
    ):
    '''
    Collect submissions across time.
    Please see the global DOCSTRING variable.
    '''
    if (subreddit is None) == (username is None):
        raise Exception('Enter subreddit or username but not both')

    common.bot.login(common.r)

    if subreddit:
        database = tsdb.TSDB.for_subreddit(subreddit)
    else:
        # When searching, we'll take the user's submissions from anywhere.
        subreddit = 'all'
        database = tsdb.TSDB.for_user(username)
    cur = database.sql.cursor()

    offset = -1 * time.timezone

    if lower == 'update':
        # Start from the latest submission
        cur.execute('SELECT * FROM submissions ORDER BY idint DESC LIMIT 1')
        f = cur.fetchone()
        if f:
            lower = f[tsdb.SQL_SUBMISSION['created']]
            print(f[tsdb.SQL_SUBMISSION['idstr']], common.human(lower), lower)
        else:
            lower = None

    if not isinstance(subreddit, common.praw.models.Subreddit):
        subreddit = common.r.subreddit(subreddit)

    if subreddit != 'all':
        if isinstance(subreddit, common.praw.models.Subreddit):
            creation = subreddit.created_utc
        else:
            subreddits = subreddit.split('+')
            subreddits = [common.r.subreddit(sr) for sr in subreddits]
            creation = min([sr.created_utc for sr in subreddits])
    else:
        if not isinstance(username, common.praw.models.Redditor):
            user = common.r.redditor(username)
        creation = user.created_utc

    if lower is None or lower < creation:
        lower = creation

    maxupper = upper
    if maxupper is None:
        maxupper = common.get_now()

    lower -= offset
    maxupper -= offset
    upper = lower + interval
    itemcount = 0

    toomany_inarow = 0
    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower:', common.human(lower), lower)
        print('Upper:', common.human(upper), upper)
        while True:
            if username:
                query = '(and author:"%s" (and timestamp:%d..%d))' % (username, lower, upper)
            else:
                query = 'timestamp:%d..%d' % (lower, upper)
            try:

                searchresults = subreddit.search(
                    query,
                    sort='new',
                    limit=100,
                    syntax='cloudsearch'
                )
                searchresults = list(searchresults)
                break
            except Exception:
                traceback.print_exc()
                print('resuming in 5...')
                time.sleep(5)
                continue

        searchresults.sort(key=lambda x: x.created_utc)
        print([i.id for i in searchresults])

        itemsfound = len(searchresults)
        itemcount += itemsfound
        print('Found', itemsfound, 'items.')
        if itemsfound < 75:
            print('Too few results, increasing interval', end='')
            diff = (1 - (itemsfound / 75)) + 1
            diff = min(MAXIMUM_EXPANSION_MULTIPLIER, diff)
            interval = int(interval * diff)
        if itemsfound > 99:
            #Intentionally not elif
            print('Too many results, reducing interval', end='')
            interval = int(interval * (0.8 - (0.05 * toomany_inarow)))
            upper = lower + interval
            toomany_inarow += 1
        else:
            lower = upper
            upper = lower + interval
            toomany_inarow = max(0, toomany_inarow-1)
            database.insert(searchresults)
        print()

    cur.execute('SELECT COUNT(idint) FROM submissions')
    itemcount = cur.fetchone()[0]

    print('Ended with %d items in %s' % (itemcount, database.filepath.basename))

def timesearch_argparse(args):
    if args.lower == 'update':
        lower = 'update'
    else:
        lower = common.int_none(args.lower)

    return timesearch(
        subreddit=args.subreddit,
        username=args.username,
        lower=lower,
        upper=common.int_none(args.upper),
        interval=common.int_none(args.interval),
    )
