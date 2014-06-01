import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
RECIPIENT = ""
#The username that will receive this PM. It can be the same as USERNAME if you want to
MTITLE = ""
#This will be the title of the PM that you get
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
PARENTSTRING = ["phrase 1", "phrase 2", "phrase 3", "phrase 4"]
#These are the words that you are looking for
MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW will download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu()
    PASSWORD = bot.getp()
    USERAGENT = bot.geta()
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
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = "[DELETED]"
        plink = post.permalink
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            try:
                cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
                ptitle = post.title.lower()
                try:
                    ptext = post.selftext.lower()
                except AttributeError:
                    ptext = "0"
                if any(key.lower() in ptitle for key in PARENTSTRING) or any(key.lower() in ptext for key in PARENTSTRING):
                    print('Found ' + pid + ' by ' + pauthor)
                    r.send_message(RECIPIENT, MTITLE, pauthor + ' has said one of your keywords.\n\n[Find it here.](' + plink + ')', captcha=None)

            except IndexError:
                pass
    sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured: ', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)