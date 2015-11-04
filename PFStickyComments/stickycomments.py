#/u/GoldenSights
import datetime
import praw
import sqlite3
import time
import traceback

''' User Config '''

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

STICKY_FORMAT = '.comments-page .sitetable.nestedlisting>.thing.id-t1_{commentid},/*{timestamp}, Auto sticky /u/{author}*/'
TIMESTAMP_FORMAT = '%Y-%m-%d'
# The CSS code for creating sticky comments.
# Timestamp formatting: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior

STICKIES_TO_KEEP = 8
# The number of sticky comments to maintain at any one time.

ANCHOR_VIP_TOP = '/* Autosticky VIP:'
ANCHOR_VIP_BOTTOM = '*/'
ANCHOR_TEXT_TOP = '.comments-page .sitetable.nestedlisting>.thing.id-t1_id_list_start,/*do not remove*/'
ANCHOR_TEXT_BOTTOM = '.comments-page .sitetable.nestedlisting>.thing.id-t1_id_list_end/*do not remove*/'
# Lines of text above and below the ID list, so the bot knows where to look.
# It's important that these lines do not change without also updating the bot.
# They are case-sensitive!

MODMAIL_SUBJECT_ANCHORS = 'Missing list anchors!'
MODMAIL_SUBJECT_VIP = 'Missing VIP anchor!'
MODMAIL_SUBJECT_VIP404 = 'VIP 404!'
MODMAIL_BODY_ANCHORS = '''
Error! I could not find the anchor points I was looking for:

top: `{top}`

bottom: `{bottom}`

I am removing myself as a moderator. Please re-invite me when the stylesheet is fixed.
'''
MODMAIL_BODY_VIP404 = '''
Error! I was able to locate the VIP (/u/{username}) but the account appears to be missing.

I am removing myself as a moderator. Please re-invite me when the stylesheet is fixed.
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
    #APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass

sql = sqlite3.connect('stickycomments.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT, username TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpostindex on oldposts(id)')

print('Logging in')
#r = praw.Reddit(USERAGENT)
#r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
#r.refresh_access_information(APP_REFRESH)
r=bot.o7()

def accept_pending_modinvites():
    print('Looking for mod invites')
    unread = list(r.get_unread(limit=None))
    for message in unread:
        if message.subreddit == None:
            continue
        subject = 'invitation to moderate /r/%s' % message.subreddit.display_name
        if message.subject.lower() != subject.lower():
            continue
        try:
            print('Accepting invite from /r/%s' % message.subreddit.display_name)
            message.subreddit.accept_moderator_invite()
        except praw.errors.InvalidInvite:
            print('No pending invite')
        message.mark_as_read()

def add_sticky_to_css(subreddit, comment):
    print('Stickying %s by %s' % (comment.id, comment.author.name))
    timestamp = datetime.datetime.utcfromtimestamp(comment.created_utc)
    timestamp = timestamp.strftime(TIMESTAMP_FORMAT)
    new_line = STICKY_FORMAT.format(commentid=comment.id,
                                    timestamp=timestamp,
                                    author=comment.author.name)

    subreddit = r.get_subreddit(subreddit)
    # This request will probably still be available in the cache
    # from finding the vip.
    original_page = subreddit.get_stylesheet()['stylesheet']
    if not (ANCHOR_TEXT_TOP in original_page and ANCHOR_TEXT_BOTTOM in original_page):
        body = MODMAIL_BODY_ANCHORS.format(top=ANCHOR_TEXT_TOP, bottom=ANCHOR_TEXT_BOTTOM)
        modmail_and_leave(subreddit, MODMAIL_SUBJECT_ANCHORS, body)
        return 'fail'
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
    subreddit.set_stylesheet(new_page)
    # Clear cache so that if we are stickying two comments at once, we aren't
    # using the outdated stylesheet as a basis for this function.
    cur.execute('INSERT INTO oldposts VALUES(?, ?)', [comment.fullname, comment.author.name])
    sql.commit()
    r.handler.clear_cache()
    return 'success'

def find_vip(subreddit):
    print('Finding VIP for /r/%s' % subreddit)
    subreddit = r.get_subreddit(subreddit)
    stylesheet = subreddit.get_stylesheet()['stylesheet']
    if not (ANCHOR_VIP_TOP in stylesheet and ANCHOR_VIP_BOTTOM in stylesheet):
        body = MODMAIL_BODY_ANCHORS.format(top=ANCHOR_VIP_TOP, bottom=ANCHOR_VIP_BOTTOM)
        modmail_and_leave(subreddit, MODMAIL_SUBJECT_VIP, body)
        return
    name = stylesheet.split(ANCHOR_VIP_TOP)[1]
    name = name.split(ANCHOR_VIP_BOTTOM)[0]
    for go_away in ('/u/', 'u/', ' '):
        name = name.replace(go_away, '')
    name = name.strip()
    print('Found: /u/%s' % name)
    return name

def look_for_comments(username, subreddit):
    print('Gathering comments from /u/%s in /r/%s' % (username, subreddit))
    user = r.get_redditor(username)
    try:
        comments = list(user.get_comments(limit=100))
    except praw.errors.NotFound:
        body = MODMAIL_BODY_VIP404.format(username=username)
        subreddit = r.get_subreddit(subreddit)
        modmail_and_leave(subreddit, MODMAIL_SUBJECT_VIP404, body)
        return []
    # Reverse to that most recent are acted on last.
    comments.reverse()

    comments_keep = []
    for comment in comments:
        if comment.subreddit.display_name.lower() != subreddit.lower():
            continue

        cur.execute('SELECT * FROM oldposts WHERE id == ?', [comment.fullname])
        if cur.fetchone():
            continue

        comments_keep.append(comment)

    return comments_keep

def modmail_and_leave(subreddit, subject, body):
    print('Uh oh! /r/%s is missing some anchors' % subreddit.display_name)
    r.send_message(subreddit, subject, body)
    print('Leave as moderator from /r/%s' % subreddit.display_name)
    r.leave_moderator(subreddit)

def stickycommentsbot():
    accept_pending_modinvites()
    moderation = list(r.get_my_moderation())
    for subreddit in moderation:
        subreddit = subreddit.display_name
        vip = find_vip(subreddit)
        if vip == None:
            # Occurs when we can't find the anchors.
            continue
        comments = look_for_comments(vip, subreddit)
        for comment in comments:
            status = add_sticky_to_css(subreddit, comment)
            if status == 'fail':
                # Occurs when we can't find the anchors.
                break

while True:
    try:
        stickycommentsbot()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)