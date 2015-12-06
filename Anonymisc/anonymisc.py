#/u/GoldenSights
import praw
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

DISTINGUISH_COMMENTS = True
# Attempt to distinguish the comments we create. If it fails, continue normally.

COMMENT_FOOTER = '''
*This text is at the bottom of the message.*
'''

MARK_REPLIES_AS_READ = True
# When scanning the inbox, mark comments as read without performing any action
# on them, to keep the inbox clean.

MARK_OTHER_AS_READ = True
# Also mark PMs as read, even if they aren't commissions, 
# to keep the inbox clean.

COMMAND_WHITELIST = 'whitelist'
COMMAND_UNWHITELIST = 'unwhitelist'
COMMAND_SHOW_WHITELIST = 'show'
# For admin usage only

MESSAGE_UNWHITELIST_ALREADY = '%s was not on the whitelist to begin with.'
MESSAGE_UNWHITELIST_PASS = 'Removed %s from the whitelist.'
MESSAGE_WHITELIST_ALREADY = '%s is already on the whitelist.'
MESSAGE_WHITELIST_PASS = 'Added %s to the whitelist.'

ADMINS = ['GoldenSights', 'Unidan']

WAIT = 60
# The number of seconds between cycles. The bot is completely inactive during this time.
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

sql = sqlite3.connect('anonymisc.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS commissions(created INT, idstr TEXT, body TEXT, commissioner TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS whitelist(name TEXT)')

print('Logging in')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)
#r = bot.o7()

ADMINS = [admin.lower() for admin in ADMINS]

def anonymisc():
    print('Checking mail')
    unread = list(r.get_unread(limit=None))
    for message in unread:
        try:
            process_message(message)
        except:
            traceback.print_exc()
            print('Marking problematic message as read.')
            message.mark_as_read()
        print()

def process_message(message):
    print('Reading message %s' % message.fullname)
    if message.subreddit is not None:
        print('Ignoring message from subreddit')
        if MARK_OTHER_AS_READ:
            message.mark_as_read()
        return

    if not isinstance(message, praw.objects.Message):
        print('Ignoring comment reply')
        if MARK_REPLIES_AS_READ:
            message.mark_as_read()
        return

    if message.author == None:
        print('Ignoring deleted user')
        message.mark_as_read()
        return

    if len(message.body) == 0:
        # This shouldn't be possible but I'm paranoid.
        print('Empty message')
        message.mark_as_read()
        return

    author = message.author.name.lower()
    first_line = message.body.splitlines()[0]
    item_id = submission_comment_from_url(first_line)
    
    if item_id is None:
        if author in ADMINS:
            reply_text = do_admin_command(first_line)
            if reply_text is not None:
                print('Performed admin action')
                message.reply(reply_text)
                message.mark_as_read()
                return
        print('Could not find an item id or command')
        if MARK_OTHER_AS_READ:
            message.mark_as_read()
        return

    print('Found item id: %s' % item_id)
    item = r.get_info(thing_id=item_id)

    if item is None:
        print('Tried to fetch item but found nothing.')
        message.mark_as_read()
        return

    print('Fetched item successfuly from /r/%s' % item.subreddit.display_name)

    item_subreddit = item.subreddit.display_name.lower()
    verified_user = author in ADMINS
    verified_user = verified_user or user_in_whitelist(username=author, subreddit=item_subreddit)
    if verified_user is False:
        print('Rejecting unverified user.')
        if MARK_OTHER_AS_READ:
            message.mark_as_read()
        return

    text = message.body.replace(first_line, '')
    text = text.strip()
    text += '\n\n' + COMMENT_FOOTER
    print('Creating reply.')
    # I want to mark as read sooner rather than later,
    # so no exception cases result in infinite commenting.
    # Some commissions may be lost but that's better than the alternative.
    message.mark_as_read()
    if isinstance(item, praw.objects.Submission):
        reply = item.add_comment(text)
    elif isinstance(item, praw.objects.Comment):
        reply = item.reply(text)
    cur.execute('INSERT INTO commissions VALUES(?, ?, ?, ?)', [reply.created_utc, reply.fullname, reply.body, author])
    sql.commit()
    if DISTINGUISH_COMMENTS:
        try:
            reply.distinguish()
        except:
            pass
    message.reply(reply.permalink)
    print('Created %s' % reply.fullname)

def do_admin_command(line):
    '''
    This function does not check the validity of the supposed username or
    subreddit name that you're whitelisting. Any invalid characters are
    assumed to be valid.

    You're the owner of the bot, you should know what you're typing.
    '''
    line = line.lower()
    line = line.strip()
    words = line.split(' ')
    command = words[0]

    if command == COMMAND_SHOW_WHITELIST.lower():
        cur.execute('SELECT * FROM whitelist')
        results = [(item[0] + '  ')for item in cur.fetchall()]
        results.sort()
        results = '\n'.join(results)
        return results

    if len(words) <= 1:
        # All other commands require an argument.
        return None

    arguments = words[1:]
    responses = []
    for argument in arguments:
        # This way /r/ does not become //r/, and I don't have to do if-statements.
        argument = argument.replace('/u/', 'u/').replace('u/', '/u/')
        argument = argument.replace('/r/', 'r/').replace('r/', '/r/')
        if '/u/' not in argument and '/r/' not in argument:
            # Asssume that unspecified names are users.
            argument = '/u/' + argument

        already_exists = False
        cur.execute('SELECT * FROM whitelist WHERE name == ?', [argument])
        if cur.fetchone() is not None:
            already_exists = True

        if command == COMMAND_WHITELIST.lower():
            if already_exists:
                responses.append(MESSAGE_WHITELIST_ALREADY % argument)
                continue
            cur.execute('INSERT INTO whitelist VALUES(?)', [argument])
            responses.append(MESSAGE_WHITELIST_PASS % argument)

        elif command == COMMAND_UNWHITELIST.lower():
            if not already_exists:
                responses.append(MESSAGE_UNWHITELIST_ALREADY % argument)
                continue
            cur.execute('DELETE FROM whitelist WHERE name == ?', [argument])
            responses.append(MESSAGE_UNWHITELIST_PASS % argument)

    if len(responses) == 0:
        return None

    sql.commit()
    return '\n\n'.join(responses)

def submission_comment_from_url(url):
    if not all(part in url for part in ['reddit.com', '/r/', '/comments/']):
        return submission_from_shortlink(url)
    url = url.split('/comments/')[1]
    url = url.split('/')

    submissionid = 't3_' + url[0]
    try:
        int(submissionid[3:], 36)
    except ValueError:
        # If we can't find a submission id, we're not
        # going to try finding a comment because it's hard
        # to say what the user was even intending to do.
        return None

    if len(url) > 2 and url[2] != '':
        commentid = 't1_' + url[2]
    else:
        commentid = ''
    try:
        int(commentid[3:], 36)
    except ValueError:
        commentid = ''

    itemid = commentid or submissionid
    return itemid

def submission_from_shortlink(url):
    if 'redd.it/' not in url:
        return None
    submissionid = url.split('redd.it/')[1]
    try:
        int(submissionid, 36)
    except ValueError:
        return None

    submissionid = 't3_' + submissionid
    return submissionid

def user_in_whitelist(username, subreddit):
    cur.execute('SELECT * FROM whitelist WHERE name == ?', ['/u/' + username])
    if cur.fetchone() is not None:
        print('Found in whitelist')
        return True

    cur.execute('SELECT * FROM whitelist WHERE name == ?', ['/r/' + subreddit])
    if cur.fetchone() is None:
        return False

    print('/r/%s is whitelisted, checking mods.' % subreddit)
    return user_is_moderator(username, subreddit)

def user_is_moderator(username, subreddit):
    moderators = list(r.get_moderators(subreddit))
    for moderator in moderators:
        if not hasattr(moderator, 'name'):
            # Can this even happen? I don't know.
            continue
        if moderator.name.lower() == username:
            print('Verified moderator!')
            return True
    print('Not a moderator.')
    return False

if __name__ == '__main__':
    while True:
        try:
            anonymisc()
        except KeyboardInterrupt:
            print('Caught keyboard interrupt')
            quit()
        except:
            traceback.print_exc()
        print('Sleeping %d seconds' % WAIT)
        print()
        time.sleep(WAIT)