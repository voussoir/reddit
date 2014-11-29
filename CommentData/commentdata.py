#/u/GoldenSights
import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import sys
import re

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
KEYWORDS = ["bot", "bots", "python"]
#These are the words you are looking for
FILENAME = "Keywords.txt"
#The name of the file to write the results to.
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.uG
    PASSWORD = bot.pG
    USERAGENT = bot.aG
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
    results = []
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        post.xauthor=pauthor
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            pbody = post.body.lower()
            for keyword in KEYWORDS:
                gex = "\\b%s\\b" % keyword.lower()
                if re.search(gex, pbody):
                    print('Found %s by %s' % (keyword, pauthor))
                    post.keyword = keyword
                    results.append(post)
                    break
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
    addtofile(results)
    sql.commit()

def addtofile(inputlist):
    if len(inputlist) > 0:
        print('Updating file...', end='')
        sys.stdout.flush()
        outfile = open(FILENAME, "a+")
        for item in inputlist:
            permalink = "http://reddit.com/r/%s/comments/%s/_/%s" %(
                item.subreddit.display_name, item.link_id[3:], item.id)
            item = "%s '%s' : %s" % (item.xauthor, item.keyword, permalink)
            print(item, file=outfile)
        outfile.close()
        print("Done.")

while True:
    try:
        scanSub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)

    