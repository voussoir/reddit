import datetime
import praw

''' USER CONFIG '''
USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

SUBREDDIT = 'Excel'
IGNORE_DELETED_AUTHORS = True
TXT_FILENAME = 'results_%Y%b%d.txt'

MINIMUM_AGE = 60 * 60 * 24
MAXIMUM_AGE = 7 * 60 * 60 * 24
# In seconds.

TABLE_HEADER =    'title | author | time | comments'
TABLE_ALIGNMENT = ':-    | :-     |   -: |       -:'
TABLE_ROW =       '[_title_](_permalink_) | _author_ | _timestamp_ | _comments_'
# Available injectors:
# _title_
# _permalink_
# _author_
# _timestamp_
# _comments_
# _score_
''' All done! '''

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def find_unsolved():
    print('getting new')
    subreddit = r.get_subreddit(SUBREDDIT)
    new = subreddit.get_new(limit=1000)
    results = []

    now = datetime.datetime.now(datetime.timezone.utc)
    nowstamp = now.timestamp()
    for (index, submission) in enumerate(new):
        age = nowstamp - submission.created_utc
        if age < MINIMUM_AGE:
            continue

        if age > MAXIMUM_AGE:
            continue

        if IGNORE_DELETED_AUTHORS and submission.author is None:
            continue

        if submission.link_flair_text not in ['unsolved', 'Waiting on OP']:
            continue

        # make sure to perform this part AS LATE AS POSSIBLE to avoid
        # api calls.
        submission.replace_more_comments(limit=None, threshold=1)
        total = praw.helpers.flatten_tree(submission.comments)
        submission.flat_comments = total
        
        if submission.link_flair_text == 'unsolved' and len(total) != 0:
            continue

        if submission.link_flair_text == 'Waiting on OP' and len(total) != 1:
            continue

        results.append(submission)
    return results

def create_table(results):
    rows = []
    results.sort(key=lambda s: (s.created_utc, s.num_comments))
    for (index, submission) in enumerate(results):
        if submission.author is None:
            author = '[deleted]'
        else:
            author = '/u/%s' % submission.author.name

        timestamp = datetime.datetime.utcfromtimestamp(submission.created_utc)
        timestamp = timestamp.strftime('%d %b %Y %H:%M:%S')

        row = TABLE_ROW
        row = row.replace('_title_', submission.title)
        row = row.replace('_permalink_', submission.permalink)
        row = row.replace('_author_', author)
        row = row.replace('_timestamp_', timestamp)
        row = row.replace('_comments_', len(submission.flat_comments))
        row = row.replace('_score_', submission.score)
        row = row.strip()

        rows.append(row)

    header = TABLE_HEADER.strip()
    alignment = TABLE_ALIGNMENT.strip()
    rows = '\n'.join(rows)

    table = '\n'.join([header, alignment, rows])
    return table

