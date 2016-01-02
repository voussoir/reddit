#/u/GoldenSights
import traceback
import json
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import requests
import sqlite3
import string

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
# This is a short description of what the bot does.
# For example "Python automatic replybot v2.0 (by /u/GoldenSights)"
SUBREDDIT = "goldtesting"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
KEYWORDS = ["randomwikipageplease"]
# These are the words you are looking for
KEYAUTHORS = []
# These are the names of the authors you are looking for
# The bot will only reply to authors on this list
# Keep it empty to allow anybody.
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
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
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

        if pauthor.lower() == r.user.name.lower():
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
            print('Replying to %s by %s' % (pid, pauthor))
            try:
                reply = get_random_wikipages(3)
                post.reply(reply)
            except praw.errors.Forbidden:
                print('403 FORBIDDEN - is the bot banned from %s?' % post.subreddit.display_name)

def get_random_wikipages(count):
    print('Generating wiki pages')
    HEADERS = {'User-Agent': 'Random wikipage fetcher v1 - puts random wiki pages into reddit comments'}
    url = 'https://en.wikipedia.org/w/api.php?action=query&list=random&rnlimit=%d&format=json&rnnamespace=0' % count
    page = requests.get(url, HEADERS)
    page.raise_for_status()
    jpage = json.loads(page.text)
    jpage = jpage['query']['random']
    links = []
    for item in jpage:
        print(''.join(c for c in item['title'] if c in string.printable))
        links.append('[%s](https://en.wikipedia.org/?curid=%s)' % (item['title'], item['id']))
    return '\n\n'.join(links)

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

    