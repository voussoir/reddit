# /u/GoldenSights
import praw
import sqlite3
import time
import traceback

''' USER CONFIG '''
USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

SUBREDDIT_TO_SCAN = 'all'
SUBREDDIT_TO_SUBMIT = 'unlockedposts'

SUBMISSION_TITLE = '/r/_subreddit_ locks _fullname_ "_title_" (+_score_) (_numcomments_ comments)'
SUBMISSION_URL = 'http://r.go1dfish.me/r/_subreddit_/comments/_id_/x'
# The terms surrounded by underscores will be replaced by the submission's actual
# properties. See `create_title` and `create_url`


MAX_TITLE_LENGTH = 300

POSTS_TO_COLLECT = 1000

WAIT = 120
# The number of seconds between each cycle. The bot is completely inactive during this time.
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

sql = sqlite3.connect('lockfinder.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS lockedposts(id TEXT, subreddit TEXT)')

print('Logging in.')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def add_to_database(submission):
    subreddit = submission.subreddit.display_name.lower()
    submission = submission.fullname

    cur.execute('INSERT INTO lockedposts VALUES(?, ?)', [submission, subreddit])
    sql.commit()

def create_title(submission):
    '''
    Format the submission's properties into the SUBMISSION_TITLE injectors.
    Returns a string which will become our new submission's title.
    '''
    if submission.author is None:
        author = '[deleted]'
    else:
        author = '/u/' + submission.author.name

    title = SUBMISSION_TITLE
    title = title.replace('_author_', author)
    title = title.replace('_fullname_', submission.fullname)
    title = title.replace('_numcomments_', str(submission.num_comments))
    title = title.replace('_score_', str(submission.score))
    title = title.replace('_subreddit_', submission.subreddit.display_name)

    # We're formatting the title last, because we need to know the length of
    # everything else to decide our ellipsis value for the original submission's
    # title. It should be the first thing to get truncated.
    if '_title_' in title:
        available_space = MAX_TITLE_LENGTH - (len(title.replace('_title_', '')))
        available_space = max(0, available_space)
        space_each = int(available_space / title.count('_title_'))
        original_title = submission.title
        original_title = ellipsis(original_title, space_each)
        title = title.replace('_title_', original_title)

    title = ellipsis(title, MAX_TITLE_LENGTH)
    return title

def create_url(submission):
    '''
    Format the submission's properties into the SUBMISSION_URL injectors.
    Returns a string which will become our new submission's url.
    '''
    url = SUBMISSION_URL
    url = url.replace('_id_', submission.id)
    url = url.replace('_subreddit_', submission.subreddit.display_name.lower())
    return url

def ellipsis(text, length):
    '''
    If the text is longer than the desired length, truncate it and add
    an ellipsis to the end. Otherwise, just return the original text.

    Example:
    ellipsis('hello', 6) -> 'hello'
    ellipsis('hello', 5) -> 'hello'
    ellipsis('hello', 4) -> 'h...'
    ellipsis('hello', 3) -> '...'
    ellipsis('hello', 2) -> '..'
    ellipsis('hello', 1) -> '.'
    '''
    if len(text) > length:
        characters = max(0, length-3)
        dots = length - characters
        text = text[:characters] + ('.' * dots)
    return text

def lockfinder():
    print('Checking /r/%s' % SUBREDDIT_TO_SCAN)
    subreddit = r.get_subreddit(SUBREDDIT_TO_SCAN)
    submissions = subreddit.get_hot(limit=POSTS_TO_COLLECT)
    for submission in submissions:
        if submission.locked is False:
            continue

        if submission_in_database(submission):
            continue

        print('Found locked post %s' % submission.fullname)
        title = create_title(submission)
        url = create_url(submission)

        #print(title)
        #print(url)
        print('Making submission')
        new_submission = r.submit(SUBREDDIT_TO_SUBMIT, title, url=url)
        print('Created %s' % new_submission.fullname)
        add_to_database(submission)

def submission_in_database(submission):
    if isinstance(submission, praw.objects.Submission):
        submission = submission.fullname
    if '_' not in submission:
        submission = 't3_' + submission

    cur.execute('SELECT * FROM lockedposts WHERE id == ?', [submission])
    item = cur.fetchone()
    return (item is not None)


if __name__ == '__main__':
    while True:
        try:
            lockfinder()
        except Exception as e:
            traceback.print_exc()
        print('Running again in %d seconds\n' % WAIT)
        time.sleep(WAIT)