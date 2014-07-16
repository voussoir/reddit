#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import random

'''USER CONFIGURATION'''

USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "GoldTesting"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."

TRIGGERSTRINGA = ["I summon you /u/" + USERNAME, "I summon you great /u/" + USERNAME, "I summon you " + USERNAME, "I summon you great " + USERNAME, "Dear great /u/" + USERNAME, "Dear great " + USERNAME, USERNAME + ", roll the 8-ball", USERNAME + " roll the 8-ball"]
#These will trigger a response from replystringa
REPLYSTRINGA = ["Yes.", "No.", "That's a stupid question.", "Maybe some day.", "Try asking again.", "You should ask the admins."]
#This is a list of potential replies. Will be randomized.

TRIGGERSTRINGB = [USERNAME + " is dumb"]
#A second set of triggers
REPLYSTRINGB = ["No you."]
#A second set of responses. Will be randomized

TRIGGERLIST = [TRIGGERSTRINGA, TRIGGERSTRINGB]
REPLYLIST = [REPLYSTRINGA, REPLYSTRINGB]
#You can also add a third or fourth set of triggers and responses. Just make sure to add them to TRIGGERLIST and REPLYLIST
#The first list in TRIGGERLIST goes to the first list in REPLYLIST. Keep them in order.
#Triggerlist and Replylist must have the same number of items

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
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
print("Logging in " + USERNAME)
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
    print('Scanning ' + SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    comments = subreddit.get_comments(limit=MAXPOSTS)
    for comment in comments:
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [comment.id])
        if not cur.fetchone():
            cbody = comment.body.lower()
            response = ''
            for m in range(len(TRIGGERLIST)):
                if any(trigger.lower() in cbody for trigger in TRIGGERLIST[m]) and response == '':
                    print(comment.id)
                    random.shuffle(REPLYLIST[m])
                    response = REPLYLIST[m][0]
            if response != '':
                print('\tPosting response')
                comment.reply(response)
                cur.execute('INSERT INTO oldposts VALUES(?)',[comment.id])
        sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)