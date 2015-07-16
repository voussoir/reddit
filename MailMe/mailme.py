#/u/GoldenSights
import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
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
# For example "Python automatic replybot v2.0 (by /u/GoldenSights)"
SUBREDDIT = "pics"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
KEYWORDS = ["phrase 1", "phrase 2", "phrase 3", "phrase 4"]
# These are the words you are looking for
KEYAUTHORS = []
# These are the names of the authors you are looking for
# Any authors not on this list will not be replied to.
# Make empty to allow anybody
MAILME_RECIPIENT = "GoldenSights"
# Who will receive this message
MAILME_SUBJECT = "MailMe"
# Subjectline
MAILME_MESSAGE = "[_author_ has said your keyword](_permalink_)"
# The message the bot will send you. Use these injectors to customize
# _author_
# _id_
# _permalink_
MAXPOSTS = 100
# This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
# This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

CLEANCYCLES = 10
# After this many cycles, the bot will clean its database
# Keeping only the latest (2*MAXPOSTS) items

'''All done!'''

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')

sql.commit()

print('Logging in...')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def replybot():
    print('Searching %s.' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = list(subreddit.get_comments(limit=MAXPOSTS))
    posts.reverse()
    for post in posts:
        # Anything that needs to happen every loop goes here.
        pid = post.id

        try:
            pauthor = post.author.name
        except AttributeError:
            # Author is deleted. We don't care about this post.
            continue

        if pauthor.lower() in [r.user.name.lower(), MAILME_RECIPIENT.lower()]:
            # Don't reply to yourself, robot!
            print('Will not reply to myself.')
            continue

        if KEYAUTHORS != [] and all(auth.lower() != pauthor for auth in KEYAUTHORS):
            # This post was not made by a keyauthor
            continue

        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if cur.fetchone():
            # Post is already in the database
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()
        pbody = post.body.lower()
        if any(key.lower() in pbody for key in KEYWORDS):
            print('Sending MailMe message')
            psub = post.subreddit.display_name
            message = MAILME_MESSAGE
            message = message.replace('_author_', pauthor)
            message = message.replace('_id_', pid)
            permalink = 'https://reddit.com/r/%s/comments/%s/_/%s' % (psub, post.link_id, pid)
            message = message.replace('_permalink_', permalink)
            r.send_message(MAILME_RECIPIENT, MAILME_SUBJECT, message)

cycles = 0
while True:
    try:
        replybot()
        cycles += 1
    except Exception as e:
        traceback.print_exc()
    if cycles >= CLEANCYCLES:
        print('Cleaning database')
        cur.execute('DELETE FROM oldposts WHERE id NOT IN (SELECT id FROM oldposts ORDER BY id DESC LIMIT ?)', [MAXPOSTS * 2])
        sql.commit()
        cycles = 0
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)

    