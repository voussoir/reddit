# /u/GoldenSights
import praw3 as praw
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
SUBREDDIT_TO_SUBMIT = 'OpenAndGenuine'

# _title_ is special because it has to be done after all the other formats.
SUBMISSION_TITLE = '/r/{subreddit} locks "_title_" (+{score}) ({numcomments} comments)'
SUBMISSION_TEXT = '''
https://old.reddit.com/r/{subreddit}/comments/{id}

https://r.go1dfish.me/r/{subreddit}/comments/{id}/
'''

MAX_TITLE_LENGTH = 300

POSTS_TO_COLLECT = 1000

WAIT = 120
# The number of seconds between each cycle. The bot is completely inactive during this time.
''' All done! '''

try:
    import bot
    USERAGENT = bot.lock_ua
    APP_ID = bot.lock_id
    APP_SECRET = bot.lock_secret
    APP_URI = bot.lock_uri
    APP_REFRESH = bot.lock_refresh
except ImportError:
    pass

sql = sqlite3.connect('lockfinder.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS lockedposts(id TEXT, subreddit TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS postindex on lockedposts(id)')

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

    title = SUBMISSION_TITLE.format(
        author=author,
        fullname=submission.fullname,
        numcomments=str(submission.num_comments),
        score=str(submission.score),
        subreddit=submission.subreddit.display_name,
    )

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

def create_selftext(submission):
    '''
    Format the submission's properties into a string which will become our
    new submission's body.
    '''
    text = SUBMISSION_TEXT.format(
        subreddit=submission.subreddit.display_name.lower(),
        id=submission.id
    )
    return text

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

def submission_in_database(submission):
    if isinstance(submission, praw.objects.Submission):
        submission = submission.fullname
    if '_' not in submission:
        submission = 't3_' + submission

    cur.execute('SELECT * FROM lockedposts WHERE id == ?', [submission])
    item = cur.fetchone()
    return (item is not None)



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
        selftext = create_selftext(submission)

        #print(title)
        #print(url)
        print('Making submission')
        new_submission = r.submit(SUBREDDIT_TO_SUBMIT, title, text=selftext)
        print('Created %s' % new_submission.fullname)
        add_to_database(submission)


if __name__ == '__main__':
    while True:
        try:
            lockfinder()
        except Exception as e:
            traceback.print_exc()
        print('Running again in %d seconds\n' % WAIT)
        time.sleep(WAIT)
