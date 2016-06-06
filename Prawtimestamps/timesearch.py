#/u/GoldenSights
import datetime
import os
import praw
import sqlite3
import sys
import time
import traceback


USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
MAXIMUM_EXPANSION_MULTIPLIER = 2
# The maximum amount by which it can multiply the interval
# when not enough posts are found.
DATABASE_FOLDER = 'databases'
if not os.path.exists(DATABASE_FOLDER):
    os.makedirs(DATABASE_FOLDER)
DATABASE_SUBREDDIT = '%s/%s.db' % (DATABASE_FOLDER, '%s')
DATABASE_USER = '%s/@%s.db' % (DATABASE_FOLDER, '%s')



try:
    import bot
    USERAGENT = bot.aPT
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

SQL_SUBMISSION_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'self',
    'nsfw',
    'author',
    'title',
    'url',
    'selftext',
    'score',
    'subreddit',
    'distinguish',
    'textlen',
    'num_comments',
    'flair_text',
    'flair_css_class',
    'augmented_at',
    'augmented_count',
]

SQL_COMMENT_COLUMNS = [
    'idint',
    'idstr',
    'created',
    'author',
    'parent',
    'submission',
    'body',
    'score',
    'subreddit',
    'distinguish',
    'textlen',
]

SQL_SUBMISSION = {key:index for (index, key) in enumerate(SQL_SUBMISSION_COLUMNS)}
SQL_COMMENT = {key:index for (index, key) in enumerate(SQL_COMMENT_COLUMNS)}

prompt_ca_database = '''
- Database filename
  Leave blank to do 1 submission
  ]: '''
prompt_ca_specific = '''
- ID of submisson
  ]: '''
prompt_ca_limit = '''
- Limit - number of MoreComments objects to replace.
  Enter 0 to have no limit and get all.
  ]: '''
prompt_ca_threshold = '''
- Threshold - minimum number of children comments a MoreComments
  object must have to warrant a replacement.
  ]: '''
prompt_ca_numthresh = '''
- Minimum num_comments a thread must have to be scanned
  ]: '''
prompt_ca_skips = '''
- Skips - Skip ahead by this many threads, to pick up where you left off.
  ]: '''
prompt_ca_verbosity = '''
- Verbosity. 0=quiter, 1=louder
  ]: '''

prompt_ts_subreddit = '''
- Subreddit
  Leave blank to get username instead
  /r/'''
prompt_ts_username = '''
- Get posts from user
  /u/'''
prompt_ts_lowerbound = '''
- Lower bound
  Leave blank to get ALL POSTS
  Enter "update" to use last entry
  ]: '''
prompt_ts_startinginterval = '''
- Starting interval
  Leave blank for standard
  ]: '''



def b36(i):
    if type(i) == int:
        return base36encode(i)
    if type(i) == str:
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

def commentaugment(databasename, limit, threshold, numthresh, skips, verbose, specific_submission=None):
    '''
    Take the IDs of collected submissions, and gather comments from those threads.
    '''
    if specific_submission is not None:
        if not specific_submission.startswith('t3_'):
            specific_submission = 't3_' + specific_submission
        specific_submission_obj = r.get_submission(submission_id=specific_submission[3:])
        databasename = specific_submission_obj.subreddit.display_name

    databasename = databasename.replace('.db', '')
    databasename = databasename.replace('/', '\\')
    databasename = databasename.split('\\')[-1]
    databasename = database_filename(subreddit=databasename)
    #print(databasename)
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    initialize_database(sql, cur)

    if specific_submission is None:
        cur.execute('''
            SELECT idstr FROM submissions
            WHERE augmented_at IS NULL
            AND num_comments > ?
            ORDER BY num_comments DESC''',
            [numthresh])
        fetchall = cur.fetchall()
        fetchall = [item[0] for item in fetchall]
    else:
        # Make sure the object we're augmenting is in the table too!
        smartinsert(sql, cur, [specific_submission_obj])
        fetchall = [specific_submission]

    totalthreads = len(fetchall)

    if verbose:
        spacer = '\n\t'
    else:
        spacer = ' '

    scannedthreads = 0
    while True:
        id_batch = fetchall[:100]
        fetchall = fetchall[100:]
        id_batch = list(filter(None, id_batch))
        if len(id_batch) == 0:
            return

        for submission in id_batch:
            submission = r.get_submission(submission_id=submission.split('_')[-1])
            print('Processing %s%sexpecting %d | ' % (submission.fullname, spacer, submission.num_comments), end='')
            sys.stdout.flush()
            if verbose:
                print()
            comments = get_comments_for_thread(submission, limit, threshold, verbose)

            smartinsert(sql, cur, comments, nosave=True)
            cur.execute('''
                UPDATE submissions
                set augmented_at = ?,
                augmented_count = ?
                WHERE idstr == ?''',
                [get_now(), len(comments), submission.fullname])
            sql.commit()

            scannedthreads += 1
            if verbose:
                print('\t', end='')
            print('Found %d |%s%d / %d threads complete' % (len(comments), spacer, scannedthreads, totalthreads))

def commentaugment_prompt():
    print(prompt_ca_database, end='')
    databasename = input()
    if databasename != '':
        if databasename[-3:] != '.db':
            databasename += '.db'
        specific_submission = ''
    else:
        print(prompt_ca_specific, end='')
        specific_submission = input()
    print(prompt_ca_limit, end='')
    limit = input()
    if limit == '':
        limit = None
    else:
        limit = int(limit)
        if limit < 1:
            limit = None

    print(prompt_ca_threshold, end='')
    threshold = input()
    threshold = fixint(threshold)

    if specific_submission == '':
        print(prompt_ca_numthresh, end='')
        numthresh = input()
        numthresh = fixint(numthresh)

        print(prompt_ca_skips, end='')
        skips = input()
        skips = fixint(skips)
        specific_submission = None
    else:
        numthresh = 0
        skips = 0

    print(prompt_ca_verbosity, end='')
    verbose = input()
    verbose = fixint(verbose)
    verbose = (verbose is 1)

    commentaugment(databasename, limit, threshold, numthresh, skips, verbose, specific_submission)
    print('Done')

def database_filename(subreddit=None, username=None):
    '''
    Given a subreddit name or username, return the appropriate database filename.
    '''
    if bool(subreddit) == bool(username):
        raise ValueError('One and only one of subreddit and username please')
    text = subreddit or username
    if text.endswith('.db'):
        text = text[:-3]
    text = text.replace('/', '\\')
    text = text.split('\\')[-1]
    if subreddit:
        return DATABASE_SUBREDDIT % text
    else:
        return DATABASE_USER % text

def fixint(i):
    if i == '':
        return 0
    i = int(i)
    if i < 0:
        return 0
    return i

def get_all_posts(subreddit, lower=None, maxupper=None,
                  interval=86400, usermode=False):
    '''
    Get submissions from a subreddit or user between two points in time
    If lower and upper are None, get ALL posts from the subreddit or user.
    '''
    if usermode is False:
        databasename = database_filename(subreddit=subreddit)
    else:
        databasename = database_filename(username=usermode)

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    initialize_database(sql, cur)

    offset = -time.timezone

    if isinstance(subreddit, praw.objects.Subreddit):
        subreddit = subreddit.display_name
    elif subreddit is None:
        subreddit = 'all'

    if lower == 'update':
        # Get the item with the highest ID number, and use it's
        # timestamp as the lower.
        cur.execute('SELECT * FROM submissions ORDER BY idint DESC LIMIT 1')
        f = cur.fetchone()
        if f:
            lower = f[SQL_SUBMISSION['created']]
            print(f[SQL_SUBMISSION['idstr']], human(lower), lower)
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

    lower -= offset
    maxupper -= offset
    cutlower = lower
    cutupper = maxupper
    upper = lower + interval
    itemcount = 0

    toomany_inarow = 0
    while lower < maxupper:
        print('\nCurrent interval:', interval, 'seconds')
        print('Lower', human(lower), lower)
        print('Upper', human(upper), upper)
        while True:
            try:
                if usermode is not False:
                    query = '(and author:"%s" (and timestamp:%d..%d))' % (
                        usermode, lower, upper)
                else:
                    query = 'timestamp:%d..%d' % (lower, upper)
                searchresults = list(r.search(query, subreddit=subreddit,
                                              sort='new', limit=100,
                                              syntax='cloudsearch'))
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
            #Intentionally not elif
            print('Too many results, reducing interval', end='')
            interval = int(interval * (0.8 - (0.05 * toomany_inarow)))
            upper = lower + interval
            toomany_inarow += 1
        else:
            lower = upper
            upper = lower + interval
            toomany_inarow = max(0, toomany_inarow-1)
            smartinsert(sql, cur, searchresults)
        print()

    cur.execute('SELECT COUNT(idint) FROM submissions')
    itemcount = cur.fetchone()[SQL_SUBMISSION['idint']]
    print('Ended with %d items in %s' % (itemcount, databasename))
    sql.close()
    del cur
    del sql

def get_comments_for_thread(submission, limit, threshold, verbose):
    comments = nofailrequest(lambda x: x.comments)(submission)
    comments = praw.helpers.flatten_tree(comments)
    comments = manually_replace_comments(comments, limit, threshold, verbose)
    return comments

def get_now(stamp=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    if stamp:
        return int(now.timestamp())
    return now

def human(timestamp):
    x = datetime.datetime.utcfromtimestamp(timestamp)
    x = datetime.datetime.strftime(x, "%b %d %Y %H:%M:%S")
    return x

def initialize_database(sql, cur):
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS submissions(
        idint INT,
        idstr TEXT,
        created INT,
        self INT,
        nsfw INT,
        author TEXT,
        title TEXT,
        url TEXT,
        selftext TEXT,
        score INT,
        subreddit TEXT,
        distinguish INT,
        textlen INT,
        num_comments INT,
        flair_text TEXT,
        flair_css_class TEXT,
        augmented_at INT,
        augmented_count INT)''')
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS comments(
        idint INT,
        idstr TEXT,
        created INT,
        author TEXT,
        parent TEXT,
        submission TEXT,
        body TEXT,
        score INT,
        subreddit TEXT,
        distinguish TEXT,
        textlen INT)''')

    cur.execute('CREATE INDEX IF NOT EXISTS submission_index ON submissions(idstr)')
    cur.execute('CREATE INDEX IF NOT EXISTS comment_index ON comments(idstr)')

def livestream(subreddit=None, username=None, sleepy=30, limit=100, submissions=True, comments=False, debug=False):
    '''
    Continuously get posts from this source
    and insert them into the database
    '''
    if subreddit is None and username is None:
        print('Enter username or subreddit parameter')
        return
    if subreddit is not None and username is not None:
        print('Enter subreddit OR username, not both')
        return

    if subreddit:
        print('Getting subreddit %s' % subreddit)
        sql = sqlite3.connect(database_filename(subreddit=subreddit))
        item = r.get_subreddit(subreddit)
        submissions = item.get_new if submissions else None
        comments = item.get_comments if comments else None
    else:
        print('Getting redditor %s' % username)
        sql = sqlite3.connect(database_filename(username=username))
        item = r.get_redditor(username)
        submissions = item.get_submitted if submissions else None
        comments = item.get_comments if comments else None
    
    livestreamer = lambda *a, **k: livestream_helper(submissions, comments, debug, *a, **k)

    cur = sql.cursor()
    while True:
        try:
            bot.refresh(r)  # personal use
            items = livestreamer(limit=limit)
            newitems = smartinsert(sql, cur, items)
            print('%s +%d' % (human(get_now()), newitems), end='')
            if newitems == 0:
                print('\r', end='')
            else:
                print()
            if debug:
                print('Loop finished.')
            time.sleep(sleepy)
        except KeyboardInterrupt:
            print()
            sql.commit()
            sql.close()
            del cur
            del sql
            return
        except Exception as e:
            traceback.print_exc()
            time.sleep(5)
hangman = lambda: livestream(username='gallowboob', sleepy=60, submissions=True, comments=True)

def livestream_helper(submission_function=None, comment_function=None, debug=False, *a, **k):
    '''
    Given a submission-retrieving function and/or a comment-retrieving function,
    collect submissions and comments in a list together and return that.
    '''
    if (submission_function, comment_function) == (None, None):
        raise TypeError('livestream helper got double Nones')
    results = []

    if submission_function:
        if debug: print('Getting submissions', a, k)
        results += list(submission_function(*a, **k))
    if comment_function:
        if debug: print('Getting comments', a, k)
        results += list(comment_function(*a, **k))
    if debug:
        print('Collected. Saving...')
    return results

def manually_replace_comments(incomments, limit=None, threshold=0, verbose=False):
    '''
    PRAW's replace_more_comments method cannot continue
    where it left off in the case of an Ow! screen.
    So I'm writing my own function to get each MoreComments item individually

    Furthermore, this function will maximize the number of retrieved comments by
    sorting the MoreComments objects and getting the big chunks before worrying
    about the tail ends.
    '''

    comments = []
    morecomments = []
    while len(incomments) > 0:
        item = incomments.pop()
        if isinstance(item, praw.objects.MoreComments) and item.count >= threshold:
            morecomments.append(item)
        elif isinstance(item, praw.objects.Comment):
            comments.append(item)

    try:
        while True:
            if limit is not None and limit <= 0:
                break
            if len(morecomments) == 0:
                break
            morecomments.sort(key=lambda x: x.count)
            mc = morecomments.pop()
            additional = nofailrequest(mc.comments)()
            additionals = 0
            if limit is not None:
                limit -= 1
            for item in additional:
                if isinstance(item, praw.objects.MoreComments) and item.count >= threshold:
                    morecomments.append(item)
                elif isinstance(item, praw.objects.Comment):
                    comments.append(item)
                    additionals += 1
            if verbose:
                s = '\tGot %d more, %d so far.' % (additionals, len(comments))
                if limit is not None:
                    s += ' Can perform %d more replacements' % limit
                print(s)
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
    return comments

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
                try:
                    result = function(*args, **kwargs)
                    return result
                except AssertionError:
                    # Strange PRAW bug causes certain MoreComments
                    # To throw assertion error, so just ignore it
                    # And get onto the next one.
                    return []
            except:
                traceback.print_exc()
                print('Retrying in 2...')
                time.sleep(2)
    return a

def smartinsert(sql, cur, results, delaysave=False, nosave=False):
    '''
    Insert the data into the database
    Or update the listing if it already exists
    `results` is a list of submission or comment objects
    `delaysave` commits after all inserts
    `nosave` does not commit

    returns the number of posts that were new.
    '''
    newposts = 0
    for o in results:
        author = o.author.name if o.author else '[DELETED]'

        if isinstance(o, praw.objects.Submission):
            cur.execute('SELECT * FROM submissions WHERE idstr == ?', [o.fullname])
            if not cur.fetchone():
                newposts += 1
                postdata = [None] * len(SQL_SUBMISSION)
                if o.is_self:
                    o.url = None

                postdata[SQL_SUBMISSION['idint']] = b36(o.id)
                postdata[SQL_SUBMISSION['idstr']] = o.fullname
                postdata[SQL_SUBMISSION['created']] = o.created_utc
                postdata[SQL_SUBMISSION['self']] = o.is_self
                postdata[SQL_SUBMISSION['nsfw']] = o.over_18
                postdata[SQL_SUBMISSION['author']] = author
                postdata[SQL_SUBMISSION['title']] = o.title
                postdata[SQL_SUBMISSION['url']] = o.url
                postdata[SQL_SUBMISSION['selftext']] = o.selftext
                postdata[SQL_SUBMISSION['score']] = o.score
                postdata[SQL_SUBMISSION['subreddit']] = o.subreddit.display_name
                postdata[SQL_SUBMISSION['distinguish']] = o.distinguished
                postdata[SQL_SUBMISSION['textlen']] = len(o.selftext)
                postdata[SQL_SUBMISSION['num_comments']] = o.num_comments
                postdata[SQL_SUBMISSION['flair_text']] = o.link_flair_text
                postdata[SQL_SUBMISSION['flair_css_class']] = o.link_flair_css_class

                cur.execute('''INSERT INTO submissions VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', postdata)
            else:
                cur.execute('''
                    UPDATE submissions SET
                    nsfw = coalesce(?, nsfw),
                    score = coalesce(?, score),
                    selftext = coalesce(?, selftext),
                    distinguish = coalesce(?, distinguish),
                    num_comments = coalesce(?, num_comments),
                    flair_text = coalesce(?, flair_text),
                    flair_css_class = coalesce(?, flair_css_class)
                    WHERE idstr == ?
                ''',
                [o.over_18, o.score, o.selftext, o.distinguished, o.num_comments,
                o.link_flair_text, o.link_flair_css_class, o.fullname])

        if isinstance(o, praw.objects.Comment):
            cur.execute('SELECT * FROM comments WHERE idstr == ?', [o.fullname])

            if not cur.fetchone():
                newposts += 1
                postdata = [None] * len(SQL_COMMENT)

                postdata[SQL_COMMENT['idint']] = b36(o.id)
                postdata[SQL_COMMENT['idstr']] = o.fullname
                postdata[SQL_COMMENT['created']] = o.created_utc
                postdata[SQL_COMMENT['author']] = author
                postdata[SQL_COMMENT['parent']] = o.parent_id
                postdata[SQL_COMMENT['submission']] = o.link_id
                postdata[SQL_COMMENT['body']] = o.body
                postdata[SQL_COMMENT['score']] = o.score
                postdata[SQL_COMMENT['subreddit']] = o.subreddit.display_name
                postdata[SQL_COMMENT['distinguish']] = o.distinguished
                postdata[SQL_COMMENT['textlen']] = len(o.body)

                cur.execute('''INSERT INTO comments VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', postdata)
            else:
                cur.execute('''
                    UPDATE comments SET
                    score = coalesce(?, score),
                    body = coalesce(?, body),
                    distinguish = coalesce(?, distinguish)
                    WHERE idstr == ?
                ''',
                [o.score, o.body, o.distinguished, o.fullname])

        if not delaysave and not nosave:
            sql.commit()
    if delaysave and not nosave:
        sql.commit()
    return newposts

def timesearch_prompt():
    while True:
        usermode = False
        maxupper = None
        interval = 86400
        print(prompt_ts_subreddit, end='')
        sub = input()
        if sub == '':
            print(prompt_ts_username, end='')
            usermode = input()
            sub = 'all'
        if usermode:
            p = database_filename(username=usermode)
        else:
            p = database_filename(subreddit=sub)
        if os.path.exists(p):
            print('Found %s' % p)
        print(prompt_ts_lowerbound, end='')
        lower  = input().lower()
        if lower == '':
            lower = None
        if lower not in [None, 'update']:
            print('- Maximum upper bound\n]: ', end='')
            maxupper = input()
            if maxupper == '':
                maxupper = datetime.datetime.now(datetime.timezone.utc)
                maxupper = maxupper.timestamp()
            print(prompt_ts_startinginterval, end='')
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
        if input().lower() != 'restart':
            break

def updatescores(databasename, submissions=True, comments=False):
    '''
    Get all submissions or comments from the database, and update
    them with the current scores.
    '''
    databasename = database_filename(subreddit=databasename)
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    
    if submissions and comments:
        cur2.execute('SELECT COUNT(*) FROM posts')
        cur.execute('SELECT * FROM posts')

    elif submissions:
        cur2.execute('SELECT COUNT(*) FROM posts WHERE idstr LIKE "t3_%"')
        cur.execute('SELECT * FROM posts WHERE idstr LIKE "t3_%"')

    elif comments:
        cur2.execute('SELECT COUNT(*) FROM posts WHERE idstr LIKE "t1_%"')
        cur.execute('SELECT * FROM posts WHERE idstr LIKE "t1_%"')
    
    totalitems = cur2.fetchone()[0]
    itemcount = 0
    while True:
        f = []
        for x in range(100):
            x = cur.fetchone()
            if x is not None:
                f.append(x[SQL_SUBMISSION['idstr']])
        if len(f) == 0:
            break
        posts = r.get_info(thing_id=f)
        itemcount += len(f)
        print('%d / %d updated' % (itemcount, totalitems))
        smartinsert(sql, cur2, posts, nosave=True)
    sql.commit()
    sql.close()
    del cur
    del sql

if __name__ == '__main__':
    if len(sys.argv) > 1:
        c = sys.argv[1]
        exec(c)
    else:
        timesearch_prompt()
