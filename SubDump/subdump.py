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
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS ["flying cat"]
#Any comment containing these words will be saved.

RSAVE = False
#Do you want the bot to save via Reddit Saving? Use True or False (Use capitals! no quotations!)
#praw DOES NOT allow comments to be saved. Don't ask me why. This will save the submission the comment is connected to.

MAILME = False
#Do you want the bot to send you a PM when it gets something? Use True or False (Use capitals! No quotations!)
RECIPIENT = "GoldenSights"
#If MAILME is set to True, you will need a name for the PM to go to
MTITLE = "SubDump automated message"
#If MAILME is set to True, you will need the PM to have a subject line.
MHEADER = "Comments containing your keywords:"
#This is part of the message body, on a line above the list of results. You can set it to "" if you just want the list by itself.


SUBDUMP = False
#Do you want the bot to dump into a subreddit as posts? Use True or False (Use capitals! No quotations!)
DSUB = "GoldTesting"
#If SUBDUMP is set to True, you will need to choose a subreddit to submit to.

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

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    result = []
    authors = []
    for post in posts:
        pid = post.id
        plink = post.permalink
        pbody = post.body
        cur.execute('SELECT * FROM oldposts WHERE ID="%s"' % pid)
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES("%s")' % pid)    
            if any(key.lower() in pbody for key in KEYWORDS):
                try:
                    pauthor = post.author.name
                    print(pid + ', ' + pauthor)
                    result.append(plink)
                    authors.append(pauthor + ' in /r/' + post.submission.subreddit.display_name)
                    if RSAVE == True:
                        submission = post.submission
                        submission.save()
                        print('\tSaved submission')
                    if SUBDUMP == True:
                        create = r.submit(DSUB, pauthor + ' in /r/' + post.submission.subreddit.display_name, url=plink, captcha = None)
                        print('\tDumped to ' + DSUB)
                except AttributeError:
                    print(pid + ': Author deleted. Ignoring comment')
    if len(result) > 0 and MAILME == True:
        for m in range(len(result)):
            result[m] = '- [' + authors[m] + '](' + result[m] + ')'
        r.send_message(RECIPIENT, MTITLE, MHEADER + '\n\n' + '\n\n'.join(result), captcha=None)
        print('Mailed ' + RECIPIENT)
        
    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 