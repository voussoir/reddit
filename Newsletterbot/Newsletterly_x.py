#/u/GoldenSights

import datetime
import os
import praw3 as praw
import requests
import sqlite3
import string
import sys
import time
import traceback

from voussoirkit import operatornotify
from voussoirkit import vlogging

log = vlogging.getLogger(__name__, 'newsletterly')

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

MULTIREDDIT_NAME_LENGTH = 21

MAX_PER_MESSAGE = 20
# Only this many posts may be compiled into a newsletter
# to avoid massive walls of text

MAX_SUBSCRIPTION_POSTS_PER_HOUR = 2
# When a user subscribes to a subreddit, the subreddit will first
# undergo a posts/hour check. If the pph of the last 100 submissions
# exceeds this value, the user will not be allowed to subscribe to
# that subreddit


MESSAGE_DELETION_DROPPED = '''
Hi {username},

On {warned_at}, your account was marked to have its subscriptions dropped.
Because you did not respond to that message, your subscriptions
have been removed. You may re-subscribe at any time.

Your subscriptions were:

{subreddits}
'''
MESSAGE_DELETION_REDEEMED = '''
Thanks for confirming your Newsletterly activity. All of your subscriptions will be
kept.
'''

MESSAGE_SUBJECT = "Newsletterly"
MESSAGE_POSTFORMAT = "{subreddit} {author}: [{title}]({link})"
MESSAGE_FOOTER = "\n\n_____\n\n[About Newsletterly](https://old.reddit.com/comments/26xset)"

MESSAGE_NEW_POSTS = "Your subscribed subreddits have had some new posts:\n\n"

MESSAGE_MESSAGE_LONG = "This message ended up being too long!"
MESSAGE_SUBSCRIBE = "You have subscribed to /r/%s"
MESSAGE_SUBSCRIBE_ALREADY = "You are already subscribed to /r/%s"
MESSAGE_SUBSCRIBE_BLACKLISTED = '''
Sorry, but Newsletterly is designed for keeping an eye on very small or niche
subreddits. Currently, only subreddits with less than {maxpph} posts per hour
are accepted, and /r/%s is too active. Maybe an RSS reader would be a better
option. You can message /u/{admin} if you think this is in error.
'''.format(maxpph=MAX_SUBSCRIPTION_POSTS_PER_HOUR, admin=ADMINS[0])

MESSAGE_SUBSCRIBE_FORCE = "You have forcefully added /u/%s to /r/%s"
MESSAGE_SUBREDDIT_FAIL = '''
Could not find /r/%s. Make sure it's spelled correctly and is a
public subreddit (If it's private, add /u/{self} as a contributor).
'''.format(self=SELF_USERNAME)

MESSAGE_UNSUBSCRIBE = "You have unsubscribed from /r/%s"
MESSAGE_UNSUBSCRIBE_ALL = "You have unsubscribed from all subreddits."
MESSAGE_UNSUBSCRIBE_ALREADY = "You are not currently subscribed to /r/%s"
MESSAGE_UNSUBSCRIBE_ALREADY_ALL = "You don't have any subscriptions!"
MESSAGE_UNSUBSCRIBE_FORCE = "You have forcefully removed /u/%s from /r/%s"
MESSAGE_UNSUBSCRIBE_PRIVATIZED = '''
While I was building your Newsletter for /r/%s, I received a 403 Forbidden error.
This means the subreddit became private or banned, or I lost my Approved Submitter
status. Your subscription has been removed -- please subscribe again when the
issue has been resolved by the moderators of the subreddit.
'''
MESSAGE_REPORT_ALL = "All Newsletterly subscriptions:"
MESSAGE_REPORT_EMPTY = "There's nothing here!"
MESSAGE_REPORT_REQUEST = "You have requested a list of your subscriptions:"
MESSAGE_REPORT_USER = "Newsletterly subscriptions for /u/%s:"
MESSAGE_TOOLONG = '''
Your message was too long. This measure is in place to prevent abuse.

When subscribing to multiple subreddits, use the comma syntax instead of
making new lines.
'''

'''END OF USER CONFIGURATION'''

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

sql = sqlite3.connect('newsletterly.db')
cur = sql.cursor()
DB_INIT = '''
CREATE TABLE IF NOT EXISTS flag_deletion(
    username TEXT COLLATE NOCASE,
    warned_at INT,
    delete_at INT
);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS oldposts(id TEXT);
CREATE INDEX IF NOT EXISTS index_oldposts_id ON oldposts(id);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS spool(name TEXT, message TEXT);
----------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscribers(
    name TEXT COLLATE NOCASE,
    reddit TEXT COLLATE NOCASE
);
CREATE INDEX IF NOT EXISTS index_subscribers_name ON subscribers(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS index_subscribers_reddit ON subscribers(reddit COLLATE NOCASE);
'''

statements = DB_INIT.split(';')
for statement in statements:
    cur.execute(statement)
sql.commit()

# Sqlite column names
SQL_USERNAME = 0
SQL_SUBREDDIT = 1

def login():
    log.info('Logging in')
    r = praw.Reddit(USERAGENT)
    r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
    r.refresh_access_information(APP_REFRESH)

    # multireddit.add_subreddit is currently experiencing a bug under OAuth
    # because it's expecting the session to have a modhash. It means nothing.
    r.modhash = 'newsletters'

    log.info('I am /u/%s', r.user.name)
    return r

def add_subreddit_to_multireddit(subreddit):
    '''
    Ensure that this subreddit is part of a multireddit, creating a new multi
    if necessary.

    Multireddits are not grouped by any criteria. Any multi with an open slot
    will take this subreddit, or a new multi will be created.
    '''
    subreddit = normalize(subreddit)
    log.info('Assigning /r/%s to a multireddit', subreddit)

    # Originally I was going to keep multireddit-subreddit mappings in the local
    # database, but decided against it because that makes it harder to edit the
    # multis online and have the changes reflect.
    r.handler.clear_cache()
    my_multireddits = r.get_my_multireddits()
    for multireddit in my_multireddits:
        if any(subreddit == s.display_name.lower() for s in multireddit.subreddits):
            log.debug('Already have it')
            return

    # Prefer the one with most open spaces.
    my_multireddits = my_multireddits.sort(key=lambda m: len(m.subreddits))
    for multireddit in my_multireddits:
        multireddit._author = r.user.name
        if len(multireddit.subreddits) >= 90:
            continue
        try:
            r.modhash = 'newsletters'
            multireddit.add_subreddit(subreddit)
        except praw.errors.HTTPException as exc:
            if exc.response.status_code == 409:
                # The multi is full
                # Already checked for len but just in case...
                pass
            else:
                raise
        else:
            # Addition was successful, break the for loop
            break
    else:
        # No open multi was found
        r.modhash = 'newsletters'
        multireddit = create_multireddit()
        multireddit.add_subreddit(subreddit)

    log.info('Added /r/%s to /m/%s', subreddit, multireddit.name)

def add_subscription(user, subreddit, bypass_pph=False):
    user = normalize(user)
    subreddit = normalize(subreddit)
    try:
        # Using fetch=True will cause invalid subreddits to error immediately.
        subreddit = r.get_subreddit(subreddit, fetch=True).display_name
    except (
            praw.errors.Forbidden,
            praw.errors.InvalidSubreddit,
            praw.errors.NotFound,
            praw.errors.OAuthException,
            praw.errors.RedirectException,
            ):
        log.info('Subreddit %s does not exist', subreddit)
        return (MESSAGE_SUBREDDIT_FAIL % subreddit)

    subreddit = normalize(subreddit)
    if get_subscriptions(user=user, subreddit=subreddit):
        log.info('%s is already subscribed to %s', user, subreddit)
        return (MESSAGE_SUBSCRIBE_ALREADY % subreddit)

    if not bypass_pph:
        pph = get_posts_per_hour(subreddit)
        if pph > MAX_SUBSCRIPTION_POSTS_PER_HOUR:
            return (MESSAGE_SUBSCRIBE_BLACKLISTED % subreddit)

    add_subreddit_to_multireddit(subreddit)

    cur.execute('INSERT INTO subscribers VALUES(?, ?)', [user, subreddit])
    sql.commit()
    log.info('%s has subscribed to %s', user, subreddit)
    return (MESSAGE_SUBSCRIBE % subreddit)

def add_to_spool(user, message, do_commit=True):
    '''
    Spool a message to be sent at a later time by the spool handler.
    This keeps message sending separate from other operations and helps
    isolate error handling.
    '''
    if isinstance(user, praw.objects.Redditor):
        user = user.name
    user = user.lower()
    message = message.strip()
    cur.execute('SELECT * FROM spool WHERE name == ? AND message == ?', [user, message])
    if cur.fetchone():
        return False
    cur.execute('INSERT INTO spool VALUES(?, ?)', [user, message])
    if do_commit:
        sql.commit()
    return True

def broadcast(message):
    '''
    Spool this message for *ALL* users.
    '''
    subscriptions = get_subscriptions(user=None, subreddit=None)
    usernames = [item[SQL_USERNAME] for item in usernames]
    usernames = set(usernames)
    messages = 0
    for username in usernames:
        new_message = add_to_spool(username, message)
        if new_message:
            messages += 1
    log.info('Added %d messages to the spool.', messages)

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
        # cur.execute('SELECT * FROM subscribers')
        # fetch = cur.fetchall()
        # fetch = [f[0].lower() for f in fetch]
        # userlist = list(set(fetch))
        subscriptions = get_subscriptions()
        userlist = list(set(s[SQL_USERNAME] for s in subscriptions))
        subreddits = list(set(s[SQL_SUBREDDIT] for s in subscriptions))
        subreddits = '+'.join(subreddits)
        subreddits = 'ALL REDDITS: /r/' + subreddits + '\n\n'
        results.append(subreddits)
    for user in userlist:
        subreddits = get_subscriptions(user=user)
        subreddits.sort(key=str.lower)
        if len(subreddits) > 0:
            if len(subreddits) > 1:
                subreddits.append('+'.join(subreddits))
            subreddits = [('/r/%s/new' % f) for f in subreddits]
            subreddits = '\n\n'.join(subreddits)
            if get_all_users:
                subreddits = '/u/' + user + '\n\n' + subreddits + '\n\n&nbsp;\n\n'
            results.append(subreddits)

    if len(results) == 0:
        results = MESSAGE_REPORT_EMPTY
    else:
        results = '\n\n'.join(results)
    return results

def count_subscriptions():
    cur.execute('SELECT COUNT(*) FROM subscribers')
    return cur.fetchone()[0]

def create_multireddit():
    '''
    Create a new multireddit with a random name. Return the new object.
    '''
    for retry in range(10):
        new_multi = uid(MULTIREDDIT_NAME_LENGTH)
        try:
            # In case the planets align
            existing = r.get_multireddit(SELF_USERNAME, new_multi)
            existing.id
        except praw.errors.NotFound:
            break
    else:
        raise Exception('Couldnt create a unique multireddit')
    multireddit = r.create_multireddit(new_multi)
    log.info('Created /m/%s', multireddit.name)
    return multireddit

def drop_from_spool(name, message):
    cur.execute('DELETE FROM spool WHERE name == ? AND message == ?', [name, message])
    sql.commit()

def drop_subscription(user, subreddit, do_commit=True):
    user = normalize(user)
    subreddit = normalize(subreddit)
    if user is None:
        # This happens on 403 Forbidden when making newsletters
        log.info('Removing all subscriptions to /r/%s', subreddit)
        cur.execute('DELETE FROM subscribers WHERE LOWER(reddit) == ?', [subreddit])
        return ''

    if subreddit == 'all':
        subreddits_to_remove = []
        subscriptions = get_subscriptions(user=user)
        subreddits_to_remove.extend(subscriptions)
        if subscriptions:
            cur.execute('DELETE FROM subscribers WHERE LOWER(name) == ?', [user])
            if do_commit:
                sql.commit()
            log.info('%s has unsubscribed from everything', user)
            for subreddit in subreddits_to_remove:
                remove_subreddit_from_multireddit(subreddit)
            return MESSAGE_UNSUBSCRIBE_ALL
        else:
            log.info('%s doesnt have any subscriptions', user)
            return MESSAGE_UNSUBSCRIBE_ALREADY_ALL

    subscription = get_subscriptions(user=user, subreddit=subreddit)
    if subscription:
        cur.execute('DELETE FROM subscribers WHERE LOWER(name) == ? AND LOWER(reddit) == ?', [user, subreddit])
        if do_commit:
            sql.commit()
        log.info('%s has unsubscribed from %s', user, subreddit)
        remove_subreddit_from_multireddit(subscription[SQL_SUBREDDIT])
        return (MESSAGE_UNSUBSCRIBE % subreddit)
    else:
        log.info('%s is already unsubscribed from %s', user, subreddit)
        return (MESSAGE_UNSUBSCRIBE_ALREADY % subreddit)

def flag_for_deletion(username, seconds_from_now, message=None, do_commit=True):
    '''
    Flag the user to be dropped from the database. They must respond with a message
    containing the command "keep" within `seconds_from_now` or else all of their
    subscriptions will be deleted.

    If the user is already flagged, update their parameters.
    '''
    username = normalize(username)
    warned_at = int(get_now().timestamp())
    delete_at = int(warned_at + seconds_from_now)

    cur.execute('SELECT * FROM flag_deletion WHERE username == ?', [username])
    fetch = cur.fetchone()
    if fetch is None:
        cur.execute('INSERT INTO flag_deletion VALUES(?, ?, ?)', [username, warned_at, delete_at])
    else:
        cur.execute(
            'UPDATE flag_deletion SET warned_at = ?, delete_at = ? WHERE username == ?',
            [warned_at, delete_at, username]
        )

    if message is not None:
        add_to_spool(username, message, do_commit=False)

    if do_commit:
        sql.commit()

def format_post(submission):
    try:
        author = '/u/' + submission.author.name
    except AttributeError:
        author = "[deleted]"

    subreddit = '/r/' + submission.subreddit.display_name
    title = submission.title
    title = title.replace(']', '\]').replace('[', '\[')
    link = 'https://old.reddit.com/comments/' + submission.id

    template = MESSAGE_POSTFORMAT.format(
        author=author,
        subreddit=subreddit,
        title=title,
        link=link,
        )
    return template

def fetchgenerator(cur):
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
    log.debug('Getting PPH for /r/%s', subreddit)
    subreddit = r.get_subreddit(subreddit)
    # Any 403 errors will be caught by the calling function.
    submissions = list(subreddit.get_new())
    if len(submissions) < 2:
        return 0
    newest = submissions[0]
    oldest = submissions[-1]
    agediff = (newest.created_utc - oldest.created_utc) / 3600
    pph = len(submissions) / agediff
    return pph

def get_now():
    return datetime.datetime.now(datetime.timezone.utc)

def get_subscriptions(user=None, subreddit=None):
    '''
    Return subscriptions matching the parameters.

    user  | subreddit | return value
    ------|-----------|---------------------------------------------------------
    None  | None      | list of all (user, sub) pairs.
    '...' | None      | list of all subreddits this user subscribes to.
    None  | '...'     | list of all users subscribed to this subreddit.
    '...' | '...'     | the (user, sub) tuple if that user is subscribed there,
                        or None if he is not.
    '''
    user = normalize(user)
    subreddit = normalize(subreddit)
    if user is None and subreddit is None:
        cur.execute('SELECT * FROM subscribers')
        mode = 'everybody'
    elif user is None:
        cur.execute('SELECT name FROM subscribers WHERE reddit == ?', [subreddit])
        mode = 'portion'
    elif subreddit is None:
        cur.execute('SELECT reddit FROM subscribers WHERE name == ?', [user])
        mode = 'portion'
    else:
        cur.execute('SELECT * FROM subscribers WHERE name == ? AND reddit == ?', [user, subreddit])
        mode = 'individual'

    fetch = cur.fetchall()
    if mode == 'portion':
        fetch = [f[0] for f in fetch]
        fetch = list(set(fetch))
        fetch.sort()
    if mode == 'individual':
        if len(fetch) > 0:
            fetch = fetch[0]
        else:
            fetch = None

    return fetch

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
    is_admin = author_lower in ADMINS
    body = pm.body.lower()
    lines = body.split('\n\n')


    if len(lines) > 10 and author_lower not in ADMINS:
        results = MESSAGE_TOOLONG + MESSAGE_FOOTER
        return results

    for line in lines:
        words = line.replace(', ', ' ')
        words = words.replace(',', ' ')
        words = words.replace('+', ' ')
        words = words.split(' ')
        words = [word for word in words if word != '']

        if len(words) == 0:
            continue

        command = words[0]
        arguments = words[1:]

        # Cheaty way of guaranteeing at least 1 loop.
        if len(arguments) == 0:
            arguments.append('')

        log.info('%s %s', command, arguments)
        for argument in arguments:
            log.info(argument)
            argument = argument.replace(',', '')
            argument = argument.replace(' ', '')
            log.info('%s : %s - %s', author, command, argument)

            if command == 'report':
                status = MESSAGE_REPORT_REQUEST + '\n\n'
                status += build_report(author)
                results.append(status)
                break

            elif command == 'keep':
                status = MESSAGE_DELETION_REDEEMED + '\n\n'
                unflag_for_deletion(author)
                results.append(status)
                break

            elif command == 'reportall' and is_admin:
                status = MESSAGE_REPORT_ALL + '\n\n'
                status += build_report(None)
                results.append(status)
                break

            elif command == 'kill' and is_admin:
                pm.mark_as_read()
                mail_admins_now('bot is being turned off')
                quit()

            elif command == 'operatornotify' and is_admin:
                pm.mark_as_read()
                log.error('Testing operatornotify')
                break

            if not argument:
                # We've reached an argument-based function with
                # no argument, skip.
                continue

            if command == 'subscribe':
                status = add_subscription(author, argument)
                results.append(status)

            elif command == 'unsubscribe':
                status = drop_subscription(author, argument)
                results.append(status)

            if not is_admin:
                # We've reached an admin function with no admin, skip.
                continue

            if command == 'forcesubscribe':
                argument = argument.split('.')
                user = argument[0]
                subreddit = argument[1]
                add_subscription(user, subreddit, bypass_pph=True)
                status = (MESSAGE_SUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
                results.append(status)

            elif command == 'forceunsubscribe':
                argument = argument.split('.')
                user = argument[0]
                subreddit = argument[1]
                drop_subscription(user, subreddit)
                status = (MESSAGE_UNSUBSCRIBE_FORCE % (user, subreddit)) + '\n\n'
                results.append(status)

            elif command == 'reportuser':
                status = (MESSAGE_REPORT_USER % argument) + '\n\n'
                status += build_report(argument)
                results.append(status)

    if len(results) == 0:
        return None

    results = '\n\n_____\n\n'.join(results)
    if len(results) > 9900:
        results = results[:9900]
        results += '\n\n' + MESSAGE_MESSAGE_LONG
    results += MESSAGE_FOOTER
    return results

def mail_admins_now(message):
    for admin in ADMINS:
        r.send_message(admin, MESSAGE_SUBJECT, message)

def mail_admins_spool(message):
    for admin in ADMINS:
        add_to_spool(admin, message)

def manage_deletions():
    '''
    Look for users who are flagged for removal, drop
    their subscriptions, and spool a message.
    '''
    log.info('Managing deletions.')

    now = get_now().timestamp()

    cur.execute('SELECT username, warned_at FROM flag_deletion WHERE delete_at < ?', [now])
    flagged_users = cur.fetchall()

    # To keep only 1 query running at a time, this list stores names
    # so we can remove them all at the end.
    to_unflag = []

    for (username, warned_at) in flagged_users:
        warned_at = int(warned_at)

        subreddits = get_subscriptions(user=username)
        if len(subreddits) > 0:
            warned_at = datetime.datetime.utcfromtimestamp(warned_at)
            warned_at = warned_at.strftime('%B %d %Y')
            subreddits = [f'/r/{s}' for s in subreddits]
            subreddits = ', '.join(subreddits)

            message = MESSAGE_DELETION_DROPPED.format(
                username=username,
                warned_at=warned_at,
                subreddits=subreddits,
            )
            message += MESSAGE_FOOTER

            log.info('DROPPING %s', username)
            add_to_spool(username, message, do_commit=False)
            drop_subscription(username, 'all', do_commit=False)

        to_unflag.append(username)

    for username in to_unflag:
        unflag_for_deletion(username, do_commit=False)
    sql.commit()

def manage_inbox():
    log.info('Managing inbox.')
    r.evict(r.config['unread'])
    messages = list(r.get_unread(limit=None))
    for message in messages:
        try:
            author = message.author.name
        except AttributeError:
            continue

        try:
            interpretation = interpret_message(message)
            if interpretation and NOSEND is False:
                add_to_spool(author, interpretation)
        except Exception:
            traceback.print_exc()
        message.mark_as_read()

def manage_posts():
    '''
    Build newsletters for each user.

    1. Get ALL of the subscriptions from the database into a dict of the form
       {
           username: [subreddit, subreddit, ...],
       }
    
    2. Check the /new queue of each unique subreddit and add the submissions
       into a dict of the form
       {
           subreddit: [submission, submission, ...],
       }
    
    3. For each user, take the lists from the dictionary for the subreddits they
       are subscribed to, and compile a newsletter.

    Nothing is written into the database until the very end.
    '''

    # Compile sets of all our subscribers
    log.info('Managing subscriptions.')
    subreddits_per_user = {}
    users_per_subreddit = {}
    all_subreddits = set()

    for subscription in get_subscriptions():
        user = normalize(subscription[SQL_USERNAME])
        subreddit = normalize(subscription[SQL_SUBREDDIT])

        subreddits_per_user.setdefault(user, set())
        subreddits_per_user[user].add(subreddit)
        users_per_subreddit.setdefault(subreddit, set())
        users_per_subreddit[subreddit].add(user)

        all_subreddits.add(subreddit)

    all_subreddits = list(all_subreddits)
    all_subreddits.sort(key=str.lower)

    # Collect /new for all of the subreddits
    r.handler.clear_cache()
    total_submissions = []
    my_multireddits = r.get_my_multireddits()
    for multireddit in my_multireddits:
        log.info('Checking /m/%s' % multireddit.name)
        # Reddit has introduced a bug which causes incorrect multireddit URLs.
        multireddit._url = 'https://api.reddit.com/me/m/%s/' % multireddit.name
        multireddit._author = r.user.name
        total_submissions.extend(multireddit.get_new(limit=100))
    total_submissions.sort(key=lambda x: x.created_utc, reverse=True)

    # Discard old submissions, and sort the new ones into their subreddit bucket.
    # Format them for the newsletter.
    keep_submissions = []
    submissions_per_subreddit = {}
    formatted_submissions = {}
    for submission in total_submissions:
        cur.execute('SELECT * FROM oldposts WHERE id == ?', [submission.id])
        if cur.fetchone():
            continue

        subreddit = normalize(submission.subreddit.display_name)
        keep_submissions.append(submission)
        submissions_per_subreddit.setdefault(subreddit, list())
        submissions_per_subreddit[subreddit].append(submission)
        formatted_submissions[submission.id] = format_post(submission)

    log.info('Found %d new submissions', len(keep_submissions))

    if len(keep_submissions) == 0:
        return

    # Now, go through each user and take the submission list
    # from the submissions_per_subreddit dict, then compile their message
    # and add it to the spool.
    log.info('Compiling per-user newsletters.')

    for (user, users_subreddits) in subreddits_per_user.items():
        submissions_for_user = []
        for subreddit in users_subreddits:
            if subreddit in submissions_per_subreddit:
                submissions_for_user.extend(submissions_per_subreddit[subreddit])

        if len(submissions_for_user) == 0:
            continue

        submissions_for_user = submissions_for_user[:MAX_PER_MESSAGE]
        submissions_for_user = [formatted_submissions[x.id] for x in submissions_for_user]
        message = MESSAGE_NEW_POSTS
        message += '\n\n'.join(submissions_for_user)
        message += MESSAGE_FOOTER
        log.info('/u/%s gets %d new posts.', user, len(submissions_for_user))
        if NOSEND:
            log.info('nosend')
        else:
            # We'll do one big commit at the end
            add_to_spool(user, message, do_commit=False)

    # Finally, mark all the submissions in the database.
    for submission in keep_submissions:
        cur.execute('INSERT INTO oldposts VALUES(?)', [submission.id])
    sql.commit()


        # try:
        #     submissions = list(subreddit_obj.get_new(limit=100))
        # except praw.errors.Forbidden:
        #     # Subreddit has become private or banned?
        #     message = MESSAGE_UNSUBSCRIBE_PRIVATIZED % subreddit
        #     message += MESSAGE_FOOTER
        #     for user in users_per_subreddit[subreddit]:
        #         add_to_spool(user, message, do_commit=False)
        #     # Drop all subcscriptions to this subreddit.
        #     drop_subscription(user=None, subreddit=subreddit, do_commit=True)
        #     submissions_per_subreddit[subreddit] = []
        #     continue    

def manage_spool():
    '''
    Send all the messages from the spool.
    '''
    log.info('Managing spool.')
    if NOSEND:
        log.info('nosend')
        return

    if DROPSPOOL:
        log.info('dropspool')
        sql.execute('DELETE FROM spool')
        sql.commit()
        return

    spool = sql.execute('SELECT name, message FROM spool').fetchall()

    if not spool:
        return

    for (user, message) in spool:
        preview = message[:30].replace('\n', ' ')
        log.info('Mailing /u/%s: %s...', user, preview)
        try:
            r.send_message(user, MESSAGE_SUBJECT, message, captcha=None)
        except (praw.errors.InvalidUser, praw.errors.APIException) as exc:
            if isinstance(exc, praw.errors.InvalidUser):
                reason = 'praw.errors.invaliduser'
            if isinstance(exc, praw.errors.APIException):
                if exc.error_type not in ['INVALID_USER', 'USER_DOESNT_EXIST', 'NOT_WHITELISTED_BY_USER_MESSAGE']:
                    raise
                if exc.error_type == 'NOT_WHITELISTED_BY_USER_MESSAGE':
                    # 2021-05-14 Reddit has changed something on their end and
                    # lots of users are suddenly raising this exception.
                    # I don't want to delete all of their subscriptions but
                    # we're gonna have to drop this message.
                    drop_from_spool(user, message)
                    continue
                reason = exc.error_type
            # The user is deleted, so remove all of their subscriptions.
            # Any other exceptions will be uncaught, meaning the message
            # will remain in the database safe for next time.
            log.warning('Message to /u/%s failed because of %s.', user, reason)
            drop_subscription(user, 'all')

        drop_from_spool(user, message)
    sql.commit()

def normalize(text):
    '''
    Lowercase it, and remove /u/, /r/.
    '''
    if text is None:
        return None
    text = text.lower()
    text = text.replace('/u/', '')
    text = text.replace('u/', '')
    text = text.replace('/r/', '')
    text = text.replace('r/', '')
    return text

def operatornotify_override(subject, body=''):
    return mail_admins_now(body)
operatornotify.notify = operatornotify_override

def remove_subreddit_from_multireddit(subreddit, only_unused=True):
    '''
    Go through our multireddits and remove this subreddit from them.

    Keep `only_unused` True to make sure you don't remove an active subscription.
    '''
    subreddit = normalize(subreddit)
    if get_subscriptions(subreddit=subreddit):
        # Someone else needs this
        return

    my_multireddits = r.get_my_multireddits()
    for multireddit in my_multireddits:
        if any(subreddit == s.display_name.lower() for s in multireddit.subreddits):
            r.modhash = 'newsletters'
            multireddit.remove_subreddit(subreddit)

        if len(multireddit.subreddits) <= 1:
            # This must have been the only subreddit in there.
            # The count is not updated by PRAW when removing a sub,
            # so the len is whatever it was when we fetched it. Thus 1.
            log.info('Deleting /m/%s', multireddit.name)
            multireddit.delete()

    log.info('Removed /r/%s from multireddits', subreddit)

def uid(length=8):
    '''
    Generate a urandom hex string of `length` characters.
    '''
    import os
    import math
    identifier = ''.join('{:02x}'.format(x) for x in os.urandom(math.ceil(length / 2)))
    if len(identifier) > length:
        identifier = identifier[:length]
    return identifier

def unflag_for_deletion(username, do_commit=True):
    username = normalize(username)
    cur.execute('DELETE FROM flag_deletion WHERE username == ?', [username])
    if do_commit:
        sql.commit()

def main_forever():
    while True:
        try:
            main_once()
            log.info('Sleeping %d seconds.\n\n\n', WAIT)
            time.sleep(WAIT)
        except KeyboardInterrupt:
            return

def main_once():
    r.handler.clear_cache()
    try:
        manage_inbox()
        log.info('---')
        manage_deletions()
        log.info('---')
        manage_posts()
        log.info('---')
        manage_spool()
        log.info('---')
    except KeyboardInterrupt:
        raise
    except requests.exceptions.ConnectionError:
        log.info('Request raised ConnectionError')
    except requests.exceptions.Timeout:
        log.info('Request raised Timeout')
    except (requests.exceptions.HTTPError, praw.errors.HTTPException) as exc:
        if isinstance(exc, requests.exceptions.HTTPError):
            response = exc.response
        elif isinstance(exc, praw.errors.HTTPException):
            response = exc._raw
        status = response.status_code
        log.info('Request raised %d', status)
        if status == 500:
            pass
        if status == 503:
            pass
        else:
            message = '\n\n'.join([
                'Newsletterly encountered an unhandled HTTP status:',
                str(exc),
                str(response),
                traceback.format_exc(),
            ])
            log.error(message)
    except Exception as exc:
        message = '\n\n'.join([
            'Newsletterly encountered an unhandled exception:',
            traceback.format_exc(),
        ])
        log.error(message)
    log.info('%d active subscriptions', count_subscriptions())

def main(argv):
    global r
    global NOSEND
    global DROPSPOOL

    argv = vlogging.main_level_by_argv(argv)

    handler = operatornotify.LogHandler(subject='Newsletterly', notify_every_line=True)
    handler.setLevel(vlogging.WARNING)
    handler.setFormatter(vlogging.Formatter('{levelname}:{name}:{message}', style='{'))
    vlogging.getLogger().addHandler(handler)

    NOSEND = 'nosend' in [x.replace('-', '') for x in sys.argv]
    if NOSEND:
        log.info('NOSEND active!')

    DROPSPOOL = 'dropspool' in [x.replace('-', '') for x in sys.argv]
    if DROPSPOOL:
        log.info('DROPSPOOL active!')

    r = login()

    return main_forever()

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
