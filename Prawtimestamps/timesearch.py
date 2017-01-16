#/u/GoldenSights
DOCSTRING='''
Timesearch
The subreddit archiver

The basics:
1. Collect a subreddit's submissions
    > timesearch timesearch -r subredditname

2. Collect the comments for those submissions
    > timesearch commentaugment subredditname.db


Commands for collecting:
{docheader_timesearch}
{docheader_commentaugment}
{docheader_livestream}
{docheader_getstyles}

Commands for processing:
{docheader_offline_reading}
{docheader_redmash}
{docheader_breakdown}

TO SEE DETAILS ON EACH COMMAND, RUN
> timesearch <command>
'''

DOCSTRING_TIMESEARCH = '''
timesearch:
    Collect submissions from the subreddit across all of history, or
    Collect submissions by a user (as many as possible).

    > timesearch timesearch -r subredditname <flags>
    > timesearch timesearch -u username <flags>

    -r "test" | --subreddit "test":
        The subreddit to scan. Mutually exclusive with username.

    -u "test" | --username "test":
        The user to scan. Mutually exclusive with subreddit.

    -l "update" | --lower "update":
        If a number - the unix timestamp to start at.
        If "update" - continue from latest submission in db.
        Default: update

    -up 1467460221 | --upper 1467460221:
        If a number - the unix timestamp to stop at.
        If not provided - stop at current time.
        Default: current time

    -i 86400 | --interval 86400:
        The initial interval for the scanning window, in seconds.
        This is only a starting value. The window will shrink and stretch
        as necessary based on received submission counts.
        Default: 86400
'''

DOCSTRING_COMMENTAUGMENT = '''
commentaugment:
    Collect comments for the submissions in the database.
    NOTE - if you did a timesearch scan on a username, this function is
    useless because it finds comments on the submissions you collected,
    even if the target user was not the OP.
    It does not find the user's comment history. That's not possible.

    > timesearch commentaugment database.db <flags>

    flags:
    -l 18 | --limit 18:
        The number of MoreComments objects to replace.
        Default: No limit

    -t 5 | --threshold 5:
        The number of comments a MoreComments object must claim to have
        for us to open it.
        Actual number received may be lower.
        Default: >= 0

    -n 4 | --num_thresh 4:
        The number of comments a submission must claim to have for us to
        scan it at all.
        Actual number received may be lower.
        Default: >= 1

    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, scan only that submission.

    -v | --verbose:
        If provided, print more stuff while working.
'''

DOCSTRING_LIVESTREAM = '''
livestream:
    Continously collect submissions and/or comments.

    > timesearch livestream -r subredditname <flags>
    > timesearch livestream -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit to collect from.

    -u "test" | --username "test":
        The redditor to collect from.

    -s | --submissions:
        If provided, do collect submissions. Otherwise don't.

    -c | --comments:
        If provided, do collect comments. Otherwise don't.
    If submissions and comments are BOTH left unspecified, then they will
    BOTH be collected.

    -v | --verbose:
        If provided, print extra information to the screen.

    -w 30 | --wait 30:
        The number of seconds to wait between cycles.

    -1 | --once:
        If provided, only do a single loop. Otherwise go forever.
'''

DOCSTRING_GETSTYLES = '''
getstyles:
    Collect the sidebar text, stylesheet, and css images.

    > timesearch getstyles subredditname <flags>

    flags:
        There are no flags at this time.
'''

DOCSTRING_OFFLINE_READING = '''
offline_reading:
    Render submissions and comment threads to HTML.

    > timesearch offline_reading database.db <flags>

    flags:
    -s "t3_xxxxxx" | --specific "t3_xxxxxx":
        Given a submission ID, t3_xxxxxx, render only that submission.
        Otherwise render every submission in the database.
'''

DOCSTRING_REDMASH = '''
redmash:
    Dump submission information to a readable file in the `REDMASH_FOLDER`

    > timesearch redmash -r subredditname <flags>
    > timesearch redmash -u username <flags>

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to dump

    -u "test" | --username "test":
        The username database to dump

    --html:
        Write HTML files instead of plain text.

    -st 50 | --score_threshold 50:
        Only mash posts with at least this many points.
        Applies to ALL mashes!

    --all:
        Perform all of the mashes listed below.

    --date:
        Perform a mash sorted by date.

    --title:
        Perform a mash sorted by title.

    --score:
        Perform a mash sorted by score.

    --author:
        For subreddit databases only.
        Perform a mash sorted by author.

    --sub:
        For username databases only.
        Perform a mash sorted by subreddit.

    --flair:
        Perform a mash sorted by flair.

    examples:
        `timesearch redmash -r botwatch --date`
        does only the date file.

        `timesearch redmash -r botwatch --score --title`
        does both the score and title files.

        `timesearch redmash -r botwatch --score --score_threshold 50`
        only shows submissions with >= 50 points.

        `timesearch redmash -r botwatch --all`
        performs all of the different mashes.
'''

DOCSTRING_BREAKDOWN = '''
breakdown:
    Give the comment / submission counts for users in a subreddit, or
    the subreddits that a user posts to.

    Automatically dumps into a <database>_breakdown.json file
    in the same directory as the database.

    > timesearch breakdown -r subredditname
    > timesearch breakdown -u username

    flags:
    -r "test" | --subreddit "test":
        The subreddit database to break down.

    -u "test" | --username "test":
        The username database to break down.

    -p | --pretty
        If provided, make the json file indented and sorted.
'''

def indent(text, spaces=4):
    spaces = ' ' * spaces
    return '\n'.join(spaces + line if line.strip() != '' else line for line in text.split('\n'))

def _docstring_headerify(text):
    '''
    Return the brief description at the top of the text.
    User can get full text by looking at each specifically.
    '''
    return text.split('\n\n')[0]

DOCSTRING_MAP = {
    'timesearch': DOCSTRING_TIMESEARCH,
    'commentaugment': DOCSTRING_COMMENTAUGMENT,
    'offline_reading': DOCSTRING_OFFLINE_READING,
    'livestream': DOCSTRING_LIVESTREAM,
    'redmash': DOCSTRING_REDMASH,
    'breakdown': DOCSTRING_BREAKDOWN,
    'getstyles': DOCSTRING_GETSTYLES,
}

DOCSTRING = DOCSTRING.format(
    docheader_timesearch=indent(_docstring_headerify(DOCSTRING_TIMESEARCH)),
    docheader_commentaugment=indent(_docstring_headerify(DOCSTRING_COMMENTAUGMENT)),
    docheader_livestream=indent(_docstring_headerify(DOCSTRING_LIVESTREAM)),
    docheader_getstyles=indent(_docstring_headerify(DOCSTRING_GETSTYLES)),
    docheader_offline_reading=indent(_docstring_headerify(DOCSTRING_OFFLINE_READING)),
    docheader_redmash=indent(_docstring_headerify(DOCSTRING_REDMASH)),
    docheader_breakdown=indent(_docstring_headerify(DOCSTRING_BREAKDOWN)),
)

import argparse
import copy
import datetime
import json
import markdown  # If you're not interested in offline_reading, you may delete
import os
import praw
import requests
import sqlite3
import sys
import time
import traceback


''' USER CONFIGURATION '''

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

MAXIMUM_EXPANSION_MULTIPLIER = 2
# The maximum amount by which it can multiply the interval
# when not enough posts are found.

STYLE_FOLDER = 'styles/'
DATABASE_FOLDER = 'databases/'
HTML_FOLDER = 'html/'
REDMASH_FOLDER = 'redmash/'

DATABASE_PLAIN = '%s%s' % (DATABASE_FOLDER, '%s')
DATABASE_SUBREDDIT = '%s%s' % (DATABASE_FOLDER, '%s')
DATABASE_USER = '%s@%s' % (DATABASE_FOLDER, '%s')

REDMASH_FORMAT_TXT = '''
{timestamp}: [{title}]({shortlink}) - /u/{author} (+{score})
'''.replace('\n', '')
REDMASH_FORMAT_HTML = '''
{timestamp}: <a href=\"{shortlink}\">[{flairtext}] {title}</a> - <a href=\"{authorlink}\">{author}</a> (+{score})<br>
'''.replace('\n', '')

REDMASH_TIMESTAMP = '%Y %b %d'
#The time format.
# "%Y %b %d" = "2016 August 10"
# See http://strftime.org/

REDMASH_HTML_HEADER = '''
<html>
<head>
<meta charset="UTF-8">
<style>
    *
    {
        font-family: Consolas;
    }
</style>
</head>

<body>
'''
REDMASH_HTML_FOOTER = '''
</body>
</html>
'''

''' All done! '''


try:
    import bot
    USERAGENT = bot.aPT
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

# http://redd.it/3cm1p8
r = praw.Reddit(USERAGENT)

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
prompt_ca_num_thresh = '''
- Minimum num_comments a thread must have to be scanned
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



############      ########  
##  ####  ##    ####    ####
    ####        ####    ####
    ####        ####        
    ####          ######    
    ####              ####  
    ####        ####    ####
    ####        ####    ####
  ########        ########  
# Timesearch

def livestream(
        subreddit=None,
        username=None,
        verbose=False,
        as_a_generator=False,
        do_submissions=True,
        do_comments=True,
        limit=100,
        only_once=False,
        sleepy=30,
    ):
    '''
    Continuously get posts from this source
    and insert them into the database

    as_a_generator:
        return a generator where every iteration does a single livestream loop.
        This is good if you want to manage multiple livestreams yourself by
        calling `next` on each of them, instead of getting stuck in here.
    '''
    if bool(subreddit) == bool(username):
        raise Exception('Require either username / subreddit parameter, but not both')
    if bool(do_submissions) is bool(do_comments) is False:
        raise Exception('Require do_submissions and/or do_comments parameter')
    login()

    if subreddit:
        print('Getting subreddit %s' % subreddit)
        databasename = database_filename(subreddit=subreddit)
        stream_target = r.get_subreddit(subreddit)
        submissions = stream_target.get_new if do_submissions else None
        comments = stream_target.get_comments if do_comments else None
    else:
        print('Getting redditor %s' % username)
        databasename = database_filename(username=username)
        stream_target = r.get_redditor(username)
        submissions = stream_target.get_submitted if do_submissions else None
        comments = stream_target.get_comments if do_comments else None
    
    sql = sql_open(databasename)
    cur = sql.cursor()
    initialize_database(sql, cur)

    generator = _livestream_as_a_generator(
        sql,
        cur,
        submission_function=submissions,
        comment_function=comments,
        limit=limit,
        params={'show': 'all'},
        verbose=verbose,
    )
    if as_a_generator:
        return generator

    while True:
        try:
            step = next(generator)
            newtext = '%ds, %dc' % (step['new_submissions'], step['new_comments'])
            totalnew = step['new_submissions'] + step['new_comments']
            status = '{now} +{new}'.format(now=human(get_now()), new=newtext)
            print(status, end='', flush=True)
            if totalnew == 0 and verbose is False:
                # Since there were no news, allow the next line to overwrite status
                print('\r', end='')
            else:
                print()

            if verbose:
                print('Loop finished.')
            if only_once:
                break
            time.sleep(sleepy)

        except KeyboardInterrupt:
            print()
            sql.commit()
            sql.close()
            return

        except Exception as e:
            traceback.print_exc()
            time.sleep(5)

hangman = lambda: livestream(username='gallowboob', sleepy=60, submissions=True, comments=True)

def _livestream_as_a_generator(
        sql,
        cur,
        submission_function,
        comment_function,
        limit,
        params,
        verbose,
    ):
    while True:
        r.handler.clear_cache()
        items = _livestream_helper(
            submission_function=submission_function,
            comment_function=comment_function,
            limit=limit,
            params={'show': 'all'},
            verbose=verbose,
        )
        newitems = smartinsert(sql, cur, items, delaysave=True)
        yield newitems
        

def _livestream_helper(
        submission_function=None,
        comment_function=None,
        verbose=False,
        *args,
        **kwargs
    ):
    '''
    Given a submission-retrieving function and/or a comment-retrieving function,
    collect submissions and comments in a list together and return that.

    args and kwargs go into the collecting functions.
    '''
    if bool(submission_function) is bool(comment_function) is False:
        raise Exception('Require submissions and/or comments parameter')
    results = []

    if submission_function:
        if verbose: print('Getting submissions', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        submission_batch = submission_function(*args, **this_kwargs)
        results.extend(submission_batch)
    if comment_function:
        if verbose: print('Getting comments', args, kwargs)
        this_kwargs = copy.deepcopy(kwargs)
        comment_batch = comment_function(*args, **this_kwargs)
        results.extend(comment_batch)
    if verbose:
        print('Collected. Saving...')
    return results

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
    if bool(subreddit) == bool(username):
        raise Exception('Enter subreddit or username but not both')
    login()

    if subreddit:
        databasename = database_filename(subreddit=subreddit)
    else:
        # When searching, we'll take the user's submissions from anywhere.
        subreddit = 'all'
        databasename = database_filename(username=username)

    sql = sql_open(databasename)
    cur = sql.cursor()
    initialize_database(sql, cur)

    offset = -time.timezone

    if lower == 'update':
        # Start from the latest submission
        cur.execute('SELECT * FROM submissions ORDER BY idint DESC LIMIT 1')
        f = cur.fetchone()
        if f:
            lower = f[SQL_SUBMISSION['created']]
            print(f[SQL_SUBMISSION['idstr']], human(lower), lower)
        else:
            lower = None

    if subreddit:
        if isinstance(subreddit, praw.objects.Subreddit):
            creation = subreddit.created_utc
        else:
            subreddits = subreddit.split('+')
            subreddits = [r.get_subreddit(sr) for sr in subreddits]
            creation = min([sr.created_utc for sr in subreddits])
    else:
        if not isinstance(username, praw.objects.Redditor):
            user = r.get_redditor(username)
        creation = user.created_utc

    if lower is None or lower < creation:
        lower = creation

    maxupper = upper
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
                if username:
                    query = '(and author:"%s" (and timestamp:%d..%d))' % (
                        username, lower, upper)
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

def timesearch_prompt():
    while True:
        username = False
        maxupper = None
        interval = 86400
        print(prompt_ts_subreddit, end='')
        sub = input()
        if sub == '':
            print(prompt_ts_username, end='')
            username = input()
            sub = 'all'
        if username:
            p = database_filename(username=username)
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
        get_all_posts(sub, lower, maxupper, interval, username)
        print('\nDone. Press Enter to close window or type "restart"')
        if input().lower() != 'restart':
            break


    ########        ####    
  ####    ####    ########  
####      ####  ####    ####
####            ####    ####
####            ####    ####
####            ############
####      ####  ####    ####
  ####    ####  ####    ####
    ########    ####    ####
# Commentaugment

def commentaugment(
        databasename,
        limit=0,
        num_thresh=0,
        specific_submission=None,
        threshold=0,
        verbose=0,
    ):
    '''
    Take the IDs of collected submissions, and gather comments from those threads.
    Please see the global DOCSTRING_COMMENTAUGMENT variable.
    '''
    databasename = database_filename(subreddit=databasename)
    assert_file_exists(databasename)

    login()
    if specific_submission is not None:
        if not specific_submission.startswith('t3_'):
            specific_submission = 't3_' + specific_submission
        specific_submission_obj = r.get_submission(
            submission_id=specific_submission[3:],
            comment_limit=90000,
        )

    #print(databasename)
    sql = sql_open(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()
    initialize_database(sql, cur)

    if limit == 0:
        limit = None

    if specific_submission is None:
        cur.execute('''
            SELECT idstr FROM submissions
            WHERE augmented_at IS NULL
            AND num_comments >= ?
            ORDER BY num_comments DESC''',
            [num_thresh])
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
    r.handler.clear_cache()
    get_submission = nofailrequest(r.get_submission)
    while True:
        id_batch = fetchall[:100]
        fetchall = fetchall[100:]
        id_batch = list(filter(None, id_batch))
        if len(id_batch) == 0:
            return

        for submission in id_batch:
            submission = get_submission(submission_id=submission.split('_')[-1], comment_limit=90000)
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
        print(prompt_ca_num_thresh, end='')
        num_thresh = input()
        num_thresh = fixint(num_thresh)

        specific_submission = None
    else:
        num_thresh = 0
        skips = 0

    print(prompt_ca_verbosity, end='')
    verbose = input()
    verbose = fixint(verbose)
    verbose = (verbose is 1)

    commentaugment(databasename, limit, threshold, num_thresh, verbose, specific_submission)
    print('Done')

def get_comments_for_thread(submission, limit, threshold, verbose):
    comments = nofailrequest(lambda x: x.comments)(submission)
    comments = praw.helpers.flatten_tree(comments)
    comments = manually_replace_comments(comments, limit, threshold, verbose)
    return comments

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

    while True:
        try:
            if limit is not None and limit <= 0:
                break
            if len(morecomments) == 0:
                break
            morecomments.sort(key=lambda x: x.count)
            mc = morecomments.pop()
            #print('more')
            additional = nofailrequest(mc.comments)()
            #print('moremore')
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
            raise
        except:
            traceback.print_exc()
    return comments


    ######      ############  
  ####  ####      ####    ####
####      ####    ####    ####
####      ####    ####    ####
####      ####    ##########  
####      ####    ####  ####  
####      ####    ####    ####
  ####  ####      ####    ####
    ######      ######    ####
# Offline Reading

class DBEntry:
    def __init__(self, fetch):
        if fetch[1].startswith('t3_'):
            columns = SQL_SUBMISSION_COLUMNS
            self.object_type = 'submission'
        else:
            columns = SQL_COMMENT_COLUMNS
            self.object_type = 'comment'

        for (index, attribute) in enumerate(columns):
            setattr(self, attribute, fetch[index])

    def __repr__(self):
        return 'DBEntry(\'%s\')' % self.id


class TreeNode:
    def __init__(self, identifier, data, parent=None):
        assert isinstance(identifier, str)
        assert '\\' not in identifier
        self.identifier = identifier
        self.data = data
        self.parent = parent
        self.children = {}

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return 'TreeNode %s' % self.abspath()

    def abspath(self):
        node = self
        nodes = [node]
        while node.parent is not None:
            node = node.parent
            nodes.append(node)
        nodes.reverse()
        nodes = [node.identifier for node in nodes]
        return '\\'.join(nodes)

    def add_child(self, other_node, overwrite_parent=False):
        self.check_child_availability(other_node.identifier)
        if other_node.parent is not None and not overwrite_parent:
            raise ValueError('That node already has a parent. Try `overwrite_parent=True`')

        other_node.parent = self
        self.children[other_node.identifier] = other_node
        return other_node

    def check_child_availability(self, identifier):
        if ':' in identifier:
            raise Exception('Only roots may have a colon')
        if identifier in self.children:
            raise Exception('Node %s already has child %s' % (self.identifier, identifier))

    def detach(self):
        del self.parent.children[self.identifier]
        self.parent = None

    def listnodes(self, customsort=None):
        items = list(self.children.items())
        if customsort is None:
            items.sort(key=lambda x: x[0].lower())
        else:
            items.sort(key=customsort)
        return [item[1] for item in items]

    def merge_other(self, othertree, otherroot=None):
        newroot = None
        if ':' in othertree.identifier:
            if otherroot is None:
                raise Exception('Must specify a new name for the other tree\'s root')
            else:
                newroot = otherroot
        else:
            newroot = othertree.identifier
        othertree.identifier = newroot
        othertree.parent = self
        self.check_child_availability(newroot)
        self.children[newroot] = othertree

    def printtree(self, customsort=None):
        for node in self.walk(customsort):
            print(node.abspath())

    def walk(self, customsort=None):
        yield self
        for child in self.listnodes(customsort=customsort):
            #print(child)
            #print(child.listnodes())
            yield from child.walk(customsort=customsort)

def html_format_comment(comment):
    text = '''
    <div class="comment"
        id="{id}" 
        style="
        padding-left: 20px;
        margin-top: 4px;
        margin-right: 4px;
        margin-bottom: 4px;
        border: 2px #000 solid;
    ">
        <p class="userinfo">
            {usernamelink}
            <span class="score"> | {score} points</span>
            <span class="timestamp"> | {human}</span>
        </p>

        <p>{body}</p>

        <p class="toolbar">
            {permalink}
        </p>
    {children}
    </div>
    '''.format(
        id = comment.idstr,
        body = sanitize_braces(render_markdown(comment.body)),
        usernamelink = html_helper_userlink(comment),
        score = comment.score,
        human = human(comment.created),
        permalink = html_helper_permalink(comment),
        children = '{children}',
    )
    return text

def html_format_submission(submission):
    text = '''
    <div class="submission"
        id="{id}" 
        style="
        border: 4px #00f solid;
        padding-left: 20px;
    ">

        <p class="userinfo">
            {usernamelink}
            <span class="score"> | {score} points</span>
            <span class="timestamp"> | {human}</span>
        </p>

        <strong>{title}</strong>
        <p>{url_or_text}</p>

        <p class="toolbar">
            {permalink}
        </p>
    </div>
    {children}
    '''.format(
        id = submission.idstr,
        title = sanitize_braces(submission.title),
        usernamelink = html_helper_userlink(submission),
        score = submission.score,
        human = human(submission.created),
        permalink = html_helper_permalink(submission),
        url_or_text = html_helper_urlortext(submission),
        children = '{children}',
    )
    return text

def html_from_database(databasename, specific_submission=None):
    '''
    Given a timesearch database filename, produce .html files for each
    of the submissions it contains (or one particular submission fullname)
    '''
    submission_trees = trees_from_database(databasename, specific_submission)
    for submission_tree in submission_trees:
        page = html_from_tree(submission_tree, sort=lambda x: x.data.score * -1)
        if HTML_FOLDER != '':
            os.makedirs(HTML_FOLDER, exist_ok=True)
        html_basename = '%s.html' % submission_tree.identifier
        html_filename = os.path.join(HTML_FOLDER, html_basename)
        html_handle = open(html_filename, 'w', encoding='utf-8')
        html_handle.write('<html><body><meta charset="UTF-8">')
        html_handle.write(page)
        html_handle.write('</body></html>')
        html_handle.close()
        print('Wrote', html_filename)

def html_from_tree(tree, sort=None):
    '''
    Given a tree *whose root is the submission*, return
    HTML-formatted text representing each submission's comment page.
    '''
    if tree.data.object_type == 'submission':
        page = html_format_submission(tree.data)
    elif tree.data.object_type == 'comment':
        page = html_format_comment(tree.data)
    children = tree.listnodes()
    if sort is not None:
        children.sort(key=sort)
    children = [html_from_tree(child, sort) for child in children]
    if len(children) == 0:
        children = ''
    else:
        children = '\n\n'.join(children)
    try:
        page = page.format(children=children)
    except IndexError:
        print(page)
        raise
    return page

def html_helper_permalink(item):
    link = 'https://www.reddit.com/r/%s/comments/' % item.subreddit
    if item.object_type == 'submission':
        link += item.idstr[3:]
    elif item.object_type == 'comment':
        link += '%s/_/%s' % (item.submission[3:], item.idstr[3:])
    link = '<a href="%s">permalink</a>' % link
    return link

def html_helper_urlortext(submission):
    if submission.url:
        text = '<a href="{url}">{url}</a>'.format(url=submission.url)
    elif submission.selftext:
        text = render_markdown(submission.selftext)
    else:
        text = ''
    text = sanitize_braces(text)
    return text

def html_helper_userlink(item):
    name = item.author
    if name.lower() == '[deleted]':
        return '[deleted]'
    link = 'https://www.reddit.com/u/{name}'
    link = '<a href="%s">{name}</a>' % link
    link = link.format(name=name)
    return link

def render_markdown(text):
    text = markdown.markdown(text, output_format='html5')
    return text

def sanitize_braces(text):
    text = text.replace('{', '{{')
    text = text.replace('}', '}}')
    return text

def trees_from_database(databasename, specific_submission=None):
    '''
    Given a timesearch database filename, take all of the submission
    ids, take all of the comments for each submission id, and run them
    through `tree_from_submission`.

    Yield each submission's tree as it is generated.
    '''
    databasename = database_filename(plain=databasename)
    assert_file_exists(databasename)

    sql = sql_open(databasename)
    cur1 = sql.cursor()
    cur2 = sql.cursor()

    if specific_submission is None:
        cur1.execute('SELECT idstr FROM submissions ORDER BY created ASC')
        submission_ids = fetchgenerator(cur1)
    else:
        specific_submission = 't3_' + specific_submission.split('_')[-1]
        # Insert as a tuple to behave like the sql fetch results
        submission_ids = [(specific_submission, None)]

    found_some_posts = False
    for submission_id in submission_ids:
        # Extract sql fetch
        submission_id = submission_id[0]
        found_some_posts = True
        cur2.execute('SELECT * FROM submissions WHERE idstr == ?', [submission_id])
        submission = cur2.fetchone()
        cur2.execute('SELECT * FROM comments WHERE submission == ?', [submission_id])
        fetched_comments = cur2.fetchall()
        submission_tree = tree_from_submission(submission, fetched_comments)
        yield submission_tree

    if not found_some_posts:
        raise Exception('Found no submissions!')

def tree_from_submission(submission, commentpool):
    '''
    Given the sqlite data for a submission and all of its comments,
    return a tree with the submission id as the root
    '''
    submission = DBEntry(submission)
    commentpool = [DBEntry(c) for c in commentpool]
    commentpool.sort(key=lambda x: x.created)
    
    print('Building tree for %s (%d comments)' % (submission.idstr, len(commentpool)))
    # Thanks Martin Schmidt for the algorithm
    # http://stackoverflow.com/a/29942118/5430534
    tree = TreeNode(identifier=submission.idstr, data=submission)
    node_map = {}

    for comment in commentpool:
        # Ensure this comment is in a node of its own
        this_node = node_map.get(comment.idstr, None)
        if this_node:
            # This ID was detected as a parent of a previous iteration
            # Now we're actually filling it in.
            this_node.data = comment
        else:
            this_node = TreeNode(comment.idstr, comment)
            node_map[comment.idstr] = this_node

        # Attach this node to the parent.
        if comment.parent.startswith('t3_'):
            tree.add_child(this_node)
        else:
            parent_node = node_map.get(comment.parent, None)
            if not parent_node:
                parent_node = TreeNode(comment.parent, data=None)
                node_map[comment.parent] = parent_node
            parent_node.add_child(this_node)
            this_node.parent = parent_node
    return tree


############    ####      #### 
  ####    ####  ######  ###### 
  ####    ####  ############## 
  ####    ####  ############## 
  ##########    ####  ##  #### 
  ####  ####    ####      #### 
  ####    ####  ####      #### 
  ####    ####  ####      #### 
######    ####  ####      #### 
# Redmash

def redmash(
        subreddit=None,
        username=None,
        do_all=False,
        do_date=False,
        do_title=False,
        do_score=False,
        do_author=False,
        do_subreddit=False,
        do_flair=False,
        html=False,
        score_threshold=0,
    ):
    databasename = database_filename(subreddit=subreddit, username=username)
    assert_file_exists(databasename)

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    kwargs = {'html': html, 'score_threshold': score_threshold}
    wrote = None

    if do_all or do_date:
        print('Writing time file')
        wrote = redmash_worker(databasename, suffix='_date', cur=cur, orderby='created ASC', **kwargs)
        print('Wrote', wrote)
    
    if do_all or do_title:
        print('Writing title file')
        wrote = redmash_worker(databasename, suffix='_title', cur=cur, orderby='title ASC', **kwargs)
        print('Wrote', wrote)

    if do_all or do_score:
        print('Writing score file')
        wrote = redmash_worker(databasename, suffix='_score', cur=cur, orderby='score DESC', **kwargs)
        print('Wrote', wrote)
    
    if not username and (do_all or do_author):
        print('Writing author file')
        wrote = redmash_worker(databasename, suffix='_author', cur=cur, orderby='author ASC', **kwargs)
        print('Wrote', wrote)

    if username and (do_all or do_subreddit):
        print('Writing subreddit file')
        wrote = redmash_worker(databasename, suffix='_subreddit', cur=cur, orderby='subreddit ASC', **kwargs)
        print('Wrote', wrote)
    
    if do_all or do_flair:
        print('Writing flair file')
        # Items with flair come before items without. Each group is sorted by time separately.
        orderby = 'flair_text IS NULL ASC, created ASC'
        wrote = redmash_worker(databasename, suffix='_flair', cur=cur, orderby=orderby, **kwargs)
        print('Wrote', wrote)

    if not wrote:
        raise Exception('No sorts selected! Read the docstring')
    print('Done.')

def redmash_worker(
        databasename,
        suffix,
        cur,
        orderby,
        score_threshold=0,
        html=False,
    ):
    template = 'SELECT * FROM submissions WHERE score >= %d ORDER BY {order}' % score_threshold
    statement = template.format(order=orderby)
    cur.execute(statement)

    if REDMASH_FOLDER != '':
        os.makedirs(REDMASH_FOLDER, exist_ok=True)

    mash_basename = os.path.basename(databasename)
    mash_fullname = os.path.join(REDMASH_FOLDER, mash_basename)

    # subreddit.db -> subreddit_date.html
    extension = '.html' if html else '.txt'
    extension = suffix + extension
    mash_fullname = mash_fullname.replace('.db', extension)

    mash_handle = open(mash_fullname, 'w', encoding='UTF-8')
    if html:
        mash_handle.write(REDMASH_HTML_HEADER)
        line_format = REDMASH_FORMAT_HTML
    else:
        line_format = REDMASH_FORMAT_TXT

    do_timestamp = '{timestamp}' in line_format

    for item in fetchgenerator(cur):
        if do_timestamp:
            timestamp = int(item[SQL_SUBMISSION['created']])
            timestamp = datetime.datetime.utcfromtimestamp(timestamp)
            timestamp = timestamp.strftime(REDMASH_TIMESTAMP)
        else:
            timestamp = ''

        short_link = 'https://redd.it/%s' % item[SQL_SUBMISSION['idstr']][3:]
        author = item[SQL_SUBMISSION['author']]
        if author.lower() == '[deleted]':
            author_link = '#'
        else:
            author_link = 'https://reddit.com/u/%s' % author
        line = line_format.format(
            author=author,
            authorlink=author_link,
            flaircss=item[SQL_SUBMISSION['flair_css_class']] or '',
            flairtext=item[SQL_SUBMISSION['flair_text']] or '',
            id=item[SQL_SUBMISSION['idstr']],
            numcomments=item[SQL_SUBMISSION['num_comments']],
            score=item[SQL_SUBMISSION['score']],
            shortlink=short_link,
            subreddit=item[SQL_SUBMISSION['subreddit']],
            timestamp=timestamp,
            title=item[SQL_SUBMISSION['title']].replace('\n', ' '),
            url=item[SQL_SUBMISSION['url']] or short_link,
        )
        line += '\n'
        mash_handle.write(line)

    if html:
        mash_handle.write(REDMASH_HTML_FOOTER)
    mash_handle.close()
    return mash_fullname


############     ##########
  ####    ####     ####  ####
  ####    ####     ####    ####
  ####    ####     ####    ####
  ##########       ####    ####
  ####    ####     ####    ####
  ####    ####     ####    ####
  ####    ####     ####  ####
############     ##########
# Breakdown

def breakdown_database(databasename, breakdown_type):
    '''
    Given a database, return a json dict breaking down the submission / comment count for
    users (if a subreddit database) or subreddits (if a user database).

    breakdown_type:
        String, either 'subreddit' or 'user' to indicate what kind of database this is.
    '''
    databasename = database_filename(plain=databasename)
    assert_file_exists(databasename)

    sql = sqlite3.connect(databasename)
    submission_cur = sql.cursor()
    comment_cur = sql.cursor()

    breakdown_results = {}
    def _ingest(generator, subkey):
        for name in generator:
            breakdown_results.setdefault(name, {})
            breakdown_results[name].setdefault(subkey, 0)
            breakdown_results[name][subkey] += 1

    submission_cur.execute('SELECT * FROM submissions')
    comment_cur.execute('SELECT * FROM comments')
    if breakdown_type == 'subreddit':
        submissions = (submission[SQL_SUBMISSION['author']] for submission in fetchgenerator(submission_cur))
        comments = (comment[SQL_COMMENT['author']] for comment in fetchgenerator(comment_cur))
    if breakdown_type == 'user':
        submissions = (submission[SQL_SUBMISSION['subreddit']] for submission in fetchgenerator(submission_cur))
        comments = (comment[SQL_COMMENT['subreddit']] for comment in fetchgenerator(comment_cur))
    _ingest(submissions, 'submissions')
    _ingest(comments, 'comments')
    for name in breakdown_results:
        breakdown_results[name].setdefault('submissions', 0)
        breakdown_results[name].setdefault('comments', 0)

    return breakdown_results


  ########                                  ########                                 
####    ####      ##                            ####                                 
####    ####    ####                            ####                                 
####          ############    ####    ####      ####        ########      ########   
  ######        ####          ####    ####      ####      ####    ####  ####    #### 
      ####      ####          ####    ####      ####      ############    ####       
####    ####    ####          ####    ####      ####      ####                ####   
####    ####    ####  ####      ########        ####      ####    ####  ####    #### 
  ########        ######            ####    ############    ########      ########   
                                  ####                                               
                            ########                                                 
# Styles

def getstyles(subreddit):
    #login()
    print('Getting styles for /r/%s' % subreddit)
    download_directory = os.path.join(STYLE_FOLDER, subreddit)
    subreddit = r.get_subreddit(subreddit)

    # To perform the lazy load
    subreddit.id
    styles = subreddit.get_stylesheet()

    # Only makedirs after the potential 404
    os.makedirs(download_directory, exist_ok=True)

    sidebar_filename = os.path.join(download_directory, 'sidebar.md')
    print('Downloading %s' % sidebar_filename)
    with open(sidebar_filename, 'w') as sidebar:
        sidebar.write(subreddit.description)

    stylesheet_filename = os.path.join(download_directory, 'stylesheet.css')
    print('Downloading %s' % stylesheet_filename)
    with open(stylesheet_filename, 'w') as stylesheet:
        stylesheet.write(styles['stylesheet'])

    for image in styles['images']:
        filename = os.path.join(download_directory, image['name'])
        filename += '.' + image['url'].split('.')[-1]
        print('Downloading %s' % filename)
        with open(filename, 'wb') as image_file:
            response = requests.get(image['url'])
            image_file.write(response.content)


    ########                                                                              ########    
  ####    ####                                                                                ####    
####      ####                                                                                ####    
####              ########    ##########      ########    ######  ####      ########          ####    
####            ####    ####  ####    ####  ####    ####    ####  ######          ####        ####    
####    ######  ############  ####    ####  ############    ######  ####    ##########        ####    
####      ####  ####          ####    ####  ####            ####          ####    ####        ####    
  ####    ####  ####    ####  ####    ####  ####    ####    ####          ####    ####        ####    
    ##########    ########    ####    ####    ########    ########          ######  ####  ############
# General

def assert_file_exists(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

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

def binding_filler(column_names, values, require_all=True):
    '''
    Manually aligning question marks and bindings is annoying.
    Given the table's column names and a dictionary of {column: value},
    return the question marks and the list of bindings in the right order.
    '''
    values = values.copy()
    for column in column_names:
        if column in values:
            continue
        if require_all:
            raise ValueError('Missing column "%s"' % column)
        else:
            values.setdefault(column, None)
    qmarks = '?' * len(column_names)
    qmarks = ', '.join(qmarks)
    bindings = [values[column] for column in column_names]
    return (qmarks, bindings)

def database_filename(subreddit=None, username=None, plain=None):
    '''
    Given a subreddit name or username, return the appropriate database filename.
    '''

    args = [subreddit, username, plain]
    if args.count(None) != len(args)-1:
        raise Exception('Incorrect number of arguments. One and only one please.')

    text = subreddit or username or plain
    text = text.replace('/', os.sep)
    text = text.replace('\\', os.sep)

    if os.sep in text:
        # If they've given us a full path, don't mess
        # with it
        return text

    if not text.endswith('.db'):
        text += '.db'

    if plain:
        full_path = DATABASE_PLAIN % text
    elif subreddit:
        full_path = DATABASE_SUBREDDIT % text
    else:
        full_path = DATABASE_USER % text

    basename = os.path.basename(full_path)
    if os.path.exists(basename):
        # Prioritize existing local files of the same name before creating
        # the deeper, proper one.
        return basename

    return full_path

def fetchgenerator(cursor):
    while True:
        item = cursor.fetchone()
        if item is None:
            break
        yield item

def fixint(i):
    if i == '':
        return 0
    i = int(i)
    if i < 0:
        return 0
    return i

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
        augmented_count INT)'''
    )
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
        textlen INT)'''
    )

    cur.execute('CREATE INDEX IF NOT EXISTS submission_index ON submissions(idstr)')
    cur.execute('CREATE INDEX IF NOT EXISTS comment_index ON comments(idstr)')

def listget(li, index, fallback=None):
    try:
        return li[index]
    except IndexError:
        return fallback

def login():
    if r.access_token is None:
        print('Logging in.')
        r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
        r.refresh_access_information(APP_REFRESH)
        r.config.api_request_delay = 1

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
            except KeyboardInterrupt:
                raise
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
    new_submissions = 0
    new_comments = 0
    for item in results:
        if item.author is None:
            author = '[DELETED]'
        else:
            author = item.author.name

        if isinstance(item, praw.objects.Submission):
            cur.execute('SELECT * FROM submissions WHERE idstr == ?', [item.fullname])
            existing_entry = cur.fetchone()
            if not existing_entry:
                new_submissions += 1

                if item.is_self:
                    # Selfpost's URL leads back to itself, so just ignore it.
                    url = None
                else:
                    url = item.url

                postdata = {}
                postdata['idint'] = b36(item.id)
                postdata['idstr'] = item.fullname
                postdata['created'] = item.created_utc
                postdata['self'] = item.is_self
                postdata['nsfw'] = item.over_18
                postdata['author'] = author
                postdata['title'] = item.title
                postdata['url'] = url
                postdata['selftext'] = item.selftext
                postdata['score'] = item.score
                postdata['subreddit'] = item.subreddit.display_name
                postdata['distinguish'] = item.distinguished
                postdata['textlen'] = len(item.selftext)
                postdata['num_comments'] = item.num_comments
                postdata['flair_text'] = item.link_flair_text
                postdata['flair_css_class'] = item.link_flair_css_class
                postdata['augmented_at'] = None
                postdata['augmented_count'] = None
                (qmarks, bindings) = binding_filler(SQL_SUBMISSION_COLUMNS, postdata, require_all=True)
                query = 'INSERT INTO submissions VALUES(%s)' % qmarks
                cur.execute(query, bindings)

            else:
                if item.author is None:
                    # This post is deleted, therefore its text probably says [deleted] or [removed].
                    # Discard that, and keep the data we already had here.
                    selftext = existing_entry[SQL_SUBMISSION['selftext']]
                else:
                    selftext = item.selftext

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
                [item.over_18, item.score, selftext, item.distinguished, item.num_comments,
                item.link_flair_text, item.link_flair_css_class, item.fullname])

        if isinstance(item, praw.objects.Comment):
            cur.execute('SELECT * FROM comments WHERE idstr == ?', [item.fullname])
            existing_entry = cur.fetchone()
            if not existing_entry:
                new_comments += 1

                postdata = {}
                postdata['idint'] = b36(item.id)
                postdata['idstr'] = item.fullname
                postdata['created'] = item.created_utc
                postdata['author'] = author
                postdata['parent'] = item.parent_id
                postdata['submission'] = item.link_id
                postdata['body'] = item.body
                postdata['score'] = item.score
                postdata['subreddit'] = item.subreddit.display_name
                postdata['distinguish'] = item.distinguished
                postdata['textlen'] = len(item.body)
                (qmarks, bindings) = binding_filler(SQL_COMMENT_COLUMNS, postdata, require_all=True)
                query = 'INSERT INTO comments VALUES(%s)' % qmarks
                cur.execute(query, bindings)

            else:
                greasy = 'has been overwritten'
                if item.author is None or greasy in item.body:
                    body = existing_entry[SQL_COMMENT['body']]
                else:
                    body = item.body

                cur.execute('''
                    UPDATE comments SET
                    score = coalesce(?, score),
                    body = coalesce(?, body),
                    distinguish = coalesce(?, distinguish)
                    WHERE idstr == ?
                ''',
                [item.score, body, item.distinguished, item.fullname])

        if not delaysave and not nosave:
            sql.commit()
    if delaysave and not nosave:
        sql.commit()
    return {'new_submissions': new_submissions, 'new_comments': new_comments}

def sql_open(databasename):
    '''
    Open the sql connection, creating the folder if necessary.
    '''
    dirname = os.path.dirname(databasename)
    if dirname != '':
        os.makedirs(dirname, exist_ok=True)
    return sqlite3.connect(databasename)

def update_scores(databasename, submissions=True, comments=False):
    '''
    Get all submissions or comments from the database, and update
    them with the current scores.
    '''
    login()
    import itertools

    databasename = database_filename(subreddit=databasename)
    sql = sql_open(databasename)
    cur_submission = sql.cursor()
    cur_comment = sql.cursor()
    cur_insert = sql.cursor()

    generators = []
    total_items = 0
    if submissions:
        cur_submission.execute('SELECT COUNT(idstr) FROM submissions')
        submission_count = cur_submission.fetchone()[0]
        total_items += submission_count
        print('Updating %d submissions' % submission_count)

        cur_submission.execute('SELECT idstr FROM submissions')
        generators.append(fetchgenerator(cur_submission))

    if comments:
        cur_comment.execute('SELECT COUNT(idstr) FROM comments')
        comment_count = cur_comment.fetchone()[0]
        total_items += comment_count
        print('Updating %d comments' % comment_count)

        cur_comment.execute('SELECT idstr FROM comments')
        generators.append(fetchgenerator(cur_comment))

    items_updated = [0]
    generators = itertools.chain(*generators)

    def do_chunk(chunk):
        if len(chunk) == 0:
            return
        info = r.get_info(thing_id=chunk)
        smartinsert(sql, cur_insert, info, delaysave=True)
        items_updated[0] += len(chunk)
        print('Updated %d/%d' % (items_updated[0], total_items))

    chunk_cache = []
    for item in generators:
        chunk_cache.append(item[0])
        if len(chunk_cache) == 100:
            do_chunk(chunk_cache)
            chunk_cache = []
    else:
        do_chunk(chunk_cache)


    ####                                                  
  ########                                                
####    ####                                              
####    ####  ######  ####      ######  ####    ########  
####    ####    ####  ######  ####    ####    ####    ####
############    ######  ####  ####    ####      ####      
####    ####    ####          ####    ####          ####  
####    ####    ####            ##########    ####    ####
####    ####  ########                ####      ########  
                              ####    ####                
                                ########                  

int_none = lambda x: int(x) if x is not None else x

def breakdown_argparse(args):
    if args.subreddit is args.username is None:
        raise ValueError('-r subreddit OR -u username must be provided')
    if args.subreddit:
        databasename = database_filename(subreddit=args.subreddit)
        breakdown_type = 'subreddit'
    else:
        databasename = database_filename(username=args.username)
        breakdown_type = 'user'

    breakdown_results = breakdown_database(
        databasename=databasename,
        breakdown_type=breakdown_type,
    )

    breakdown_filename = os.path.splitext(databasename)[0]
    breakdown_filename = '%s_breakdown.json' % breakdown_filename
    breakdown_file = open(breakdown_filename, 'w')
    with breakdown_file:
        if args.pretty:
            dump = json.dumps(breakdown_results, sort_keys=True, indent=4)
        else:
            dump = json.dumps(breakdown_results)
        breakdown_file.write(dump)

    return breakdown_results

def commentaugment_argparse(args):
    return commentaugment(
        databasename=args.databasename,
        limit=int_none(args.limit),
        threshold=int_none(args.threshold),
        num_thresh=int_none(args.num_thresh),
        verbose=args.verbose,
        specific_submission=args.specific_submission,
    )

def getstyles_argparse(args):
    return getstyles(args.subreddit)

def livestream_argparse(args):
    if args.submissions is args.comments is False:
        args.submissions = True
        args.comments = True
    if args.limit is None:
        limit = 100
    else:
        limit = int(args.limit)

    if args.submissions is False and args.comments is False:
        args.submissions = True
        args.comments = True

    return livestream(
        subreddit=args.subreddit,
        username=args.username,
        do_comments=args.comments,
        do_submissions=args.submissions,
        limit=limit,
        verbose=args.verbose,
        only_once=args.once,
        sleepy=int_none(args.sleepy),
    )

def offline_reading_argparse(args):
    return html_from_database(
        databasename=args.databasename,
        specific_submission=args.specific_submission,
    )

def redmash_argparse(args):
    if args.subreddit is args.username is None:
        raise ValueError('-r subreddit OR -u username must be provided')

    return redmash(
        subreddit=args.subreddit,
        username=args.username,
        do_all=args.do_all,
        do_date=args.do_date,
        do_title=args.do_title,
        do_score=args.do_score,
        do_author=args.do_author,
        do_subreddit=args.do_subreddit,
        do_flair=args.do_flair,
        html=args.html,
        score_threshold=int_none(args.score_threshold),
    )

def timesearch_argparse(args):
    if args.lower == 'update':
        lower = 'update'
    else:
        lower = int_none(args.lower)

    return timesearch(
        subreddit=args.subreddit,
        username=args.username,
        lower=lower,
        upper=int_none(args.upper),
        interval=int_none(args.interval),
    )


def main():
    helpstrings = {'', 'help', '-h', '--help'}
    arg_1 = listget(sys.argv, 1, '').lower()

    if arg_1 not in DOCSTRING_MAP:
        print(DOCSTRING)
        raise SystemExit(1)

    arg_2 = listget(sys.argv, 2, '').lower()
    if arg_2 in helpstrings:
        print(DOCSTRING_MAP[arg_1])
        raise SystemExit(1)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_timesearch = subparsers.add_parser('timesearch')
    p_timesearch.add_argument('-r', '--subreddit', dest='subreddit', default=None)
    p_timesearch.add_argument('-u', '--user', dest='username', default=None)
    p_timesearch.add_argument('-l', '--lower', dest='lower', default='update')
    p_timesearch.add_argument('-up', '--uppper', dest='upper', default=None)
    p_timesearch.add_argument('-i', '--interval', dest='interval', default=86400)
    p_timesearch.set_defaults(func=timesearch_argparse)

    p_commentaugment = subparsers.add_parser('commentaugment')
    p_commentaugment.add_argument('databasename')
    p_commentaugment.add_argument('-l', '--limit', dest='limit', default=None)
    p_commentaugment.add_argument('-t', '--threshold', dest='threshold', default=0)
    p_commentaugment.add_argument('-n', '--num_thresh', dest='num_thresh', default=1)
    p_commentaugment.add_argument('-s', '--specific', dest='specific_submission', default=None)
    p_commentaugment.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    p_commentaugment.set_defaults(func=commentaugment_argparse)

    p_livestream = subparsers.add_parser('livestream')
    p_livestream.add_argument('-r', '--subreddit', dest='subreddit', default=None)
    p_livestream.add_argument('-u', '--user', dest='username', default=None)
    p_livestream.add_argument('-s', '--submissions', dest='submissions', action='store_true')
    p_livestream.add_argument('-c', '--comments', dest='comments', action='store_true')
    p_livestream.add_argument('-1', '--once', dest='once', action='store_true')
    p_livestream.add_argument('-l', '--limit', dest='limit', default=None)
    p_livestream.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    p_livestream.add_argument('-w', '--wait', dest='sleepy', default=30)
    p_livestream.set_defaults(func=livestream_argparse)

    p_getstyles = subparsers.add_parser('getstyles')
    p_getstyles.add_argument('subreddit')
    p_getstyles.set_defaults(func=getstyles_argparse)

    p_offline_reading = subparsers.add_parser('offline_reading')
    p_offline_reading.add_argument('databasename')
    p_offline_reading.add_argument('-s', '--specific', dest='specific_submission', default=None)
    p_offline_reading.set_defaults(func=offline_reading_argparse)

    p_redmash = subparsers.add_parser('redmash')
    p_redmash.add_argument('-r', '--subreddit', dest='subreddit', default=None)
    p_redmash.add_argument('-u', '--user', dest='username', default=None)
    p_redmash.add_argument('--all', dest='do_all', action='store_true')
    p_redmash.add_argument('--date', dest='do_date', action='store_true')
    p_redmash.add_argument('--title', dest='do_title', action='store_true')
    p_redmash.add_argument('--score', dest='do_score', action='store_true')
    p_redmash.add_argument('--author', dest='do_author', action='store_true')
    p_redmash.add_argument('--sub', dest='do_subreddit', action='store_true')
    p_redmash.add_argument('--flair', dest='do_flair', action='store_true')
    p_redmash.add_argument('--html', dest='html', action='store_true')
    p_redmash.add_argument('-st', '--score_threshold', dest='score_threshold', default=0)
    p_redmash.set_defaults(func=redmash_argparse)

    p_breakdown = subparsers.add_parser('breakdown')
    p_breakdown.add_argument('-r', '--subreddit', dest='subreddit', default=None)
    p_breakdown.add_argument('-u', '--user', dest='username', default=None)
    p_breakdown.add_argument('-p', '--pretty', dest='pretty', action='store_true')
    p_breakdown.set_defaults(func=breakdown_argparse)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
