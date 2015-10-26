#/u/GoldenSights

import praw
import time
import os
import sys
import sqlite3
import string
import traceback

'''USER CONFIGURATION'''
SELF_USERNAME = 'Newsletterly'
# This is not used for login purposes, just message text

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""

MAXPOSTS = 100
WAIT = 30
ADMINS = ["GoldenSights"]
# The Admins have the ability to see other peoples' subscriptions
# as well as forcibly subscribe people to subreddits.
# They can also send the "kill" message to the bot and have it 
# turn off.
# The first name on the list will receive the error messages.

MAX_PER_MESSAGE = 20
# Only this many posts may be compiled into a newsletter
# to avoid massive walls of text

MAX_SUBSCRIPTION_POSTS_PER_HOUR = 2
# When a user subscribes to a subreddit, the subreddit will first
# undergo a posts/hour check. If the pph of the last 100 submissions
# exceeds this value, the user will not be allowed to subscribe to
# that subreddit

MESSAGE_FOOTER = "\n\n_____\n\n[In operating Newsletterly](http://redd.it/26xset)"
MESSAGE_MESSAGE_LONG = "This message ended up being too long!"
MESSAGE_NEW_POSTS = "Your subscribed subreddits have had some new posts:\n\n"
MESSAGE_POSTFORMAT = "_reddit_ _author_: _title_"
MESSAGE_SUBJECT = "Newsletterly"
MESSAGE_SUBSCRIBE = "You have subscribed to /r/%s"
MESSAGE_SUBSCRIBE_ALREADY = "You are already subscribed to /r/%s"
MESSAGE_SUBSCRIBE_BLACKLISTED = """
Sorry, but Newsletterly is designed for keeping an eye on very small or niche
subreddits. Currently, only subreddits with less than {maxpph} posts per hour
are accepted, and /r/%s is too active. Maybe an RSS reader would be a better
option. You can message /u/{admin} if you think this is in error.
""".format(maxpph=MAX_SUBSCRIPTION_POSTS_PER_HOUR, admin=ADMINS[0])
MESSAGE_SUBSCRIBE_FORCE = "You have forcefully added /u/%s to /r/%s"
MESSAGE_SUBREDDIT_FAIL = """
Could not find /r/%s. Make sure it's spelled correctly and is a
public subreddit (If it's private, add /u/{self} as a contributor).
""".format(self=SELF_USERNAME)
MESSAGE_UNSUBSCRIBE = "You have unsubscribed from /r/%s"
MESSAGE_UNSUBSCRIBE_ALL = "You have unsubscribed from all subreddits."
MESSAGE_UNSUBSCRIBE_ALREADY = "You are not currently subscribed to /r/%s"
MESSAGE_UNSUBSCRIBE_ALREADY_ALL = "You don't have any subscriptions!"
MESSAGE_UNSUBSCRIBE_FORCE = "You have forcefully removed /u/%s from /r/%s"
MESSAGE_REPORT_ALL = "All Newsletterly subscriptions:"
MESSAGE_REPORT_EMPTY = "There's nothing here!"
MESSAGE_REPORT_REQUEST = "You have requested a list of your subscriptions:"
MESSAGE_REPORT_USER = "Newsletterly subscriptions for /u/%s:"
MESSAGE_TOOLONG = """
Your message was too long. This measure is in place to prevent abuse.

When subscribing to multiple subreddits, use the comma syntax instead of
making new lines.


"""

'''ALL DONE'''

NOSEND = 'nosend' in sys.argv
if NOSEND:
    print('NOSEND active!')
ADMINS = [admin.lower() for admin in ADMINS]

try:
    import newsletterly_creds
    USERAGENT = newsletterly_creds.aN
    APP_ID = newsletterly_creds.oN_id
    APP_SECRET = newsletterly_creds.oN_secret
    APP_URI = newsletterly_creds.oN_uri
    APP_REFRESH = newsletterly_creds.oN_refresh
except ImportError:
    pass

WAITS = str(WAIT)

sql = sqlite3.connect('newsletterly.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpostindex ON oldposts(ID)')
cur.execute('CREATE TABLE IF NOT EXISTS subscribers(name TEXT, reddit TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS spool(name TEXT, message TEXT)')
sql.commit()

# Sqlite column names
SQL_USERNAME = 0
SQL_SUBREDDIT = 1

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
#import bot
#r = bot.o7()

def to_printable(s):
    return ''.join(character for character in s if character in string.printable)

def printlog(*args, **kwargs):
    args = list(args)
    args = [str(x) for x in args]
    args = [to_printable(x) for x in args]
    print(*args, **kwargs)

def fetchgenerator():
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def get_posts_per_hour(subreddit):
    '''
    Given a subreddit, return a float representing the posts/hour
    of the last 100 submissions.
    '''
    subreddit = r.get_subreddit(subreddit)
    submissions = list(subreddit.get_new())
    if len(submissions) < 2:
        return 0
    newest = submissions[0]
    oldest = submissions[-1]
    agediff = (newest.created_utc - oldest.created_utc) / 3600
    pph = len(submissions) / agediff
    return pph

def get_subscription_reddits(user=None, join=True):
    '''
    Return the subreddits which this user is subscribed to

    If `user` is None, get all users.
    If `join` is True, join the subreddits into /r/a+b+c

    '''
    if user is None:
        cur.execute('SELECT * FROM subscribers')
    else:
        user = user.lower()
        cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=?', [user])
    fetch = cur.fetchall()
    fetch = [f[SQL_SUBREDDIT] for f in fetch]
    fetch = list(set(fetch))
    if not join:
        return fetch
    return "+".join(fetch)

def add_subscription(user, subreddit):
    user = user.lower()
    subreddit = subreddit.lower()
    try:
        subreddit = r.get_subreddit(subreddit, fetch=True).display_name
        pph = get_posts_per_hour(subreddit)
        if pph > MAX_SUBSCRIPTION_POSTS_PER_HOUR:
            return (MESSAGE_SUBSCRIBE_BLACKLISTED % subreddit)
        cur.execute('SELECT * FROM subscribers WHERE LOWER(name)=? AND LOWER(reddit)=?', [user, subreddit])
        fetch = cur.fetchall()
        if len(fetch) > 0:
            printlog('\t%s is already subscribed to %s' % (user, subreddit))
            return (MESSAGE_SUBSCRIBE_ALREADY % subreddit)
        else:
            cur.execute('INSERT INTO subscribers VALUES(?, ?)', [user, subreddit])
            sql.commit()
            printlog('\t%s has subscribed to %s' % (user, subreddit))
            return (MESSAGE_SUBSCRIBE % subreddit)
    except (praw.errors.NotFound, praw.errors.Forbidden):
        printlog('\tSubreddit does not exist')
        return (MESSAGE_SUBREDDIT_FAIL % subreddit)

def drop_subscription(user, subreddit):
    user = user.lower()
    subreddit = subreddit.lower()
    subreddit = subreddit.replace('/r/', '')
    subreddit = subreddit.replace('r/', '')
    if subreddit == 'all':
        cur.execute('SELECT * FROM subscribers WHERE LOWER(name) == ?', [user])
        if cur.fetchone():
            cur.execute('DELETE FROM subscribers WHERE LOWER(name)=?', [user])
            sql.commit()
            printlog('\t%s has unsubscribed from everything' % user)
            return MESSAGE_UNSUBSCRIBE_ALL
        else:
            printlog('\t%s doesnt have any subscriptions' % user)
            return MESSAGE_UNSUBSCRIBE_ALREADY_ALL

    cur.execute('SELECT * FROM subscribers WHERE LOWER(name) == ? AND LOWER(reddit) ==?', [user, subreddit])
    if cur.fetchone():
        cur.execute('DELETE FROM subscribers WHERE LOWER(name) == ? AND LOWER(reddit) ==?', [user, subreddit])
        sql.commit()
        printlog('\t%s has unsubscribed from %s' % (user, subreddit))
        return (MESSAGE_UNSUBSCRIBE % subreddit)
    else:
        printlog('\t%s is already unsubscribed from %s' % (user, subreddit))
        return (MESSAGE_UNSUBSCRIBE_ALREADY % subreddit)

def count_subscriptions():
    cur.execute('SELECT COUNT(*) FROM subscribers')
    return cur.fetchone()[0]

def format_post(submission):
    template = MESSAGE_POSTFORMAT
    try:
        author = '/u/' + submission.author.name
    except:
        author = "[deleted]"
    subreddit = '/r/' + submission.subreddit.display_name
    template = template.replace("_reddit_", subreddit)
    template = template.replace("_author_", author)
    template = template.replace("_title_", submission.title)
    template = template.replace(']', '\]')
    template = template.replace('[', '\[')
    link = 'http://redd.it/' + submission.id
    template = '[%s](%s)' % (template, link)
    return template

def add_to_spool(user, message):
    if isinstance(user, praw.objects.Redditor):
        user = user.name
    user = user.lower()
    message = message.strip()
    cur.execute('SELECT * FROM spool WHERE name==? AND message==?', [user, message])
    if cur.fetchone():
        return False
        #raise Exception("Message already exists in spool")
    cur.execute('INSERT INTO spool VALUES(?, ?)', [user, message])
    #printlog('\tadded %s to spool' % user)
    sql.commit()
    return True

def get_from_spool():
    cur.execute('SELECT ROWID, * FROM spool')
    return cur.fetchone()

def drop_from_spool(rowid):
    cur.execute('DELETE FROM spool WHERE ROWID=?', [rowid])
    #printlog('\tdropped %s from spool' % spool[1])
    sql.commit()

def manage_spool():
    '''
    As long as there are more items in the spool, fetch
    one and send the message.
    '''
    printlog('Managing spool.')
    if NOSEND:
        return
    while True:
        spoolmessage = get_from_spool()
        if spoolmessage is None:
            break
        rowid = spoolmessage[0]
        user = spoolmessage[1]
        message = spoolmessage[2]
        printlog('Mailing %s : %s' % (user, message[:30]))
        try:
            r.send_message(user, MESSAGE_SUBJECT, message, captcha=None)
        except praw.errors.InvalidUser:
            # The user is deleted, so remove all of their subscriptions.
            drop_subscription(user, 'all')
            r.send_message(ADMINS[0], 'invalid user', user, captcha=None)
        
        # Any other exceptions will be uncaught, meaning the message
        # will remain in the database safe for next time.
        drop_from_spool(rowid)

def manage_inbox():
    printlog('Managing inbox')
    r.evict(r.config['unread'])
    messages = list(r.get_unread(limit=None))
    for message in messages:
        try:
            author = message.author.name
            interpretation = interpret_message(message)
            if interpretation:
                add_to_spool(author, interpretation)
        except AttributeError:
            pass
        message.mark_as_read()

def manage_posts():
    '''
    Build newsletters for each user.

    1. Get ALL of the subscriptions from the database
    2. Check the /new queue of each unique subreddit and add the submissions
       into a dict of the form {subreddit: [submission, submission, ...]}
    3. For each user, take the lists from the dictionary for the subreddits they
       are subscribed to, and compile a newsletter.
    '''

    # Compile sets of all our subscribers
    printlog('Managing subscriptions.')
    submissions_per_subreddit = {}
    subscriptions_per_user = {}
    all_subreddits = set()
    all_new_submissions = set()
    formatted_submissions = {}

    cur.execute('SELECT * FROM subscribers')
    for entry in fetchgenerator():
        user = entry[0].lower()
        subreddit = entry[1].lower()
        if user in subscriptions_per_user:
            subscriptions_per_user[user].add(subreddit)
        else:
            subscriptions_per_user[user] = set([subreddit])
        all_subreddits.add(subreddit)
    all_subreddits = list(all_subreddits)
    all_subreddits.sort(key=lambda x: x.lower())

    # First, go through all of the subreddits we have.
    # Take the items from their /new queue, remove the ones
    # which are already in the database, and add the rest
    # to the submissions_per_subreddit dictionary, and render
    # them into text that can be sent in the newsletter.
    for subreddit in all_subreddits:
        printlog('Checking /r/%s: ' % subreddit, end='')
        sys.stdout.flush()
        subreddit_obj = r.get_subreddit(subreddit)
        submissions = list(subreddit_obj.get_new(limit=100))
        keep_submissions = []
        for submission in submissions:
            cur.execute('SELECT * FROM oldposts WHERE id == ?', [submission.id])
            if cur.fetchone():
                continue
            all_new_submissions.add(submission.id)
            keep_submissions.append(submission)
        submissions_per_subreddit[subreddit] = keep_submissions
        for submission in keep_submissions:
            formatted_submissions[submission.id] = format_post(submission)
        printlog(len(keep_submissions))
    printlog()

    # Now, go through each user and take the submission list
    # from the submissions_per_subreddit dict, then compile a message
    # and add the message to the spool
    printlog('Compiling per-user newsletters.')
    for (user, subreddits) in subscriptions_per_user.items():
        submissions_for_user = []
        for subreddit in subreddits:
            submissions_for_user += submissions_per_subreddit[subreddit]
        if len(submissions_for_user) == 0:
            continue
        submissions_for_user.sort(key=lambda x: x.created_utc, reverse=True)
        submissions_for_user = submissions_for_user[:MAX_PER_MESSAGE]
        submissions_for_user = [formatted_submissions[x.id] for x in submissions_for_user]
        message = MESSAGE_NEW_POSTS
        message += '\n\n'.join(submissions_for_user)
        message += MESSAGE_FOOTER
        printlog('/u/%s: %d' % (user, len(submissions_for_user)))
        if NOSEND:
            printlog('nosend')
        else:
            add_to_spool(user, message)

    # Finally, mark all the submissions in the database.
    for submission in all_new_submissions:
        cur.execute('INSERT INTO oldposts VALUES(?)', [submission])
    sql.commit()

def interpret_message(pm):
    '''
    Given a Message object, split the body into its lines,
    try to understand what each line means, and do the appropriate
    functions (add user to subscriptions, etc).

    Returns the string that will be sent as a response.
    '''
    results = []
    author = pm.author.name
    author_lower = author.lower()
    bodysplit = pm.body.lower()
    bodysplit = bodysplit.split('\n\n')
    if len(bodysplit) > 10 and author_lower not in ADMINS:
        results = MESSAGE_TOOLONG + MESSAGE_FOOTER
        return results

    for line in bodysplit:
        linesplit = line.replace(', ', ' ')
        linesplit = linesplit.replace(',', ' ')
        linesplit = linesplit.split(' ')
        try:
            command = linesplit[0]
            command = command.replace(',', '')
            command = command.replace(' ', '')
        except IndexError:
            continue
        args = linesplit[1:]
        if command in ['report', 'reportall', 'kill']:
            args = [""]

        for argument in args:
            argument = argument.replace(',', '')
            argument = argument.replace(' ', '')
            printlog("%s : %s - %s" % (author, command, argument))

            if command == 'report':
                status = MESSAGE_REPORT_REQUEST + '\n\n'
                status += build_report(author)
                results.append(status)

            elif command == 'reportall' and author_lower in ADMINS:
                status = MESSAGE_REPORT_ALL + '\n\n'
                status += build_report(None)
                results.append(status)

            elif command == 'kill' and author_lower in ADMINS:
                pm.mark_as_read()
                r.send_message(ADMINS[0], "force kill", "bot is being turned off")
                quit()

            if not argument:
                # If we've reached an argument-based function with
                # no argument, skip.
                continue

            if command == 'subscribe':
                status = add_subscription(author, argument)
                results.append(status)

            elif command == 'unsubscribe':
                status = drop_subscription(author, argument)
                results.append(status)

            elif command == 'reportuser' and author_lower in ADMINS:
                status = (MESSAGE_REPORT_USER % argument) + '\n\n'
                status += build_report(argument)
                results.append(status)

            elif command == 'forcesubscribe' and author_lower in ADMINS:
                argument = argument.split('.')
                user = argument[0]
                subreddit = argument[1]
                add_subscription(user, subreddit)
                status = (MESSAGE_SUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
                results.append(status)

            elif command == 'forceunsubscribe' and author_lower in ADMINS:
                argument = argument.split('.')
                user = argument[0]
                subreddit = argument[1]
                drop_subscription(user, subreddit)
                status = (MESSAGE_UNSUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
                results.append(status)

    if len(results) > 0:
        results = '\n\n_____\n\n'.join(results)
        if len(results) > 9900:
            results = results[:9900]
            results += '\n\n' + MESSAGE_MESSAGE_LONG
        results += MESSAGE_FOOTER
        return results
    return None

def build_report(user):
    '''
    Given a username, display all the subreddits the user is subscribed to,
    and include a /r/a+b+c link

    If `user` is None, get EVERYBODY's list.
    '''
    if isinstance(user, str):
        userlist = [user]
    results = []
    get_all_users = user is None
    if get_all_users:
        cur.execute('SELECT * FROM subscribers')
        fetch = cur.fetchall()
        fetch = [f[0].lower() for f in fetch]
        userlist = list(set(fetch))
        status = get_subscription_reddits(None, join=True)
        status = "ALL REDDITS: /r/" + status + '\n\n'
        results.append(status)
    for user in userlist:
        # join=False because I want the list to contain all the individuals
        # as well as a join at the very end.
        status = get_subscription_reddits(user, join=False)
        if len(status) > 0:
            status.append('+'.join(status))
            status = ['/r/' + f for f in status]
            status[-1] = "All: " + status[-1]
            status = '\n\n'.join(status)
            if get_all_users:
                status = '/u/' + user + '\n\n' + status + '\n\n&nbsp;\n\n'
            results.append(status)

    if len(results) == 0:
        results = MESSAGE_REPORT_EMPTY
    else:
        results = '\n\n'.join(results)
    return results

while True:
    try:
        manage_inbox()
        printlog('--')
        manage_posts()
        printlog('--')
        manage_spool()
        printlog('--')
    except Exception:
        traceback.print_exc()
    printlog('%d active subscriptions' % count_subscriptions())
    printlog('Sleeping %s seconds\n\n\n' % WAITS)
    time.sleep(WAIT)