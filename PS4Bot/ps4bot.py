import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys
import sqlite3

''''USER CONFIGURATION'''
USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = ""
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
MAXPOSTS = 10
#This is how many posts you want to retrieve all at once. PRAW will download 100 at a time.
WAIT = 600
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''





try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
except ImportError:
    pass
WAITS = str(WAIT)
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
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        ptitle = post.title
        pauthor = post.author.name
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            try:
                cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
                
                titlesplit = ptitle.split()
                for word in titlesplit:
                    if len(word) > 1 and word[0] == '#':
                        print(pid + ', ' + pauthor + ': ' + word)
                        hashtag = word[1:]
                        link = 'http://twitter.com/intent/tweet?button_hashtag=' + hashtag
                        post.add_comment('[Use this hashtag!](' + link + ')')

            except IndexError:
                pass
    sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)