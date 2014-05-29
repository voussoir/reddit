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
RESPONSE = "I have detected some mobile links in your comment. Here are the non-mobile clickables:\n\n"
#This is what the bot says right before all the fixed links
MOBILES = ["http://m.", "http://en.m.", "http://i.reddit."]
#These are the different forms of mobile links. To handle each one, scroll down to line 70.
MAXPOSTS = 100
#This is how many posts you want to retreieve all at once. PRAW will download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getuG()
    PASSWORD = bot.getpG()
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
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        corrections = []
        pid = post.id
        try:
            pauthor = post.author.name
        except AttributeError:
            pauthor = '[DELETED]'
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)
            pbody = post.body
            pbodysplit = pbody.split()
            for word in pbodysplit:
                if any(mobile in word for mobile in MOBILES):
                    word = word.replace('http://m.', 'http://')
                    word = word.replace('http://i.reddit', 'http://reddit')
                    word = word.replace('http://en.m.', 'http://en.')
                    corrections.append(word)
            if len(corrections) > 0:
                print(pid + ' by ' + pauthor + ': Fixed ' + str(len(corrections)) + ' links.')
                f = '\n\n'.join(corrections)
                post.reply(RESPONSE + f)


    sql.commit()


while True:
    scanSub()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)