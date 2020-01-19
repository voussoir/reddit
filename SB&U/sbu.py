import sqlite3
import sys
import time
import traceback

sys.path.append('..\\SubredditBirthdays')
import sb

sys.path.append('..\\Usernames')
import un4

newnames_sql = sqlite3.connect('..\\Usernames\\newnames.db')
newnames_cur = newnames_sql.cursor()

def migrate():
    resume_from = int(open('latest.txt', 'r').read().strip())
    sb.cur.execute(
        'SELECT name, created FROM subreddits WHERE subreddit_type == 8 AND created >= ? ORDER BY created ASC',
        [resume_from]
    )
    f = sb.cur.fetchall()
    resume_from = f[-1][1]
    f = [x[0] for x in f]
    for x in f:
        newnames_cur.execute('INSERT INTO names3 VALUES(?)', [x])
    print('Moved %d records' % len(f))
    newnames_sql.commit()
    open('latest.txt', 'w').write(str(resume_from))

def run_newnames():
    while True:
        try:
            if newnames_cur.execute('SELECT count(*) from names3').fetchone() == 0:
                break
            un4.process_from_database('..\\Usernames\\newnames.db', 'names3', 'name', True)
        except sqlite3.OperationalError:
            raise
        except Exception:
            traceback.print_exc()
        time.sleep(60)

def run_modernize():
    while True:
        try:
            sb.modernize(limit=10000)
        except Exception:
            traceback.print_exc()
        time.sleep(60)
