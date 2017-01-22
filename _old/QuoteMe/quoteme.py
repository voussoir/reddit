#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
PARENTSTRING = ["don't quote me", "dont quote me"]
#These are the words you are looking for
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 10
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE INDEX IF NOT EXISTS oldpost_index ON oldposts(id)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        pbody = post.body
        pbody = pbody.replace('\n\n', '.\n\n>')
        if any(key.lower() in pbody.lower() for key in PARENTSTRING):
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
                pbodysplit = pbody.split('.')
                for sent in pbodysplit:
                    if any(key.lower() in sent.lower() for key in PARENTSTRING):
                        try:
                            pauthor = post.author.name
                            if pauthor != r.user.name:
                                response = ">" + sent + "\n\n- /u/" + pauthor
                                print('Replying to ' + pid + ' by ' + pauthor)
                                print(sent.strip())
                                post.reply(response)
                                break
                        except Exception:
                            print('Failed.')
    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 