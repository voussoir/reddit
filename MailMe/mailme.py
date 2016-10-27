#/u/GoldenSights
import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

USERAGENT = ""
# This is a short description of what the bot does.
# For example "Python automatic replybot v2.0 (by /u/GoldenSights)"
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
SUBREDDIT = "test"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
KEYWORDS = ["phrase 1", "phrase 2", "phrase 3", "phrase 4", 'test']
# These are the words you are looking for
KEYAUTHORS = []
# These are the names of the authors you are looking for
# Any authors not on this list will not be replied to.
# Make empty to allow anybody
MAILME_RECIPIENT = "GoldenSights"
# Who will receive this message
MAILME_SUBJECT = "MailMe"
# Subjectline
MAILME_MESSAGE = "[/u/_author_ said these keywords in /r/_subreddit_: _results_](_permalink_)"
# The message the bot will send you. Use these injectors to customize
# _author_
# _id_
# _permalink_
# _subreddit_
# _results_
MULTIPLE_MESSAGE_SEPARATOR = '\n\n_______\n\n'
# If you get multiple results in a single PM, use this to separate them.
MAXPOSTS = 100
# This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
# This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

DO_COMMENTS = True
DO_SUBMISSIONS = False
# Should check submissions and / or comments?

PERMALINK_SUBMISSION = 'https://reddit.com/r/%s/comments/%s'
PERMALINK_COMMENT = 'https://reddit.com/r/%s/comments/%s/_/%s'

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
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index ON oldposts(id)')
sql.commit()

print('Logging in...')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

KEYWORDS = [k.lower() for k in KEYWORDS]

def mailme():
    print('Searching %s.' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    
    posts = []
    if DO_SUBMISSIONS:
        print('Collecting submissions')
        posts += list(subreddit.get_new(limit=MAXPOSTS))
    if DO_COMMENTS:
        print('Collecting comments')
        posts += list(subreddit.get_comments(limit=MAXPOSTS))

    posts.sort(key= lambda x: x.created_utc)

    # Collect all of the message results into a list, so we can
    # package it all into one PM at the end
    message_results = []

    for post in posts:
        # Anything that needs to happen every loop goes here.
        pid = post.id

        try:
            pauthor = post.author.name
        except AttributeError:
            # Author is deleted. We don't care about this post.
            continue

        if r.has_scope('identity'):
            myself = r.user.name.lower()
        else:
            myself = ''

        if pauthor.lower() in [myself, MAILME_RECIPIENT.lower()]:
            print('Will not reply to myself.')
            continue

        if KEYAUTHORS != [] and all(auth.lower() != pauthor for auth in KEYAUTHORS):
            # The Kayauthors list has names in it, but this person
            # is not one of them.
            continue

        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if cur.fetchone():
            # Post is already in the database
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()

        subreddit = post.subreddit.display_name
        # I separate the permalink defnitions because they tend to consume
        # API calls despite not being technically required.
        # So I'll do it myself.
        if isinstance(post, praw.objects.Submission):
            pbody = '%s\n\n%s' % (post.title.lower(), post.selftext.lower())
            permalink = PERMALINK_SUBMISSION % (subreddit, post.id)
        
        elif isinstance(post, praw.objects.Comment):
            pbody = post.body.lower()
            link = post.link_id.split('_')[-1]
            permalink = PERMALINK_COMMENT % (subreddit, link, post.id)

        # Previously I used an if-any check, but this way allows me
        # to include the matches in the message text.
        matched_keywords = []
        for key in KEYWORDS:
            if key not in pbody:
                continue
            matched_keywords.append(key)
        if len(matched_keywords) == 0:
            continue

        message = MAILME_MESSAGE
        message = message.replace('_author_', pauthor)
        message = message.replace('_subreddit_', subreddit)
        message = message.replace('_id_', pid)
        message = message.replace('_permalink_', permalink)
        if '_results_' in message:
            matched_keywords = [('"%s"' % x) for x in matched_keywords]
            matched_keywords = '[%s]' % (', '.join(matched_keywords))
            message = message.replace('_results_', matched_keywords)

        message_results.append(message)

    if len(message_results) == 0:
        return

    print('Sending MailMe message with %d results' % len(message_results))
    message = MULTIPLE_MESSAGE_SEPARATOR.join(message_results)
    #print(message)
    r.send_message(MAILME_RECIPIENT, MAILME_SUBJECT, message)


cycles = 0
if (DO_SUBMISSIONS, DO_COMMENTS) == (False, False):
    raise Exception('do_comments and do_submissions cannot both be false!')
while True:
    try:
        mailme()
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

    