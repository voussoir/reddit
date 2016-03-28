#/u/GoldenSights
import traceback
import praw
import time
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
# This is a short description of what the bot does.
# For example "/u/GoldenSights' Newsletter bot"

SUBREDDIT = "GoldTesting"
# This is the sub or list of subs to scan for new posts.
# For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...".
# For all use "all"
DUMPSUBREDDIT = "test"
# The alternate subreddit to submit to.

KEYWORDS = ['Request', 'Submitted', 'Release', 'Concept']
# Posts must contain these words. Case does not matter
KEYDOMAINS = []
# Linkposts must contain these strings in their URL.

TITLE_FORMAT = "_title_"
# This is the title of the post that will go in DUMPSUBREDDIT
# You may use the following injectors to create a dynamic title
# _author_
# _subreddit_
# _score_
# _title_

DO_LINKPOSTS = True
DO_SELFPOSTS = True
# Which types of submissions to consider.

TRUEURL = True
# If True, submit the actual link or selftext from the original post.
# If False, submit a permalink to the post.

MAXPOSTS = 100
# This is how many posts you want to retrieve all at once.
# PRAW can download 100 at a time.
WAIT = 20
# This is how many seconds you will wait between cycles.
# The bot is completely inactive during this time.


'''All done!'''


try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

KEYWORDS = [key.lower() for key in KEYWORDS]
KEYDOMAINS = [key.lower() for key in KEYDOMAINS]

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS idindex on oldposts(id)')

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)


def ellipsis(text, length):
    '''
    If the text is longer than the desired length, truncate it and add
    an ellipsis to the end. Otherwise, just return the original text.

    Example:
    ellipsis('hello', 6) -> 'hello'
    ellipsis('hello', 5) -> 'hello'
    ellipsis('hello', 4) -> 'h...'
    '''
    if len(text) > length:
        characters = max(0, length-3)
        dots = length - characters
        text = text[:characters] + ('.' * dots)
    return text

def scansub():
    print('Checking /r/%s.' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    submissions = subreddit.get_new(limit=MAXPOSTS)
    for submission in submissions:
        if submission.author is None:
            continue

        if submission.subreddit.display_name.lower() == DUMPSUBREDDIT.lower():
            continue

        if submission.is_self and not DO_SELFPOSTS:
            continue

        if not submission.is_self and not DO_LINKPOSTS:
            continue            

        body = '%s\n%s' % (submission.title, submission.selftext)
        body = body.lower()
        if KEYWORDS and not any(key in body for key in KEYWORDS):
            continue

        if KEYDOMAINS:
            url = submission.url.lower()
            if submission.is_self:
                continue
            if not any(key in url for key in KEYDOMAINS):
                continue

        cur.execute('SELECT * FROM oldposts WHERE id == ?', [submission.id])
        if cur.fetchone() is not None:
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [submission.id])
        sql.commit()

        if TRUEURL:
            if submission.is_self:
                kwargs = {'text': submission.selftext}
            else:
                kwargs = {'url': submission.url}
        else:
            kwargs = {'url': submission.permalink}

        print('Dumping', submission.id)
        title = TITLE_FORMAT
        title = title.replace('_author_', submission.author.name)
        title = title.replace('_subreddit_', submission.subreddit.display_name)
        title = title.replace('_score_', str(submission.score))
        title = title.replace('_title_', submission.title)
        title = ellipsis(title, 300)

        new_submission = r.submit(DUMPSUBREDDIT, title, resubmit=True, captcha=None, **kwargs)
        print('Created', new_submission.id)
        

while True:
    try:
        scansub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)
 