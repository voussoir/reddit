#/u/GoldenSights
import praw
import time
import traceback
import sqlite3

'''USER CONFIGURATION'''

APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "all"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = ["flying cat"]
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
POSTTITLE = "_author_ in /r/_subreddit_"
#This is the title of the post that will go in DSUB
#You may use the following injectors to create a dynamic title
#_author_
#_subreddit_
#_score_

MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot
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
 r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
 r.refresh_access_information(APP_REFRESH) 

def scan_sub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    result = []
    authors = []
    for post in posts:
        pid = post.id
        pbody = post.body.lower()
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            if KEYWORDS == [] or any(key.lower() in pbody for key in KEYWORDS):
                try:
                    pauthor = post.author.name
                    print(pid + ', ' + pauthor)
                    plink = post.permalink
                    result.append(plink)
                    authors.append(pauthor + ' in /r/' + post.subreddit.display_name)
                    if RSAVE is True:
                        submission = post.submission
                        submission.save()
                        print('\tSaved submission')
                    if SUBDUMP is True:
                        newtitle = POSTTITLE
                        newtitle = newtitle.replace('_author_', pauthor)
                        newtitle = newtitle.replace('_subreddit_', post.subreddit.display_name)
                        newtitle = newtitle.replace('_score_', str(post.score) + ' points')
                        create = r.submit(DSUB, newtitle, url=plink, captcha = None)
                        print('\tDumped to ' + DSUB)
                except AttributeError:
                    print(pid + ': Author deleted. Ignoring comment')
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])    
    if len(result) > 0 and MAILME is True:
        for m in range(len(result)):
            result[m] = '- [' + authors[m] + '](' + result[m] + ')'
        r.send_message(RECIPIENT, MTITLE, MHEADER + '\n\n' + '\n\n'.join(result), captcha=None)
        print('Mailed ' + RECIPIENT)
        
    sql.commit()

while True:
    try:
        scan_sub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 