#/u/GoldenSights
import datetime
import praw
import sqlite3
import time

''' User Config '''

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

SUBREDDIT = 'GoldTesting'

STICKY_AUTHORS = ['GoldenSights', 'adeadhead']
# The usernames of the people whose comments will be stickied

STICKY_FORMAT = '.comments-page .sitetable.nestedlisting>.thing.id-t1_{commentid},/*{timestamp}, Auto sticky /u/{author}*/'
TIMESTAMP_FORMAT = '%Y-%m-%d'
# The CSS code for creating sticky comments.
# Timestamp formatting: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior

STICKIES_TO_KEEP = 8
# The number of sticky comments to maintain at any one time.

ANCHOR_TEXT_TOP = '.comments-page .sitetable.nestedlisting>.thing.id-t1_youridhere,/**/'
ANCHOR_TEXT_BOTTOM = '.comments-page .sitetable.nestedlisting>.thing.id-t1_nocomma/* do not remove this */'
# Lines of text above and below the ID list, so the bot knows where to look.
# It's important that these lines do not change without also updating the bot.
# They are case-sensitive!

SEND_MODMAIL_WHEN_MISSING = True
MODMAIL_ANCHORS_SUBJECT = 'Missing anchors!'
MODMAIL_ANCHORS_BODY = '''
Error! I could not find the anchor points for the sticky comment ID list. I was looking for:

top: `{top}`

bottom: `{bottom}`

I'm shutting down! Restart me please.
'''

WAIT = 60
# This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

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

sql = sqlite3.connect('stickycomments.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpostindex on oldposts(id)')

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

STICKY_AUTHORS = [r.get_redditor(name) for name in STICKY_AUTHORS]
SUBREDDIT = r.get_subreddit(SUBREDDIT)

def look_for_comments():
    comments = []
    for user in STICKY_AUTHORS:
        print('Gathering comments from /u/%s' % user.name)
        comments.extend(list(user.get_comments(limit=100)))

    comments.sort(key=lambda x: x.created_utc)
    for comment in comments:
        if comment.subreddit.display_name.lower() != SUBREDDIT.display_name.lower():
            continue

        cur.execute('SELECT * FROM oldposts WHERE id == ?', [comment.fullname])
        if cur.fetchone():
            continue

        add_sticky_to_css(comment)
        cur.execute('INSERT INTO oldposts VALUES(?)', [comment.fullname])
        sql.commit()

def add_sticky_to_css(comment):
    print('Stickying %s by %s' % (comment.id, comment.author.name))
    timestamp = datetime.datetime.utcfromtimestamp(comment.created_utc)
    timestamp = timestamp.strftime(TIMESTAMP_FORMAT)
    new_line = STICKY_FORMAT.format(commentid=comment.id,
                                    timestamp=timestamp,
                                    author=comment.author.name)

    original_page = SUBREDDIT.get_stylesheet()['stylesheet']
    if SEND_MODMAIL_WHEN_MISSING:
        if not (ANCHOR_TEXT_TOP in original_page and ANCHOR_TEXT_BOTTOM in original_page):
            modmail_missing_anchors()
            quit()
    original_block = original_page.split(ANCHOR_TEXT_TOP)[1]
    original_block = original_block.split(ANCHOR_TEXT_BOTTOM)[0]

    new_block = original_block.strip()
    new_block = new_block.split('\n')
    new_block = [line for line in new_block if line != '']
    new_block.insert(0, new_line)
    new_block = new_block[:STICKIES_TO_KEEP]
    new_block = '\n'.join(new_block)

    original_block = ANCHOR_TEXT_TOP + original_block + ANCHOR_TEXT_BOTTOM
    new_block = '%s\n%s\n%s' % (ANCHOR_TEXT_TOP, new_block, ANCHOR_TEXT_BOTTOM)
    new_page = original_page.replace(original_block, new_block)
    SUBREDDIT.set_stylesheet(new_page)

def modmail_missing_anchors():
    print('Uh oh! Where did the anchors go?')
    body = MODMAIL_ANCHORS_BODY.format(top=ANCHOR_TEXT_TOP, bottom=ANCHOR_TEXT_BOTTOM)
    r.send_message(SUBREDDIT, MODMAIL_ANCHORS_SUBJECT, body)

while True:
    try:
        look_for_comments()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)