import sqlite3
import sys
import os

def old_new_name(text):
    new_name = text.replace('.original', '')
    old_name = new_name + '.original'
    return (old_name, new_name)

SQL_COLUMNCOUNT = 16
SQL_IDINT = 0
SQL_IDSTR = 1
SQL_CREATED = 2
SQL_SELF = 3
SQL_NSFW = 4
SQL_AUTHOR = 5
SQL_TITLE = 6
SQL_URL = 7
SQL_SELFTEXT = 8
SQL_SCORE = 9
SQL_SUBREDDIT = 10
SQL_DISTINGUISHED = 11
SQL_TEXTLEN = 12
SQL_NUM_COMMENTS = 13
SQL_FLAIR_TEXT = 14
SQL_FLAIR_CSS_CLASS = 15

databasename = sys.argv[1]

(old_name, new_name) = old_new_name(databasename)
if os.path.exists(new_name) and not os.path.exists(old_name):
    os.rename(new_name, old_name)

old_sql = sqlite3.connect(old_name)
old_cur = old_sql.cursor()

new_sql = sqlite3.connect(new_name)
new_cur = new_sql.cursor()

new_cur.execute(
    '''CREATE TABLE IF NOT EXISTS submissions(
    idint INT,
    idstr TEXT,
    created INT,
    self INT,
    nsfw INT,
    author TEXT,
    title TEXT,
    url TEXT,
    selftext TEXT,
    score INT,
    subreddit TEXT,
    distinguish INT,
    textlen INT,
    num_comments INT,
    flair_text TEXT,
    flair_css_class TEXT,
    augmented_at INT,
    augmented_count INT)''')
new_cur.execute(
    '''CREATE TABLE IF NOT EXISTS comments(
    idint INT,
    idstr TEXT,
    created INT,
    author TEXT,
    parent TEXT,
    submission TEXT,
    body TEXT,
    score INT,
    subreddit TEXT,
    distinguish TEXT,
    textlen INT)''')

new_cur.execute('CREATE INDEX IF NOT EXISTS submission_index ON submissions(idstr)')
new_cur.execute('CREATE INDEX IF NOT EXISTS comment_index ON comments(idstr)')

old_cur.execute('SELECT * FROM posts ORDER BY created ASC')
while True:
    item = old_cur.fetchone()
    if item is None:
        break
    #print('Moving', item[SQL_IDSTR])
    if item[SQL_IDSTR].startswith('t3_'):
        # All the new columns are the same, with two new: augmented_at, augmented_count
        postdata = item + (None, None)
        new_cur.execute('''INSERT INTO submissions VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', postdata)
    else:
        postdata = [
            item[SQL_IDINT],
            item[SQL_IDSTR],
            item[SQL_CREATED],
            item[SQL_AUTHOR],
            item[SQL_TITLE],
            item[SQL_URL],
            item[SQL_SELFTEXT],
            item[SQL_SCORE],
            item[SQL_SUBREDDIT],
            item[SQL_DISTINGUISHED],
            item[SQL_TEXTLEN],
        ]
        new_cur.execute('''INSERT INTO comments VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', postdata)
new_sql.commit()