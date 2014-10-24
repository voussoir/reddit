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
PARENTSTRING = "beetlejuice"
#This is the string you're looking for
REPLYSTRING = "We are deeply sorry, but Mr. Beetlejuice can't join you in this comment thread right now. Would you like to leave a message?"
#This will be put in reply
DEPTHREQ = 3
#How many comments down to take action
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

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT, DEPTH INT)')
print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
    print('Scanning ' + SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    comments = list(subreddit.get_comments(limit=MAXPOSTS))
    for comment in comments:
        cid = comment.fullname
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [cid])
        if not cur.fetchone():
            try:
                cauthor = comment.author.name
                if cauthor.lower() != USERNAME.lower():
                    cbody = comment.body.lower()
                    if PARENTSTRING.lower() in cbody:
                        if 't3_' in comment.parent_id:
                            #is a root comment on the post
                            cdepth = 0
                        else:
                            cur.execute('SELECT * FROM oldposts WHERE ID=?', [comment.parent_id])
                            fetch = cur.fetchone()
                            if not fetch:
                                cdepth = 0
                            else:
                                cdepth = fetch[1] + 1
                        print(cid, '- Depth:', cdepth)

                        if cdepth >= DEPTHREQ-1:
                            print('\tAttempting to reply')
                            cur.execute('SELECT * FROM oldposts WHERE ID=?', [comment.link_id])
                            if cur.fetchone():
                                print('\tAlready posted in this thread')
                            else:
                                comment.reply(REPLYSTRING)
                                print('\tSuccess')
                                cur.execute('INSERT INTO oldposts VALUES(?, ?)', [comment.link_id, 0])
                    else:
                        #Does not contain interest
                        cdepth = -1
                        print(cid, '- Depth:', cdepth)
                else:
                    #Will not reply to self
                    cdepth=-1
                    pass
            except AttributeError:
                #Author is deleted
                cdepth = 0
            cur.execute('INSERT INTO oldposts VALUES(?, ?)', [cid, cdepth])
        sql.commit()


while True:
    try:
        scanSub()
    except AttributeError as e:
        print('An error has occured:', e)
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)

    