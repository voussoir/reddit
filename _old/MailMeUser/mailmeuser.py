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
RECIPIENT = "75000"
#The username that will receive this PM. It can be your username if you want to
MTITLE = "0"
#This will be the title of the PM that you get
REDDITORS = ["Unidan", "GoldenSights"]
#This is the person or people you want to. Add or remove items from this list with commas serparating each.
MAXPOSTS = 10
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot
    USERAGENT = bot.geta()
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
    result = []
    for REDDITOR in REDDITORS:
        print('Searching '+ REDDITOR + '.')
        redditor = r.get_redditor(REDDITOR)
        posts = redditor.get_overview(limit=MAXPOSTS)
        for post in posts:
            pid = post.id
            plink = post.permalink
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                print('Found ' + pid + ' by ' + REDDITOR)
                result.append(REDDITOR + ' has made a comment or post. [Find it here.](' + plink + ')')
    if len(result) > 0:
        r.send_message(RECIPIENT, MTITLE, '\n\n'.join(result), captcha=None)
        print('Message sent')
    
    sql.commit()


while True:
    scanSub()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)