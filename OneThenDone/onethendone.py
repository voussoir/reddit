#/u/GoldenSights
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

SENDMESSAGE = True
#Do you want to send them a message indicating the OneThenDone rule? Use True or False, with capitals, no quotations
MESSAGETITLE = "Your /r/OneThenDone post has been processed"
MESSAGEBODY = "Your fate has been sealed. From now on, any submissions you make to /r/OneThenDone will be removed."
#If SENDMESSAGE is True, this will be sent as a PM when they make their submission
#Remember that it follows markdown formatting, where "\n" will represent hitting Enter

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
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT, USERNAME TEXT)')
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
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            try:
                success = False
                pauthor = post.author.name
                cur.execute('SELECT * FROM oldposts WHERE USERNAME=?', [pauthor])
                if not cur.fetchone():
                    print(pid, pauthor + ': Successful submission.')
                    if SENDMESSAGE:
                        pass
                        try:
                            r.send_message(pauthor, MESSAGETITLE, MESSAGEBODY, captcha=None)
                            success = True
                            pass
                        except:
                            print(pid, 'Message failed to send. Will not mark in database')
                    else:
                        success = True
                else:
                    print(pid, pauthor + ': Duplicate submission, removing')
                    success = True
                    post.remove()
                if success:
                    cur.execute('INSERT INTO oldposts VALUES(?, ?)', [pid, pauthor])
            except AttributeError:
                pauthor = '[DELETED]'
                print(pid, 'Deleted Author, ignoring')
        sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)