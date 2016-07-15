#/u/goldensights
import datetime
import praw
import time
import sqlite3
import traceback

''' USER CONFIGURATION '''

USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/

SUBREDDIT = "GoldTesting"
# Subreddit to scan for posts. For a single sub, use "subreddit"
# For multiple subreddits, use "sub1+sub2+..."

MAXPOSTS = 100
# How many submissions and comments (each) to collect on each cycle
# Can get up to 100 in a single request. Max 1000 per subreddit.

REQUIRED_RATIO = 2
# The required ratio of COMMENTS divided by SUBMISSIONS

REQUIRED_RATIO_DO_MODMAIL = False
REQUIRED_RATIO_MESSAGE_SUBREDDIT = "GoldTesting"
REQUIRED_RATIO_MESSAGE_SUBJECT = "SubmissionRatio warning"
REQUIRED_RATIO_MESSAGE_TEXT = '''
/u/{username} has fallen below the required ratio of {required}.
Their current ratio is {ratio:.2f}.

Please investigate.
'''
# When a user falls below the required threshold, should the bot notify the
# moderators?

PUSH_TO_WIKI = True
# Should the bot publish ratios on a wiki page?
PUSH_TO_WIKI_SUBREDDIT = "GoldTesting"
# The subreddit whose wiki page will receive the publish.
# This is separate from SUBREDDIT because SUBREDDIT can be multiple subs.
PUSH_TO_WIKI_PAGE = "heyo"
# The wiki page
PUSH_TO_WIKI_TEMPLATE_FILE = "wiki.txt"
# The base text for the wiki page.
PUSH_TO_WIKI_WAIT = 3600
# How many seconds between wiki publishes?

TABLE_SORT = 'ratio'
# How will the table on the wiki page be sorted. Pick one:
# 'username'
# 'submissions'
# 'comments'
# 'ratio'
TABLE_DESCENDING = True
# Should the table be greatest-first

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

SQL_USER_COLUMNS = [
    'username',
    'submissions',
    'comments',
    'warned',
]
SQL_USER = {key:index for (index, key) in enumerate(SQL_USER_COLUMNS)}

TABLE_TEMPLATE = '''
Username | Comments | Submissions | Ratio
:-       |       -: |          -: |    -:
{rows}
'''
ROW_TEMPLATE = '{username} | {comments} | {submissions} | {ratio:.2f}'

sql = sqlite3.connect('sql.db')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT, author TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(username TEXT, submissions INT, comments INT, warned INT)')
cur.execute('CREATE INDEX IF NOT EXISTS post_index ON oldposts(id)')
cur.execute('CREATE INDEX IF NOT EXISTS user_index ON users(username)')
sql.commit()

last_wiki_update = 0

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def build_table(table_sort=None, table_descending=None):
    table_sort = table_sort or TABLE_SORT
    if table_descending is None:
        table_descending = TABLE_DESCENDING
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    user_details = []

    for user in users:
        detail = {columnname: user[index] for (columnname, index) in SQL_USER.items()}
        user_details.append(detail)

    for detail in user_details:
        detail['ratio'] = detail['comments'] / max(detail['submissions'], 1)

    def key(x):
        if table_sort in x:
            entry = x[table_sort]
        else:
            entry = x['username']

        try:
            return entry.lower()
        except AttributeError:
            return entry

    user_details.sort(key=key, reverse=table_descending)

    rows = [format_row(detail) for detail in user_details]
    rows = '\n'.join(rows)
    table = TABLE_TEMPLATE.format(rows=rows)
    table = '\n\n{t}\n\n'.format(t=table)
    return table

def digest_posts(posts):
    '''
    Given a list of Submission and Comment objects, update the user data
    '''
    user_posts_map = posts_to_user_map(posts)

    for (username, user_posts) in user_posts_map.items():
        new_submissions = 0
        new_comments = 0
        for post in user_posts:
            cur.execute('SELECT * FROM oldposts WHERE id == ?', [post.fullname])
            if cur.fetchone():
                continue

            cur.execute('INSERT INTO oldposts VALUES(@id, @author)', [post.fullname, username])

            if isinstance(post, praw.objects.Submission):
                new_submissions += 1
            elif isinstance(post, praw.objects.Comment):
                new_comments += 1

        cur.execute('SELECT * FROM users WHERE username == ?', [username])
        user_detail = cur.fetchone()
        if user_detail is None:
            total_submissions = new_submissions
            total_comments = new_comments
            warned = False
            cur.execute('INSERT INTO users VALUES(@username, @submissions, @comments, @warned)', [username, total_submissions, total_comments, 0])
        else:
            total_submissions = new_submissions + user_detail[SQL_USER['submissions']]
            total_comments = new_comments + user_detail[SQL_USER['comments']]
            warned = user_detail[SQL_USER['warned']]
            cur.execute('UPDATE users SET submissions = ?, comments = ? WHERE username == ?', [total_submissions, total_comments, username])

        sql.commit()

def format_row(detail):
    row = ROW_TEMPLATE.format(
        username=detail['username'],
        comments=detail['comments'],
        submissions=detail['submissions'],
        ratio=detail['ratio'],
    )
    return row

def get_now(timestamp=True):
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        return now.timestamp()
    return now

def posts_to_user_map(posts):
    subreddits = SUBREDDIT.lower()
    subreddits = set(subreddits.split('+'))
    user_posts_map = {}
    for post in posts:
        if post.author is None:
            continue
        if post.subreddit.display_name.lower() not in subreddits:
            continue
        author = post.author.name
        user_posts_map.setdefault(author, [])
        user_posts_map[author].append(post)
    return user_posts_map

def scan(limit=None):
    limit = limit or MAXPOSTS
    print('Scanning /r/%s' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = []
    posts.extend(subreddit.get_new(limit=limit))
    posts.extend(subreddit.get_comments(limit=limit))

    digest_posts(posts)

def send_warnings():
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    for user in users:
        username = user[SQL_USER['username']]
        submissions = user[SQL_USER['submissions']]
        comments = user[SQL_USER['comments']]
        previous_warned = user[SQL_USER['warned']]
        ratio = comments / max(submissions, 1)

        if ratio < REQUIRED_RATIO:
            warned = True
        else:
            warned = False
        cur.execute('UPDATE users SET warned = ? WHERE username == ?', [warned, username])

        if warned and not previous_warned and REQUIRED_RATIO_DO_MODMAIL:
            print('Warning {username} for ratio {ratio:.2f}'.format(username=username, ratio=ratio))
            recipient = '/r/' + REQUIRED_RATIO_MESSAGE_SUBREDDIT
            subject = REQUIRED_RATIO_MESSAGE_SUBJECT
            text = REQUIRED_RATIO_MESSAGE_TEXT.format(
                username=username,
                required=REQUIRED_RATIO,
                ratio=ratio,
                )
            r.send_message(recipient, subject, text)
            sql.commit()
    sql.commit()

def update_wiki_page():
    global last_wiki_update
    now = get_now()

    if now - last_wiki_update < PUSH_TO_WIKI_WAIT:
        return

    print('Updating wiki page')
    with open(PUSH_TO_WIKI_TEMPLATE_FILE, 'r') as template_file:
        lines = [line.strip() for line in template_file]

    for (line_index, line) in enumerate(lines):
        if len(line) == 0:
            continue
        if line[0] == '#':
            # Blank out the comments
            lines[line_index] = ''
            continue
        if '__BUILDTABLE__' in line:
            table = build_table()
            lines[line_index] = line.replace('__BUILDTABLE__', table)
        if '__STRFTIME' in line:
            # If the user formatted their line badly, it's their fault.
            strf = line.split('__STRFTIME')[1]
            strf = strf.split('"')[1]
            timestamp = get_now(timestamp=False)
            timestamp = timestamp.strftime(strf)
            form = '__STRFTIME("' + strf + '")__'
            lines[line_index] = line.replace(form, timestamp)

    final = '\n\n'.join(lines)
    r.edit_wiki_page(PUSH_TO_WIKI_SUBREDDIT, PUSH_TO_WIKI_PAGE, final, reason=now)
    last_wiki_update = now


def main_once():
    try:
        scan()
        send_warnings()
        update_wiki_page()
    except Exception:
        traceback.print_exc()

def main_forever():
    while True:
        main_once()

if __name__ == '__main__':
    main_forever()