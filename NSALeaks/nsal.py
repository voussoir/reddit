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
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subs, use "sub1+sub2+sub3+...". For all use "all"
KEYWORDS = ["snowden", "greenwald", "nsa"]
#Any comment containing these words will be saved.
KEYDOMAINS = ["theguardian.com", "techdirt.com"]

SUBDUMP = True
#Do you want the bot to dump into a subreddit as posts? Use True or False (Use capitals! No quotations!)
DSUB = "Test"
#If SUBDUMP is set to True, you will need to choose a subreddit to submit to.
ALLOWSELF = False
#Do you want the bot to dump selfposts? Use True or False (Use capitals! No quotations!)
DISTINGUISHPOST = False
#Do you want the bot to mod-distinguish the post?
TITLE = "_subreddit_: _ptitle_"
#This is the title of the submission to your dump
#Leave blank to keep the original post's title
#Otherwise, use these injectors to create dynamic title:
#_subreddit_ = subreddit of original post
#_author_ = OP of original post
#_ptitle_ = Title of original post


MAXPOSTS = 100
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.


'''All done!'''




WAITS = str(WAIT)
try:
    import bot #This is a file in my python library which contains my Bot's username and password. I can push code to Git without showing credentials
    USERNAME = bot.getu7()
    PASSWORD = bot.getp7()
    USERAGENT = bot.getaG()
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS oldlinks(ID TEXT)')
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
        plink = post.permalink
        if not post.is_self or ALLOWSELF == False:
            ptitle = post.title
            purl = post.url
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('SELECT * FROM oldlinks WHERE ID=?', [purl])
                if not cur.fetchone():
                    if any(key.lower() in ptitle.lower() for key in KEYWORDS) and any(key.lower() in purl.lower() for key in KEYDOMAINS):
                        try:
                            pauthor = post.author.name
                            psub = post.subreddit.display_name
                            print(pid + ', ' + pauthor)
                            if TITLE == "":
                                newtitle = ptitle
                            else:
                                newtitle = TITLE
                                newtitle = newtitle.replace('_ptitle_', ptitle)
                                newtitle = newtitle.replace('_author_', pauthor)
                                newtitle = newtitle.replace('_subreddit_', psub)

                            if SUBDUMP == True:
                                print('\tDumping to ' + DSUB)
                                create = r.submit(DSUB, newtitle, url=purl, captcha = None)
                                print('\tCreated post ' + create.id)
                                if DISTINGUISHPOST == True:
                                    print('\tDistinguishing post')
                                    create.distinguish()
                        except AttributeError:
                            print(pid + ': Author deleted. Ignoring')
                    cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                    cur.execute('INSERT INTO oldlinks VALUES(?)', [purl])
                else:
                    print(pid + ': Already linked somewhere else')  
        else:
            print(pid + ': Ignoring selfpost')
        
    sql.commit()

while True:
    try:
        scanSub()
    except Exception as e:
        print('An error has occured:', str(e))
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
 