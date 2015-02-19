#/u/GoldenSights
import traceback
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
SEARCHTITLE = True
SEARCHTEXT = False
#Should the bot check within the title?
#Should the bot check within the selftext?
KEYWORDS = ["phrase 1", "phrase 2", "phrase 3", "phrase 4"]
#These are the words you are looking for.
#Make empty to reply to ANY post that also matches keyauthor
KEYAUTHORS = ["GoldenSights"]
#These are the names of the authors you are looking for
#Any authors not on this list will not be replied to.
#Make empty to allow anybody
REPLYSTRING = "Hi hungry, I'm dad"
#This is the word you want to put in reply
MAXPOSTS = 100
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


def scansub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name.lower()
        except AttributeError:
            pauthor = '[DELETED]'
        if KEYAUTHORS == [] or any(auth.lower() == pauthor for auth in KEYAUTHORS):
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                pbody = ''
                if SEARCHTITLE:
                    pbody += post.title + ' '
                if SEARCHTEXT:
                    pbody += post.selftext
                if KEYWORDS == [] or any(key.lower() in pbody.lower() for key in KEYWORDS):
                    print('Replying to ' + pid + ' by ' + pauthor)
                    post.add_comment(REPLYSTRING)
    sql.commit()


while True:
    try:
        scansub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)