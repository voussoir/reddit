# /u/Goldensights

import datetime
import json
import praw
import sqlite3
import sys
import textwrap

'''USER CONFIG'''
USERAGENT = ""
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
WIDTH = 120
DO_TEXTWRAP = True
# Wrap the text to line width of WIDTH
SEPARATOR = '\n\n*%s*\n\n' % ('='*(WIDTH-2))
STRFTIME = '%d %b %Y %H:%M:%S'
MODMAIL = True
''' All done! '''

if MODMAIL:
    dbname = 'messagearchive_mod.db'
else:
    dbname = 'messagearchive.db'
sql = sqlite3.connect(dbname)
cur = sql.cursor()
cur.execute(('CREATE TABLE IF NOT EXISTS messages('
             'idstr TEXT,'
             'parent_id TEXT,'
             'author TEXT,'
             'dest TEXT,'
             'subject TEXT,'
             'body TEXT,'
             'created INT,'
             'first_message TEXT,'
             'link_id TEXT)'))

cur.execute('CREATE INDEX IF NOT EXISTS idindex ON messages(idstr)')

SQL_COLUMNCOUNT = 9
SQL_IDSTR = 0
SQL_PARENT_ID = 1
SQL_AUTHOR = 2
SQL_DEST = 3
SQL_SUBJECT = 4
SQL_BODY = 5
SQL_CREATED = 6
SQL_FIRST_MESSAGE = 7
SQL_LINK_ID = 8

#####

try:
    import bot
    USERAGENT = bot.aG
    APP_ID = bot.oG_id
    APP_SECRET = bot.oG_secret
    APP_URI = bot.oG_uri
    APP_REFRESH = bot.oG_scopes['all']
except ImportError:
    pass


def fetchgenerator():
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def smartinsert(item, nosave=False):
    '''
    Given an inboxed item, compile the necessary information into a
    database row.

    Return the number of new items (only 0 or 1)
    '''
    cur.execute('SELECT * FROM messages WHERE idstr=?', [item.fullname])
    if cur.fetchone():
        return 0
        # not doing any sql updates for this bot
    data = [None] * SQL_COLUMNCOUNT
    data[SQL_IDSTR] = item.fullname
    if not bool(item.parent_id):
        parent = None
    else:
        parent = item.parent_id
    data[SQL_PARENT_ID] = parent
    data[SQL_AUTHOR] = item.author.name if item.author else None
    data[SQL_DEST] = item.dest
    data[SQL_SUBJECT] = item.subject
    data[SQL_BODY] = item.body
    data[SQL_CREATED] = int(item.created_utc)
    if not bool(item.context):
        link = None
    elif '/comments/' in item.context:
        link = item.context.split('/comments/')[1].split('/')[0]
        link = 't3_' + link
    data[SQL_FIRST_MESSAGE] = item.first_message_name
    data[SQL_LINK_ID] = link
    cur.execute('INSERT INTO messages VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)', data)
    if nosave is False:
        sql.commit()
    return 1

def fetch_mail():
    print('Logging in.')
    r = praw.Reddit(USERAGENT)
    r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
    r.refresh_access_information(APP_REFRESH)
    new = 0
    if MODMAIL:
        print('Checking modmail...')
        mail = list(r.get_mod_mail(limit=None))
        mail = praw.helpers.flatten_tree(mail)
        for item in mail:
            new += smartinsert(item)
    else:
        print('Checking inbox... be patient')
        for item in r.get_inbox(limit=None):
            new += smartinsert(item)
        print('Checking outbox...')
        for item in r.get_sent(limit=None):
            new += smartinsert(item)
    print('Collected %d new items.' % new)

def build_tree():
    print('Building message tree')
    cur.execute('SELECT * FROM messages ORDER BY first_message, idstr ASC')
    roots = {}
    for item in fetchgenerator():
        if item[SQL_PARENT_ID] is None:
            # For root messages
            roots[item[SQL_IDSTR]] = [item]
            continue
        if 't4_' not in item[SQL_PARENT_ID]:
            # For comment and submission replies
            if item[SQL_PARENT_ID] in roots:
                roots[item[SQL_PARENT_ID]].append(item)
            else:
                roots[item[SQL_PARENT_ID]] = [item]
            continue
        if 't4_' in item[SQL_PARENT_ID]:
            # For message replies
            if item[SQL_FIRST_MESSAGE] in roots:
                roots[item[SQL_FIRST_MESSAGE]].append(item)
            else:
                # Message replies where the root is beyond
                # the api limitation of 1,000 items.
                roots[item[SQL_FIRST_MESSAGE]] = [item]
            continue
    for root in roots:
        roots[root].sort(key=lambda x: (int(x[SQL_PARENT_ID].split('_')[1],
                                        36) if x[SQL_PARENT_ID] else 0,
                                        x[SQL_CREATED]))
    keys = list(roots.keys())
    keys.sort(key=lambda x: roots[x][0][SQL_CREATED], reverse=True)
    print('Found %d threads' % len(keys))
    return (keys, roots)

def render_txt(keys, roots):
    print('Rendering text')
    if MODMAIL:
        outfile = open('render_mod_txt.txt', 'w', encoding='utf-8')
    else:
        outfile = open('render_txt.txt', 'w', encoding='utf-8')
    threads = []
    for key in keys:
        threadtext = []
        depth = 1
        if 't3_' in key:
            depth = 1
            threadtext.append(('Submission %s received the '
                               'following replies:') % key)
        if 't1_' in key:
            depth = 1
            threadtext.append(('Comment %s received the '
                               'following replies:') % key)
        for item in roots[key]:
            itemtext = ''
            d = datetime.datetime.utcfromtimestamp(item[SQL_CREATED])
            d = d.strftime(STRFTIME)
            itemtext += '%s %s -> %s: %s %s\n' % (item[SQL_IDSTR],
                item[SQL_AUTHOR], item[SQL_DEST], d, item[SQL_SUBJECT])
            body = item[SQL_BODY]
            if DO_TEXTWRAP:
                # http://stackoverflow.com/a/26538082 ##########################
                body = '\n'.join(['\n'.join(textwrap.wrap(line, WIDTH-(4*depth),
                     break_long_words=True, replace_whitespace=False))##########
                     for line in body.split('\n')])#############################
                ################################################################
            body = body.replace('\n', '\n'+'\t'*depth)
            body = ('\t'*depth) + body
            itemtext += body
            threadtext.append(itemtext)
        threadtext = '\n\n-\n\n'.join(threadtext)
        threads.append(threadtext)
    threads = SEPARATOR.join(threads)
    outfile.write(threads)
    outfile.close()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Use either of:')
        print('> messagearchive.py fetch')
        print('> messagearchive.py render')
    if 'render' in sys.argv:
        render_txt(*build_tree())
    elif 'fetch' in sys.argv:
        fetch_mail()