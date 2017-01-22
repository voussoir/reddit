#/u/GoldenSights
import praw
import sqlite3
import time
import traceback
import urllib.parse

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
# This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
# This is the sub or list of subs to scan for new posts.
# For a single sub, use "sub1".
# For multiple subs, use "sub1+sub2+sub3+...".
# For all use "all"
KEYWORDS = ["flying cat"]
# Any comment containing these words will be saved.
KEYDOMAINS = []
# If non-empty, linkposts must have these strings in their URL

DO_COMMENTS = True
DO_LINKPOSTS = True
DO_SELFPOSTS = True
# Configure the types of objects you're looking for.

DO_ACTUAL_URL = False
# If this is a link submission (with DO_LINKPOSTS enabled),
# submit the actual URL rather than the reddit submission.

RSAVE = False
#Do you want the bot to save via Reddit Saving? Use True or False (Use capitals! no quotations!)
#praw DOES NOT allow comments to be saved. Don't ask me why. This will save the submission the comment is connected to.

MAILME = False
# Do you want the bot to send you a PM when it gets something?
RECIPIENT = "GoldenSights"
# If MAILME is set to True, you will need a name for the PM to go to
MSUBJECT = "SubDump automated message"
# If MAILME is set to True, you will need the PM to have a subject line.
MHEADER = "Comments containing your keywords:"
# This is part of the message body, on a line above the list of results. You can set it to "" if you just want the list by itself.

SUBDUMP = False
# Do you want the bot to dump into a subreddit as posts? Use True or False (Use capitals! No quotations!)
DUMP_SUB = "GoldTesting"
# If SUBDUMP is set to True, you will need to choose a subreddit to submit to.
DUMP_TITLE = "_author_ in /r/_subreddit_"
#This is the title of the post that will go in DUMP_SUB
#You may use the following injectors to create a dynamic title
#_author_
#_subreddit_
#_score_

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''


try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

KEYWORDS = [k.lower() for k in KEYWORDS]
KEYDOMAINS = [k.lower() for k in KEYDOMAINS]

sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index on oldposts(id)')
sql.commit()

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH) 


def title_format(post):
    text = DUMP_TITLE
    text = text.replace('_author_', post.author.name)
    text = text.replace('_subreddit_', post.subreddit.display_name)
    text = text.replace('_score_', '%d points' % post.score)
    return text

def subdump():
    print('Scanning /r/%s' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = []
    if DO_COMMENTS:
        posts += list(subreddit.get_comments(limit=MAXPOSTS))
    if DO_LINKPOSTS or DO_SELFPOSTS:
        posts += list(subreddit.get_new(limit=MAXPOSTS))

    mailme_results = []

    for post in posts:
        if post.author is None:
            # Item is deleted or removed
            continue

        if isistance(post, praw.objects.Submission):
            # Clear out the items that don't meet the user's config
            if post.subreddit.display_name.lower() == DUMP_SUB.lower():
                continue

            if post.is_self:
                if not DO_SELFPOSTS:
                    continue
            else:
                if not DO_LINKPOSTS:
                    continue
                domain = urllib.parse.urlparse(post.url).netloc.lower()
                if KEYDOMAINS != [] and not any(key.lower() in domain for key in KEYDOMAINS):
                    continue

        if isinstance(post, praw.objects.Submission):
            body = post.title + '\n' + post.selftext
        else:
            body = post.body
        body = body.lower()

        if KEYWORDS != [] and not any(key.lower() in body for key in KEYWORDS):
            continue

        cur.execute('SELECT * FROM oldposts WHERE id == ?', [post.id])
        if cur.fetchone():
            continue

        # Commit to the database before performing any of the save actions
        # This means if the saving fails, we will have the item marked when it
        # really shouldn't be. But this is better than risking getting into a
        # loop that causes endless spam without committing to the db.
        cur.execute('INSERT INTO oldposts VALUES(?)', [post.id])
        sql.commit()
        mailme_results.append(post)

        if RSAVE:
            post.save()
        if SUBDUMP:
            newtitle = title_format(post)
            if isinstance(post, praw.objects.Submission) and not post.is_self and DO_ACTUAL_URL:
                url = post.url
            else:
                url = post.permalink
            create = r.submit(DUMP_SUB, newtitle, url=url)

    if MAILME and len(mailme_results) > 0:
        mailme_results = ['[%s](%s)' % (title_format(post), post.permalink) for post in mailme_results]
        mailme_results = '\n\n'.join(mailme_results)
        mailme_results = MHEADER + '\n\n' + mailme_results
        r.send_message(RECIPIENT, MSUBJECT, mailme_results)


def scan_sub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    result = []
    authors = []
    for post in posts:
        pid = post.id
        pbody = post.body.lower()
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            if KEYWORDS == [] or any(key.lower() in pbody for key in KEYWORDS):
                try:
                    pauthor = post.author.name
                    print(pid + ', ' + pauthor)
                    plink = post.permalink
                    result.append(plink)
                    authors.append(pauthor + ' in /r/' + post.subreddit.display_name)
                    if RSAVE is True:
                        submission = post.submission
                        submission.save()
                        print('\tSaved submission')
                    if SUBDUMP is True:
                        newtitle = DUMP_TITLE
                        newtitle = newtitle.replace('_author_', pauthor)
                        newtitle = newtitle.replace('_subreddit_', post.subreddit.display_name)
                        newtitle = newtitle.replace('_score_', str(post.score) + ' points')
                        create = r.submit(DUMP_SUB, newtitle, url=plink, captcha = None)
                        print('\tDumped to ' + DUMP_SUB)
                except AttributeError:
                    print(pid + ': Author deleted. Ignoring comment')
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    if len(result) > 0 and MAILME is True:
        for m in range(len(result)):
            result[m] = '- [' + authors[m] + '](' + result[m] + ')'
        r.send_message(RECIPIENT, MTITLE, MHEADER + '\n\n' + '\n\n'.join(result), captcha=None)
        print('Mailed ' + RECIPIENT)
        
    sql.commit()

while True:
    try:
        subdump()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)
 