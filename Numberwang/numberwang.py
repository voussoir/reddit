import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
REPLYSTRING = "That's Numberwang!"
#This is the word you want to put in reply
MAXPOSTS = 10
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        pbody = post.body
        pnum = pbody[-5:]
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            try:
                int(pnum)
                print(pid + ": " + pnum + ' is Numberwang!')
                post.reply(REPLYSTRING)
            except ValueError:
                pass
    
        cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
    sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)